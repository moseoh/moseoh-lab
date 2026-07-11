import asyncio
from types import SimpleNamespace

import pytest
import httpx
from loguru import logger
from opentelemetry.sdk._logs.export import InMemoryLogRecordExporter
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from src import telemetry


def _metric_points(reader: InMemoryMetricReader, name: str):
    metrics_data = reader.get_metrics_data()
    for resource_metrics in metrics_data.resource_metrics:
        for scope_metrics in resource_metrics.scope_metrics:
            for metric in scope_metrics.metrics:
                if metric.name == name:
                    return list(metric.data.data_points)
    return []


@pytest.fixture
def telemetry_runtime(monkeypatch):
    span_exporter = InMemorySpanExporter()
    metric_reader = InMemoryMetricReader()
    log_exporter = InMemoryLogRecordExporter()
    runtime = telemetry._create_runtime(
        span_exporter=span_exporter,
        metric_reader=metric_reader,
        log_exporter=log_exporter,
        enable_auto_instrumentation=False,
    )
    monkeypatch.setattr(telemetry, "_runtime", runtime)
    yield runtime, span_exporter, metric_reader, log_exporter
    runtime.shutdown(timeout_seconds=1)


def test_endpoint가_없으면_telemetry를_초기화하지_않는다(monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    monkeypatch.setattr(telemetry, "_runtime", None)

    assert telemetry.initialize_telemetry() is None


def test_endpoint가_있으면_runtime을_한번만_초기화한다(monkeypatch, telemetry_runtime):
    runtime, *_ = telemetry_runtime
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-gateway:4317")
    monkeypatch.setattr(telemetry, "_runtime", None)
    calls = 0

    def build_runtime():
        nonlocal calls
        calls += 1
        return runtime

    monkeypatch.setattr(telemetry, "_build_otlp_runtime", build_runtime)

    assert telemetry.initialize_telemetry() is runtime
    assert telemetry.initialize_telemetry() is runtime
    assert calls == 1


def test_초기화_실패가_애플리케이션으로_전파되지_않는다(monkeypatch, capsys):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-gateway:4317")
    monkeypatch.setattr(telemetry, "_runtime", None)

    def fail():
        raise RuntimeError("초기화 실패")

    monkeypatch.setattr(telemetry, "_build_otlp_runtime", fail)

    assert telemetry.initialize_telemetry() is None
    assert "OpenTelemetry 초기화 실패" in capsys.readouterr().err


def test_부분_초기화_실패가_loguru_sink를_남기지_않는다(monkeypatch, capsys):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-gateway:4317")
    monkeypatch.setattr(telemetry, "_runtime", None)
    initial_handlers = len(logger._core.handlers)

    def fail_instrumentation(self, **kwargs):
        raise RuntimeError("자동 계측 실패")

    monkeypatch.setattr(
        telemetry.SystemMetricsInstrumentor,
        "instrument",
        fail_instrumentation,
    )

    assert telemetry.initialize_telemetry() is None
    assert len(logger._core.handlers) == initial_handlers
    assert "OpenTelemetry 초기화 실패" in capsys.readouterr().err


@pytest.mark.asyncio
async def test_command_성공과_실패를_span과_metric으로_기록한다(telemetry_runtime):
    runtime, span_exporter, metric_reader, _ = telemetry_runtime

    @telemetry.instrument_command("start")
    async def success():
        return "ok"

    @telemetry.instrument_command("lotto_status")
    async def failure():
        raise RuntimeError("실패")

    assert await success() == "ok"
    with pytest.raises(RuntimeError):
        await failure()

    assert runtime.force_flush(timeout_seconds=1)
    spans = span_exporter.get_finished_spans()
    assert [span.name for span in spans] == ["telegram.command", "telegram.command"]
    assert spans[0].attributes == {
        "telegram.command.name": "start",
        "operation.outcome": "success",
    }
    assert spans[1].attributes["telegram.command.name"] == "lotto_status"
    assert spans[1].attributes["operation.outcome"] == "error"
    assert spans[1].status.is_ok is False

    execution_points = _metric_points(metric_reader, "telegram.command.executions")
    failure_points = _metric_points(metric_reader, "telegram.command.failures")
    duration_points = _metric_points(metric_reader, "telegram.command.duration")
    assert {tuple(sorted(point.attributes.items())) for point in execution_points} == {
        (("command", "lotto_status"), ("outcome", "error")),
        (("command", "start"), ("outcome", "success")),
    }
    assert failure_points[0].attributes == {"command": "lotto_status"}
    assert len(duration_points) == 2


@pytest.mark.asyncio
async def test_callback_성공과_실패를_metric으로_기록한다(telemetry_runtime):
    _, _, metric_reader, _ = telemetry_runtime

    @telemetry.instrument_callback("purchase_complete")
    async def success():
        return None

    @telemetry.instrument_callback("purchase_complete")
    async def failure():
        raise RuntimeError("실패")

    await success()
    with pytest.raises(RuntimeError):
        await failure()

    assert len(_metric_points(metric_reader, "telegram.callback.executions")) == 2
    assert len(_metric_points(metric_reader, "telegram.callback.failures")) == 1
    assert len(_metric_points(metric_reader, "telegram.callback.duration")) == 2


def test_scheduler의_잡힌_오류도_error로_기록한다(telemetry_runtime):
    runtime, span_exporter, metric_reader, _ = telemetry_runtime

    with telemetry.observe_scheduler_job("weekday_reminder") as observation:
        observation.record_error(RuntimeError("전송 실패"))

    assert runtime.force_flush(timeout_seconds=1)
    span = span_exporter.get_finished_spans()[0]
    assert span.name == "scheduler.job"
    assert span.attributes == {
        "scheduler.job.name": "weekday_reminder",
        "operation.outcome": "error",
    }
    assert len(_metric_points(metric_reader, "scheduler.job.executions")) == 1
    assert len(_metric_points(metric_reader, "scheduler.job.failures")) == 1
    assert len(_metric_points(metric_reader, "scheduler.job.duration")) == 1


def test_loguru_log가_현재_span과_연결된다(telemetry_runtime):
    runtime, span_exporter, _, log_exporter = telemetry_runtime

    with runtime.tracer.start_as_current_span("telegram.command") as span:
        logger.info("계측 테스트")

    assert runtime.force_flush(timeout_seconds=1)
    log_record = log_exporter.get_finished_logs()[0].log_record
    assert log_record.trace_id == span.get_span_context().trace_id
    assert log_record.span_id == span.get_span_context().span_id
    assert log_record.body == "계측 테스트"
    assert span_exporter.get_finished_spans()[0].name == "telegram.command"


def test_metric_attribute에_식별정보가_포함되지_않는다(telemetry_runtime):
    _, _, metric_reader, _ = telemetry_runtime

    async def run():
        @telemetry.instrument_command("start")
        async def command():
            return None

        await command()

    asyncio.run(run())
    forbidden = {"user_id", "chat_id", "message_id", "request_id", "username"}
    for name in (
        "telegram.command.executions",
        "telegram.command.duration",
    ):
        for point in _metric_points(metric_reader, name):
            assert forbidden.isdisjoint(point.attributes)


def test_표준_resource_환경변수가_기본값보다_우선한다(monkeypatch):
    monkeypatch.setenv("OTEL_SERVICE_NAME", "custom-bot")
    monkeypatch.setenv(
        "OTEL_RESOURCE_ATTRIBUTES",
        "service.namespace=custom,service.version=sha-123,deployment.environment.name=staging",
    )

    attributes = telemetry._resource().attributes

    assert attributes["service.name"] == "custom-bot"
    assert attributes["service.namespace"] == "custom"
    assert attributes["service.version"] == "sha-123"
    assert attributes["deployment.environment.name"] == "staging"


def test_httpx_url에서_token과_query를_제거한다(telemetry_runtime):
    runtime, span_exporter, _, _ = telemetry_runtime
    with runtime.tracer.start_as_current_span("http") as span:
        telemetry._httpx_request_hook(
            span,
            SimpleNamespace(
                url="https://api.telegram.org/bot123456:SECRET/getUpdates?offset=99"
            ),
        )

    assert runtime.force_flush(timeout_seconds=1)
    attributes = span_exporter.get_finished_spans()[0].attributes
    assert attributes["url.full"] == "https://api.telegram.org/bot[REDACTED]/getUpdates"
    assert "SECRET" not in attributes["url.full"]
    assert "offset" not in attributes["url.full"]


@pytest.mark.asyncio
async def test_sqlalchemy_span에서_sql_원문을_제거한다(
    monkeypatch, telemetry_runtime, tmp_path
):
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    runtime, span_exporter, _, _ = telemetry_runtime
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'otel.sqlite3'}")
    runtime.instrument_sqlalchemy(engine)
    runtime.instrument_sqlalchemy(engine)

    async with engine.connect() as connection:
        await connection.execute(text("SELECT 'private-value'"))
    await engine.dispose()

    assert runtime.force_flush(timeout_seconds=1)
    spans = span_exporter.get_finished_spans()
    assert spans
    for span in spans:
        assert "db.statement" not in span.attributes
        assert "db.query.text" not in span.attributes
        assert "private-value" not in str(span.attributes)


