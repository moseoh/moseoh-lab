from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes

from .constants import LOTTO
from .week_utils import get_current_lotto_week_key
from src.db.connection import get_engine
from src.db.lotto import AsyncQuerier


async def handle_purchase_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or query.data != LOTTO.BUTTON_ID:
        return

    user = query.from_user
    user_id = str(user.id)
    user_name = user.full_name or user.username or user.first_name
    current_week_key = get_current_lotto_week_key()

    engine = get_engine()
    async with engine.connect() as conn:
        querier = AsyncQuerier(conn)
        existing_purchase = await querier.find_purchase_by_user_and_week(
            user_id=user_id, week_key=current_week_key
        )

        if existing_purchase:
            await query.answer(LOTTO.MESSAGES.ALREADY_PURCHASED, show_alert=True)
            return

        await querier.create_purchase(
            user_id=user_id, user_name=user_name, week_key=current_week_key
        )
        await conn.commit()

    await query.answer(LOTTO.MESSAGES.PURCHASE_SUCCESS, show_alert=True)
    logger.info(f"구매 완료 기록: {user_name} ({user_id})")
