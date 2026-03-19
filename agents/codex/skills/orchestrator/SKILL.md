---
name: "orch"
description: "사용자가 /orch 명령으로 명시적으로 호출할 때만 사용하는 멀티 pane 오케스트레이션 스킬이다. cmux pane으로 여러 작업 저장소에 에이전트(cx/cc)를 띄우고 작업을 분배한다. 필요하면 같은 작업 pane 안에 worker surface를 추가해 병렬 fan-out한다. 자동 트리거하지 않는다."
---

# 멀티 Pane 오케스트레이션

하나의 오케스트레이션 pane에서 여러 작업 pane에 작업을 분배하고, 각 pane에서
에이전트(cx 또는 cc)를 실행하며, 결과를 수집하는 워크플로다. 필요하면 같은
작업 pane 안에 worker surface를 추가해 병렬 fan-out할 수 있다.

이 스킬은 "무엇을, 어떤 순서로 할지"에 집중한다. pane을 어떻게 만들고 제어하는지는 터미널 스킬(cmux skill)이 담당한다.

## 터미널 스킬

pane 제어에 사용할 터미널 스킬: **cmux** (기본)

아래 워크플로에서 "pane 생성", "명령 전송", "화면 읽기", "결과 수집" 등은 모두 해당 터미널 스킬의 명령을 사용하여 수행한다.

## 레이아웃

```
┌───────────┬───────────┬───────────┬───────────┐
│           │           │           │           │
│   orch    │  work-a   │  work-b   │  work-c   │
│           │           │           │           │
└───────────┴───────────┴───────────┴───────────┘
```

기본 레이아웃은 좌측 `orch` pane 1개와, 그 오른쪽에 `orchestrator.json`에
정의된 작업 pane들을 가로로 배치한 구조다. pane 수와 이름은
`orchestrator.json`의 설정에 따라 달라진다.

기본 원칙:

- 기본 레이아웃은 `orch | work-a | work-b | work-c` 같은 가로 배치를 유지한다.
- `orchestrator.json`에 정의된 작업 pane은 작업 실행 시 항상 전부 먼저 구성한다.
- 각 작업 pane의 첫 번째 surface는 에이전트를 띄우지 않는 터미널 placeholder로 유지한다.
- 병렬 작업이 필요할 때는 기본 pane 레이아웃을 더 쪼개기보다, 기존 작업 pane
  안에 worker surface를 추가한다.
- 에이전트 worker surface는 두 번째 surface부터 사용하며, 이름은
  `<pane-name>-1`, `<pane-name>-2`, `<pane-name>-3`처럼 붙인다.

## 설정

프로젝트 루트에 `orchestrator.json`이 있어야 한다. 없으면 사용자에게 경로를 물어서 생성한다.

이 규칙은 다른 모든 단계보다 우선한다. `orchestrator.json`이 없으면 pane 생성, 외부 경로 확인, 예시 경로 검증, 작업 분배를 진행하지 않는다.

```json
{
  "panes": {
    "work-a": {
      "dir": "/path/to/project-a",
      "agent": "cx",
      "alias": ["별칭-a"]
    },
    "work-b": {
      "dir": "/path/to/project-b",
      "agent": "cx",
      "alias": ["별칭-b"]
    },
    "work-c": {
      "dir": "/path/to/project-c",
      "agent": "cx",
      "alias": ["별칭-c"]
    }
  }
}
```

- `dir`: 해당 pane이 작업할 디렉토리 경로
- `agent`: 기본 에이전트. `cx`(codex, 기본값) 또는 `cc`(claude code). 사용자가 "claude로 실행해줘"라고 하면 해당 pane만 `cc`로 오버라이드한다
- `alias` (선택): 사용자가 pane을 지칭할 때 쓸 수 있는 별칭 목록

위 JSON 블록은 형식 예시일 뿐이다. 여기에 있는 경로, pane 이름, agent 값을 현재 프로젝트의 실제 값으로 간주하면 안 된다.

## 런타임 상태 관리

