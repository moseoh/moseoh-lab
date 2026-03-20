# telegram-bot

Telegram용 로또 알림 봇입니다. Discord 봇의 핵심 기능을 Telegram으로 옮긴 버전입니다.
작은 단일 기능 봇이라 Postgres 대신 SQLite 기반으로 단순하게 운영합니다.

## 기능
- 주간 로또 구매 알림 스케줄 발송
- 인라인 버튼 제공
  - `구매하러 가기`
  - `구매 완료`
- 사용자가 `구매 완료`를 누르면 이번 주 구매 기록 저장
- 이번 주에 이미 누군가 구매 완료 처리했으면 이후 알림 스킵
- Telegram 특성에 맞춰 **DM 중심**으로 사용

## 명령어
- `/start` : 개인 자동화 봇 소개 및 사용 가능한 기능 안내
- `/lotto_enable` : 이 DM으로 로또 알림 받기
- `/lotto_disable` : 이 DM의 로또 알림 끄기
- `/lotto_status` : 이번 주 구매 상태 확인

호환용 alias:
- `/lotto_set_alarm` → `/lotto_enable`
- `/lotto_unset_alarm` → `/lotto_disable`

> Telegram 명령어 메뉴는 그룹 폴더처럼 접히지 않으므로, `lotto_*` 네이밍으로 한눈에 같은 기능군처럼 보이게 구성했습니다.

## 실행
```bash
cp .env.example .env
# 환경변수 수정
mkdir -p data
uv run telegram-bot
```

## Docker / Dokploy
- `Dockerfile` 포함
- `docker-compose.yml` 포함
- `docker-compose.dokploy.yml` 포함
- SQLite 데이터는 `/app/data/telegram-bot.sqlite3` 에 저장되며 volume으로 유지됩니다.

## DB
기본적으로 SQLite를 사용합니다.

- 기본 경로: `./data/telegram-bot.sqlite3`
- 변경 가능: `.env`의 `SQLITE_PATH`

필수 테이블:
- `lotto_purchases`
- `alarm_settings`

스키마는 `schema/schema.sql` 참고.
