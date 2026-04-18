import feedparser

# 모니터링할 RSS 피드 목록 (이름, URL)
RSS_FEEDS = [
    ("Google Dev Forum", "https://discuss.ai.google.dev/c/gemini-api/4.rss"),
]

def fetch(keyword: str) -> list[dict]:
    """RSS 피드에서 keyword 포함된 항목 반환."""
    results = []

    for feed_name, rss_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(rss_url)
        except Exception as e:
            print(f"[Forum:{feed_name}] 에러: {e}")
            continue

        if feed.bozo and not feed.entries:
            print(f"[Forum:{feed_name}] 피드 파싱 실패: {feed.bozo_exception}")
            continue

        feed_count = 0
        for entry in feed.entries:
            title   = entry.get("title", "").lower()
            summary = entry.get("summary", "").lower()

            if keyword.lower() in title or keyword.lower() in summary:
                entry_id = entry.get("id") or entry.get("link", "")
                results.append({
                    "id":     f"forum-{entry_id}",
                    "title":  entry.get("title", "제목 없음"),
                    "url":    entry.get("link", ""),
                    "source": feed_name,
                    "emoji":  "💬",
                    "state":  "",
                })
                feed_count += 1

        print(f"[Forum:{feed_name}] '{keyword}' 키워드 {feed_count}개 발견")

    print(f"[Forum] 전체 {len(results)}개")
    return results
