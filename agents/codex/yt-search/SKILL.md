---
name: yt-search
description: "[검색어] [옵션: --count N] yt-dlp를 사용해 유튜브 영상을 검색합니다. 유튜브 검색, YouTube 검색, 영상 찾기, 동영상 검색 등의 요청에 사용합니다."
allowed-tools: Bash(yt-dlp *)
---

# YouTube 검색 (yt-dlp)

yt-dlp를 사용해 유튜브에서 영상을 검색합니다.

## 사용법

사용자의 검색 요청에서 **검색어**와 **결과 수**(기본 20개)를 파악한 뒤 아래 명령을 실행합니다.

```bash
yt-dlp "ytsearch{N}:{검색어}" --flat-playlist --no-download --print "%(id)s | %(title)s | %(channel)s | %(view_count)s | %(duration_string)s | %(upload_date)s" 2>/dev/null
```

- `N` : 검색 결과 수 (기본 20, 사용자가 지정하면 해당 값 사용)
- 검색어 : 사용자가 입력한 키워드

## 출력 형식

각 결과를 아래 카드 형식으로 정리해서 보여줍니다. 조회수는 K(천), M(백만) 단위로 변환합니다. 업로드 날짜(YYYYMMDD)는 읽기 쉬운 형태(예: 2025-03-01, Today, Yesterday 등)로 변환합니다.

```
#: 1
Title: 영상 제목
Link: https://youtube.com/watch?v=VIDEO_ID
Channel: 채널명
Views: 조회수
Length: 길이
Date: 업로드일
```

## 추가 옵션

사용자가 요청하면 다음 정보도 추가로 가져올 수 있습니다:

- **설명**: `%(description).100s` (처음 100자)
- **좋아요 수**: `%(like_count)s`
- **재생목록 검색**: `ytsearchdate` (날짜순 정렬)

## 주의사항

- 검색어에 특수문자가 있으면 적절히 이스케이프 처리
- 조회수가 `None`이면 "정보 없음"으로 표시
- 네트워크 오류 시 사용자에게 안내
