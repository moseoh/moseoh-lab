---
name: git-commit
description: 변경 사항을 분석하여 conventional commit 형식으로 자동 커밋 생성
agent: build
model: openai/gpt-5.3-codex-spark
---

## Your task

변경 사항을 바탕으로 단일 git 커밋을 생성하세요.

## Arguments

Arguments: $ARGUMENTS

- **언어($1)**: 기본값은 한국어입니다. Arguments에 따라 요청한 언어로 commit 메시지를 작성하세요. (`en`, `english`, `영어` 등)
- **파일**: 기본값은 모든 변경 사항입니다. `@경로/파일` 또는 `@폴더/` 형식이 제공되면 해당 파일들만 스테이징하고 커밋하세요.

## Context

- Current git status: !`git status`
- Current branch: !`git branch --show-current`
- Current git diff (staged and unstaged changes): !`git diff HEAD`

## Commit Message Format

- 기본: 단일 행 (`type(scope): description`)
- 본문(body)은 필수적인 세부 사항이 있는 경우에만 불렛 포인트로 추가하세요.

## Important Notice

- **절대 금지**: 커밋 메시지에 AI가 생성했다는 문구(예: "Generated with Claude Code", "Co-Authored-By: Claude", "by ChatGPT", "AI generated")를 **절대** 포함하지 마세요.
- 단일 메시지 응답 내에서 한꺼번에 실행하세요.

## Output Format

커밋을 완료한 후 사용자에게 다음과 같이 표시하세요:

```
커밋 완료!:
<full commit message including title and body>
```
