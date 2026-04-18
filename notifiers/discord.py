import requests
import os

MAX_EMBEDS_PER_MSG = 10  # Discord 제한

# 소스별 embed 색상
SOURCE_COLORS = {
    "GitHub": 0x24292e,
    "Google Dev Forum": 0x4285F4,
}

def _color_for(source: str) -> int:
    for key, color in SOURCE_COLORS.items():
        if key in source:
            return color
    return 0x5865F2

def _build_embed(item: dict) -> dict:
    embed = {
        "title":       item["title"][:256],
        "url":         item["url"],
        "description": item["source"],
        "color":       _color_for(item["source"]),
    }
    if item.get("state") == "closed":
        embed["description"] += " · closed"
    return embed

def _post(webhook_url: str, payload: dict) -> None:
    resp = requests.post(webhook_url, json=payload, timeout=10)
    resp.raise_for_status()

def send(items: list[dict]) -> None:
    """새 항목 목록을 Discord로 전송. 항목이 많으면 여러 메시지로 분할."""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("[Discord] DISCORD_WEBHOOK_URL 환경변수 없음")
        return
    if not items:
        return

    embeds = [_build_embed(item) for item in items]
    chunks = [embeds[i:i + MAX_EMBEDS_PER_MSG] for i in range(0, len(embeds), MAX_EMBEDS_PER_MSG)]

    for idx, chunk in enumerate(chunks):
        payload: dict = {"embeds": chunk}
        if idx == 0:
            payload["content"] = f"🔍 **Gemini Batch API 관련 새 글 {len(items)}개**"
        try:
            _post(webhook_url, payload)
            print(f"[Discord] 메시지 {idx + 1}/{len(chunks)} 전송 완료 ({len(chunk)}개 embed)")
        except Exception as e:
            print(f"[Discord] 메시지 {idx + 1} 전송 실패: {e}")

def send_weekly(
    week_label: str,
    total: int,
    last_week_total: int,
    source_counts: dict,
    top_keywords: list[tuple[str, int]],
    items: list[dict],
) -> None:
    """주간 혼합형 요약을 Discord Embed로 전송."""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("[Discord] DISCORD_WEBHOOK_URL 환경변수 없음")
        return

    # 증감 표시
    if last_week_total == 0:
        trend = "기준 없음"
    elif total > last_week_total:
        pct = round((total - last_week_total) / last_week_total * 100)
        trend = f"▲ {pct}%  (지난 주 {last_week_total}건)"
    elif total < last_week_total:
        pct = round((last_week_total - total) / last_week_total * 100)
        trend = f"▼ {pct}%  (지난 주 {last_week_total}건)"
    else:
        trend = f"→ 동일  (지난 주 {last_week_total}건)"

    # 소스별 건수
    if source_counts:
        source_lines = "\n".join(
            f"{src}  **{cnt}건**"
            for src, cnt in sorted(source_counts.items(), key=lambda x: -x[1])
        )
    else:
        source_lines = "이번 주 새 글 없음"

    # 키워드 막대 그래프
    if top_keywords:
        max_cnt = top_keywords[0][1]
        bar_width = 8

        def bar(cnt):
            filled = round(cnt / max_cnt * bar_width) if max_cnt else 0
            return "█" * filled + "░" * (bar_width - filled)

        kw_lines = "\n".join(
            f"`{word:<14}` {bar(cnt)}  {cnt}회"
            for word, cnt in top_keywords
        )
    else:
        kw_lines = "분석할 키워드 없음"

    # 항목 목록 (최대 5개)
    if items:
        item_lines = "\n".join(
            f"{item['emoji']} [{item['title'][:55]}]({item['url']})"
            for item in items[:5]
        )
        if len(items) > 5:
            item_lines += f"\n_외 {len(items) - 5}건 더 있음_"
    else:
        item_lines = "없음"

    embed = {
        "title": f"📊  주간 리포트  {week_label}",
        "color": 0x58a6ff,
        "fields": [
            {
                "name": f"이번 주 새 글  **{total}건**  ({trend})",
                "value": source_lines,
                "inline": False,
            },
            {
                "name": "🔑  자주 언급된 키워드",
                "value": kw_lines,
                "inline": False,
            },
            {
                "name": "📝  이번 주 항목",
                "value": item_lines,
                "inline": False,
            },
        ],
    }

    try:
        _post(webhook_url, {"embeds": [embed]})
        print("[Discord] 주간 요약 전송 완료")
    except Exception as e:
        print(f"[Discord] 주간 요약 전송 실패: {e}")