오케스트레이션 중 생성한 pane/surface ref, worker 배정 상태 같은 운영 정보는
사용자 응답에 계속 노출하지 말고 프로젝트 루트의 런타임 JSON 파일로 관리한다.

권장 파일:

```text
state/cmux-session.json
```

이 파일에는 최소한 아래 정보를 유지한다.

- workspace ref
- orchestration pane/surface 정보
- 각 작업 pane ref
- 각 pane의 placeholder surface ref
- worker surface ref와 이름
- worker별 현재 배정 task

예시 구조:

```json
{
  "workspace": { "ref": "workspace-or-window-id" },
  "orchestration": {
    "pane": "pane:2",
    "surfaces": [
      { "ref": "surface:3", "name": "orch", "role": "orchestration" }
    ]
  },
  "workspaces": {
    "work-a": {
      "pane": "pane:6",
      "placeholder": {
        "ref": "surface:11",
        "name": "work-a",
        "dir": "/path/to/project-a"
      },
      "workers": [
        { "ref": "surface:14", "name": "work-a-1", "task": "T-..." }
      ]
    }
  }
}
```

운영 규칙:

- pane/surface를 새로 만들거나 닫을 때마다 JSON을 갱신한다.
- worker에 task를 배정하거나 회수할 때도 JSON을 갱신한다.
- 실제 cmux 상태와 JSON이 어긋난 것 같으면 cmux를 다시 조회해 JSON을 복구한다.
- 이 파일은 내부 운영 상태 파일이지, 사용자 보고 문서가 아니다.

## 워크플로

### 1단계: 설정 로드 (전제 조건)

다른 모든 단계에 앞서 반드시 `orchestrator.json`이 존재하는지 확인한다. 이 파일이 없으면 어떤 pane을 어떤 디렉토리에서 띄울지 알 수 없으므로 이후 단계를 진행할 수 없다.

- **파일이 있으면**: 읽어서 pane 구성을 파악하고 2단계로 진행한다.
- **파일이 없으면**: 사용자에게 각 프로젝트의 이름과 디렉토리 경로를 물어서 생성한 후 진행한다.

필수 행동 규칙:

- `orchestrator.json`이 없을 때는 먼저 사용자에게 필요한 pane 목록과 각 디렉토리 경로를 요청한다.
- 사용자 답변 전에는 현재 작업 디렉터리 밖의 경로 존재 여부를 확인하지 않는다.
- 사용자 답변 전에는 임의의 pane 이름을 기본값처럼 전제하지 않는다.
- 설정 파일 생성은 사용자에게 받은 값으로만 수행한다.

권장 질문 항목:

- 어떤 pane들을 둘지
- 각 pane의 실제 디렉토리 경로
- pane별 기본 agent가 `cx`인지 `cc`인지
- 필요한 alias가 있는지

### 2단계: pane 확보

터미널 스킬을 사용하여 기존 pane을 먼저 확인하고, 없는 pane만 새로 만든다. 이미 작업 중인 pane을 날리지 않기 위해서다.

- 기존 pane 목록 조회
- 탭/윈도우 이름으로 매칭하여 기존 pane을 재사용
- 없는 pane만 새로 생성하고 이름을 지정
- 각 pane의 참조(surface ref, pane index 등)를 보관
- 각 pane의 첫 번째 surface는 placeholder 터미널로 유지한다
- 확보한 pane/surface 정보를 런타임 JSON에 기록한다

이 단계의 목표는 "필요한 pane을 그때그때 만드는 것"이 아니라, 설정된 작업 pane을
항상 전부 준비해 두는 것이다.

placeholder surface 규칙:

- 각 작업 pane의 첫 surface 이름은 pane 이름 그대로 둔다
- 이 surface는 사용자의 수동 작업 공간 겸 placeholder다
- 기본적으로 에이전트는 이 surface에 띄우지 않는다
- 에이전트를 실행할 때는 같은 pane 안에 새 surface를 추가해서 사용한다

이 단계에서 보관해야 할 것:

