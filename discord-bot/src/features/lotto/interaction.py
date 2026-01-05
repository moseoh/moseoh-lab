import discord
from loguru import logger

from .constants import LOTTO
from .week_utils import get_current_lotto_week_key
from src.db.connection import get_engine
from src.db.lotto import AsyncQuerier


async def handle_purchase_button(interaction: discord.Interaction) -> None:
    if interaction.data.get("custom_id") != LOTTO.BUTTON_ID:
        return

    user_id = str(interaction.user.id)
    user_name = interaction.user.name
    current_week_key = get_current_lotto_week_key()

    engine = get_engine()
    async with engine.connect() as conn:
        querier = AsyncQuerier(conn)

        # 중복 구매 확인
        existing_purchase = await querier.find_purchase_by_user_and_week(
            user_id=user_id, week_key=current_week_key
        )

        if existing_purchase:
            await interaction.response.send_message(
                LOTTO.MESSAGES.ALREADY_PURCHASED, ephemeral=True
            )
            return

        # 구매 기록 저장
        await querier.create_purchase(
            user_id=user_id, user_name=user_name, week_key=current_week_key
        )
        await conn.commit()

    await interaction.response.send_message(
        LOTTO.MESSAGES.PURCHASE_SUCCESS, ephemeral=True
    )
    logger.info(f"구매 완료 기록: {user_name} ({user_id})")
