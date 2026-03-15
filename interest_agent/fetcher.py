"""
fetcher.py – 從三個來源抓取文章
  1. RSS Feeds（Reddit subreddits、Dev.to、TechCrunch 等）
  2. Hacker News Top Stories（官方 Firebase API）
  3. DuckDuckGo Web Search（免費、無需 API key）
"""

import requests
import feedparser
from ddgs import DDGS

import config

_HEADERS = {"User-Agent": "InterestAgent/1.0 (personal digest bot)"}


def _clean(text: str, limit: int = 400) -> str:
    """移除多餘空白並截斷"""
    return " ".join((text or "").split())[:limit]


# ────────────────────────────────────────────────────────────
# RSS Feeds
# ────────────────────────────────────────────────────────────

def fetch_rss() -> list[dict]:
    articles = []
    for feed_cfg in config.RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed_cfg["url"], request_headers=_HEADERS)
            for entry in parsed.entries[: config.MAX_ARTICLES_PER_FEED]:
                url = entry.get("link", "")
                title = _clean(entry.get("title", ""))
                summary = _clean(entry.get("summary", "") or entry.get("description", ""))
                if not url or not title:
                    continue
                articles.append({
                    "title":    title,
                    "url":      url,
                    "summary":  summary,
                    "category": feed_cfg["category"],
                    "source":   parsed.feed.get("title") or feed_cfg["url"],
                })
        except Exception as e:
            print(f"  [RSS] 無法抓取 {feed_cfg['url']}: {e}")
    return articles


# ────────────────────────────────────────────────────────────
# Hacker News（Algolia Firebase API）
# ────────────────────────────────────────────────────────────

def fetch_hn(limit: int = 20) -> list[dict]:
    articles = []
    try:
        ids = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=10,
        ).json()[:limit]

        for sid in ids:
            try:
                story = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                    timeout=5,
                ).json()
                url = story.get("url", "")
                if not url:
                    url = f"https://news.ycombinator.com/item?id={sid}"
                articles.append({
                    "title":    _clean(story.get("title", "")),
                    "url":      url,
                    "summary":  f"HN 分數: {story.get('score', 0)}，留言數: {story.get('descendants', 0)}",
                    "category": "Tech/Dev",
                    "source":   "Hacker News",
                })
            except Exception:
                continue
    except Exception as e:
        print(f"  [HN] 抓取失敗: {e}")
    return articles


# ────────────────────────────────────────────────────────────
# DuckDuckGo Web Search
# ────────────────────────────────────────────────────────────

def fetch_web_search() -> list[dict]:
    articles = []
    try:
        with DDGS() as ddgs:
            for query in config.SEARCH_QUERIES:
                try:
                    results = list(ddgs.text(query, max_results=5, timelimit="w"))
                    for r in results:
                        articles.append({
                            "title":    _clean(r.get("title", "")),
                            "url":      r.get("href", ""),
                            "summary":  _clean(r.get("body", "")),
                            "category": "Web Search",
                            "source":   "DuckDuckGo",
                        })
                except Exception as e:
                    print(f"  [DDG] 搜尋 '{query}' 失敗: {e}")
    except Exception as e:
        print(f"  [DDG] 初始化失敗: {e}")
    return articles


# ────────────────────────────────────────────────────────────
# 統一入口：抓取並去重
# ────────────────────────────────────────────────────────────

def fetch_all() -> list[dict]:
    print("  📡 RSS feeds...")
    rss = fetch_rss()
    print(f"     → {len(rss)} 篇")

    print("  📡 Hacker News...")
    hn = fetch_hn()
    print(f"     → {len(hn)} 篇")

    print("  📡 Web search...")
    web = fetch_web_search()
    print(f"     → {len(web)} 篇")

    # 合併並以 URL 去重
    all_articles = rss + hn + web
    seen: set[str] = set()
    unique = []
    for a in all_articles:
        if a["url"] and a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)

    print(f"  ✅ 共 {len(unique)} 篇（去重後）")
    return unique
