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

## OpenTelemetry

Kubernetes base는 환경별 OTel Gateway 주소나 Grafana Cloud 인증정보를 포함하지 않습니다. 소비 저장소의 Kustomize overlay에서 Deployment에 endpoint를 주입합니다.

```yaml
patches:
  - target:
      kind: Deployment
      name: telegram-bot
    patch: |-
      - op: add
        path: /spec/template/spec/containers/0/env/-
        value:
          name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: http://otel-gateway.observability.svc.cluster.local:4317
```

`OTEL_EXPORTER_OTLP_ENDPOINT`가 없으면 애플리케이션 계측은 비활성화되고 Bot은 기존처럼 실행됩니다. stdout은 `kubectl logs` 확인용으로 유지하며, 이 앱의 로그를 Collector의 filelog receiver로 다시 수집하지 않습니다. Grafana에는 애플리케이션 OTel Logs SDK가 전송한 로그만 저장해 중복을 방지합니다.
