import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from telegram.ext import Application

from .constants import LOTTO
from .notification import send_reminder_if_needed
from src.db.connection import get_engine
from src.db.settings import AsyncQuerier


def start_lotto_scheduler(application: Application) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    timezone = os.getenv("TZ", "Asia/Seoul")

    async def send_reminder(label: str) -> None:
        logger.info(f"스케줄 실행: {label}")
        engine = get_engine()
        async with engine.connect() as conn:
            querier = AsyncQuerier(conn)
            async for row in querier.get_alarm_settings_by_type(alarm_type=LOTTO.ALARM_TYPE):
                try:
                    await send_reminder_if_needed(application.bot, row.chat_id)
                except Exception as e:
                    logger.error(f"알림 전송 실패 (scope={row.scope_id}, chat={row.chat_id}): {e}")

    weekday_hours = ",".join(str(h) for h in LOTTO.WEEKDAY_HOURS)
    scheduler.add_job(
        send_reminder,
        CronTrigger(day_of_week="mon,tue,wed,thu,fri", hour=weekday_hours, minute=0, timezone=timezone),
        args=["월~금"],
    )

    saturday_hours = ",".join(str(h) for h in LOTTO.SATURDAY_HOURS)
    scheduler.add_job(
        send_reminder,
        CronTrigger(day_of_week="sat", hour=saturday_hours, minute=0, timezone=timezone),
        args=["토요일"],
    )

    scheduler.start()
    logger.info("로또 스케줄러 시작 완료")
    return scheduler
