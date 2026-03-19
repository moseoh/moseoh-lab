---
name: "tmux"
description: "tmux 터미널 멀티플렉서를 사용하여 pane을 생성, 분할, 제어하는 방법을 안내한다. tmux로 pane을 띄우거나, 다른 pane에 명령을 보내거나, pane 화면을 읽거나, 레이아웃을 구성하려고 하면 이 스킬을 사용한다. 'pane 만들어줘', '터미널 띄워줘', '다른 pane에 명령 보내줘', 'pane 출력 읽어와', 'tmux', '화면 분할' 같은 표현이 트리거다."
---

# tmux 사용 가이드

tmux는 터미널 멀티플렉서다. 이 스킬은 pane 생성, 명령 전송, 화면 읽기 등 자주 쓰는 패턴을 정리한다.

## 핵심 원칙

### pane 식별은 타겟 지정으로 한다

tmux의 pane은 `{session}:{window}.{pane}` 형식으로 지정한다. 예: `orch:1.0`, `orch:1.1`. pane index는 `list-panes`로 동적으로 확인한다.

### 세션 기반 구조

tmux는 session > window > pane 계층이다. 오케스트레이션에서는 하나의 세션, 하나의 윈도우 안에서 여러 pane을 사용한다.

## 명령 레퍼런스

### 현재 상태 확인

```bash
# 현재 세션 목록
tmux list-sessions
# 출력 예시:
# orch: 1 windows (created ...)

# 현재 윈도우의 모든 pane 목록
tmux list-panes -t orch
# 출력 예시:
# 0: [80x24] [history 0/50000] (active)
# 1: [80x24] [history 0/50000]
# 2: [80x24] [history 0/50000]

# pane 제목 확인
tmux list-panes -t orch -F '#{pane_index}: #{pane_title}'
```

### pane 생성

```bash
# 수평 분할 (오른쪽에 새 pane)
tmux split-window -h -t orch

# 수직 분할 (아래에 새 pane)
tmux split-window -v -t orch

# 크기를 퍼센트로 지정
tmux split-window -h -t orch -p 25
```

cmux와 달리 `split-window -p`로 퍼센트 기반 크기 지정이 가능하다.

### 균등 분할

```bash
# 수평 균등 분할 (1:1:1:1)
tmux select-layout -t orch even-horizontal

# 수직 균등 분할
tmux select-layout -t orch even-vertical

# 타일 배치 (격자형)
tmux select-layout -t orch tiled
```

pane을 여러 개 만든 후 `select-layout even-horizontal`을 실행하면 한 줄로 균등 분할된다.

### 명령 전송

```bash
# pane에 텍스트 전송 + 실행 (Enter 포함)
tmux send-keys -t orch:1.1 "echo hello" Enter

# Enter 없이 텍스트만 전송
tmux send-keys -t orch:1.1 "echo hello"

# 특수 키 전송
tmux send-keys -t orch:1.1 Escape
tmux send-keys -t orch:1.1 C-c
```

cmux와 달리 `send-keys`에 `Enter`를 바로 붙일 수 있어서 한 번에 전송+실행이 가능하다.

### 화면 읽기

```bash
# 현재 화면 캡처
tmux capture-pane -t orch:1.1 -p

# 스크롤백 포함 (최근 200줄)
tmux capture-pane -t orch:1.1 -p -S -200
```

`-p`는 stdout으로 출력, `-S -200`은 시작점을 200줄 전으로 설정한다.

### pane 관리

```bash
# pane 제목 설정 (식별용)
tmux select-pane -t orch:1.1 -T "docs"

# pane 포커스
tmux select-pane -t orch:1.1

# pane 닫기
tmux kill-pane -t orch:1.1

# pane 크기 조절 (칸 단위)
tmux resize-pane -t orch:1.1 -R 10
tmux resize-pane -t orch:1.1 -L 10
```

### 세션/윈도우 관리

```bash
# 새 세션 생성
tmux new-session -d -s orch

# 윈도우 이름 변경
tmux rename-window -t orch:1 "orchestration"

# 세션 종료
tmux kill-session -t orch
```

### 결과 수집

tmux에는 cmux의 `list-notifications` 같은 알림 시스템이 없다. 결과 수집은 `capture-pane`으로 화면을 읽어서 처리한다.

```bash
# 각 pane의 출력 수집
tmux capture-pane -t orch:1.1 -p -S -200
tmux capture-pane -t orch:1.2 -p -S -200
tmux capture-pane -t orch:1.3 -p -S -200
```

### 완료 감지 (hook)

tmux hook은 실제로 동작한다. pane에서 명령이 끝나면 감지할 수 있다.

```bash
# pane 변경 시 hook 실행
tmux set-hook -t orch pane-exited 'run-shell "echo done > /tmp/pane_done"'

# hook 목록 확인
tmux show-hooks -t orch

# hook 제거
tmux set-hook -u -t orch pane-exited
```

## 자주 쓰는 워크플로

### 수평 4분할 균등 레이아웃 만들기

```bash
# 세션 생성 (없으면)
tmux new-session -d -s orch 2>/dev/null || true

# pane 3개 추가 (총 4개)
tmux split-window -h -t orch
tmux split-window -h -t orch
tmux split-window -h -t orch

# 균등 분할
tmux select-layout -t orch even-horizontal

# 이름 지정
tmux select-pane -t orch:1.0 -T "orch"
tmux select-pane -t orch:1.1 -T "docs"
tmux select-pane -t orch:1.2 -T "be"
tmux select-pane -t orch:1.3 -T "fe"
```

### pane에서 에이전트 실행

```bash
# codex (기본 alias: cx) — 최초 실행
tmux send-keys -t orch:1.1 "cd /path/to/project && cx \"작업 내용\"" Enter

# claude code (alias: cc) — 사용자가 명시적으로 요청할 때
tmux send-keys -t orch:1.1 "cd /path/to/project && cc \"작업 내용\"" Enter
```

### 실행 중인 에이전트에 추가 입력

에이전트(cx/cc)가 이미 실행 중인 pane에는 에이전트의 입력 프롬프트에 직접 텍스트가 들어간다. 세션을 종료하지 않고 추가 작업을 보낼 수 있다.

```bash
# 에이전트가 대기 중인지 확인
tmux capture-pane -t orch:1.1 -p | tail -3

# 대기 상태이면 바로 추가 입력
tmux send-keys -t orch:1.1 "추가 작업 내용" Enter
```

에이전트가 응답 생성 중일 때 입력을 보내면 꼬일 수 있다. 반드시 `capture-pane`으로 대기 상태를 확인한 후 전송한다.

### 기존 pane 재사용 (이름으로 찾기)

```bash
# pane 제목으로 확인
tmux list-panes -t orch -F '#{pane_index}: #{pane_title}'
# 출력 예시:
# 0: orch
# 1: docs
# 2: be
# 3: fe
```

## 주의사항

- `send-keys`에 `Enter`를 붙이면 바로 실행된다. cmux처럼 별도 `send-key Enter`가 필요 없다.
- pane index는 0부터 시작한다.
- tmux 세션이 없으면 `new-session -d -s orch`로 먼저 생성해야 한다.
- 현재 터미널이 tmux 안이 아니어도 `-t` 타겟으로 원격 제어 가능하다.