- 기본 pane ref
- placeholder surface ref
- 같은 pane 안에 추가된 worker surface ref 목록

즉, 오케스트레이션 관점에서 관리 대상은 "pane만"이 아니라 "pane + worker
surface 집합"이다.

### 3단계: 작업 분배

사용자의 요청에서 각 pane별 작업을 추출한다. 사용자가 명시적으로 pane별 작업을 나누지 않았다면, 작업 성격에 따라 적절히 분배한다.

각 pane에 터미널 스킬을 사용하여 명령을 전송한다. 이때 pane 상태에 따라 전송 방식이 달라진다:

**worker surface가 아직 없는 pane** — 최초 실행:

- placeholder surface는 그대로 둔다
- 같은 pane에 새 worker surface를 만든다
- 새 worker surface에서 디렉토리 이동 + 에이전트(cx/cc) 실행 + 프롬프트를 한 번에 전송

**에이전트 worker surface가 이미 있는 pane (대기 상태)** — 추가 작업:

- 적절한 worker surface를 먼저 고른다
- 해당 worker가 대기 중인지 확인한다
- 대기 상태이면 그 worker에 프롬프트만 전송한다

에이전트가 응답 생성 중일 때 입력을 보내면 꼬이므로, 반드시 대기 상태를 확인한 후 전송한다.

에이전트 선택:

- 기본: `orchestrator.json`의 `agent` 값 (보통 `cx`)
- 사용자가 "claude로 해줘" 또는 "cc로 실행해줘"라고 하면 해당 pane만 `cc` 사용
- 특정 pane만 다른 에이전트를 쓰고 싶으면 해당 pane만 오버라이드한다

### 3-1단계: 병렬 fan-out 판단

기본은 pane당 worker 1개다. 다만 아래 조건이면 같은 작업 pane 안에 worker
surface를 추가해 병렬 fan-out한다.

- 같은 저장소 안에서 서로 다른 하위 작업으로 자연스럽게 분리될 때
- 산출물 파일이 worker별로 분리 가능할 때
- 한 worker가 조사, 다른 worker가 구현처럼 역할을 나눌 수 있을 때
- 기존 worker가 오래 걸리는 동안 같은 pane backlog를 더 처리할 수 있을 때
- 다른 pane이 idle인데 전체 backlog가 남아 있을 때

반대로 아래 조건이면 fan-out하지 않는다.

- 같은 파일을 동시에 수정할 가능성이 높을 때
- 결과가 한 파일에 강하게 얽혀 있어 병합 비용이 큰 때
- 짧은 작업이라 나누는 오버헤드가 더 큰 때

권장 naming:

- placeholder surface: `<pane-name>`
- 첫 번째 agent worker: `<pane-name>-1`
- 추가 worker: `<pane-name>-2`, `<pane-name>-3`

예: `work-b`, `work-b-1`, `work-b-2`

fan-out 방식:

1. 먼저 pane의 placeholder surface를 확인한다.
2. 첫 agent worker가 없으면 같은 pane에 새 surface를 만들고 `<pane-name>-1`로 이름 붙인다.
3. 추가 병렬이 필요하면 `<pane-name>-2`, `<pane-name>-3`를 같은 방식으로 만든다.
4. worker를 런타임 JSON에 기록하고 현재 task를 연결한다.
5. worker별 책임 범위와 산출물 파일을 분리한다.
6. 결과 수집 시 worker별 결과를 먼저 확인한 뒤 pane 단위로 병합한다.

필수 규칙:

- placeholder surface는 에이전트 전용 surface로 재사용하지 않는다.
- worker를 늘릴 때는 같은 저장소라도 write scope를 명시적으로 분리한다.
- worker별 결과 파일을 따로 두거나, 적어도 worker별 섹션을 나눠 기록한다.
- 한 worker가 응답 생성 중이면 그 surface에는 새 입력을 보내지 않는다.

### 4단계: 결과 수집

작업 분배 전에 이전 결과를 초기화해둔다. 에이전트(cx/cc)가 작업을 완료하면 터미널의 알림/출력을 통해 결과를 확인할 수 있다.

