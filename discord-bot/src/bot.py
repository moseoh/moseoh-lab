import discord
from discord import Intents, app_commands
from loguru import logger

from src.db.connection import get_engine
from src.db.settings import AsyncQuerier as SettingsQuerier
from src.features.lotto.scheduler import start_lotto_scheduler
from src.features.lotto.interaction import handle_purchase_button
from src.features.lotto.commands import LottoCommands


class DiscordBot(discord.Client):
    def __init__(self):
        intents = Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.tree.add_command(LottoCommands())
        self.scheduler = None

    async def setup_hook(self) -> None:
        await self.tree.sync()
        logger.info("슬래시 커맨드 동기화 완료")

    async def on_ready(self):
        logger.info(f"봇이 준비되었습니다! {self.user}로 로그인했습니다.")
        self.scheduler = start_lotto_scheduler(self)

    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return

        try:
            await handle_purchase_button(interaction)
        except Exception as e:
            logger.error(f"버튼 처리 실패: {e}")

    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        channel_id = str(channel.id)

        try:
            engine = get_engine()
            async with engine.connect() as conn:
                querier = SettingsQuerier(conn)
                await querier.delete_alarm_settings_by_channel(channel_id=channel_id)
                await conn.commit()
            logger.info(f"삭제된 채널 알람 설정 정리: {channel_id}")
        except Exception as e:
            logger.error(f"채널 삭제 처리 실패: {e}")
