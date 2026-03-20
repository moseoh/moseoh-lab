# telegram-bot

Telegram용 로또 알림 봇입니다. Discord 봇의 핵심 기능을 Telegram으로 옮긴 버전입니다.

## 기능
- 주간 로또 구매 알림 스케줄 발송
- 인라인 버튼 제공
  - `구매하러 가기`
  - `구매 완료`
- 사용자가 `구매 완료`를 누르면 이번 주 구매 기록 저장
- 이번 주에 이미 누군가 구매 완료 처리했으면 이후 알림 스킵
- 관리자만 알림 채팅방 설정/해제 가능

## 명령어
- `/start` : 봇 소개
- `/lotto_set_alarm` : 현재 채팅을 로또 알림 채팅으로 설정 (관리자 전용)
- `/lotto_unset_alarm` : 로또 알림 해제 (관리자 전용)
- `/lotto_status` : 이번 주 구매 상태 확인

## 실행
```bash
cp .env.example .env
# 환경변수 수정
uv run telegram-bot
```

## DB
기본적으로 PostgreSQL을 사용합니다.

필수 테이블:
- `lotto_purchases`
- `alarm_settings`

스키마는 `schema/schema.sql` 참고.