사용자가 "결과 확인해줘", "다 끝났어?" 등으로 요청하면 터미널 스킬을 사용하여 결과를 수집한다. 수집한 결과를 pane별로 요약하여 사용자에게 보고한다. 아직 완료되지 않은 pane이 있으면 작업 진행 중으로 안내한다.

결과 수집 순서:

1. `list-notifications`로 에이전트 완료 알림 확인
2. 필요한 worker surface를 `read-screen`으로 직접 확인
3. worker별 결과를 pane 단위로 병합
4. 최종적으로 사용자에게 pane 기준으로 보고

수동 `notify`는 보조 수단일 뿐, 항상 수집 가능한 신호라고 가정하지 않는다.

사용자 보고 규칙:

- 사용자에게는 "어떤 작업을 어디에 분배했는지", "무엇이 끝났는지", "무엇이
  진행 중인지"를 중심으로 보고한다.
- 병렬 작업을 실행한 직후에는 worker별 분배 목록을 먼저 짧게 알려준다.
- 이때 보고 형식은 내부 ref가 아니라 task 중심으로 적는다.
  - 예: `docs-1: Site 신청/전환 흐름 문서`
  - 예: `server-1: 최신 OpenAPI 기준 수동 REST/예외 경로 분류`
- `surface:11`, `pane:6` 같은 cmux 내부 식별자는 기본적으로 사용자 응답에
  노출하지 않는다.
- 내부 식별자가 필요한 경우는 디버깅, 복구, 또는 사용자가 명시적으로 요청한
  경우로 한정한다.
- 내부 식별자는 런타임 JSON에서 관리하고, 사용자 응답은 task 중심으로 요약한다.

### 완료 알림 규칙

병렬 작업을 실행한 뒤, 오케스트레이션 에이전트는 사용자에게
"어떤 worker 완료를 보면 나에게 알려주면 되는지"를 함께 요청해야 한다.
핵심은 "어떤 worker들을 묶어서 알려달라고 할지"와 "끝나는 즉시 알려달라고 할지"를
명확히 정하는 것이다.

완료 알림 방식은 두 가지가 기본값이다.

- `grouped completion`
  - 지정한 worker 묶음이 전부 끝난 뒤 한 번에 보고한다
- `immediate completion`
  - 각 worker가 끝나는 즉시 개별 보고한다

오케스트레이션 에이전트가 사용자에게 요청하는 방식:

- 전부 완료 후 다음 단계로 넘어가야 하는 경우
  - `이 4개 작업은 전부 끝나면 알려주세요.`
- 일부는 묶고 일부는 즉시 받아야 하는 경우
  - `docs-1, docs-2는 같이 끝나면 알려주시고, server-1과 web-1은 끝나는대로 알려주세요.`
- 특정 조합이 끝나야 다음 작업을 열 수 있는 경우
  - `docs-1, server-1이 끝나면 먼저 알려주세요. 나머지는 계속 진행시키겠습니다.`
- 먼저 끝나는 것부터 다음 분배에 활용할 수 있는 경우
  - `먼저 끝나는 worker가 있으면 바로 알려주세요.`

권장 내부 표현:

```json
{
  "completion_policy": {
    "groups": [
      {
        "mode": "grouped",
        "workers": ["docs-1", "docs-2"]
      },
      {
        "mode": "immediate",
        "workers": ["server-1", "web-1"]
      }
    ]
  }
}
```

기본 요청 규칙:

- 사용자가 별도 기준을 아직 주지 않았다면, 오케스트레이션 에이전트가
  분배 직후 완료 알림 요청 문구를 먼저 제안한다.
- 이 요청은 "내가 어떤 완료 신호를 기다리고 있는지"를 사용자에게 명확히 알려주는
  용도다.
- 사용자가 이후 `다 끝났다`, `docs 둘 다 끝났다`, `server 먼저 끝났다`처럼
  알려주면 그 신호를 completion policy에 맞춰 해석한다.

