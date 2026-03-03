---
name: skill-manager
description: OpenAI Agent Skills 스펙 기준으로 스킬을 생성, 점검, 리팩토링할 때 사용.
---

# Skill Manager

스킬을 생성, 점검, 리팩토링하는 도우미.

## Context

반드시 [openai.md](openai.md), [agentskillsspecification.md](agentskillsspecification.md)를 먼저 읽고, 공식 스펙에 맞춰 작업할 것.
이 저장소의 기본 스킬 경로는 `.codex/skills/`(repo)와 `~/.codex/skills/`(user)로 간주한다.

## 모드

### Create (생성)

새 스킬을 만들 때:

1. Context에서 frontmatter 스펙과 디렉토리 구조 확인
2. 사용자에게 스킬의 목적, 호출 방식(명시적/암시적), 필요한 도구 확인
3. 적절한 경로에 디렉토리 생성 (`~/.codex/skills/` 또는 `.codex/skills/`)
4. SKILL.md 작성 (필수 frontmatter: `name`, `description`)
5. 필요시 optional frontmatter(`license`, `compatibility`, `metadata`, `allowed-tools`) 추가
6. 필요시 supporting files(`scripts/`, `references/`, `assets/`) 추가
7. 필요시 `agents/openai.yaml`에 invocation policy/의존성 설정 추가

### Review (점검)

기존 스킬을 점검할 때:

1. 대상 스킬의 SKILL.md 읽기
2. Context 기준으로 다음 항목 검증:
   - frontmatter 필드가 올바른지 (`name`, `description` 필수 + optional 필드 형식)
   - `name` 제약(1-64자, 소문자/숫자/하이픈, 연속 하이픈 금지, 시작/끝 하이픈 금지)과 디렉토리명 일치 여부
   - `description`이 암시적 호출 판단에 충분히 명확한지 (작업 범위 + 트리거 키워드)
   - `allowed-tools`를 쓴 경우 최소 권한 원칙을 지키는지
   - `agents/openai.yaml`가 있다면 `policy.allow_implicit_invocation` 설정이 용도에 맞는지
   - SKILL.md가 500줄 이하인지, 초과 시 supporting files 분리 필요
   - supporting files가 있다면 SKILL.md에서 올바르게 참조하는지
3. 문제점과 개선사항 보고

### Refactor (리팩토링)

기존 스킬을 개선할 때:

1. Review 단계를 먼저 수행
2. 발견된 문제점 기반으로 개선 적용:
   - description 명확화
   - frontmatter 최적화
   - `agents/openai.yaml` policy/metadata 정합성 개선
   - 지시사항 구조 개선
   - 큰 SKILL.md를 본문 + supporting files로 분리
   - `$ARGUMENTS` 활용 개선
3. 변경 전/후 요약 제공

## 규칙

- 스킬 name은 소문자, 숫자, 하이픈만 사용 (최대 64자, 시작/끝/연속 하이픈 금지)
- 스킬 name은 디렉토리명과 일치해야 함
- SKILL.md는 500줄 이하 유지, 상세 내용은 별도 파일로 분리
- description은 Codex가 자동 판단할 수 있도록 작업 범위/키워드를 구체적으로 포함
- 부작용이 크거나 오동작 위험이 큰 스킬은 `agents/openai.yaml`에 `policy.allow_implicit_invocation: false`를 설정해 명시적 호출 중심으로 운영
- 기본 설치 경로는 `.codex/skills/` 또는 `~/.codex/skills/`를 사용
