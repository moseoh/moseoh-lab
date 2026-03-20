from datetime import datetime, timedelta

from .constants import LOTTO


def get_current_lotto_week_key(date: datetime | None = None) -> str:
    if date is None:
        date = datetime.now()

    start_day = LOTTO.WEEK_START.DAY
    start_hour = LOTTO.WEEK_START.HOUR

    day_of_week = (date.weekday() + 1) % 7  # 0=일, 6=토
    hour = date.hour

    is_before_week_start = day_of_week < start_day or (
        day_of_week == start_day and hour < start_hour
    )

    week_start = date
    if is_before_week_start:
        days_to_subtract = 1 if day_of_week == 0 else day_of_week + 1
        week_start = date - timedelta(days=days_to_subtract)
    else:
        days_to_subtract = day_of_week - start_day
        week_start = date - timedelta(days=days_to_subtract)

    return week_start.strftime("%Y-%m-%d")
