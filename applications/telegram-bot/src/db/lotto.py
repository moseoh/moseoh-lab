from typing import Optional

import sqlalchemy
import sqlalchemy.ext.asyncio

from src.db import models

CREATE_PURCHASE = """
INSERT INTO lotto_purchases (user_id, user_name, week_key)
VALUES (:user_id, :user_name, :week_key)
RETURNING id, user_id, user_name, week_key, purchased_at
"""

FIND_PURCHASE_BY_USER_AND_WEEK = """
SELECT id, user_id, user_name, week_key, purchased_at
FROM lotto_purchases
WHERE user_id = :user_id AND week_key = :week_key
LIMIT 1
"""

FIND_PURCHASE_BY_WEEK_KEY = """
SELECT id, user_id, user_name, week_key, purchased_at
FROM lotto_purchases
WHERE week_key = :week_key
LIMIT 1
"""


class AsyncQuerier:
    def __init__(self, conn: sqlalchemy.ext.asyncio.AsyncConnection):
        self._conn = conn

    async def create_purchase(self, *, user_id: str, user_name: str, week_key: str) -> Optional[models.LottoPurchase]:
        row = (
            await self._conn.execute(
                sqlalchemy.text(CREATE_PURCHASE),
                {"user_id": user_id, "user_name": user_name, "week_key": week_key},
            )
        ).first()
        if row is None:
            return None
        return models.LottoPurchase(*row)

    async def find_purchase_by_user_and_week(self, *, user_id: str, week_key: str) -> Optional[models.LottoPurchase]:
        row = (
            await self._conn.execute(
                sqlalchemy.text(FIND_PURCHASE_BY_USER_AND_WEEK),
                {"user_id": user_id, "week_key": week_key},
            )
        ).first()
        if row is None:
            return None
        return models.LottoPurchase(*row)

    async def find_purchase_by_week_key(self, *, week_key: str) -> Optional[models.LottoPurchase]:
        row = (
            await self._conn.execute(
                sqlalchemy.text(FIND_PURCHASE_BY_WEEK_KEY),
                {"week_key": week_key},
            )
        ).first()
        if row is None:
            return None
        return models.LottoPurchase(*row)
