# Telegram Bot Kubernetes Base 설계

## 목적

Telegram Bot의 Kubernetes 배포 기본 구성을 애플리케이션 저장소에서 함께 관리한다. 다른 저장소나 클러스터는 이 구성을 Kustomize remote base로 참조하고 이미지 버전, Namespace, 스토리지 같은 환경별 값만 오버라이드한다.

## 범위

이번 작업은 `moseoh-lab`에 공식 Kubernetes base와 사용 문서를 추가하는 데 한정한다. 기존 homelab 저장소의 Telegram Bot 매니페스트를 remote base 기반 overlay로 전환하는 작업은 이 변경이 병합되어 참조할 커밋 SHA가 확정된 후 별도로 진행한다.

## 디렉터리 구조

기존 애플리케이션 구조는 유지하고 배포 자산만 `deploy/kubernetes` 아래에 추가한다.

```text
applications/telegram-bot/
├── deploy/
│   └── kubernetes/
│       ├── README.md
│       ├── deployment.yaml
│       ├── kustomization.yaml
│       └── pvc.yaml
├── migrations/
├── schema/
├── src/
├── Dockerfile
├── docker-compose.yml
├── docker-compose.dokploy.yml
├── atlas.hcl
├── pyproject.toml
└── README.md
```

Dockerfile과 Compose 파일은 앱 루트가 빌드 컨텍스트이자 로컬 개발 진입점이므로 이동하지 않는다. `migrations`, `schema`, `atlas.hcl`도 이번 작업에서는 기존 경로를 유지한다.

## Kustomize base

`deploy/kubernetes/kustomization.yaml`은 다음 리소스를 포함한다.

- `deployment.yaml`
- `pvc.yaml`

Namespace는 소비 환경이 결정하므로 포함하지 않는다. Secret 리소스도 저장소에 생성하지 않는다. 소비자는 Kustomization의 `namespace`를 지정하고 같은 Namespace에 `telegram-bot` Secret을 생성해야 한다.

## Deployment

Telegram long polling은 동시에 여러 프로세스가 같은 token을 사용하면 충돌하므로 replica는 1로 고정하고 배포 전략은 `Recreate`를 사용한다. Service와 Ingress는 만들지 않는다.

Pod에는 다음 컨테이너를 구성한다.

1. `copy-migrations` initContainer
   - `ghcr.io/moseoh/telegram-bot:latest` 이미지에 포함된 `/app/migrations`를 `emptyDir`에 복사한다.
2. `migrate` initContainer
   - `arigaio/atlas:1.2.2`로 공유 SQLite 파일에 migration을 적용한다.
3. `bot` 컨테이너
   - `/app/.venv/bin/telegram-bot`을 실행한다.
   - `telegram-bot` Secret의 `TELEGRAM_BOT_TOKEN` 값을 읽는다.
   - SQLite PVC를 `/app/data`에 마운트한다.

앱 이미지의 기본 태그는 base를 독립적으로 렌더링할 수 있도록 `latest`를 사용한다. 실제 배포에서는 Kustomize `images`로 `sha-<짧은 커밋 SHA>` 태그에 고정한다. 두 앱 이미지 참조는 같은 이름을 사용하므로 하나의 image override가 initContainer와 Bot 컨테이너에 함께 적용된다.

## 데이터와 migration

`telegram-bot-data` PVC는 `ReadWriteOnce`, 1Gi를 기본값으로 사용하며 StorageClass는 지정하지 않는다. 소비 환경은 필요할 때 PVC patch로 용량이나 StorageClass를 변경한다.

앱 이미지가 migration 파일을 포함하므로 별도 ConfigMap에 SQL을 복제하지 않는다. Pod가 시작될 때 migration 파일을 임시 볼륨에 복사한 다음 Atlas가 PVC의 SQLite DB에 적용한다. migration이 실패하면 Bot 컨테이너는 시작되지 않는다.

`Recreate` 전략과 단일 replica는 SQLite PVC의 동시 접근과 Telegram long polling 중복 실행을 방지한다.

## 설정과 Secret

base가 정의하는 일반 환경 변수는 다음과 같다.

- `TZ=Asia/Seoul`
- `SQLITE_PATH=/app/data/telegram-bot.sqlite3`
- `PYTHONUNBUFFERED=1`
- `PYTHONDONTWRITEBYTECODE=1`

`TELEGRAM_BOT_TOKEN`은 `telegram-bot` Secret의 같은 이름 key에서 읽는다. 실제 token이나 예시 Secret manifest는 Git에 저장하지 않는다. 문서에는 `kubectl create secret generic`을 이용한 생성 절차만 제공한다.

## 보안과 리소스

Pod는 ServiceAccount token을 자동 마운트하지 않는다. Pod 수준에서 RuntimeDefault seccomp와 `fsGroup: 1000`을 사용한다. 모든 initContainer와 Bot 컨테이너는 UID/GID 1000의 non-root로 실행하고 privilege escalation을 금지하며 root filesystem을 읽기 전용으로 설정하고 Linux capabilities를 모두 제거한다.

각 컨테이너에는 작은 홈서버와 일반 클러스터에서 시작점으로 사용할 CPU·메모리 requests/limits를 지정한다. 소비 환경은 필요할 때 Deployment patch로 값을 조정한다.

## Remote base 사용

소비 저장소는 병합된 커밋 SHA로 base를 고정한다.

```yaml
resources:
  - github.com/moseoh/moseoh-lab//applications/telegram-bot/deploy/kubernetes?ref=<매니페스트 커밋 SHA>

images:
  - name: ghcr.io/moseoh/telegram-bot
    newTag: sha-<이미지 커밋 SHA>
```

`main`이나 `latest`에 배포 구성을 고정하지 않는다. 커밋 SHA와 이미지 SHA 태그를 사용해 같은 입력이 항상 같은 매니페스트와 이미지를 가리키도록 한다.

## 오류 처리

- Secret이 없거나 key가 잘못되면 Pod 생성이 실패하고 Kubernetes 이벤트에 원인이 표시된다.
- migration 복사나 Atlas 적용이 실패하면 initContainer가 실패하며 Bot은 시작되지 않는다.
- PVC가 바인딩되지 않으면 Pod는 Pending 상태로 유지되어 스토리지 문제를 확인할 수 있다.
- Bot 프로세스가 종료되면 Deployment가 컨테이너를 재시작한다.

## 검증

- `kubectl kustomize applications/telegram-bot/deploy/kubernetes`가 오류 없이 단일 Deployment와 PVC를 렌더링한다.
- `kubectl apply --dry-run=client`가 렌더링 결과를 유효한 Kubernetes 리소스로 인식한다.
- 렌더링 결과에 Namespace와 Secret 리소스가 포함되지 않는다.
- Deployment는 replica 1, Recreate 전략, 두 initContainer, Bot 컨테이너와 PVC mount를 포함한다.
- CI에서 기존 Docker 이미지 빌드가 계속 성공한다.
- 애플리케이션 README는 Kubernetes 배포 문서 위치와 remote base 사용법을 안내한다.
