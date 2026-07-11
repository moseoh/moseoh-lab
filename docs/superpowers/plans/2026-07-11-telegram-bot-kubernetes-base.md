# Telegram Bot Kubernetes Base Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Telegram Bot을 Kubernetes에 배포할 수 있는 재사용 가능한 Kustomize base와 사용 문서를 애플리케이션 저장소에 추가한다.

**Architecture:** `applications/telegram-bot/deploy/kubernetes`가 Deployment와 PVC를 소유하고, 소비 저장소는 커밋 SHA로 이 base를 참조한다. Namespace, 실제 Secret, 이미지 SHA 태그, 환경별 스토리지 설정은 소비 저장소가 관리한다.

**Tech Stack:** Kubernetes manifests, Kustomize, Atlas migration initContainer, SQLite PVC, kubectl

## Global Constraints

- Kubernetes 파일은 `applications/telegram-bot/deploy/kubernetes`에 둔다.
- Namespace, Service, Ingress, 실제 Secret manifest는 만들지 않는다.
- Bot replica는 1이며 Deployment 전략은 `Recreate`다.
- 기본 앱 이미지는 `ghcr.io/moseoh/telegram-bot:latest`이고 소비 환경은 `sha-<짧은 커밋 SHA>`로 교체한다.
- Atlas 이미지는 `arigaio/atlas:1.2.2`다.
- PVC 이름은 `telegram-bot-data`, access mode는 `ReadWriteOnce`, 기본 용량은 1Gi다.
- Secret 이름과 key는 모두 `telegram-bot`, `TELEGRAM_BOT_TOKEN`이다.
- 모든 코드 주석과 문서는 한국어를 사용한다.

---

### Task 1: Kubernetes base 리소스

**Files:**
- Create: `applications/telegram-bot/deploy/kubernetes/kustomization.yaml`
- Create: `applications/telegram-bot/deploy/kubernetes/deployment.yaml`
- Create: `applications/telegram-bot/deploy/kubernetes/pvc.yaml`
- Reference: `applications/telegram-bot/Dockerfile`
- Reference: `applications/telegram-bot/migrations/`

**Interfaces:**
- Consumes: `ghcr.io/moseoh/telegram-bot` 이미지의 `/app/migrations`와 `/app/.venv/bin/telegram-bot`
- Consumes: `telegram-bot` Secret의 `TELEGRAM_BOT_TOKEN` key
- Produces: Kustomize로 렌더링 가능한 Deployment와 PersistentVolumeClaim

- [ ] **Step 1: base 부재를 확인한다**

Run:

```bash
test ! -e applications/telegram-bot/deploy/kubernetes/kustomization.yaml
```

Expected: exit code `0`.

- [ ] **Step 2: Kustomization을 작성한다**

Create `applications/telegram-bot/deploy/kubernetes/kustomization.yaml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - pvc.yaml
```

- [ ] **Step 3: PVC를 작성한다**

Create `applications/telegram-bot/deploy/kubernetes/pvc.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: telegram-bot-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

- [ ] **Step 4: Deployment를 작성한다**

Create `applications/telegram-bot/deploy/kubernetes/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: telegram-bot
  labels:
    app.kubernetes.io/name: telegram-bot
