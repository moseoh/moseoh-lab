from datetime import datetime, timedelta
from .constants import LOTTO


def get_current_lotto_week_key(date: datetime | None = None) -> str:
    """
    토요일 18:00 기준으로 현재 "로또 주차"를 계산

    로직:
    - 토요일 18:00 이후 ~ 다음 토요일 17:59:59 = 새로운 주
    - 예: 토요일 19:00에 버튼 누르면 -> 새 주로 기록
    - 예: 토요일 17:00에 버튼 누르면 -> 이전 주로 기록
    """
    if date is None:
        date = datetime.now()

    start_day = LOTTO.WEEK_START.DAY
    start_hour = LOTTO.WEEK_START.HOUR

    day_of_week = date.weekday()  # 0=월, 6=일
    # Python weekday를 JS getDay()와 맞추기 (0=일, 6=토)
    day_of_week = (day_of_week + 1) % 7
    hour = date.hour

    # 현재가 "이번 주 토요일 18:00 이전"인지 판단
    is_before_week_start = day_of_week < start_day or (
        day_of_week == start_day and hour < start_hour
    )

    week_start = date

    if is_before_week_start:
        # 지난 주 토요일로 이동
        days_to_subtract = 1 if day_of_week == 0 else day_of_week + 1
        week_start = date - timedelta(days=days_to_subtract)
    else:
        # 이번 주 토요일로 이동
        days_to_subtract = day_of_week - start_day
        week_start = date - timedelta(days=days_to_subtract)

    return week_start.strftime("%Y-%m-%d")
