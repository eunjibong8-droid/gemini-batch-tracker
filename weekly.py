import json
import os
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from sources import github_issues, forum_rss
from notifiers import discord

KEYWORDS     = ["batch"]
SEEN_FILE    = "seen.json"

# 키워드 분석에서 제외할 단어
STOP_WORDS = {
    "the", "a", "an", "is", "in", "for", "to", "of", "with", "how",
    "this", "that", "on", "at", "be", "are", "was", "it", "as", "or",
    "and", "not", "from", "by", "when", "what", "can", "use", "using",
    "has", "does", "but", "you", "have", "more", "will", "would",
    "about", "help", "via", "get", "new", "add", "fix", "run",
    "batch", "api", "gemini", "google", "issue", "error", "support",
}

def extract_keywords(titles: list[str]) -> list[tuple[str, int]]:
    words = []
    for title in titles:
        tokens = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())
        words.extend(t for t in tokens if t not in STOP_WORDS)
    return Counter(words).most_common(5)

def count_last_week(seen: dict, now: datetime) -> int:
    """지난 주(7~14일 전) seen.json에 기록된 항목 수."""
    two_weeks_ago = (now - timedelta(days=14)).isoformat()
    week_ago      = (now - timedelta(days=7)).isoformat()
    return sum(1 for ts in seen.values() if two_weeks_ago <= ts < week_ago)

def main():
    now      = datetime.now(timezone.utc)
    since_dt = now - timedelta(days=7)
    since_iso = since_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    week_label = f"{since_dt.strftime('%m/%d')} ~ {now.strftime('%m/%d')}"
    print(f"=== 주간 요약 생성 ({week_label}) ===")

    # 지난 7일 항목 수집
    all_items = []
    for keyword in KEYWORDS:
        all_items += github_issues.fetch(keyword, since=since_iso)
        all_items += forum_rss.fetch(keyword, since=since_dt)

    # 중복 제거
    seen_ids: set[str] = set()
    unique_items = []
    for item in all_items:
        if item["id"] not in seen_ids:
            seen_ids.add(item["id"])
            unique_items.append(item)

    print(f"이번 주 항목: {len(unique_items)}개")

    # 소스별 건수
    source_counts = dict(Counter(item["source"] for item in unique_items))

    # 키워드 분석
    top_keywords = extract_keywords([item["title"] for item in unique_items])

    # 지난 주 건수 (seen.json 기준)
    last_week_total = 0
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            seen = json.load(f)
        if isinstance(seen, dict):
            last_week_total = count_last_week(seen, now)

    discord.send_weekly(
        week_label=week_label,
        total=len(unique_items),
        last_week_total=last_week_total,
        source_counts=source_counts,
        top_keywords=top_keywords,
        items=unique_items,
    )

    print("=== 완료 ===")

if __name__ == "__main__":
    main()