spec:
  replicas: 1
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app.kubernetes.io/name: telegram-bot
  template:
    metadata:
      labels:
        app.kubernetes.io/name: telegram-bot
    spec:
      automountServiceAccountToken: false
      securityContext:
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      initContainers:
        - name: copy-migrations
          image: ghcr.io/moseoh/telegram-bot:latest
          imagePullPolicy: IfNotPresent
          command: ["sh", "-c", "cp -R /app/migrations/. /migrations/"]
          resources:
            requests: {cpu: 10m, memory: 16Mi}
            limits: {cpu: 100m, memory: 64Mi}
          securityContext:
            runAsNonRoot: true
            runAsUser: 1000
            runAsGroup: 1000
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: {drop: ["ALL"]}
          volumeMounts:
            - {name: migrations, mountPath: /migrations}
        - name: migrate
          image: arigaio/atlas:1.2.2
          imagePullPolicy: IfNotPresent
          env:
            - {name: HOME, value: /tmp}
          args: ["migrate", "apply", "--url", "sqlite:///data/telegram-bot.sqlite3", "--dir", "file:///migrations"]
          resources:
            requests: {cpu: 10m, memory: 32Mi}
            limits: {cpu: 100m, memory: 128Mi}
          securityContext:
            runAsNonRoot: true
            runAsUser: 1000
            runAsGroup: 1000
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: {drop: ["ALL"]}
          volumeMounts:
            - {name: data, mountPath: /data}
            - {name: migrations, mountPath: /migrations, readOnly: true}
            - {name: tmp, mountPath: /tmp}
      containers:
        - name: bot
          image: ghcr.io/moseoh/telegram-bot:latest
          imagePullPolicy: IfNotPresent
          command: ["/app/.venv/bin/telegram-bot"]
          env:
            - name: TELEGRAM_BOT_TOKEN
              valueFrom:
                secretKeyRef:
                  name: telegram-bot
                  key: TELEGRAM_BOT_TOKEN
            - {name: TZ, value: Asia/Seoul}
            - {name: SQLITE_PATH, value: /app/data/telegram-bot.sqlite3}
            - {name: PYTHONUNBUFFERED, value: "1"}
            - {name: PYTHONDONTWRITEBYTECODE, value: "1"}
          resources:
            requests: {cpu: 25m, memory: 64Mi}
            limits: {cpu: 250m, memory: 256Mi}
          securityContext:
            runAsNonRoot: true
            runAsUser: 1000
            runAsGroup: 1000
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: {drop: ["ALL"]}
          volumeMounts:
            - {name: data, mountPath: /app/data}
            - {name: tmp, mountPath: /tmp}
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: telegram-bot-data
        - name: migrations
          emptyDir: {}
        - name: tmp
          emptyDir: {}
```

- [ ] **Step 5: base 렌더링을 검증한다**

Run:

```bash
kubectl kustomize applications/telegram-bot/deploy/kubernetes >/tmp/telegram-bot-base.yaml
kubectl apply --dry-run=client -f /tmp/telegram-bot-base.yaml
```

Expected:

```text
deployment.apps/telegram-bot created (dry run)
persistentvolumeclaim/telegram-bot-data created (dry run)
```

- [ ] **Step 6: 설계 불변 조건을 검증한다**

Run:

```bash
test "$(rg -c '^kind: Deployment$' /tmp/telegram-bot-base.yaml)" = 1
test "$(rg -c '^kind: PersistentVolumeClaim$' /tmp/telegram-bot-base.yaml)" = 1
! rg -q '^kind: (Namespace|Secret|Service|Ingress)$' /tmp/telegram-bot-base.yaml
rg -n 'replicas: 1|type: Recreate|name: copy-migrations|name: migrate|claimName: telegram-bot-data|TELEGRAM_BOT_TOKEN|runAsNonRoot: true|readOnlyRootFilesystem: true' /tmp/telegram-bot-base.yaml
git diff --check
```

Expected: 모든 `test`와 `git diff --check`가 exit code `0`이고 `rg`가 각 필수 설정을 출력한다.

- [ ] **Step 7: 리소스를 커밋한다**

```bash
git add applications/telegram-bot/deploy/kubernetes/kustomization.yaml applications/telegram-bot/deploy/kubernetes/deployment.yaml applications/telegram-bot/deploy/kubernetes/pvc.yaml
git commit -m "Add telegram bot Kubernetes base"
```

### Task 2: Kubernetes 사용 문서

**Files:**
- Create: `applications/telegram-bot/deploy/kubernetes/README.md`
- Modify: `applications/telegram-bot/README.md`

**Interfaces:**
- Consumes: Task 1의 Kustomize base 경로와 리소스 이름
- Produces: 로컬 렌더링, Secret 생성, remote base 고정, 이미지 SHA 고정 사용법

- [ ] **Step 1: 배포 README를 작성한다**

Create `applications/telegram-bot/deploy/kubernetes/README.md`:

````markdown
# Kubernetes

Telegram Bot의 재사용 가능한 Kustomize base입니다. Telegram long polling을 사용하므로 Service와 Ingress는 필요하지 않습니다.

## 리소스

- replica 1과 `Recreate` 전략을 사용하는 Deployment
- SQLite 데이터를 저장하는 1Gi `ReadWriteOnce` PVC
- 앱 이미지의 migration을 복사하고 Atlas로 적용하는 initContainer

Namespace와 Secret은 이 base에 포함되지 않습니다.

## Secret

배포할 Namespace에 Telegram Bot token을 생성합니다. 실제 token은 Git에 저장하지 않습니다.

```bash
kubectl create secret generic telegram-bot \
  --namespace <namespace> \
  --from-literal=TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
