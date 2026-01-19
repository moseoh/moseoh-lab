from dataclasses import dataclass


@dataclass(frozen=True)
class WeekStart:
    DAY: int = 6  # 0=일, 6=토
    HOUR: int = 18


@dataclass(frozen=True)
class Messages:
    REMINDER: str = "로또 구매할 시간입니다!"
    BUTTON_LABEL: str = "구매 완료"
    PURCHASE_SUCCESS: str = "이번 주 구매 완료로 기록되었습니다!"
    ALREADY_PURCHASED: str = "이번 주에 이미 구매 완료 처리되었습니다."


@dataclass(frozen=True)
class LottoConstants:
    WEEKDAY_HOURS: tuple[int, ...] = (13, 18)
    SATURDAY_HOURS: tuple[int, ...] = (12, 13, 14, 15, 16, 17)
    WEEK_START: WeekStart = WeekStart()
    BUTTON_ID: str = "lotto_purchase_complete"
    PURCHASE_URL: str = "https://www.dhlottery.co.kr/"
    MESSAGES: Messages = Messages()


LOTTO = LottoConstants()
