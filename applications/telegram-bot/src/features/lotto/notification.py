from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from loguru import logger

from .constants import LOTTO
from .week_utils import get_current_lotto_week_key
from src.db.connection import get_engine
from src.db.lotto import AsyncQuerier


def create_reminder_message() -> tuple[str, InlineKeyboardMarkup]:
    text = (
        "🎰 <b>로또 구매 알림</b>\n\n"
        "이번 주 로또를 아직 구매하지 않았습니다!\n"
        "행운의 번호를 선택하고 구매를 완료하세요.\n\n"
        "📅 <b>마감 안내</b>\n"
        "토요일 오후 6시 이전까지 구매해야 합니다.\n\n"
        "구매 후 아래 버튼을 눌러주세요."
    )
    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("구매하러 가기", url=LOTTO.PURCHASE_URL),
            InlineKeyboardButton(LOTTO.MESSAGES.BUTTON_LABEL, callback_data=LOTTO.BUTTON_ID),
        ]]
    )
    return text, keyboard


async def send_reminder_if_needed(bot, chat_id: str) -> None:
    current_week_key = get_current_lotto_week_key()

    engine = get_engine()
    async with engine.connect() as conn:
        querier = AsyncQuerier(conn)
        existing_purchase = await querier.find_purchase_by_week_key(week_key=current_week_key)

    if existing_purchase:
        logger.info(f"이번 주({current_week_key}) 이미 구매 완료됨. 알림 스킵.")
        return

    text, reply_markup = create_reminder_message()
    await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
    )
    logger.info(f"알림 전송 완료: chat_id={chat_id}")
