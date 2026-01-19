import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import discord
from loguru import logger

from .constants import LOTTO
from .notification import send_reminder_if_needed
from src.db.connection import get_engine
from src.db.settings import AsyncQuerier

ALARM_TYPE = "lotto"


def start_lotto_scheduler(client: discord.Client) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    timezone = os.getenv("TZ", "Asia/Seoul")

    async def send_reminder(label: str):
        logger.info(f"스케줄 실행: {label}")

        engine = get_engine()
        async with engine.connect() as conn:
            querier = AsyncQuerier(conn)
            async for row in querier.get_alarm_settings_by_type(alarm_type=ALARM_TYPE):
                try:
                    channel = client.get_channel(int(row.channel_id))
                    if channel is None:
                        channel = await client.fetch_channel(int(row.channel_id))

                    if channel is None or not isinstance(channel, discord.TextChannel):
                        logger.warning(f"유효하지 않은 채널: {row.channel_id}")
                        continue

                    await send_reminder_if_needed(channel)
                except Exception as e:
                    logger.error(f"알림 전송 실패 (guild={row.guild_id}): {e}")

    # 월~금: 13시, 18시
    weekday_hours = ",".join(str(h) for h in LOTTO.WEEKDAY_HOURS)
    scheduler.add_job(
        send_reminder,
        CronTrigger(
            day_of_week="mon,tue,wed,thu,fri",
            hour=weekday_hours,
            minute=0,
            timezone=timezone,
        ),
        args=["월~금"],
    )
    logger.info(
        f"스케줄 등록: 월~금 {', '.join(str(h) for h in LOTTO.WEEKDAY_HOURS)}시 ({timezone})"
    )

    # 토요일: 12시~17시
    saturday_hours = ",".join(str(h) for h in LOTTO.SATURDAY_HOURS)
    scheduler.add_job(
        send_reminder,
        CronTrigger(
            day_of_week="sat",
            hour=saturday_hours,
            minute=0,
            timezone=timezone,
        ),
        args=["토요일"],
    )
    logger.info(
        f"스케줄 등록: 토요일 {', '.join(str(h) for h in LOTTO.SATURDAY_HOURS)}시 ({timezone})"
    )

    scheduler.start()
    return scheduler
