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
