---
name: "cmux"
description: "cmux 터미널 멀티플렉서 CLI를 사용하여 pane을 생성, 분할, 제어하는 방법을 안내한다. cmux로 pane을 띄우거나, 다른 pane에 명령을 보내거나, pane 화면을 읽거나, 레이아웃을 구성하려고 하면 이 스킬을 사용한다. 'pane 만들어줘', '오른쪽에 터미널 띄워줘', '다른 pane에 명령 보내줘', 'pane 출력 읽어와', 'cmux', '화면 분할' 같은 표현이 트리거다."
---

# cmux CLI 사용 가이드

cmux는 Unix 소켓 기반 터미널 멀티플렉서다. 이 스킬은 pane 생성, 명령 전송, 화면 읽기 등 자주 쓰는 패턴을 정리한다.

## 핵심 원칙

### surface ref는 반드시 동적으로 획득한다

cmux의 모든 pane/surface 조작은 `surface:<N>` 형태의 ref를 사용한다. 이 숫자는 세션마다 달라지므로 절대 하드코딩하지 않는다. 항상 명령 실행 결과에서 파싱하거나, `list-panes` / `identify`로 조회해서 사용한다.

### 환경변수

cmux 터미널 안에서는 아래 환경변수가 자동 설정된다:
- `CMUX_WORKSPACE_ID` — 현재 workspace (대부분의 명령에서 `--workspace` 기본값)
- `CMUX_SURFACE_ID` — 현재 surface
- `CMUX_SOCKET_PATH` — 소켓 경로 (기본: `/tmp/cmux.sock`)

## 명령 레퍼런스

### 현재 상태 확인

```bash
# 현재 pane/surface/workspace 정보 확인
cmux identify --json
# 반환 예시:
# {
#   "caller": { "surface_ref": "surface:1", "pane_ref": "pane:1", "workspace_ref": "workspace:1", ... },
#   "focused": { ... }
# }

# workspace 내 모든 pane 목록
cmux list-panes
# 출력 예시:
# * pane:1  [1 surface]  [focused]
#   pane:3  [1 surface]

# 특정 pane의 surface 확인
cmux list-pane-surfaces --pane pane:3
# 출력 예시:
# * surface:3  seongha.moon@host:~/path  [selected]
```

### pane 생성

```bash
# 새 pane 생성 (방향: left, right, up, down)
cmux new-pane --direction right
# 출력: OK surface:<N> pane:<N> workspace:<N>
# → surface ref를 파싱해서 이후 명령에 사용

# 기존 surface를 기준으로 분할
cmux new-split down --surface surface:3
# 출력: OK surface:<N> workspace:<N>
```

**출력 파싱 패턴**: `new-pane`과 `new-split`의 출력에서 surface ref를 추출하려면:
```bash
result=$(cmux new-pane --direction right 2>&1)
surface_ref=$(echo "$result" | grep -o 'surface:[0-9]*')
```

### 같은 pane에 surface(탭) 추가

우측 작업 pane 구조를 유지한 채 같은 pane 안에 worker 탭을 더 만들고 싶을 때는
`new-surface`를 사용한다. 이 방식은 split 레이아웃을 바꾸지 않고 같은 작업
pane 안에서 병렬 worker를 늘릴 때 적합하다.

```bash
# 예: 기존 작업 pane(pane:<N>)에 새 terminal surface 추가
result=$(cmux new-surface --pane pane:<N> 2>&1)
surface_ref=$(echo "$result" | grep -o 'surface:[0-9]*')

# 탭 이름 지정
cmux rename-tab --surface $surface_ref "<worker-name>-2"

# 같은 pane 안의 surface 목록 확인
cmux list-pane-surfaces --pane pane:<N>
```

권장 naming:

- 첫 worker: `<worker-name>`
- 추가 worker: `<worker-name>-2`, `<worker-name>-3`
- 또는 팀 규칙상 숫자만 붙이고 싶다면 `<worker-name>2`, `<worker-name>3`

추가 worker를 닫을 때는:

