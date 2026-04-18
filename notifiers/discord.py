import requests
import os

MAX_EMBEDS_PER_MSG = 10  # Discord 제한

# 소스별 embed 색상
SOURCE_COLORS = {
    "GitHub": 0x24292e,       # GitHub 다크
    "Google Dev Forum": 0x4285F4,  # Google 블루
}

def _color_for(source: str) -> int:
    for key, color in SOURCE_COLORS.items():
        if key in source:
            return color
    return 0x5865F2  # Discord 기본 보라

def _build_embed(item: dict) -> dict:
    embed = {
        "title":       item["title"][:256],   # Discord 제한
        "url":         item["url"],
        "description": item["source"],
        "color":       _color_for(item["source"]),
    }
    if item.get("state") == "closed":
        embed["description"] += " · closed"
    return embed

def send(items: list[dict]) -> None:
    """새 항목 목록을 Discord로 전송. 항목이 많으면 여러 메시지로 분할."""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("[Discord] DISCORD_WEBHOOK_URL 환경변수 없음")
        return
    if not items:
        return

    embeds = [_build_embed(item) for item in items]

    # MAX_EMBEDS_PER_MSG 단위로 분할 전송
    chunks = [embeds[i:i + MAX_EMBEDS_PER_MSG] for i in range(0, len(embeds), MAX_EMBEDS_PER_MSG)]

    for idx, chunk in enumerate(chunks):
        content = None
        if idx == 0:
            content = f"🔍 **Gemini Batch API 관련 새 글 {len(items)}개**"

        payload: dict = {"embeds": chunk}
        if content:
            payload["content"] = content

        try:
            resp = requests.post(webhook_url, json=payload, timeout=10)
            resp.raise_for_status()
            print(f"[Discord] 메시지 {idx + 1}/{len(chunks)} 전송 완료 ({len(chunk)}개 embed)")
        except Exception as e:
            print(f"[Discord] 메시지 {idx + 1} 전송 실패: {e}")
