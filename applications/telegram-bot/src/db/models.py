import dataclasses
import datetime
from typing import Optional


@dataclasses.dataclass()
class AlarmSetting:
    scope_id: str
    alarm_type: str
    chat_id: str
    chat_title: Optional[str]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]


@dataclasses.dataclass()
class LottoPurchase:
    id: int
    user_id: str
    user_name: str
    week_key: str
    purchased_at: Optional[datetime.datetime]