```bash
cmux close-surface --surface $surface_ref
```

즉, pane은 레이아웃 단위이고, 같은 pane 안의 surface는 병렬 worker 탭 단위로
생각하면 된다.

### 명령 전송

```bash
# pane에 텍스트 전송 (타이핑만 됨, 실행은 안 됨)
cmux send --surface surface:3 "echo hello"

# 실행하려면 Enter 키를 별도로 전송
cmux send-key --surface surface:3 Enter
```

텍스트 전송과 키 전송은 별개 동작이다. 명령을 실행시키려면 반드시 `send` 후 `send-key Enter`를 보내야 한다. 한 줄로 합치면:
```bash
cmux send --surface surface:3 "echo hello" && cmux send-key --surface surface:3 Enter
```

### 화면 읽기

```bash
# 현재 화면 읽기
cmux read-screen --surface surface:3

# 스크롤백 포함, 최근 N줄
cmux read-screen --surface surface:3 --scrollback --lines 200
```

결과 수집이나 완료 감지에 사용한다. 셸 프롬프트 패턴(예: `>`, `$`, `❯`)이 마지막 줄에 나타나면 이전 명령이 끝났다고 판단할 수 있다.

### 탭/pane 관리

```bash
# 탭 이름 변경 (pane 식별용)
cmux rename-tab --surface surface:3 "docs"

# pane 포커스
cmux focus-pane --pane pane:3

# surface 닫기
cmux close-surface --surface surface:3
```

### workspace 관리

```bash
# workspace 이름 변경
cmux rename-workspace "orchestration"
# 출력: OK workspace:<N>

# 현재 workspace 확인
cmux current-workspace

# 모든 workspace 목록
cmux list-workspaces
# 출력 예시:
# * workspace:1  orchestration  [selected]

# surface 상태 확인 (디버깅용)
cmux surface-health
# 출력 예시:
# surface:1  type=terminal in_window=true
```

### 알림과 결과 수집

에이전트(cx/cc)가 작업을 완료하면 cmux notification이 자동 발생하며, 응답 본문이 포함된다. `read-screen` 없이 `list-notifications`만으로 결과를 수집할 수 있다.

```bash
# 작업 전송 전 알림 초기화 (이전 결과와 섞이지 않게)
cmux clear-notifications

# (작업 전송 후, 사용자가 결과 확인을 요청하면)

# 알림 목록 확인 — 각 pane의 에이전트 응답 본문이 포함됨
cmux list-notifications

# 수동 알림 보내기
cmux notify --title "작업 완료" --body "BE 빌드 성공"
```

중요:

- `list-notifications`는 에이전트 완료 알림 수집에는 유효하다.
- 수동 `cmux notify`는 실행은 되더라도 `list-notifications`에 항상 다시 잡힌다고
  가정하면 안 된다.
- 따라서 결과 수집 우선순위는 아래처럼 잡는다.

1. `list-notifications`로 에이전트 완료 알림 확인
2. 필요한 surface를 `read-screen`으로 직접 읽기
3. 수동 `notify`는 보조 신호로만 사용

## 자주 쓰는 워크플로

### 오른쪽 수직 3분할 레이아웃 만들기

오케스트레이션 pane(왼쪽)에서 오른쪽에 3개 pane을 만드는 패턴:

```bash
# 1단계: 오른쪽에 첫 pane
result1=$(cmux new-pane --direction right 2>&1)
s1=$(echo "$result1" | grep -o 'surface:[0-9]*')

# 2단계: 첫 pane 아래로 분할
result2=$(cmux new-split down --surface $s1 2>&1)
s2=$(echo "$result2" | grep -o 'surface:[0-9]*')

# 3단계: 두 번째 pane 아래로 분할
result3=$(cmux new-split down --surface $s2 2>&1)
s3=$(echo "$result3" | grep -o 'surface:[0-9]*')

# 4단계: 이름 지정
cmux rename-tab --surface $s1 "work-a"
cmux rename-tab --surface $s2 "work-b"
cmux rename-tab --surface $s3 "work-c"
```

