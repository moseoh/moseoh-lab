---
name: git-pr
description: 브랜치 생성 -> 푸쉬 -> PR 생성
agent: build
model: openai/gpt-5.3-codex-spark
---

## Your task

현재 `main` 브랜치에 커밋된 내용을 바탕으로 새 브랜치를 만들고 PR을 생성하세요.

1.  **브랜치 생성**: 현재 브랜치가 `main`인 경우, 아직 push되지 않은 커밋 메시지들을 분석하여 적절한 브랜치 이름(예: `feat/setup-config`, `fix/login-bug`)을 생성하고 해당 브랜치로 전환하세요.
2.  **푸쉬**: 생성한 새 브랜치를 `origin`으로 push하세요. (`git push -u origin <branch-name>`)
3.  **PR 생성**: `gh pr create` 명령어를 사용하여 PR을 생성하세요.

## Arguments

Arguments: $ARGUMENTS

- **언어($1)**: 기본값은 한국어입니다. Arguments에 따라 요청한 언어로 commit 메시지를 작성하세요. (`en`, `english`, `영어` 등)

## Context

- Current git status: !`git status`
- Current branch: !`git branch --show-current`
- Unpushed commits: !`git log origin/main..HEAD --oneline`

## PR Format

먼저 `.github/PULL_REQUEST_TEMPLATE.md` 또는 `.github/pull_request_template.md` 파일이 존재하는지 확인하세요.

- **템플릿이 있는 경우**: 해당 템플릿의 구조를 따라 PR 본문을 작성하세요. 섹션 제목과 형식을 그대로 유지하되, 내용이 없는 섹션은 생략하세요. 템플릿에 지침이 있다면 해당 지침을 따르세요.
- **템플릿이 없는 경우**: 아래 기본 포맷을 사용하세요.

### 기본 포맷

- 제목: `<type>(<scope>): <description>` (max 72 chars, lowercase start, no period)
- 본문:

  ```
  ## Summary

  <purpose and changes>

  ## Changes (optional)

  <implementation details>

  ## Related Issues (optional)
  Closes #123
  ```

- 내용이 없는 섹션은 생략하세요.

## Important Notice

- **절대 금지**: 커밋 메시지에 AI가 생성했다는 문구(예: "Generated with Claude Code", "Co-Authored-By: Claude", "by ChatGPT", "AI generated")를 **절대** 포함하지 마세요.
- 새로운 커밋을 생성하지 마세요. 이미 존재하는 커밋만 사용합니다.
- 단일 메시지 응답 내에서 한꺼번에 실행하세요.

## Output Format

PR 생성 후 사용자에게 다음과 같이 표시하세요:

```
PR 생성 완료!:
- 제목: <title>
- 브랜치: <new-branch> → main
- URL: <pr url>
```
