from pathlib import Path


APP_ROOT = Path(__file__).parents[1]


def test_kubernetes_base에_otel_endpoint를_고정하지_않는다():
    deployment = (APP_ROOT / "deploy/kubernetes/deployment.yaml").read_text()

    assert "OTEL_EXPORTER_OTLP_ENDPOINT" not in deployment
    assert "otel-gateway" not in deployment


def test_kubernetes_readme가_overlay_endpoint_주입을_안내한다():
    readme = (APP_ROOT / "deploy/kubernetes/README.md").read_text()

    assert "OTEL_EXPORTER_OTLP_ENDPOINT" in readme
    assert "http://otel-gateway.observability.svc.cluster.local:4317" in readme
    assert "Collector의 filelog receiver" in readme


def test_app_readme가_telemetry와_벤치마크_정책을_설명한다():
    readme = (APP_ROOT / "README.md").read_text()

    assert "Metrics는 전부 수집" in readme
    assert "Trace는 100%" in readme
    assert "정상 Trace는 1~5% sampling" in readme
    assert "Logs는 WARN 이상" in readme
    assert "테스트 종료 후 Collector 수집 대상에서 제거" in readme
