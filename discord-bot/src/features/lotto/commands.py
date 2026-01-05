import discord
from discord import app_commands
from loguru import logger

from .week_utils import get_current_lotto_week_key
from src.db.connection import get_engine
from src.db.lotto import AsyncQuerier as LottoQuerier
from src.db.settings import AsyncQuerier as SettingsQuerier

ALARM_TYPE = "lotto"


class LottoCommands(app_commands.Group):
    def __init__(self):
        super().__init__(name="로또", description="로또 관련 명령어")

    @app_commands.command(name="알람설정", description="현재 채널을 로또 알림 채널로 설정합니다")
    @app_commands.default_permissions(administrator=True)
    async def alarm_set(self, interaction: discord.Interaction) -> None:
        if not interaction.guild:
            await interaction.response.send_message(
                "서버에서만 사용할 수 있는 명령어입니다.", ephemeral=True
            )
            return

        guild_id = str(interaction.guild.id)
        channel_id = str(interaction.channel_id)

        engine = get_engine()
        async with engine.connect() as conn:
            querier = SettingsQuerier(conn)
            existing = await querier.get_alarm_setting(
                guild_id=guild_id, alarm_type=ALARM_TYPE
            )

            if existing:
                await interaction.response.send_message(
                    f"이미 알림 채널이 설정되어 있습니다. (<#{existing.channel_id}>)",
                    ephemeral=True
                )
                return

            await querier.upsert_alarm_setting(
                guild_id=guild_id, alarm_type=ALARM_TYPE, channel_id=channel_id
            )
            await conn.commit()

        logger.info(f"알람 채널 설정: guild={guild_id}, channel={channel_id}")
        await interaction.response.send_message(
            f"이 채널(<#{channel_id}>)을 로또 알림 채널로 설정했습니다.", ephemeral=True
        )

    @app_commands.command(name="알람해제", description="로또 알림을 해제합니다")
    @app_commands.default_permissions(administrator=True)
    async def alarm_unset(self, interaction: discord.Interaction) -> None:
        if not interaction.guild:
            await interaction.response.send_message(
                "서버에서만 사용할 수 있는 명령어입니다.", ephemeral=True
            )
            return

        guild_id = str(interaction.guild.id)

        engine = get_engine()
        async with engine.connect() as conn:
            querier = SettingsQuerier(conn)
            existing = await querier.get_alarm_setting(
                guild_id=guild_id, alarm_type=ALARM_TYPE
            )

            if not existing:
                await interaction.response.send_message(
                    "설정된 알림이 없습니다.", ephemeral=True
                )
                return

            await querier.delete_alarm_setting(
                guild_id=guild_id, alarm_type=ALARM_TYPE
            )
            await conn.commit()

        logger.info(f"알람 채널 해제: guild={guild_id}")
        await interaction.response.send_message(
            "로또 알림이 해제되었습니다.", ephemeral=True
        )

    @app_commands.command(name="상태확인", description="이번 주 로또 구매 상태를 확인합니다")
    async def status_check(self, interaction: discord.Interaction) -> None:
        user_id = str(interaction.user.id)
        current_week_key = get_current_lotto_week_key()

        engine = get_engine()
        async with engine.connect() as conn:
            querier = LottoQuerier(conn)
            purchase = await querier.find_purchase_by_user_and_week(
                user_id=user_id, week_key=current_week_key
            )

        if purchase:
            purchased_at = purchase.purchased_at.strftime("%Y-%m-%d %H:%M") if purchase.purchased_at else "알 수 없음"
            await interaction.response.send_message(
                f"✅ 이번 주({current_week_key}) 구매 완료!\n"
                f"📅 기록 시간: {purchased_at}",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ 이번 주({current_week_key}) 아직 구매 기록이 없습니다.",
                ephemeral=True
            )
