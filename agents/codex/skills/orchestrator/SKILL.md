---
name: "orch"
description: "사용자가 /orch 명령으로 명시적으로 호출할 때만 사용하는 멀티 pane 오케스트레이션 스킬이다. cmux pane으로 여러 작업 저장소에 에이전트(cx/cc)를 띄우고 작업을 분배한다. 필요하면 같은 작업 pane 안에 worker surface를 추가해 병렬 fan-out한다. 자동 트리거하지 않는다."
---

# 멀티 Pane 오케스트레이션

`orch`는 작업 분배 정책만 담당한다. pane/surface 생성, 명령 전송, 화면 읽기는
`cmux` 스킬을 사용한다.

`orch`는 단순 전달자가 아니다. 사용자 요청을 그대로 복사해 각 pane에 뿌리는
역할이 아니라, 선행 조건, 의존성, 작업 순서, 병렬 가능 범위를 판단해 실행
순서를 잡는 역할을 맡는다.

## 전제

- 프로젝트 루트에 `orchestrator.json`이 있어야 한다.
- 없으면 먼저 사용자에게 pane 목록, 경로, 기본 agent, alias를 받아 생성한다.
- 설정 파일이 없을 때는 외부 경로 탐색이나 pane 준비를 먼저 하지 않는다.

오케스트레이션 기본 자세:

- 사용자 요청을 그대로 전달하지 말고, 선행 조건과 의존성을 먼저 판별한다.
- 작업을 실행 가능한 단위로 재구성하고, 올바른 순서로 재배치한다.
- 선행 산출물이 비어 있으면 구현 작업부터 밀어넣지 않는다.
- 어느 저장소가 source of truth인지 먼저 정하고, 충돌하는 정보를 그대로 병렬 실행하지 않는다.
- 프로젝트별 단계명, 폴더 구조, 저장소 역할은 이 스킬에 하드코딩하지 않는다.
- 프로젝트 고유 규칙은 해당 저장소 문서나 task 문서에서 읽어 적용한다.
- 오케스트레이터는 직접 작업자가 아니라 분배자이자 조정자다.
- 대상 저장소 변경은 `orchestrator.json`에 정의된 전담 worker에게만 위임한다.
- 오케스트레이터가 직접 수정하는 범위는 `orchestration` 관리 파일로 제한한다.

예시:

```json
{
  "panes": {
    "work-a": { "dir": "/path/to/project-a", "agent": "cx", "alias": ["a"] },
    "work-b": { "dir": "/path/to/project-b", "agent": "cx", "alias": ["b"] },
    "work-c": { "dir": "/path/to/project-c", "agent": "cx", "alias": ["c"] }
  }
}
```

## 레이아웃

기본 레이아웃은 가로 배치다.

```text
orch | work-a | work-b | work-c
```

규칙:

- `orch` pane은 유지한다.
- 설정된 `work-*` pane은 작업 실행 시 항상 전부 먼저 구성한다.
- 각 work pane의 첫 surface는 placeholder 터미널이다.
- 에이전트는 placeholder가 아니라 두 번째 surface부터 사용한다.
- 추가 병렬은 pane split이 아니라 같은 pane 안의 worker surface로 확장한다.

## naming

- pane 이름: `work-a`, `work-b`, `work-c`
- placeholder surface: pane 이름 그대로
- 첫 worker: `<pane-name>-1`
- 추가 worker: `<pane-name>-2`, `<pane-name>-3`

예:

- `work-b`
- `work-b-1`
- `work-b-2`

## 런타임 상태

cmux 내부 식별자와 배정 상태는 런타임 JSON으로 관리한다.

권장 파일:

```text
state/cmux-session.json
```

최소 기록 항목:

- workspace
- orchestration pane/surface
- 각 work pane
- placeholder surface
- worker surface
- worker별 현재 task
- worker별 마지막 지시 요약
- worker별 상태
- worker별 결과 수집 여부
- worker별 문맥 유지 여부
- completion policy

규칙:

- pane/surface 생성, 종료, task 배정, 회수 시 JSON을 갱신한다.
- cmux 실제 상태와 JSON이 다르면 cmux를 기준으로 복구한다.
- 이 JSON은 내부 운영 파일이다.
- 마지막 지시는 원문 전체보다 `last_instruction_summary` 같은 짧은 요약으로 남긴다.
- 필요하면 task 파일 경로나 continuity key를 함께 기록해 후속 작업 선택에 쓴다.

권장 worker 상태 필드:

- `role`: `placeholder` | `worker`
- `status`: `busy` | `idle` | `done-awaiting-cleanup`
- `task`
- `continuity_key`
- `last_instruction_summary`
- `last_activity`
- `result_collected`
- `keep_alive`

## 작업 분배

기본 규칙:

- 먼저 이 요청이 어떤 단계의 작업인지 판별한다.
- 단계상 선행 작업이 비어 있으면 그 선행 작업부터 연다.
- 요청을 pane별 작업으로 먼저 분해한다.
- placeholder surface는 사용자 작업 공간으로 남겨둔다.
- worker가 없으면 `<pane-name>-1`을 만든 뒤 거기서 agent를 실행한다.
- 기존 worker가 대기 중이면 그 worker에 추가 입력한다.
- 응답 생성 중인 worker에는 입력하지 않는다.
- agent 기본값은 `orchestrator.json`의 `agent`다.
- 사용자가 특정 pane만 `cc`를 원하면 그 pane만 오버라이드한다.
- 새 작업을 어느 worker에 보낼지 판단할 때는 아래 순서를 따른다.
  1. 같은 task 또는 같은 `continuity_key`를 가진 worker
  2. 같은 pane의 idle worker
  3. 새 worker 생성
  4. placeholder는 제외

