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

## Docker

```bash
docker build -t telegram-bot .
```

컨테이너에서 SQLite 데이터는 `/app/data/telegram-bot.sqlite3`에 저장됩니다.

## Kubernetes

재사용 가능한 Kustomize base와 배포 방법은 [`deploy/kubernetes`](deploy/kubernetes/README.md)를 참고하세요.

## OpenTelemetry

`OTEL_EXPORTER_OTLP_ENDPOINT`가 설정된 경우에만 Metrics, Traces, Logs를 OTLP/gRPC로 전송합니다. 애플리케이션은 클러스터 내부 OTel Gateway만 바라보며 Grafana Cloud 인증정보를 사용하지 않습니다.

기본 Resource attribute:

- `service.name=telegram-bot`
- `service.namespace=homelab`
- `deployment.environment.name=production`
- `service.version=0.1.0`

표준 `OTEL_SERVICE_NAME`, `OTEL_RESOURCE_ATTRIBUTES`, `OTEL_TRACES_SAMPLER`, `OTEL_TRACES_SAMPLER_ARG`로 기본값을 변경할 수 있습니다. `service.version`을 이미지 버전으로 지정하려면 다음처럼 설정합니다.

```bash
OTEL_RESOURCE_ATTRIBUTES=service.version=sha-abcdef0
```

Telegram Bot의 수집 정책:

- Metrics는 전부 수집
- Trace는 100% 수집
- Logs는 INFO 이상 수집
- HTTPX와 SQLAlchemy 자동 계측 수집
- Python process/runtime metrics 수집

수집되는 custom metric:

- `telegram.command.executions`, `telegram.command.failures`, `telegram.command.duration`
- `telegram.callback.executions`, `telegram.callback.failures`, `telegram.callback.duration`
- `scheduler.job.executions`, `scheduler.job.failures`, `scheduler.job.duration`

벤치마크 앱은 비용과 데이터량을 줄이기 위해 별도 정책을 사용합니다.

- Metrics는 전부 수집
- 정상 Trace는 1~5% sampling
- 오류 및 느린 Trace는 가능한 경우 보존
- Logs는 WARN 이상 또는 반복 로그 제거
- 테스트 종료 후 Collector 수집 대상에서 제거

## Migration
- Atlas 사용
- 설정 파일: `atlas.hcl`
- 마이그레이션 파일: `migrations/`
- 새 스키마 변경이 생기면 migration 파일을 추가하고, 배포 시 자동 적용됩니다.

## DB
기본적으로 SQLite를 사용합니다.

- 기본 경로: `./data/telegram-bot.sqlite3`
- 변경 가능: `.env`의 `SQLITE_PATH`

기본 스키마 소스:
- `schema/schema.sql`

배포 적용 기준:
- `migrations/` 의 Atlas migration 파일