```

## 로컬 렌더링

```bash
kubectl kustomize applications/telegram-bot/deploy/kubernetes
```

## Remote base

소비 저장소에서는 매니페스트와 이미지 버전을 커밋 SHA로 고정합니다.

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: telegram-bot
resources:
  - namespace.yaml
  - github.com/moseoh/moseoh-lab//applications/telegram-bot/deploy/kubernetes?ref=<매니페스트 커밋 SHA>
images:
  - name: ghcr.io/moseoh/telegram-bot
    newTag: sha-<이미지 커밋 SHA>
```

PVC 용량이나 StorageClass는 소비 저장소의 patch에서 변경합니다.
````

- [ ] **Step 2: 앱 README에 Kubernetes 문서 링크를 추가한다**

Add this section after the existing Docker/Dokploy section in `applications/telegram-bot/README.md`:

```markdown
## Kubernetes

재사용 가능한 Kustomize base와 배포 방법은 [`deploy/kubernetes`](deploy/kubernetes/README.md)를 참고하세요.
```

- [ ] **Step 3: 문서 경로와 명령을 검증한다**

Run:

```bash
test -f applications/telegram-bot/deploy/kubernetes/README.md
rg -n 'Namespace와 Secret|kubectl create secret generic telegram-bot|ref=<매니페스트 커밋 SHA>|newTag: sha-<이미지 커밋 SHA>' applications/telegram-bot/deploy/kubernetes/README.md
rg -n 'deploy/kubernetes/README.md' applications/telegram-bot/README.md
git diff --check
```

Expected: 모든 명령이 exit code `0`이고 문서의 필수 안내가 출력된다.

- [ ] **Step 4: 문서를 커밋한다**

```bash
git add applications/telegram-bot/deploy/kubernetes/README.md applications/telegram-bot/README.md
git commit -m "Document telegram bot Kubernetes deployment"
```

### Task 3: 최종 회귀 검증

**Files:**
- Verify: `applications/telegram-bot/deploy/kubernetes/`
- Verify: `applications/telegram-bot/Dockerfile`

**Interfaces:**
- Consumes: Task 1과 Task 2의 전체 결과
- Produces: 렌더링 및 Docker 빌드 검증 증거

- [ ] **Step 1: Kubernetes base를 새로 렌더링하고 검증한다**

```bash
kubectl kustomize applications/telegram-bot/deploy/kubernetes >/tmp/telegram-bot-base-final.yaml
kubectl apply --dry-run=client -f /tmp/telegram-bot-base-final.yaml
```

Expected: Deployment와 PVC가 각각 `created (dry run)`으로 출력된다.

- [ ] **Step 2: Docker 이미지를 빌드한다**

```bash
docker build -f applications/telegram-bot/Dockerfile applications/telegram-bot
```

Expected: Docker build가 exit code `0`으로 완료된다.

- [ ] **Step 3: 작업 범위를 확인한다**

```bash
git status -sb
git diff main...HEAD --stat
git diff --check main...HEAD
```

Expected: 계획된 설계 문서, 계획 문서, Kubernetes base, README만 변경되며 diff check가 통과한다.