def test_debug_log는_otel로_전송하지_않는다(telemetry_runtime):
    runtime, _, _, log_exporter = telemetry_runtime

    logger.debug("debug 로그")
    logger.info("info 로그")

    assert runtime.force_flush(timeout_seconds=1)
    bodies = [record.log_record.body for record in log_exporter.get_finished_logs()]
    assert bodies == ["info 로그"]


def test_force_flush_실패가_예외로_전파되지_않는다(monkeypatch, telemetry_runtime):
    runtime, *_ = telemetry_runtime

    def fail(timeout_millis):
        raise RuntimeError("flush 실패")

    original = runtime.tracer_provider.force_flush
    monkeypatch.setattr(runtime.tracer_provider, "force_flush", fail)
    try:
        assert runtime.force_flush(timeout_seconds=0.1) is False
    finally:
        monkeypatch.setattr(runtime.tracer_provider, "force_flush", original)


@pytest.mark.asyncio
async def test_async_httpx_계측이_token을_제거하고_요청을_방해하지_않는다():
    span_exporter = InMemorySpanExporter()
    runtime = telemetry._create_runtime(
        span_exporter=span_exporter,
        metric_reader=InMemoryMetricReader(),
        log_exporter=InMemoryLogRecordExporter(),
        enable_auto_instrumentation=True,
    )
    transport = httpx.MockTransport(lambda request: httpx.Response(200))

    try:
        async with httpx.AsyncClient(transport=transport) as client:
            HTTPXClientInstrumentor.instrument_client(
                client,
                tracer_provider=runtime.tracer_provider,
                meter_provider=runtime.meter_provider,
                request_hook=telemetry._httpx_async_request_hook,
            )
            response = await client.get(
                "https://api.telegram.org/bot123456:SECRET/getUpdates?offset=99"
            )
            HTTPXClientInstrumentor.uninstrument_client(client)
        assert response.status_code == 200
        assert runtime.force_flush(timeout_seconds=1)
        http_span = next(
            span
            for span in span_exporter.get_finished_spans()
            if span.kind.name == "CLIENT"
        )
        assert "SECRET" not in str(http_span.attributes)
        assert "offset=99" not in str(http_span.attributes)
    finally:
        runtime.shutdown(timeout_seconds=1)
