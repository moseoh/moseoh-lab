# AGENTS.md - Discord Lotto Bot

이 문서는 AI 코딩 에이전트가 이 코드베이스에서 작업할 때 참고해야 할 가이드라인입니다.

## 프로젝트 개요

Discord 로또 알림 봇 - Python 3.12 기반 비동기 애플리케이션

- **패키지 관리자**: uv (Astral)
- **프레임워크**: discord.py
- **데이터베이스**: PostgreSQL + SQLAlchemy async + asyncpg
- **쿼리 생성**: sqlc (Python 코드 자동 생성)
- **마이그레이션**: Atlas
- **스케줄링**: APScheduler

## 빌드/실행 명령어

### 의존성 설치
```bash
uv sync
```

### 애플리케이션 실행
```bash
uv run discord-bot
```

### Docker로 실행
```bash
docker compose up -d
```

### sqlc 코드 생성 (SQL 쿼리 변경 시)
```bash
make sqlc
# 또는
sqlc generate
```

### 데이터베이스 마이그레이션
```bash
# 새 마이그레이션 생성
make migrate-diff name=migration_name

# 마이그레이션 해시 업데이트
make migrate-hash

# 마이그레이션 적용 (Docker)
docker compose up migrate
```

## 테스트

> **주의**: 현재 테스트 프레임워크가 설정되어 있지 않음

테스트를 추가할 경우 pytest 사용 권장:
```bash
# pyproject.toml에 추가
# [project.optional-dependencies]
# dev = ["pytest", "pytest-asyncio"]

uv run pytest
uv run pytest tests/test_specific.py
uv run pytest tests/test_specific.py::test_function_name -v
```

## 프로젝트 구조

```
src/
├── __init__.py
├── main.py                 # 진입점
├── bot.py                  # Discord 봇 클래스
├── db/                     # 데이터베이스 레이어 (sqlc 생성)
│   ├── connection.py       # DB 연결 관리
│   ├── models.py           # 데이터 모델 (자동 생성)
│   ├── lotto.py            # 로또 쿼리 (자동 생성)
│   └── settings.py         # 설정 쿼리 (자동 생성)
└── features/               # 기능 모듈
    └── lotto/
        ├── commands.py     # 슬래시 커맨드
        ├── constants.py    # 상수 정의
        ├── interaction.py  # 버튼 인터랙션
        ├── notification.py # 알림 메시지 생성
        ├── scheduler.py    # 스케줄러 설정
        └── week_utils.py   # 주차 계산 유틸리티
```

## 코드 스타일 가이드라인

### 임포트 순서
1. 표준 라이브러리 (`os`, `datetime` 등)
2. 서드파티 라이브러리 (`discord`, `sqlalchemy`, `loguru` 등)
3. 로컬 모듈 (`src.*`, 상대 임포트)

```python
import os
from datetime import datetime

import discord
from discord import app_commands
from loguru import logger

from src.db.connection import get_engine
from .constants import LOTTO
```

### 타입 힌트
- 모든 함수에 타입 힌트 사용
- Python 3.12+ 문법 사용 (`X | None` 대신 `Optional[X]` 가능)

```python
def get_engine() -> AsyncEngine:
    ...

async def send_reminder(channel: TextChannel) -> None:
    ...

_engine: AsyncEngine | None = None
```

### 네이밍 컨벤션
- 함수/변수: `snake_case`
- 클래스: `PascalCase`
- 상수: `UPPER_SNAKE_CASE` 또는 frozen dataclass 사용
- 파일명: `snake_case.py`

```python
# 상수는 frozen dataclass로 그룹화
@dataclass(frozen=True)
class LottoConstants:
    WEEKDAY_HOURS: tuple[int, ...] = (13, 18)
    BUTTON_ID: str = "lotto_purchase_complete"

LOTTO = LottoConstants()
```

### 비동기 패턴
- 모든 DB 작업은 async/await 사용
- SQLAlchemy async engine과 connection 사용

```python
engine = get_engine()
async with engine.connect() as conn:
    querier = AsyncQuerier(conn)
    result = await querier.some_query(param=value)
    await conn.commit()  # 변경 작업 시 필수
```

### 로깅
- `loguru` 라이브러리 사용
- 로그 메시지는 한국어로 작성

```python
from loguru import logger

logger.info("알림 전송 완료")
logger.error(f"버튼 처리 실패: {e}")
logger.warning(f"유효하지 않은 채널: {channel_id}")
```

### 에러 핸들링
- try/except로 예외 처리
- 에러 발생 시 logger.error로 기록
- 사용자에게는 친절한 한국어 메시지 표시

```python
try:
    await handle_purchase_button(interaction)
except Exception as e:
    logger.error(f"버튼 처리 실패: {e}")
```

### Discord 슬래시 커맨드
- `app_commands.Group`으로 명령어 그룹화
- 명령어/설명은 한국어 사용
- `ephemeral=True`로 비공개 응답

```python
class LottoCommands(app_commands.Group):
    def __init__(self):
        super().__init__(name="로또", description="로또 관련 명령어")

    @app_commands.command(name="알람설정", description="현재 채널을 로또 알림 채널로 설정합니다")
    @app_commands.default_permissions(administrator=True)
    async def alarm_set(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message("메시지", ephemeral=True)
```

## 데이터베이스 작업

### 스키마 변경 시
1. `schema/schema.sql` 수정
2. `make migrate-diff name=변경사항_설명`
3. `make migrate-hash`

### 쿼리 추가/수정 시
1. `queries/*.sql` 파일 수정
2. `make sqlc` 실행
3. `src/db/` 디렉토리에 자동 생성된 코드 확인

> **중요**: `src/db/models.py`, `src/db/lotto.py`, `src/db/settings.py`는
> sqlc가 자동 생성하므로 직접 수정하지 마세요.

## 환경 변수

`.env.example` 참조:
```
DISCORD_TOKEN=your_discord_bot_token_here
TZ=Asia/Seoul
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_NAME=discord
```

## 새 기능 추가 시

1. `src/features/` 아래에 새 디렉토리 생성
2. 관련 파일 구조화:
   - `commands.py` - 슬래시 커맨드
   - `constants.py` - 상수
   - `*.py` - 기타 로직
3. `src/bot.py`에서 커맨드 등록