### pane에서 에이전트 실행

```bash
# codex (기본 alias: cx) — 최초 실행
cmux send --surface $s1 "cd /path/to/project && cx \"작업 내용\"" && cmux send-key --surface $s1 Enter

# claude code (alias: cc) — 사용자가 명시적으로 요청할 때
cmux send --surface $s1 "cd /path/to/project && cc \"작업 내용\"" && cmux send-key --surface $s1 Enter
```

### 실행 중인 에이전트에 추가 입력

에이전트(cx/cc)가 이미 실행 중인 pane에는 셸 명령이 아니라 에이전트의 입력 프롬프트(`›`)에 직접 텍스트가 들어간다. 세션을 종료하지 않고 추가 작업을 보낼 수 있다.

```bash
# 에이전트가 대기 중인지 확인 (› 프롬프트가 보이면 대기 상태)
cmux read-screen --surface $s1 --lines 3

# 대기 상태이면 바로 추가 입력
cmux send --surface $s1 "추가 작업 내용" && cmux send-key --surface $s1 Enter
```

에이전트가 아직 응답을 생성 중일 때 입력을 보내면 꼬일 수 있다. 반드시 `read-screen`으로 `›` 프롬프트가 나타난 것을 확인한 후 전송한다.

### 같은 프로젝트를 여러 worker로 병렬 실행

레이아웃은 그대로 두고, 같은 프로젝트 pane 안에 surface를 여러 개 두어 병렬
worker를 운용할 수 있다.

예: 기존 작업 pane에 추가 worker를 붙여 병렬 작업

```bash
# 1) 기존 작업 pane 확인
cmux list-pane-surfaces --pane pane:<N>

# 2) 새 worker surface 추가
result=$(cmux new-surface --pane pane:<N> 2>&1)
s2=$(echo "$result" | grep -o 'surface:[0-9]*')
cmux rename-tab --surface $s2 "<worker-name>-2"

# 3) 새 worker에서 에이전트 실행
cmux send --surface $s2 "cd /path/to/project && cx \"작업 내용\"" && cmux send-key --surface $s2 Enter

# 4) 결과는 알림 또는 직접 화면 읽기로 수집
cmux list-notifications
cmux read-screen --surface $s2 --scrollback --lines 120

# 5) 작업 종료 후 worker 정리
cmux close-surface --surface $s2
```

이 패턴은 아래 상황에 적합하다:

- 같은 저장소에서 서로 다른 파일 묶음을 병렬 처리할 때
- 조사 작업과 구현 작업을 분리할 때
- 한 worker가 오래 걸리는 동안 같은 프로젝트 backlog를 더 처리할 때

주의:

- 같은 저장소라도 write scope가 겹치면 surface를 늘리지 말고 순차 처리하는 편이
  안전하다.
- worker surface별로 책임 파일이나 산출물 파일을 분리해 두는 것이 좋다.

### 기존 pane 재사용 (이름으로 찾기)

이미 띄운 pane이 있을 수 있으므로, 새로 만들기 전에 먼저 확인한다:

```bash
# 모든 pane의 surface와 탭 이름 확인
cmux list-panes
# 각 pane에 대해:
cmux list-pane-surfaces --pane pane:<N>
# 출력에서 탭 이름(예: "work-a", "<worker-name>-2")을 확인하여 기존 surface ref를 재사용
```

## 주의사항

- `send`는 타이핑만 한다. 실행하려면 `send-key Enter`가 필수다.
- `--json` 플래그는 `identify`, `list-*` 등 조회 명령에서 구조화된 출력을 준다. `new-pane`/`new-split`은 `OK surface:<N> ...` 형태의 플레인 텍스트를 반환한다.
- surface ref 숫자는 세션 내에서 단조 증가하지만, 닫힌 surface의 번호가 재사용되지는 않는다.
- cmux 터미널이 아닌 환경에서는 소켓 연결이 실패한다 (exit code 141).
