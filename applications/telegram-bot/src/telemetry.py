import atexit
import copy
import os
import re
import sys
import threading
from contextlib import AbstractContextManager
from dataclasses import dataclass
from functools import wraps
from importlib.metadata import version
from time import monotonic, perf_counter, time_ns
from typing import Any, Callable, TypeVar

from loguru import logger
from opentelemetry import context
from opentelemetry._logs import SeverityNumber
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.system_metrics import SystemMetricsInstrumentor
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, LogRecordExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import MetricReader, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import OTELResourceDetector, Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    SpanExportResult,
    SpanExporter,
)
from opentelemetry.trace import SpanKind, Status, StatusCode


_F = TypeVar("_F", bound=Callable[..., Any])
_TELEGRAM_TOKEN_PATH = re.compile(r"/bot[^/]+")
_SQL_ATTRIBUTES = {"db.statement", "db.query.text"}
_runtime: "TelemetryRuntime | None" = None
_runtime_lock = threading.Lock()


class _SanitizingSpanExporter(SpanExporter):
    def __init__(self, exporter: SpanExporter) -> None:
        self._exporter = exporter

    def export(self, spans: list[ReadableSpan]) -> SpanExportResult:
        sanitized_spans = []
        for span in spans:
            sanitized = copy.copy(span)
            sanitized._attributes = {
                key: value
                for key, value in (span.attributes or {}).items()
                if key not in _SQL_ATTRIBUTES
            }
            sanitized_spans.append(sanitized)
        return self._exporter.export(sanitized_spans)

    def shutdown(self) -> None:
        self._exporter.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return self._exporter.force_flush(timeout_millis)


@dataclass(frozen=True)
class _MetricInstruments:
    command_executions: Any
    command_failures: Any
    command_duration: Any
    callback_executions: Any
    callback_failures: Any
    callback_duration: Any
    scheduler_executions: Any
    scheduler_failures: Any
    scheduler_duration: Any


class TelemetryRuntime:
    def __init__(
        self,
        tracer_provider: TracerProvider,
        meter_provider: MeterProvider,
        logger_provider: LoggerProvider,
        log_sink_id: int,
        auto_instrumentation_enabled: bool,
    ) -> None:
        self.tracer_provider = tracer_provider
        self.meter_provider = meter_provider
        self.logger_provider = logger_provider
        self.log_sink_id = log_sink_id
        self.auto_instrumentation_enabled = auto_instrumentation_enabled
        self.tracer = tracer_provider.get_tracer("telegram-bot")
        meter = meter_provider.get_meter("telegram-bot")
        self.metrics = _MetricInstruments(
            command_executions=meter.create_counter("telegram.command.executions"),
            command_failures=meter.create_counter("telegram.command.failures"),
            command_duration=meter.create_histogram(
                "telegram.command.duration", unit="s"
            ),
            callback_executions=meter.create_counter("telegram.callback.executions"),
            callback_failures=meter.create_counter("telegram.callback.failures"),
            callback_duration=meter.create_histogram(
                "telegram.callback.duration", unit="s"
            ),
            scheduler_executions=meter.create_counter("scheduler.job.executions"),
            scheduler_failures=meter.create_counter("scheduler.job.failures"),
            scheduler_duration=meter.create_histogram(
                "scheduler.job.duration", unit="s"
            ),
        )
        self._sqlalchemy_instrumentor: SQLAlchemyInstrumentor | None = None
        self._instrumented_engine_ids: set[int] = set()
        self._shutdown = False

    def instrument_sqlalchemy(self, async_engine: Any) -> None:
        engine = async_engine.sync_engine
        engine_id = id(engine)
        if engine_id in self._instrumented_engine_ids:
            return
        instrumentor = SQLAlchemyInstrumentor()
        instrumentor.instrument(
            engine=engine,
            tracer_provider=self.tracer_provider,
            meter_provider=self.meter_provider,
            enable_commenter=False,
        )
        self._sqlalchemy_instrumentor = instrumentor
        self._instrumented_engine_ids.add(engine_id)

    def force_flush(self, timeout_seconds: float = 5) -> bool:
        deadline = monotonic() + timeout_seconds
        providers = (self.tracer_provider, self.logger_provider, self.meter_provider)
        result = True
        for provider in providers:
            remaining = max(0, int((deadline - monotonic()) * 1000))
            try:
                flushed = remaining > 0 and provider.force_flush(
                    timeout_millis=remaining
                )
            except Exception:
                flushed = False
            if not flushed:
                result = False
        return result

    def shutdown(self, timeout_seconds: float = 5) -> None:
        if self._shutdown:
            return
        self._shutdown = True
        try:
            logger.remove(self.log_sink_id)
        except ValueError:
            pass
        try:
            if self.auto_instrumentation_enabled:
                HTTPXClientInstrumentor().uninstrument()
                SystemMetricsInstrumentor().uninstrument()
            if self._sqlalchemy_instrumentor is not None:
                self._sqlalchemy_instrumentor.uninstrument()
        except Exception:
            pass
        self.force_flush(timeout_seconds=max(0.1, timeout_seconds / 2))
        _run_with_timeout(
            lambda: (
                self.tracer_provider.shutdown(),
                self.logger_provider.shutdown(),
                self.meter_provider.shutdown(
                    timeout_millis=int(timeout_seconds * 1000)
                ),
            ),
            timeout_seconds=max(0.1, timeout_seconds / 2),
        )


