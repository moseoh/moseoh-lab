---
name: pr
description: 현재 브랜치의 커밋을 기반으로 원격 브랜치를 푸시하고 GitHub Pull Request를 생성합니다. "PR 만들어줘", "브랜치 푸시하고 PR 열어줘" 같은 요청에서 사용하세요.
---

## Your task

현재 커밋 상태를 바탕으로 브랜치를 준비하고 PR을 생성하세요.

1. **브랜치 결정**:
   - 현재 브랜치가 `main`이면, 아직 push되지 않은 커밋 메시지를 분석해 적절한 브랜치 이름(예: `feat/setup-config`, `fix/login-bug`)을 만들고 해당 브랜치로 전환하세요.
   - 현재 브랜치가 `main`이 아니면, 현재 브랜치를 그대로 사용하세요.
2. **푸시**: 작업 브랜치를 `origin`으로 push하세요. (`git push -u origin <branch-name>`)
3. **PR 생성**: `gh pr create` 명령어로 PR을 생성하세요.

## Arguments

Arguments: $ARGUMENTS

- **언어($0)**: 기본값은 한국어입니다. Arguments에 따라 PR 제목/본문을 요청한 언어로 작성하세요. (`en`, `english`, `영어` 등)

## Context

- Current git status: !`git status`
- Current branch: !`git branch --show-current`
- Unpushed commits: !`git log origin/main..HEAD --oneline`

## PR Format

먼저 `.github/PULL_REQUEST_TEMPLATE.md` 또는 `.github/pull_request_template.md` 파일이 존재하는지 확인하세요.

- **템플릿이 있는 경우**: 템플릿 구조와 섹션 제목을 유지하여 PR 본문을 작성하세요. 내용이 없는 섹션은 생략하세요.
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

- 새로운 커밋을 생성하지 마세요. 이미 존재하는 커밋만 사용합니다.
- 단일 메시지 응답 내에서 한꺼번에 실행하세요.
- 메시지에 Co-Authored-By 등 불필요한 attribution을 포함하지 마세요.

## Output Format

PR 생성 후 사용자에게 다음과 같이 표시하세요:

```
PR 생성 완료!:
- 제목: <title>
- 브랜치: <new-branch> → main
- URL: <pr url>
```
