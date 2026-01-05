import discord
from discord import TextChannel
from loguru import logger

from .constants import LOTTO
from .week_utils import get_current_lotto_week_key
from src.db.connection import get_engine
from src.db.lotto import AsyncQuerier


def create_reminder_message() -> dict:
    embed = discord.Embed(
        title="🎰 로또 구매 알림",
        description="이번 주 로또를 아직 구매하지 않았습니다!\n행운의 번호를 선택하고 구매를 완료하세요.",
        color=0xFFD700,
    )
    embed.add_field(
        name="📅 마감 안내",
        value="토요일 오후 6시 이전까지 구매해야 합니다.",
        inline=False,
    )
    embed.set_footer(text="구매 후 아래 버튼을 눌러주세요")
    embed.timestamp = discord.utils.utcnow()

    view = discord.ui.View()
    view.add_item(
        discord.ui.Button(
            label="구매하러 가기",
            style=discord.ButtonStyle.link,
            url=LOTTO.PURCHASE_URL,
            emoji="🔗",
        )
    )
    view.add_item(
        discord.ui.Button(
            label=LOTTO.MESSAGES.BUTTON_LABEL,
            style=discord.ButtonStyle.success,
            custom_id=LOTTO.BUTTON_ID,
            emoji="✅",
        )
    )

    return {"embed": embed, "view": view}


async def send_reminder_if_needed(channel: TextChannel) -> None:
    current_week_key = get_current_lotto_week_key()

    engine = get_engine()
    async with engine.connect() as conn:
        querier = AsyncQuerier(conn)
        existing_purchase = await querier.find_purchase_by_week_key(
            week_key=current_week_key
        )

    if existing_purchase:
        logger.info(f"이번 주({current_week_key}) 이미 구매 완료됨. 알림 스킵.")
        return

    message = create_reminder_message()
    await channel.send(embed=message["embed"], view=message["view"])
    logger.info(f"알림 전송 완료: {discord.utils.utcnow().isoformat()}")
