from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes

from .constants import LOTTO
from .week_utils import get_current_lotto_week_key
from src.db.connection import get_engine
from src.db.lotto import AsyncQuerier as LottoQuerier
from src.db.settings import AsyncQuerier as SettingsQuerier


def _scope_id(chat_id: int) -> str:
    return str(chat_id)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(
            "안녕하세요. 개인 자동화 봇입니다.\n\n"
            "현재는 로또 알림 기능이 먼저 들어가 있습니다.\n"
            "사용 가능한 명령어:\n"
            "- /lotto_set_alarm : 현재 채팅을 로또 알림 채팅으로 설정\n"
            "- /lotto_unset_alarm : 로또 알림 해제\n"
            "- /lotto_status : 이번 주 구매 상태 확인"
        )


async def lotto_set_alarm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if message is None or chat is None or user is None:
        return

    member = await context.bot.get_chat_member(chat.id, user.id)
    if member.status not in {"administrator", "creator"}:
        await message.reply_text(LOTTO.MESSAGES.ADMIN_ONLY)
        return

    scope_id = _scope_id(chat.id)
    engine = get_engine()
    async with engine.connect() as conn:
        querier = SettingsQuerier(conn)
        existing = await querier.get_alarm_setting(scope_id=scope_id, alarm_type=LOTTO.ALARM_TYPE)
        if existing:
            await message.reply_text(f"이미 알림 채팅이 설정되어 있습니다. ({existing.chat_title or existing.chat_id})")
            return

        await querier.upsert_alarm_setting(
            scope_id=scope_id,
            alarm_type=LOTTO.ALARM_TYPE,
            chat_id=str(chat.id),
            chat_title=chat.title,
        )
        await conn.commit()

    logger.info(f"알람 채팅 설정: scope={scope_id}, chat={chat.id}")
    await message.reply_text("이 채팅을 로또 알림 채팅으로 설정했습니다.")


async def lotto_unset_alarm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if message is None or chat is None or user is None:
        return

    member = await context.bot.get_chat_member(chat.id, user.id)
    if member.status not in {"administrator", "creator"}:
        await message.reply_text(LOTTO.MESSAGES.ADMIN_ONLY)
        return

    scope_id = _scope_id(chat.id)
    engine = get_engine()
    async with engine.connect() as conn:
        querier = SettingsQuerier(conn)
        existing = await querier.get_alarm_setting(scope_id=scope_id, alarm_type=LOTTO.ALARM_TYPE)
        if not existing:
            await message.reply_text("설정된 알림이 없습니다.")
            return

        await querier.delete_alarm_setting(scope_id=scope_id, alarm_type=LOTTO.ALARM_TYPE)
        await conn.commit()

    logger.info(f"알람 채팅 해제: scope={scope_id}")
    await message.reply_text("로또 알림이 해제되었습니다.")


async def lotto_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    if message is None or user is None:
        return

    current_week_key = get_current_lotto_week_key()
    engine = get_engine()
    async with engine.connect() as conn:
        querier = LottoQuerier(conn)
        purchase = await querier.find_purchase_by_user_and_week(
            user_id=str(user.id), week_key=current_week_key
        )

    if purchase:
        purchased_at = purchase.purchased_at.strftime("%Y-%m-%d %H:%M") if purchase.purchased_at else "알 수 없음"
        await message.reply_text(
            f"✅ 이번 주({current_week_key}) 구매 완료!\n📅 기록 시간: {purchased_at}"
        )
    else:
        await message.reply_text(
            f"❌ 이번 주({current_week_key}) 아직 구매 기록이 없습니다."
        )
