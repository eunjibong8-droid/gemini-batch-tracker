# 🔍 Gemini Batch Tracker

Gemini Batch API 관련 새 글을 자동으로 감지하여 Discord로 알림을 보내는 트래커입니다.

## 동작 방식

GitHub Actions가 **30분마다** 자동 실행되며, 지정된 소스에서 `batch` 키워드가 포함된 새 글을 수집합니다.
이전에 알림을 보낸 항목은 `seen.json`에 기록하여 중복 알림을 방지합니다.
새 항목이 발견되면 Discord 웹훅으로 알림을 전송하고, 발견 이력을 `HISTORY.md`에 남깁니다.

```
[GitHub Actions 30분 주기]
        │
        ▼
  [poll.py 실행]
   ├── github_issues.py  →  GitHub REST API (3개 레포)
   └── forum_rss.py      →  Google Dev Forum RSS
        │
        ▼
  [seen.json과 비교 → 새 항목 필터링]
        │
   새 항목 있을 때만
        │
        ▼
  [Discord Embed 전송] + [HISTORY.md 기록] + [seen.json 업데이트]
```

## 모니터링 소스

| 소스 | 대상 | 방식 |
|---|---|---|
| 🐙 GitHub Issues | `googleapis/js-genai` | GitHub REST API |
| 🐙 GitHub Issues | `google/generative-ai-python` | GitHub REST API |
| 🐙 GitHub Issues | `google-gemini/cookbook` | GitHub REST API |
| 💬 Google Dev Forum | Gemini API 카테고리 | RSS 피드 |

## 파일 구조

```
gemini-batch-tracker/
├── poll.py                      # 메인 실행 파일
├── seen.json                    # 처리된 항목 ID + 타임스탬프 (90일 자동 정리)
├── HISTORY.md                   # 새 항목 발견 이력
├── requirements.txt
├── sources/
│   ├── github_issues.py         # GitHub 이슈 수집
│   └── forum_rss.py             # RSS 포럼 수집
├── notifiers/
│   └── discord.py               # Discord 알림 전송
├── docs/
│   └── architecture.html        # 상세 동작 구조 문서
└── .github/workflows/
    └── poll.yml                 # GitHub Actions 자동화 정의
```

## 설정 방법

GitHub 레포 → **Settings → Secrets and variables → Actions** 에서 아래 두 값을 등록합니다.

| Secret 이름 | 필수 여부 | 설명 |
|---|---|---|
| `DISCORD_WEBHOOK_URL` | **필수** | 알림을 받을 Discord 채널의 웹훅 URL |
| `GITHUB_TOKEN_CUSTOM` | 선택 | GitHub API 인증 토큰 (미설정 시 시간당 60회 제한) |

## 발견 이력

새 항목이 발견될 때마다 자동으로 [HISTORY.md](./HISTORY.md)에 기록됩니다.
