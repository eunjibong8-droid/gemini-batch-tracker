import requests
import os

# 모니터링할 GitHub 레포지토리 목록
REPOS = [
    "googleapis/js-genai",
    "google/generative-ai-python",
    "google-gemini/cookbook",
]

GITHUB_API = "https://api.github.com/repos/{repo}/issues"

def _make_headers() -> dict:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.getenv("GITHUB_TOKEN_CUSTOM")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

def fetch(keyword: str) -> list[dict]:
    """여러 GitHub 레포의 Issues에서 keyword 포함된 항목 반환."""
    headers = _make_headers()
    results = []

    for repo in REPOS:
        url = GITHUB_API.format(repo=repo)
        params = {
            "state":     "all",       # open + closed 모두 확인
            "per_page":  100,
            "sort":      "updated",
            "direction": "desc",
        }
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            issues = resp.json()
        except Exception as e:
            print(f"[GitHub:{repo}] 에러: {e}")
            continue

        repo_count = 0
        for issue in issues:
            if "pull_request" in issue:
                continue

            title = issue.get("title", "").lower()
            body  = (issue.get("body") or "").lower()

            if keyword.lower() in title or keyword.lower() in body:
                results.append({
                    "id":     f"github-{repo}-{issue['number']}",
                    "title":  issue["title"],
                    "url":    issue["html_url"],
                    "source": f"GitHub ({repo})",
                    "emoji":  "🐙",
                    "state":  issue.get("state", ""),
                })
                repo_count += 1

        print(f"[GitHub:{repo}] '{keyword}' 키워드 {repo_count}개 발견")

    print(f"[GitHub] 전체 {len(results)}개")
    return results