권장 요청 형식:

- `전부 끝나면 알려주세요`
- `A, B는 같이 끝나면 알려주세요`
- `C, D는 끝나는대로 알려주세요`
- `A/B가 끝나면 먼저 알려주시고, 나머지는 계속 보겠습니다`

사용자 응답 해석:

- `다 끝났다`
  - 전체 grouped completion 조건이 충족된 것으로 본다
- `docs 둘 다 끝났다`
  - 해당 grouped completion 묶음이 충족된 것으로 본다
- `server 끝났다`
  - 해당 immediate completion worker가 완료된 것으로 본다
- `docs-1, server-1 끝났다`
  - 조건부 grouped completion 또는 복수 immediate completion으로 해석한다

필수 규칙:

- 완료 알림 정책을 해석했으면 런타임 JSON에도 기록한다.
- 병렬 작업을 시작한 직후에는 사용자에게 완료 알림 요청 문구를 함께 전달한다.
- grouped completion 묶음은 일부 worker만 끝났다고 바로 사용자에게 완료로 보고하지 않는다.
- immediate completion worker는 완료 확인 즉시 사용자에게 짧게 알린다.
- 최종 결과 수집/요약은 완료 알림 정책과 별개로, 사용자의 다음 지시에 따라 진행할 수 있다.

## 사용자 요청 해석 가이드

사용자의 요청은 다양한 형태로 올 수 있다. 아래는 해석 패턴이다:

### 전체 분배형

> "API 기능을 추가해줘"

하나의 기능을 여러 작업 pane으로 나눠서 분배한다:

- 문서/기획 pane: 관련 문서 작성
- 서버/API pane: 엔드포인트 구현
- 클라이언트/UI pane: 호출 UI 구현

### 개별 지정형

> "작업 A에서는 인증 미들웨어 추가하고, 작업 B에서는 로그인 페이지 만들어줘"

사용자가 지정한 대로 각 pane에 분배한다. 언급되지 않은 pane은 건드리지 않는다.

### 단일 pane형

> "특정 pane에 작업 보내줘: 데이터베이스 마이그레이션 실행"

특정 pane 하나에만 작업을 보낸다.

### 에이전트 오버라이드형

> "특정 pane은 claude로 실행해줘"

해당 pane만 `cc`로 에이전트를 변경한다.

### 내부 병렬형

> "이 작업은 같은 저장소 안에서 둘로 나눠서 병렬로 처리해"

같은 pane 안에 worker surface를 추가해 분배한다.

- placeholder: 기존 pane surface 유지
- 첫 worker: `<pane-name>-1`
- 추가 worker: `<pane-name>-2`, `<pane-name>-3`
- 산출물도 worker별로 분리해서 받는다

## 주의사항

- pane을 새로 만들기 전에 반드시 기존 pane을 확인한다. 이미 작업 중인 에이전트가 있을 수 있다.
- 작업 실행 시에는 설정된 work pane을 전부 먼저 준비하고, 각 pane의 첫 surface를
  placeholder 터미널로 유지한다.
- 에이전트가 실행 중인 pane에 새 명령을 보내면 입력이 꼬인다. 기존 작업 완료를 확인한 후 전송한다.
- 기본 가로 pane 구조는 유지하고, 추가 병렬이 필요하면 같은 pane 안에 worker
  surface를 추가한다.
- 에이전트는 항상 placeholder가 아닌 worker surface(`<pane-name>-1`부터)에 띄운다.
- 한 pane 안에 worker를 늘릴 때는 파일 ownership과 결과 병합 방식을 먼저 정한다.
- 프롬프트에 큰따옴표가 포함되면 이스케이핑이 필요하다: `\"내용\"`
- `orchestrator.json`의 디렉토리 경로가 실제로 존재하는지 첫 실행 시 확인한다.
- `orchestrator.json`이 없으면 먼저 사용자 입력을 받아 파일을 생성한다. 이 단계보다 앞서 외부 디렉토리 탐색이나 pane 준비를 시작하면 안 된다.
