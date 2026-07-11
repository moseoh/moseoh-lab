# Telegram Bot Container Publishing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `applications/telegram-bot` 변경을 Pull Request에서 Docker 빌드로 검증하고 `main` 반영 시 GHCR에 버전 태그와 함께 게시한다.

**Architecture:** 단일 GitHub Actions 워크플로가 앱 디렉터리와 워크플로 파일 변경을 감지한다. Pull Request에서는 같은 Docker 빌드를 푸시 없이 실행하고, `main` push에서는 `GITHUB_TOKEN`으로 GHCR에 로그인해 `latest`와 짧은 커밋 SHA 태그를 게시한다.

**Tech Stack:** GitHub Actions, Docker Buildx, GitHub Container Registry, `docker/login-action`, `docker/metadata-action`, `docker/build-push-action`

## Global Constraints

- 이미지 이름은 `ghcr.io/moseoh/telegram-bot`이다.
- 변경 감지 범위는 `applications/telegram-bot/**`와 `.github/workflows/telegram-bot-image.yml`이다.
- Pull Request에서는 이미지를 빌드하지만 푸시하지 않는다.
- `main` push에서는 `latest`와 `sha-<짧은 커밋 SHA>` 태그를 게시한다.
- 워크플로 권한은 `contents: read`, `packages: write`로 제한한다.
- Docker 빌드 컨텍스트는 `applications/telegram-bot`이다.

---

### Task 1: Telegram Bot 이미지 빌드 및 게시 워크플로

**Files:**
- Create: `.github/workflows/telegram-bot-image.yml`
- Reference: `applications/telegram-bot/Dockerfile`
- Reference: `docs/superpowers/specs/2026-07-11-telegram-bot-container-publish-design.md`

**Interfaces:**
- Consumes: GitHub의 `push`, `pull_request`, `GITHUB_TOKEN`, `github.sha`, `github.event_name` 컨텍스트
- Produces: Pull Request Docker 빌드 검증과 `ghcr.io/moseoh/telegram-bot:{latest,sha-<짧은 SHA>}` 이미지

- [ ] **Step 1: 워크플로 부재를 확인한다**

Run:

```bash
test ! -e .github/workflows/telegram-bot-image.yml
```

Expected: exit code `0`.

- [ ] **Step 2: 최소 워크플로를 작성한다**

Create `.github/workflows/telegram-bot-image.yml`:

```yaml
name: Telegram Bot Image

on:
  push:
    branches:
      - main
    paths:
      - "applications/telegram-bot/**"
      - ".github/workflows/telegram-bot-image.yml"
  pull_request:
    paths:
      - "applications/telegram-bot/**"
      - ".github/workflows/telegram-bot-image.yml"

permissions:
  contents: read
  packages: write

concurrency:
  group: telegram-bot-image-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        if: github.event_name == 'push'
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
            type=raw,value=latest,enable=${{ github.event_name == 'push' }}
            type=sha,prefix=sha-,format=short,enable=${{ github.event_name == 'push' }}

      - name: Build and publish image
        uses: docker/build-push-action@v6
        with:
          context: applications/telegram-bot
          file: applications/telegram-bot/Dockerfile
          push: ${{ github.event_name == 'push' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

- [ ] **Step 3: YAML 문법과 필수 설정을 검증한다**

Run:

```bash
ruby -e 'require "yaml"; YAML.load_file(".github/workflows/telegram-bot-image.yml")'
rg -n 'applications/telegram-bot/\*\*|telegram-bot-image.yml|packages: write|push: \$\{\{ github.event_name == .push. \}\}|type=raw,value=latest|type=sha,prefix=sha-,format=short|context: applications/telegram-bot' .github/workflows/telegram-bot-image.yml
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
git add .github/workflows/telegram-bot-image.yml
git commit -m "Add telegram bot image workflow"
```
