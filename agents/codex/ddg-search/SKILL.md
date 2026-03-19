---
name: ddg-search
description: "[검색어] [옵션: --count N, --time d/w/m/y, --site example.com] ddgr을 사용해 DuckDuckGo 웹 검색을 수행합니다. 웹 검색, 구글 검색, 사이트 검색, 인터넷 검색 등의 요청에 사용합니다."
---

# DuckDuckGo 웹 검색 (ddgr)

ddgr을 사용해 DuckDuckGo에서 웹 검색을 수행합니다.

## 사용법

사용자의 검색 요청에서 **검색어**와 **옵션**을 파악한 뒤 아래 명령을 실행합니다.

```bash
ddgr --np --expand --num {N} {옵션} "{검색어}" 2>/dev/null
```

- `--np` : 프롬프트 없이 결과만 출력 (필수)
- `--expand` : 전체 URL 표시 (필수)
- `--num N` : 검색 결과 수 (기본 10, 최대 25)
- 검색어 : 사용자가 입력한 키워드

## 주요 옵션

| 옵션 | 설명 | 예시 |
|------|------|------|
| `--num N` | 결과 수 (0~25) | `--num 5` |
| `--time SPAN` | 기간 필터 (d=1일, w=1주, m=1달, y=1년) | `--time w` |
| `--site SITE` | 특정 사이트 내 검색 | `--site reddit.com` |
| `--json` | JSON 형식 출력 | `--json` |
| `--reg REG` | 지역 설정 | `--reg kr-kr` |
| `--expand` | 전체 URL 표시 | `--expand` |

## 출력 형식

각 결과를 아래 카드 형식으로 정리해서 보여줍니다.

```
#: 1
Title: 페이지 제목
Link: https://example.com/page
Description: 검색 결과 요약 설명
```

## 활용 예시

### 기본 검색
```bash
ddgr --np --expand --num 10 "검색어" 2>/dev/null
```

### 최근 1주일 결과만
```bash
ddgr --np --expand --num 10 --time w "검색어" 2>/dev/null
```

### 특정 사이트 내 검색
```bash
ddgr --np --expand --num 10 --site github.com "검색어" 2>/dev/null
```

### JSON 출력 (후처리용)
```bash
ddgr --np --num 10 --json "검색어" 2>/dev/null
```

### 한국어 결과 우선
```bash
ddgr --np --expand --num 10 --reg kr-kr "검색어" 2>/dev/null
```

## 주의사항

- 검색어에 특수문자가 있으면 적절히 이스케이프 처리
- `--np` 플래그를 반드시 포함해야 인터랙티브 프롬프트 없이 결과 반환
- 네트워크 오류 시 사용자에게 안내
- 한국어 검색 시 `--reg kr-kr` 옵션을 추가하면 더 나은 결과를 얻을 수 있음
