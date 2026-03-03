---
name: commit
description: Git 저장소의 변경 사항을 분석해 Conventional Commits 형식으로 단일 커밋을 생성합니다. 사용자가 커밋 생성, 커밋 메시지 작성, @파일 지정 커밋을 요청할 때 사용하세요.
---

## Your task

변경 사항을 바탕으로 단일 git 커밋을 생성하세요.

## Arguments

Arguments: $ARGUMENTS

- **언어($0)**: 기본값은 한국어입니다. Arguments에 따라 요청한 언어로 commit 메시지를 작성하세요. (`en`, `english`, `영어` 등)
- **파일**: 기본값은 모든 변경 사항입니다. `@경로/파일` 또는 `@폴더/` 형식이 제공되면 해당 파일들만 스테이징하고 커밋하세요.

## Context

- Current git status: !`git status`
- Current branch: !`git branch --show-current`
- Current git diff (staged and unstaged changes): !`git diff HEAD`

## Commit Message Format

- 기본: 단일 행 (`type(scope): description`)
- 본문(body)은 필수적인 세부 사항이 있는 경우에만 불렛 포인트로 추가하세요.

## Important Notice

- 단일 메시지 응답 내에서 한꺼번에 실행하세요.
- 메시지에 Co-Authored-By 또는 Claude 관련 attribution을 절대 포함하지 마세요.

## Output Format

커밋을 완료한 후 사용자에게 다음과 같이 표시하세요:

```
커밋 완료!:
<full commit message including title and body>
```
