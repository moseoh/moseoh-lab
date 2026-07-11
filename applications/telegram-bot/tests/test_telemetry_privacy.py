from pathlib import Path


def test_otel로_전송되는_loguru_메시지에_사용자_식별자를_넣지_않는다():
    source_root = Path(__file__).parents[1] / "src"
    forbidden = ("user_id", "user_name", "chat_id", "chat.id", "scope_id")

    violations = []
    for path in source_root.rglob("*.py"):
        for line_number, line in enumerate(path.read_text().splitlines(), start=1):
            if "logger." in line and any(value in line for value in forbidden):
                violations.append(f"{path.relative_to(source_root)}:{line_number}")

    assert violations == []