즉, 같은 흐름은 같은 worker를 우선 재사용하고, 없으면 idle worker를 재사용하며,
둘 다 아니면 새 worker를 만든다.

추가 규칙:

- 저장소나 문서군 사이에 정보 충돌이 있으면 바로 구현을 늘리지 말고 먼저 기준 문서를 정리한다.
- 서로 다른 성격의 산출물은 한 문서로 섞지 않는다.
- 예를 들어 정책, 공개 페이지 기획, 앱 내부 플로우 기획, 구현 작업은 구분해서 다룬다.
- 어떤 저장소가 기준인지 불명확하면 먼저 source of truth를 명시하는 작업부터 연다.
- `docs`, `server`, `web` 같은 대상 저장소 파일은 오케스트레이터가 직접 수정하지 않는다.
- 대상 저장소의 실제 변경은 해당 pane의 worker에게 다시 지시해 반영한다.
- 사용자 리뷰 후 수정도 직접 편집하지 말고 재분배한다.

## 병렬 fan-out

다음 조건이면 같은 pane 안에 worker를 늘린다.

- 같은 저장소 안에서 하위 작업이 자연스럽게 분리될 때
- 산출물 파일을 worker별로 분리할 수 있을 때
- 조사/구현처럼 역할을 나눌 수 있을 때
- 기존 worker가 오래 걸리고 같은 pane backlog가 남아 있을 때

다음 조건이면 늘리지 않는다.

- 같은 파일을 동시에 수정할 가능성이 높을 때
- 결과 병합 비용이 큰 때
- 짧은 작업이라 분할 오버헤드가 더 큰 때

필수 규칙:

- write scope를 worker별로 분리한다.
- 결과 파일도 worker별로 분리하거나 섹션을 나눈다.
- placeholder surface는 에이전트 전용으로 재사용하지 않는다.

## 결과 수집

순서:

1. `list-notifications`로 완료 신호 확인
2. worker별 결과를 pane 단위로 병합
3. 필요하면 최종 task 문서로 정리

수동 `notify`는 보조 수단일 뿐, 항상 수집 가능하다고 가정하지 않는다.

규칙:

- 완료 판단은 `list-notifications`를 기준으로 한다.
- 알림만으로 처리되지 않는 문제가 생기면 먼저 사용자에게 알린다.
- `read-screen`은 기본 수집 절차로 두지 않는다.

## 사용자 커뮤니케이션

분배 직후:

- 사용자에게는 worker별 분배 작업만 짧게 알린다.
- cmux 내부 ref는 기본적으로 노출하지 않는다.

예:

- `work-a-1: 정책 문서 정리`
- `work-a-2: 사용자 흐름 기획`
- `work-b-1: 계약/API 정합성 검토`

완료 알림:

- 병렬 실행 직후, 오케스트레이션 에이전트는 사용자에게 어떤 완료 신호를 기다리는지 함께 요청한다.
- 기본값은 `전부 끝나면 알려주세요`다.
- 필요하면 묶음 완료와 즉시 완료를 섞어 요청한다.

예:

- `이 작업들은 전부 끝나면 알려주세요.`
- `work-a-1, work-a-2는 같이 끝나면 알려주시고, work-b-1은 끝나는대로 알려주세요.`

사용자 응답 해석:

- `다 끝났다` -> 전체 완료
- `work-a 둘 다 끝났다` -> 해당 묶음 완료
- `work-b 끝났다` -> 해당 worker 완료

## 요청 해석

- 전체 분배형: 여러 pane으로 나눠 분배
- 개별 지정형: 사용자가 지정한 pane만 실행
- 단일 pane형: 특정 pane 하나만 실행
- agent 오버라이드형: 특정 pane만 `cc`
- 내부 병렬형: 같은 pane 안에서 `-1`, `-2` worker로 fan-out

추가 해석 규칙:

- 사용자 요청이 바로 구현 작업처럼 들어와도, 선행 산출물이 비어 있으면 구현 지시로 바로 내려보내지 않는다.
- 오케스트레이션은 필요한 선행 작업을 먼저 제안하거나 바로 연다.
- 즉, 사용자의 문장을 그대로 전달하는 것이 아니라 올바른 실행 순서로 재구성한다.

## 금지

- `orchestrator.json` 없이 임의로 pane 구조를 가정하지 않는다.
- placeholder surface에 기본적으로 에이전트를 띄우지 않는다.
- worker가 바쁜데 같은 surface에 새 입력을 밀어넣지 않는다.
- 내부 cmux ref를 사용자 응답에 습관적으로 노출하지 않는다.
- 오케스트레이터가 대상 저장소 파일을 직접 수정하지 않는다.
- 대상 저장소 수정 사항을 작은 변경이라는 이유로 직접 처리하지 않는다.
