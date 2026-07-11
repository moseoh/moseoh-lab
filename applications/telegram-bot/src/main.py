import os

from dotenv import load_dotenv
from loguru import logger

from src.bot import run_bot
from src.telemetry import initialize_telemetry

load_dotenv()


def main() -> None:
    initialize_telemetry()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN 환경변수가 설정되지 않았습니다.")
        return

    run_bot(token)


if __name__ == "__main__":
    main()
