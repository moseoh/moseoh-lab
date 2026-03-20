from loguru import logger
from telegram import BotCommand
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
)

from src.features.lotto.commands import (
    lotto_set_alarm,
    lotto_status,
    lotto_unset_alarm,
    start_command,
)
from src.features.lotto.constants import LOTTO
from src.features.lotto.interaction import handle_purchase_button
from src.features.lotto.scheduler import start_lotto_scheduler


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(
        [
            BotCommand("start", "개인 자동화 봇 소개와 사용 가능한 기능 안내"),
            BotCommand("lotto_set_alarm", "현재 채팅을 로또 알림 채팅으로 설정"),
            BotCommand("lotto_unset_alarm", "현재 채팅의 로또 알림 설정 해제"),
            BotCommand("lotto_status", "이번 주 로또 구매 상태 확인"),
        ]
    )
    logger.info("텔레그램 봇 초기화 및 명령어 등록 완료")
    if application.bot_data.get("scheduler") is None:
        application.bot_data["scheduler"] = start_lotto_scheduler(application)


def build_application(token: str) -> Application:
    application = Application.builder().token(token).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("lotto_set_alarm", lotto_set_alarm))
    application.add_handler(CommandHandler("lotto_unset_alarm", lotto_unset_alarm))
    application.add_handler(CommandHandler("lotto_status", lotto_status))
    application.add_handler(CallbackQueryHandler(handle_purchase_button, pattern=f"^{LOTTO.BUTTON_ID}$"))
    return application


def run_bot(token: str) -> None:
    application = build_application(token)
    logger.info("텔레그램 봇 실행 시작")
    application.run_polling()
