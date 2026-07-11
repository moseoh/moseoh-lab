from typing import AsyncIterator, Optional

import sqlalchemy
import sqlalchemy.ext.asyncio

from src.db import models

GET_ALARM_SETTING = """
SELECT scope_id, alarm_type, chat_id, chat_title, created_at, updated_at
FROM alarm_settings
WHERE scope_id = :scope_id AND alarm_type = :alarm_type
LIMIT 1
"""

GET_ALARM_SETTINGS_BY_TYPE = """
SELECT scope_id, chat_id, chat_title
FROM alarm_settings
WHERE alarm_type = :alarm_type
"""

UPSERT_ALARM_SETTING = """
INSERT INTO alarm_settings (scope_id, alarm_type, chat_id, chat_title)
VALUES (:scope_id, :alarm_type, :chat_id, :chat_title)
ON CONFLICT (scope_id, alarm_type) DO UPDATE SET
    chat_id = EXCLUDED.chat_id,
    chat_title = EXCLUDED.chat_title,
    updated_at = CURRENT_TIMESTAMP
RETURNING scope_id, alarm_type, chat_id, chat_title, created_at, updated_at
"""

DELETE_ALARM_SETTING = """
DELETE FROM alarm_settings
WHERE scope_id = :scope_id AND alarm_type = :alarm_type
"""

DELETE_ALARM_SETTINGS_BY_CHAT = """
DELETE FROM alarm_settings
WHERE chat_id = :chat_id
"""


class GetAlarmSettingsByTypeRow:
    def __init__(self, scope_id: str, chat_id: str, chat_title: str | None):
        self.scope_id = scope_id
        self.chat_id = chat_id
        self.chat_title = chat_title


class AsyncQuerier:
    def __init__(self, conn: sqlalchemy.ext.asyncio.AsyncConnection):
        self._conn = conn

    async def get_alarm_setting(self, *, scope_id: str, alarm_type: str) -> Optional[models.AlarmSetting]:
        row = (
            await self._conn.execute(
                sqlalchemy.text(GET_ALARM_SETTING),
                {"scope_id": scope_id, "alarm_type": alarm_type},
            )
        ).first()
        if row is None:
            return None
        return models.AlarmSetting(*row)

    async def get_alarm_settings_by_type(self, *, alarm_type: str) -> AsyncIterator[GetAlarmSettingsByTypeRow]:
        result = await self._conn.stream(
            sqlalchemy.text(GET_ALARM_SETTINGS_BY_TYPE), {"alarm_type": alarm_type}
        )
        async for row in result:
            yield GetAlarmSettingsByTypeRow(row[0], row[1], row[2])

    async def upsert_alarm_setting(self, *, scope_id: str, alarm_type: str, chat_id: str, chat_title: str | None) -> Optional[models.AlarmSetting]:
        row = (
            await self._conn.execute(
                sqlalchemy.text(UPSERT_ALARM_SETTING),
                {
                    "scope_id": scope_id,
                    "alarm_type": alarm_type,
                    "chat_id": chat_id,
                    "chat_title": chat_title,
                },
            )
        ).first()
        if row is None:
            return None
        return models.AlarmSetting(*row)

    async def delete_alarm_setting(self, *, scope_id: str, alarm_type: str) -> None:
        await self._conn.execute(
            sqlalchemy.text(DELETE_ALARM_SETTING),
            {"scope_id": scope_id, "alarm_type": alarm_type},
        )

    async def delete_alarm_settings_by_chat(self, *, chat_id: str) -> None:
        await self._conn.execute(
            sqlalchemy.text(DELETE_ALARM_SETTINGS_BY_CHAT),
            {"chat_id": chat_id},
        )