class _OperationObservation(AbstractContextManager):
    def __init__(self, kind: str, name: str) -> None:
        self.kind = kind
        self.name = name
        self.runtime = _runtime
        self._span_context = None
        self.span = None
        self.started_at = 0.0
        self.failed = False

    def __enter__(self) -> "_OperationObservation":
        self.started_at = perf_counter()
        if self.runtime is not None:
            span_name, attribute_name = _operation_span_fields(self.kind)
            self._span_context = self.runtime.tracer.start_as_current_span(
                span_name,
                kind=_operation_span_kind(self.kind),
                attributes={attribute_name: self.name},
                record_exception=False,
                set_status_on_exception=False,
            )
            self.span = self._span_context.__enter__()
        return self

    def record_error(self, error: BaseException) -> None:
        self.failed = True
        if self.span is not None:
            self.span.record_exception(error)
            self.span.set_status(Status(StatusCode.ERROR))

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        if exc_value is not None:
            self.record_error(exc_value)
        outcome = "error" if self.failed else "success"
        if self.span is not None:
            self.span.set_attribute("operation.outcome", outcome)
        if self.runtime is not None:
            _record_operation_metrics(
                self.runtime.metrics,
                self.kind,
                self.name,
                outcome,
                perf_counter() - self.started_at,
            )
        if self._span_context is not None:
            self._span_context.__exit__(None, None, None)
        return False


def _resource() -> Resource:
    defaults = {
        "service.name": "telegram-bot",
        "service.namespace": "homelab",
        "deployment.environment.name": "production",
        "service.version": version("telegram-bot"),
    }
    resource = Resource.create(defaults).merge(OTELResourceDetector().detect())
    service_name = os.getenv("OTEL_SERVICE_NAME")
    if service_name:
        resource = resource.merge(Resource({"service.name": service_name}))
    return resource


def _create_runtime(
    span_exporter: SpanExporter,
    metric_reader: MetricReader,
    log_exporter: LogRecordExporter,
    enable_auto_instrumentation: bool,
) -> TelemetryRuntime:
    resource = _resource()
    meter_provider = MeterProvider(
        metric_readers=[metric_reader], resource=resource, shutdown_on_exit=False
    )
    tracer_provider = TracerProvider(
        resource=resource, shutdown_on_exit=False, meter_provider=meter_provider
    )
    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            _SanitizingSpanExporter(span_exporter), meter_provider=meter_provider
        )
    )
    logger_provider = LoggerProvider(
        resource=resource, shutdown_on_exit=False, meter_provider=meter_provider
    )
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(log_exporter, meter_provider=meter_provider)
    )
    otel_logger = logger_provider.get_logger("telegram-bot.loguru")

    def emit_loguru(message: Any) -> None:
        record = message.record
        otel_logger.emit(
            timestamp=time_ns(),
            context=context.get_current(),
            severity_number=_severity_number(record["level"].name),
            severity_text=record["level"].name,
            body=record["message"],
        )

    sink_id = logger.add(emit_loguru, level="INFO", format="{message}", catch=True)
    runtime = TelemetryRuntime(
        tracer_provider,
        meter_provider,
        logger_provider,
        sink_id,
        enable_auto_instrumentation,
    )
    try:
        if enable_auto_instrumentation:
            HTTPXClientInstrumentor().instrument(
                tracer_provider=tracer_provider,
                meter_provider=meter_provider,
                request_hook=_httpx_request_hook,
                async_request_hook=_httpx_async_request_hook,
            )
            SystemMetricsInstrumentor(config=_process_metric_config()).instrument(
                meter_provider=meter_provider
            )
    except Exception:
        runtime.shutdown(timeout_seconds=0.1)
        raise
    return runtime


def _build_otlp_runtime() -> TelemetryRuntime:
    return _create_runtime(
        span_exporter=OTLPSpanExporter(),
        metric_reader=PeriodicExportingMetricReader(OTLPMetricExporter()),
        log_exporter=OTLPLogExporter(),
        enable_auto_instrumentation=True,
    )


