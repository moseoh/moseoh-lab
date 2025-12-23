# Discord Bot

## Bot Customization

### Discord Developer Portal

[Discord Developer Portal](https://discord.com/developers/applications)에서 설정

| 항목 | 위치 | 설명 | 권장 사이즈 |
|------|------|------|------------|
| App Name | General Information | 봇 이름 | - |
| App Icon | General Information | 프로필 사진 | 512x512 PNG |
| Description | General Information | 봇 소개 텍스트 | - |
| Tags | General Information | 검색용 태그 (최대 5개) | - |
| Banner Image | Rich Presence > Art Assets | 앱 배너 | 1920x1080 |
| Cover Image | Rich Presence > Art Assets | 스토어 커버 | 1024x1024 |

### Code (index.ts)

코드에서 동적으로 설정

```typescript
client.once(Events.ClientReady, (readyClient) => {
  // 상태 메시지 설정
  client.user?.setActivity("상태 메시지", { type: ActivityType });

  // 온라인 상태 설정
  client.user?.setStatus("online"); // online, idle, dnd, invisible
});
```

**Activity Type:**
| 값 | 타입 | 표시 |
|----|------|------|
| 0 | Playing | ~ 플레이 중 |
| 1 | Streaming | ~ 스트리밍 중 |
| 2 | Listening | ~ 듣는 중 |
| 3 | Watching | ~ 시청 중 |
| 5 | Competing | ~ 경쟁 중 |

**Status:**
| 값 | 설명 |
|----|------|
| online | 온라인 (초록) |
| idle | 자리 비움 (노랑) |
| dnd | 방해 금지 (빨강) |
| invisible | 오프라인 표시 |

### Discord Server

서버 내에서 설정

| 항목 | 위치 | 설명 |
|------|------|------|
| 역할 색상 | 서버 설정 > 역할 > 봇 역할 | 봇 이름 색상 |
| 서버 닉네임 | 봇 우클릭 > 닉네임 변경 | 서버별 다른 이름 |

## Setup

```bash
npm install
cp .env.example .env  # DISCORD_TOKEN 설정
npm run dev
```

## Commands

| 명령어 | 설명 |
|--------|------|
| hello | Hello World! 응답 |
