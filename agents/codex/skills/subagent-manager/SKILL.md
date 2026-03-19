---
name: subagent-manager
description: Codex 환경에서 서브에이전트 위임 전략, 역할 분리, 병렬 실행 계획, 소유권 분배, spawn_agent/send_input/wait_agent 활용 방식을 설계, 점검, 리팩토링할 때 사용.
---

# Subagent Manager

서브에이전트 운영 전략을 생성, 점검, 리팩토링하는 도우미.

## Context

반드시 [subagents.md](subagents.md)를 먼저 읽고, 공식 문서 기준으로 작업할 것.
이 저장소의 기본 스킬 경로는 `.codex/skills/`(repo)와 `~/.codex/skills/`(user)로 간주한다.

## 모드

### Create (생성)

새 서브에이전트 운영 방식이나 관리 스킬을 만들 때:

1. Context에서 공식 문서와 용어를 먼저 확인
2. 사용자에게 목표, blocking 작업, 병렬화 가능 범위, agent 역할, 파일 소유권, 승인 필요 여부를 확인
3. 적절한 경로에 디렉토리 생성 (`~/.codex/skills/` 또는 `.codex/skills/`)
4. SKILL.md 또는 운영 문서에 메인 에이전트와 서브에이전트의 책임 경계를 명시
5. 각 서브에이전트별 입력, 출력, 종료 조건, 에러 처리 기준을 정의
6. `spawn_agent`, `send_input`, `wait_agent`, `close_agent` 사용 기준을 문서화
7. 필요시 supporting files(`references/`, `scripts/`, `assets/`)를 추가
8. 필요시 `agents/openai.yaml`에 invocation policy를 설정

### Review (점검)

기존 서브에이전트 운영 방식이나 관리 스킬을 점검할 때:

1. 대상 SKILL.md, 운영 문서, supporting files를 읽기
2. Context 기준으로 다음 항목 검증:
   - 역할과 책임이 명확하고 중복되지 않는지
   - 즉시 필요한 blocking 작업을 잘못 위임하고 있지 않은지
   - 병렬 작업이 실제로 독립적이며 서로를 막지 않는지
   - worker별 파일/모듈 소유권이 분리되어 있는지
   - `spawn_agent`, `send_input`, `wait_agent`, `close_agent` 사용 시점이 적절한지
   - 결과 통합 방식과 실패 시 복구 절차가 명확한지
   - `agents/openai.yaml`가 있다면 명시적/암시적 호출 정책이 용도에 맞는지
   - SKILL.md가 500줄 이하인지, 초과 시 supporting files 분리 필요 여부
3. 문제점과 개선사항 보고

### Refactor (리팩토링)

기존 서브에이전트 운영 방식을 개선할 때:

1. Review 단계를 먼저 수행
2. 발견된 문제점 기반으로 개선 적용:
   - 역할 경계 재정의
   - blocking path와 sidecar task 분리
   - worker별 write scope 재설계
   - handoff 프롬프트와 종료 조건 정리
   - `wait_agent` 사용 최소화
   - `agents/openai.yaml` policy/metadata 정합성 개선
   - 큰 문서를 본문 + supporting files로 분리
3. 변경 전/후 요약 제공

## 규칙

- blocking인 작업은 기본적으로 메인 에이전트가 처리
- 서브에이전트는 concrete, well-defined, self-contained한 작업만 맡김
- 각 worker는 가능한 한 disjoint write set을 갖도록 설계
- `wait_agent`는 다음 단계가 실제로 막혔을 때만 사용
- 서브에이전트에게는 정답이나 진단을 미리 누설하지 않고, 필요한 입력만 전달
- 비용, 승인, 부작용 위험이 큰 작업은 명시적 호출 중심으로 운영
- description은 Codex가 자동 판단할 수 있도록 작업 범위와 키워드를 구체적으로 유지