def initialize_telemetry() -> TelemetryRuntime | None:
    global _runtime
    if not os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        return None
    with _runtime_lock:
        if _runtime is not None:
            return _runtime
        try:
            _runtime = _build_otlp_runtime()
            atexit.register(shutdown_telemetry)
        except Exception as error:
            sys.stderr.write(f"OpenTelemetry 초기화 실패: {error}\n")
            _runtime = None
        return _runtime


def shutdown_telemetry(timeout_seconds: float = 5) -> None:
    global _runtime
    with _runtime_lock:
        runtime = _runtime
        _runtime = None
    if runtime is not None:
        runtime.shutdown(timeout_seconds=timeout_seconds)


def instrument_sqlalchemy_engine(async_engine: Any) -> None:
    if _runtime is not None:
        _runtime.instrument_sqlalchemy(async_engine)


def instrument_command(command: str) -> Callable[[_F], _F]:
    return _instrument_async_operation("command", command)


def instrument_callback(callback_type: str) -> Callable[[_F], _F]:
    return _instrument_async_operation("callback", callback_type)


def observe_scheduler_job(job: str) -> _OperationObservation:
    return _OperationObservation("scheduler", job)


def observe_bot_initialization() -> _OperationObservation:
    return _OperationObservation("initialization", "bot")


def _instrument_async_operation(kind: str, name: str) -> Callable[[_F], _F]:
    def decorator(function: _F) -> _F:
        @wraps(function)
        async def wrapped(*args: Any, **kwargs: Any) -> Any:
            with _OperationObservation(kind, name):
                return await function(*args, **kwargs)

        return wrapped

    return decorator


def _operation_span_fields(kind: str) -> tuple[str, str]:
    if kind == "command":
        return "telegram.command", "telegram.command.name"
    if kind == "callback":
        return "telegram.callback", "telegram.callback.type"
    if kind == "scheduler":
        return "scheduler.job", "scheduler.job.name"
    return "bot.initialize", "bot.operation"


def _operation_span_kind(kind: str) -> SpanKind:
    if kind in {"command", "callback"}:
        return SpanKind.CONSUMER
    return SpanKind.INTERNAL


def _record_operation_metrics(
    instruments: _MetricInstruments,
    kind: str,
    name: str,
    outcome: str,
    duration: float,
) -> None:
    if kind == "initialization":
        return
    if kind == "command":
        label, executions, failures, histogram = (
            "command",
            instruments.command_executions,
            instruments.command_failures,
            instruments.command_duration,
        )
    elif kind == "callback":
        label, executions, failures, histogram = (
            "callback_type",
            instruments.callback_executions,
            instruments.callback_failures,
            instruments.callback_duration,
        )
    else:
        label, executions, failures, histogram = (
            "job",
            instruments.scheduler_executions,
            instruments.scheduler_failures,
            instruments.scheduler_duration,
        )
    attributes = {label: name, "outcome": outcome}
    executions.add(1, attributes)
    histogram.record(duration, attributes)
    if outcome == "error":
        failures.add(1, {label: name})


def _severity_number(level: str) -> SeverityNumber:
    return {
        "TRACE": SeverityNumber.TRACE,
        "DEBUG": SeverityNumber.DEBUG,
        "INFO": SeverityNumber.INFO,
        "SUCCESS": SeverityNumber.INFO2,
        "WARNING": SeverityNumber.WARN,
        "ERROR": SeverityNumber.ERROR,
        "CRITICAL": SeverityNumber.FATAL,
    }.get(level, SeverityNumber.INFO)


def _httpx_request_hook(span: Any, request: Any) -> None:
    if not span or not span.is_recording():
        return
    safe_url = _sanitize_http_url(str(request.url))
    span.set_attribute("url.full", safe_url)
    span.set_attribute("http.url", safe_url)


async def _httpx_async_request_hook(span: Any, request: Any) -> None:
    _httpx_request_hook(span, request)


def _sanitize_http_url(url: str) -> str:
    return _TELEGRAM_TOKEN_PATH.sub("/bot[REDACTED]", url).split("?", 1)[0]


def _process_metric_config() -> dict[str, list[str] | None]:
    return {
        "process.cpu.time": ["user", "system"],
        "process.cpu.utilization": None,
        "process.memory.usage": None,
        "process.memory.virtual": None,
        "process.thread.count": None,
        "cpython.gc.collections": None,
        "cpython.gc.collected_objects": None,
        "cpython.gc.uncollectable_objects": None,
    }


def _run_with_timeout(function: Callable[[], Any], timeout_seconds: float) -> None:
    def run() -> None:
        try:
            function()
        except Exception:
            pass

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    thread.join(timeout_seconds)
