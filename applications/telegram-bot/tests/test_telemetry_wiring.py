from contextlib import nullcontext

import pytest

from src import bot, main
from src.db import connection
from src.features.lotto import scheduler


def test_application이_command와_callback_handler를_계측한다(monkeypatch):
    commands = []
    callbacks = []

    def command_decorator(name):
        commands.append(name)
        return lambda function: function

    def callback_decorator(name):
        callbacks.append(name)
        return lambda function: function

    monkeypatch.setattr(bot, "instrument_command", command_decorator)
    monkeypatch.setattr(bot, "instrument_callback", callback_decorator)

    bot.build_application("123456:test-token")

    assert commands == ["start", "lotto_enable", "lotto_disable", "lotto_status"]
    assert callbacks == ["purchase_complete"]


@pytest.mark.asyncio
async def test_bot_초기화를_span으로_계측한다(monkeypatch):
    entered = []

    class FakeBot:
        async def set_my_commands(self, commands):
            return None

    class FakeApplication:
        bot = FakeBot()
        bot_data = {}

    monkeypatch.setattr(
        bot,
        "observe_bot_initialization",
        lambda: nullcontext(entered.append("bot.initialize")),
    )
    monkeypatch.setattr(bot, "start_lotto_scheduler", lambda application: object())

    await bot.post_init(FakeApplication())

    assert entered == ["bot.initialize"]


@pytest.mark.asyncio
async def test_scheduler_job을_고정된_이름으로_계측한다(monkeypatch):
    jobs = []
    observed = []

    class FakeScheduler:
        def add_job(self, function, trigger, args):
            jobs.append((function, args))

        def start(self):
            return None

    class FakeConnectionContext:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, exc_type, exc_value, traceback):
            return False

    class FakeEngine:
        def connect(self):
            return FakeConnectionContext()

    class FakeQuerier:
        def __init__(self, connection):
            pass

        async def get_alarm_settings_by_type(self, alarm_type):
            if False:
                yield None

    monkeypatch.setattr(scheduler, "AsyncIOScheduler", FakeScheduler)
    monkeypatch.setattr(scheduler, "get_engine", lambda: FakeEngine())
    monkeypatch.setattr(scheduler, "AsyncQuerier", FakeQuerier)
    monkeypatch.setattr(
        scheduler,
        "observe_scheduler_job",
        lambda name: nullcontext(observed.append(name)),
    )

    created = scheduler.start_lotto_scheduler(object())
    await jobs[0][0](*jobs[0][1])
    await jobs[1][0](*jobs[1][1])

    assert isinstance(created, FakeScheduler)
    assert observed == ["weekday_reminder", "saturday_reminder"]


def test_async_engine의_sync_engine을_계측한다(monkeypatch, tmp_path):
    instrumented = []
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.sqlite3"))
    monkeypatch.setattr(connection, "_engine", None)
    monkeypatch.setattr(
        connection,
        "instrument_sqlalchemy_engine",
        lambda engine: instrumented.append(engine.sync_engine),
    )

    engine = connection.get_engine()
    assert connection.get_engine() is engine
    assert instrumented == [engine.sync_engine]


def test_main이_bot보다_먼저_telemetry를_초기화한다(monkeypatch):
    calls = []
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:test-token")
    monkeypatch.setattr(main, "initialize_telemetry", lambda: calls.append("telemetry"))
    monkeypatch.setattr(main, "run_bot", lambda token: calls.append("bot"))

    main.main()

    assert calls == ["telemetry", "bot"]
