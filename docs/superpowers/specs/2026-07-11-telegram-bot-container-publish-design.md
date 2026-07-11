# Telegram Bot 컨테이너 이미지 게시 설계

## 목적

`applications/telegram-bot` 변경을 Pull Request에서 빌드로 검증하고, 변경이 `main` 브랜치에 반영되면 GitHub Container Registry(GHCR)에 이미지를 게시한다.

## 검토한 방식

1. 앱 디렉터리 전체 감지: `applications/telegram-bot/**`의 모든 변경을 대상으로 한다. 불필요한 빌드가 일부 발생할 수 있지만, 새 런타임 파일이나 설정의 누락 위험이 가장 낮다.
2. 런타임 파일만 열거: `src`, `migrations`, `schema`, `Dockerfile`, `pyproject.toml` 등을 개별 등록한다. 빌드 횟수는 줄지만 파일 추가 시 감지 목록을 계속 관리해야 한다.
3. 모든 저장소 변경 감지: 설정은 가장 단순하지만 Telegram Bot과 무관한 변경에도 이미지를 빌드한다.

앱 디렉터리 전체 감지 방식을 사용한다. 현재 Dockerfile이 앱 디렉터리 전체를 빌드 컨텍스트로 사용하므로 변경 감지 범위와 빌드 입력 범위가 일치한다.

## 트리거

CI와 CD를 명시적인 두 워크플로로 분리한다.

- `.github/workflows/telegram-bot-ci.yml`: `applications/telegram-bot/**` 또는 CI 워크플로 자체가 변경된 Pull Request에서 실행한다.
- `.github/workflows/telegram-bot-cd.yml`: `applications/telegram-bot/**` 또는 CD 워크플로 자체가 변경된 `main` 브랜치 push에서 실행한다.

Pull Request에서는 이미지를 빌드하되 레지스트리에 푸시하지 않는다. `main` 브랜치 push에서는 빌드한 이미지를 GHCR에 푸시한다.

## 이미지와 태그

이미지 이름은 `ghcr.io/moseoh/telegram-bot`을 사용한다.

`main` 브랜치에서 다음 태그를 함께 게시한다.

- `latest`: 현재 `main`의 최신 이미지
- `sha-<짧은 커밋 SHA>`: 특정 배포 버전을 식별하고 롤백할 수 있는 불변 태그

## 워크플로 구성

CI 워크플로는 다음 단계를 수행한다.

1. 저장소를 checkout한다.
2. Docker Buildx를 설정한다.
3. `applications/telegram-bot`을 컨텍스트로 이미지를 빌드하되 푸시하지 않는다.

CD 워크플로는 다음 단계를 수행한다.

1. 저장소를 checkout한다.
2. Docker Buildx를 설정한다.
3. `GITHUB_TOKEN`으로 GHCR에 로그인한다.
4. Docker 메타데이터 액션으로 태그와 라벨을 생성한다.
5. `applications/telegram-bot`을 컨텍스트로 이미지를 빌드하고 푸시한다.

GitHub Actions 캐시를 사용해 반복 빌드 시간을 줄인다. 같은 브랜치나 Pull Request에서 새 실행이 시작되면 이전 실행을 취소해 오래된 이미지를 중복 빌드하지 않는다.

## 권한과 보안

CI 워크플로 권한은 `contents: read`로 제한한다. CD 워크플로 권한은 다음으로 제한한다.

- `contents: read`: 저장소 checkout
- `packages: write`: `main`에서 GHCR 이미지 게시

별도 PAT나 저장소 Secret은 사용하지 않고 GitHub가 제공하는 `GITHUB_TOKEN`을 사용한다. Pull Request에서는 로그인과 이미지 푸시를 수행하지 않는다.

## 오류 처리

checkout, Buildx 설정, 로그인, 메타데이터 생성 또는 Docker 빌드 중 하나라도 실패하면 job을 실패 처리한다. 이미지 푸시는 빌드와 같은 단계에서 수행하므로 빌드 실패 시 태그가 게시되지 않는다.

## 검증 기준

- 두 워크플로 YAML이 유효하다.
- 각 변경 감지 경로가 앱 전체와 해당 워크플로 파일을 포함한다.
- CI 워크플로는 Pull Request에서 `push: false`로 빌드만 수행하고 `packages: write` 권한을 갖지 않는다.
- CD 워크플로는 `main` push에서 `latest`와 짧은 SHA 태그를 생성하고 GHCR에 푸시한다.
- Docker 빌드 컨텍스트와 Dockerfile 경로가 `applications/telegram-bot`을 가리킨다.
- CI 권한은 `contents: read`, CD 권한은 `contents: read`와 `packages: write`로 제한된다.
