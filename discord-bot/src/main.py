import os

from dotenv import load_dotenv
from loguru import logger

from src.bot import DiscordBot

load_dotenv()


def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN 환경변수가 설정되지 않았습니다.")
        return

    bot = DiscordBot()
    bot.run(token)


if __name__ == "__main__":
    main()
