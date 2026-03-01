---
name: questions
description: 코드 변경 없이 사용자의 질문에 대한 답변(간단 Q&A/토론)
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - WebSearch
  - WebFetch
  - mcp__context7__resolve-library-id
  - mcp__context7__query-docs
disable-model-invocation: true
user-invocable: true
---

## Your task

사용자의 질문에 **코드 변경 없이** 답변하세요. 필요할 때만 Read/Glob/Web로 근거를 확인하세요.

### Rules (keep it light)

- 소스코드 수정안(diff/패치/“이렇게 고치세요” 코드블록) 금지. 설명/원인/선택지만 제시.
- 질문이 모호하거나 환경/버전에 따라 답이 달라지면 `AskUserQuestion`으로 먼저 확인.
- 코드/설정에 직접 관련된 경우에만 Read/Glob(필요한 파일만, 과탐색 금지).
- 버전/스펙/공식 동작 확인이 필요할 때만 WebSearch/WebFetch/context7 사용(공식 문서 우선).
- 트레이드오프가 있으면 옵션을 비교(장단점/적합 상황).
- 사용자가 특정 해법을 전제로 질문하면("Redis로 해야 할까?"), **그 전제가 맞는지부터 검토**. 다른 레이어(DB, 앱, 인프라 등)에서 더 단순하게 풀리는지 먼저 따져보고, 전제가 타당할 때만 해당 해법을 깊이 다룰 것.

### Response format (adaptive)

- 짧은 질문: 1) 답변 2) (필요 시) 확인 질문 1~3개
- 디버깅/설계 토론: 1) 요약 2) 핵심 답변 3) 체크리스트 4) 질문(1~5개)
