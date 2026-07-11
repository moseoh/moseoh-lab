# Telegram Bot Container Publishing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `applications/telegram-bot` 변경을 Pull Request에서 Docker 빌드로 검증하고 `main` 반영 시 GHCR에 버전 태그와 함께 게시한다.

**Architecture:** CI와 CD를 별도 GitHub Actions 워크플로로 구성한다. CI는 Pull Request에서 Docker 빌드만 검증하고, CD는 `main` push에서 `GITHUB_TOKEN`으로 GHCR에 로그인해 `latest`와 짧은 커밋 SHA 태그를 게시한다.

**Tech Stack:** GitHub Actions, Docker Buildx, GitHub Container Registry, `docker/login-action`, `docker/metadata-action`, `docker/build-push-action`

## Global Constraints

- 이미지 이름은 `ghcr.io/moseoh/telegram-bot`이다.
- 변경 감지 범위는 `applications/telegram-bot/**`와 각 워크플로 자체 파일이다.
- Pull Request에서는 이미지를 빌드하지만 푸시하지 않는다.
- `main` push에서는 `latest`와 `sha-<짧은 커밋 SHA>` 태그를 게시한다.
- CI 권한은 `contents: read`, CD 권한은 `contents: read`와 `packages: write`로 제한한다.
- Docker 빌드 컨텍스트는 `applications/telegram-bot`이다.

---

### Task 1: Telegram Bot CI 워크플로

**Files:**
- Create: `.github/workflows/telegram-bot-ci.yml`
- Reference: `applications/telegram-bot/Dockerfile`
- Reference: `docs/superpowers/specs/2026-07-11-telegram-bot-container-publish-design.md`

**Interfaces:**
- Consumes: GitHub의 `pull_request` 이벤트
- Produces: Pull Request Docker 빌드 검증 결과

- [ ] **Step 1: 워크플로 부재를 확인한다**

Run:

```bash
test ! -e .github/workflows/telegram-bot-ci.yml
```

Expected: exit code `0`.

- [ ] **Step 2: 최소 워크플로를 작성한다**

Create `.github/workflows/telegram-bot-ci.yml`:

```yaml
name: Telegram Bot CI

on:
  pull_request:
    paths:
      - "applications/telegram-bot/**"
      - ".github/workflows/telegram-bot-ci.yml"

permissions:
  contents: read

concurrency:
  group: telegram-bot-ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  build:
    name: Build Docker image
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build Docker image
        uses: docker/build-push-action@v6
        with:
          context: applications/telegram-bot
          file: applications/telegram-bot/Dockerfile
          push: false
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

- [ ] **Step 3: YAML 문법과 필수 설정을 검증한다**

Run:

```bash
ruby -e 'require "yaml"; YAML.load_file(".github/workflows/telegram-bot-ci.yml")'
rg -n 'pull_request:|telegram-bot-ci.yml|push: false|context: applications/telegram-bot' .github/workflows/telegram-bot-ci.yml
git diff --check
```

Expected: Ruby exits `0`, `rg` prints every required configuration, and `git diff --check` exits `0` without output.

- [ ] **Step 4: 실제 Dockerfile 빌드를 검증한다**

Run:

```bash
docker build -f applications/telegram-bot/Dockerfile applications/telegram-bot
```

Expected: Docker build exits `0` and reports a successful image build.

- [ ] **Step 5: 워크플로를 커밋한다**

```bash
git add .github/workflows/telegram-bot-ci.yml
git commit -m "Add telegram bot CI workflow"
```

### Task 2: Telegram Bot CD 워크플로

**Files:**
- Create: `.github/workflows/telegram-bot-cd.yml`
- Reference: `applications/telegram-bot/Dockerfile`

**Interfaces:**
- Consumes: GitHub의 `main` 브랜치 `push`, `GITHUB_TOKEN`, `github.sha` 컨텍스트
- Produces: `ghcr.io/moseoh/telegram-bot:{latest,sha-<짧은 SHA>}` 이미지

- [ ] **Step 1: CD 워크플로를 작성한다**

Create `.github/workflows/telegram-bot-cd.yml`:

```yaml
name: Telegram Bot CD

on:
  push:
    branches:
      - main
    paths:
      - "applications/telegram-bot/**"
      - ".github/workflows/telegram-bot-cd.yml"

permissions:
  contents: read
  packages: write

concurrency:
  group: telegram-bot-cd-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  publish:
    name: Build and publish Docker image
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract Docker metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/moseoh/telegram-bot
          tags: |
            type=raw,value=latest
            type=sha,prefix=sha-,format=short

      - name: Build and publish Docker image
        uses: docker/build-push-action@v6
        with:
          context: applications/telegram-bot
          file: applications/telegram-bot/Dockerfile
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

- [ ] **Step 2: CD 설정을 검증한다**

Run:

```bash
ruby -e 'require "yaml"; YAML.load_file(".github/workflows/telegram-bot-cd.yml")'
rg -n 'push:|main|telegram-bot-cd.yml|packages: write|login-action|push: true|type=raw,value=latest|type=sha,prefix=sha-,format=short' .github/workflows/telegram-bot-cd.yml
git diff --check
```

Expected: Ruby exits `0`, `rg` prints every required CD configuration, and `git diff --check` exits `0` without output.

- [ ] **Step 3: CD 워크플로를 커밋한다**

```bash
git add .github/workflows/telegram-bot-cd.yml
git commit -m "Add telegram bot CD workflow"
```
