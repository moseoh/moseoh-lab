from dataclasses import dataclass


@dataclass(frozen=True)
class WeekStart:
    DAY: int = 6  # 0=일, 6=토
    HOUR: int = 18


@dataclass(frozen=True)
class Messages:
    BUTTON_LABEL: str = "구매 완료"
    PURCHASE_SUCCESS: str = "이번 주 구매 완료로 기록되었습니다!"
    ALREADY_PURCHASED: str = "이번 주에 이미 구매 완료 처리되었습니다."
    ADMIN_ONLY: str = "이 명령은 관리자만 사용할 수 있습니다."


@dataclass(frozen=True)
class LottoConstants:
    WEEKDAY_HOURS: tuple[int, ...] = (13, 18)
    SATURDAY_HOURS: tuple[int, ...] = (12, 13, 14, 15, 16, 17)
    WEEK_START: WeekStart = WeekStart()
    BUTTON_ID: str = "lotto_purchase_complete"
    PURCHASE_URL: str = "https://www.dhlottery.co.kr/"
    ALARM_TYPE: str = "lotto"
    MESSAGES: Messages = Messages()


LOTTO = LottoConstants()
