---
name: "cmux"
description: "cmux 터미널 멀티플렉서 CLI를 사용하여 pane과 surface를 생성, 제어, 조회하는 방법을 안내한다. 레이아웃 정책은 갖지 않고, 재사용 가능한 조작 primitives만 다룬다."
---

# cmux CLI 사용 가이드

`cmux` 스킬은 레이아웃 정책이 아니라 조작 방법만 다룬다.

## 핵심 원칙

- `surface:<N>`, `pane:<N>` 같은 ref는 항상 동적으로 조회한다.
- pane은 레이아웃 단위다.
- surface는 같은 pane 안의 탭/worker 단위다.
- 명령 실행은 `send` 후 `send-key Enter`까지 해야 한다.

주요 조회:

```bash
cmux identify --json
cmux list-panes
cmux list-pane-surfaces --pane pane:<N>
```

## pane 생성

```bash
result=$(cmux new-pane --direction right 2>&1)
surface_ref=$(echo "$result" | grep -o 'surface:[0-9]*')
pane_ref=$(echo "$result" | grep -o 'pane:[0-9]*')
```

기존 surface 기준 분할:

```bash
result=$(cmux new-split down --surface surface:<N> 2>&1)
surface_ref=$(echo "$result" | grep -o 'surface:[0-9]*')
```

## surface 추가/삭제

같은 pane 안에 worker 탭을 추가할 때:

```bash
result=$(cmux new-surface --pane pane:<N> 2>&1)
surface_ref=$(echo "$result" | grep -o 'surface:[0-9]*')
cmux rename-tab --surface $surface_ref "<worker-name>-1"
```

삭제:

```bash
cmux close-surface --surface surface:<N>
```

## 이름과 재사용

```bash
cmux rename-tab --surface surface:<N> "<name>"
cmux list-pane-surfaces --pane pane:<N>
```

권장 규칙:

- placeholder: `<pane-name>`
- worker: `<pane-name>-1`, `<pane-name>-2`

## 명령 전송

```bash
cmux send --surface surface:<N> "echo hello"
cmux send-key --surface surface:<N> Enter
```

에이전트 최초 실행:

```bash
cmux send --surface surface:<N> "cd /path/to/project && cx \"작업 내용\""
cmux send-key --surface surface:<N> Enter
```

추가 입력 전에는 대기 상태를 먼저 확인한다.

## 화면 읽기

```bash
cmux read-screen --surface surface:<N>
cmux read-screen --surface surface:<N> --scrollback --lines 200
```

용도:

- 에이전트 대기 여부 확인
- 결과 확인
- 실패 원인 확인

## 결과 수집

우선순위:

1. `cmux list-notifications`
2. `cmux read-screen --surface ...`

주의:

- 에이전트 완료 알림은 `list-notifications`로 잘 수집된다.
- 수동 `cmux notify`는 실행되더라도 `list-notifications`에 항상 잡힌다고 가정하지 않는다.
- 따라서 `notify`는 보조 신호로만 본다.

관련 명령:

```bash
cmux clear-notifications
cmux list-notifications
cmux notify --title "작업 완료" --body "message"
```

## 최소 워크플로

placeholder만 있는 pane에 worker를 하나 추가해서 실행:

```bash
cmux list-pane-surfaces --pane pane:<N>
result=$(cmux new-surface --pane pane:<N> 2>&1)
s=$(echo "$result" | grep -o 'surface:[0-9]*')
cmux rename-tab --surface $s "<pane-name>-1"
cmux send --surface $s "cd /path/to/project && cx \"작업 내용\""
cmux send-key --surface $s Enter
```

결과 확인 후 정리:

```bash
cmux list-notifications
cmux read-screen --surface $s --scrollback --lines 120
cmux close-surface --surface $s
```

## 기억할 것

- 레이아웃은 `orch` 같은 상위 스킬이 결정한다.
- `cmux`는 만들고, 이름 붙이고, 보내고, 읽고, 닫는 도구다.
