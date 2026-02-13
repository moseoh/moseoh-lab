---
name: skill-manager
description: 스킬을 생성, 점검, 리팩토링할 때 사용.
argument-hint: [create|review|refactor] [스킬이름]
disable-model-invocation: true
user-invocable: true
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Write
  - Edit
  - Bash
---

# Skill Manager

스킬을 생성, 점검, 리팩토링하는 도우미.

반드시 [reference.md](reference.md)를 먼저 읽고, 공식 스펙에 맞춰 작업할 것.

## 모드

### Create (생성)

새 스킬을 만들 때:

1. `reference.md`에서 frontmatter 스펙과 디렉토리 구조 확인
2. 사용자에게 스킬의 목적, 호출 방식(수동/자동), 필요한 도구 확인
3. 적절한 경로에 디렉토리 생성 (`~/.claude/skills/` 또는 `.claude/skills/`)
4. SKILL.md 작성 (frontmatter + 지시사항)
5. 필요시 supporting files 추가

### Review (점검)

기존 스킬을 점검할 때:

1. 대상 스킬의 SKILL.md 읽기
2. `reference.md` 기준으로 다음 항목 검증:
   - frontmatter 필드가 올바른지 (name, description, allowed-tools 등)
   - description이 Claude가 자동 호출하기에 충분히 명확한지
   - `disable-model-invocation` / `user-invocable` 설정이 용도에 맞는지
   - allowed-tools가 필요한 최소 권한인지
   - SKILL.md가 500줄 이하인지, 초과 시 supporting files 분리 필요
   - supporting files가 있다면 SKILL.md에서 올바르게 참조하는지
3. 문제점과 개선사항 보고

### Refactor (리팩토링)

기존 스킬을 개선할 때:

1. Review 단계를 먼저 수행
2. 발견된 문제점 기반으로 개선 적용:
   - description 명확화
   - frontmatter 최적화
   - 지시사항 구조 개선
   - 큰 SKILL.md를 본문 + supporting files로 분리
   - `$ARGUMENTS` 활용 개선
3. 변경 전/후 요약 제공

## 규칙

- 스킬 name은 소문자, 숫자, 하이픈만 사용 (최대 64자)
- SKILL.md는 500줄 이하 유지, 상세 내용은 별도 파일로 분리
- description은 Claude가 자동 판단할 수 있도록 구체적 키워드 포함
- 부작용이 있는 스킬은 반드시 `disable-model-invocation: true` 설정
