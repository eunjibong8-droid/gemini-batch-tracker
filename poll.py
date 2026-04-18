import json
import os
from datetime import datetime, timedelta, timezone
from sources import github_issues, forum_rss
from notifiers import discord

KEYWORDS      = ["batch"]
SEEN_FILE     = "seen.json"
HISTORY_FILE  = "HISTORY.md"
MAX_SEEN_DAYS = 90  # seen.json에서 이 기간이 지난 항목은 자동 정리

def load_seen() -> dict:
    """seen.json 로드. 기존 리스트 형식도 자동 마이그레이션."""
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            data = json.load(f)
        if isinstance(data, list):
            # 구 형식(리스트) → 신 형식(dict) 마이그레이션
            print(f"[seen] 구 형식 감지 — dict로 마이그레이션 ({len(data)}개)")
            return {item_id: "1970-01-01T00:00:00+00:00" for item_id in data}
        return data
    return {}

def save_seen(seen: dict) -> None:
    """MAX_SEEN_DAYS 이상 지난 항목을 정리한 뒤 저장."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=MAX_SEEN_DAYS)).isoformat()
    pruned = {k: v for k, v in seen.items() if v >= cutoff}
    removed = len(seen) - len(pruned)
    if removed:
        print(f"[seen] 오래된 항목 {removed}개 정리 (90일 초과)")
    with open(SEEN_FILE, "w") as f:
        json.dump(pruned, f, indent=2, ensure_ascii=False)

def append_history(now: str, new_items: list[dict]) -> None:
    """새 항목 발견 시 HISTORY.md 맨 위에 기록 추가."""
    # 날짜/시간 포맷: 2026-04-18 10:30 UTC
    dt = datetime.fromisoformat(now)
    timestamp = dt.strftime("%Y-%m-%d %H:%M UTC")

    lines = [f"## {timestamp}\n"]
    for item in new_items:
        state_tag = " `closed`" if item.get("state") == "closed" else ""
        lines.append(f"- {item['emoji']} **[{item['source']}]**{state_tag} [{item['title']}]({item['url']})\n")
    lines.append("\n")
    new_block = "".join(lines)

    # 기존 내용 앞에 삽입 (최신이 위에 오도록)
    existing = ""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, encoding="utf-8") as f:
            existing = f.read()

    # 헤더가 없으면 최초 생성
    header = "# 발견 이력\n\n"
    if existing.startswith(header):
        content = header + new_block + existing[len(header):]
    else:
        content = header + new_block + existing

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[history] HISTORY.md에 {len(new_items)}개 항목 기록")

def main():
    now = datetime.now(timezone.utc).isoformat()
    print(f"=== Gemini Batch Tracker 실행 ({now}) ===")
    print(f"모니터링 키워드: {KEYWORDS}")

    seen = load_seen()
    print(f"이미 처리된 항목: {len(seen)}개")

    all_items = []
    for keyword in KEYWORDS:
        all_items += github_issues.fetch(keyword)
        all_items += forum_rss.fetch(keyword)

    # 중복 제거 (같은 실행에서 여러 키워드에 걸릴 수 있음)
    seen_in_run: set[str] = set()
    unique_items = []
    for item in all_items:
        if item["id"] not in seen_in_run:
            seen_in_run.add(item["id"])
            unique_items.append(item)

    new_items = [item for item in unique_items if item["id"] not in seen]
    print(f"새 항목: {len(new_items)}개")

    if new_items:
        discord.send(new_items)
        append_history(now, new_items)
        for item in new_items:
            seen[item["id"]] = now
    else:
        print("새 항목 없음 — Discord 전송 스킵")

    save_seen(seen)  # 새 항목 유무와 관계없이 항상 저장 (파일 존재 보장 + 90일 정리)

    print("=== 완료 ===")

if __name__ == "__main__":
    main()
