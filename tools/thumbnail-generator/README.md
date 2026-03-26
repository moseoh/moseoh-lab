# 자동 썸네일 생성기

assets 폴더의 로고 파일들을 자동으로 스캔하여 썸네일을 일괄 생성하는 도구입니다.

## 사용법

### 1. 로고 파일 준비

`assets/logo`와 `assets/book-cover` 폴더에 다음 형식으로 로고 파일을 배치:

```
{로고이름}-{로고색상}-{배경색상}.{확장자}
```

**예시:**

- `nextjs-ffffff-000000.svg` → 흰색 로고, 검은색 배경
- `react-61dafb-282c34.svg` → 파란색 로고, 어두운 배경
- `logo-red-white.png` → 빨간색 로고, 흰색 배경

**SVG 색상 자동 변경**: SVG 파일의 경우 로고 색상이 자동으로 변경됩니다!

### 2. 실행

#### 기본 실행 (logo/book-cover 모두 처리)

```bash
npm start
```

### 3. 결과

- `output/logo`, `output/book-cover` 폴더에 PNG 썸네일 생성
- 타겟 경로가 설정되어 있으면 자동 복사

## 설정 파일

### 기본 설정 (config/logo.json)

프로젝트의 로고 썸네일 설정 파일입니다.

```json
{
  "thumbnail": {
    "width": 1600,
    "ratio": "16:10",
    "defaultBackground": "#ffffff"
  },
  "logo": {
    "heightRatio": 0.4,
    "widthRatio": 0.7,
    "defaultColor": "#000000"
  },
  "paths": {
    "assets": "./assets/logo",
    "output": "./output/logo",
    "target": "/path/to/target/directory"
  },
  "fileConvention": {
    "separator": "-",
    "description": "파일명 형식: {로고이름}-{로고색상}-{배경색상}.{확장자}"
  }
}
```

### 책 표지 설정 (config/book-cover.json)

책 표지 썸네일 전용 설정 파일입니다.

```json
{
  "logo": {
    "heightRatio": 0.7,
    "widthRatio": 0.7
  },
  "paths": {
    "assets": "./assets/book-cover",
    "output": "./output/book-cover"
  }
}
```

## 지원 색상 형식

- **Hex 코드**: `ff6b6b`, `#ff6b6b`
- **색상명**: `red`, `green`, `blue`, `yellow`, `purple`, `orange`, `pink`, `brown`, `gray`, `black`, `white`

## 지원 파일 형식

- SVG (`.svg`)
- PNG (`.png`)
- JPG/JPEG (`.jpg`, `.jpeg`)

## npm 스크립트

| 명령어 | 설명 |
|--------|------|
| `npm start` | 로고/책표지 썸네일 생성 |
| `npm run generate` | start와 동일 |
| `npm run dev` | watch 모드로 실행 (파일 변경 감지) |

## 자동화 기능

1. **일괄 처리**: assets 폴더의 모든 로고 파일 자동 스캔
2. **파일명 파싱**: 로고명, 로고색상, 배경색상 자동 분석
3. **SVG 색상 변경**: SVG 파일의 fill/stroke 속성을 지정된 색상으로 자동 변경
4. **스마트 크기 조정**: maxWidth/maxHeight 기준으로 비율 유지하며 리사이즈
5. **중앙 배치**: 로고를 이미지 중앙에 자동 배치
6. **타겟 복사**: 설정된 경로로 자동 복사 (선택사항)
