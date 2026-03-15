"""
entity_fetcher.py – 搜尋追蹤人物與企業的最新動態
使用 DuckDuckGo News 搜尋（每日範圍），回傳標準化 article dict。
"""

import re
import config
import watch_list

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None


def _clean(text: str, max_len: int = 400) -> str:
    """清理文字：去除多餘空白，限制長度"""
    text = re.sub(r"\s+", " ", (text or "").strip())
    return text[:max_len]


def fetch_entity_news() -> list[dict]:
    """
    對 watch_list.PEOPLE 和 watch_list.COMPANIES 各自執行 DuckDuckGo News 搜尋，
    回傳標準化的 article dict 清單。

    每個 entity 最多取 2 則，整體上限由 config.TOP_ENTITY_ARTICLES 控制。
    """
    if DDGS is None:
        print("  ⚠️ duckduckgo_search 未安裝，跳過追蹤動態搜尋")
        return []

    articles: list[dict] = []
    seen_urls: set[str] = set()
    max_per_entity = 2

    # ── 搜尋追蹤人物 ──────────────────────────────────────────
    print(f"  👤 搜尋追蹤人物動態（{len(watch_list.PEOPLE)} 位）...")
    for person in watch_list.PEOPLE:
        if len(articles) >= config.TOP_ENTITY_ARTICLES:
            break
        try:
            with DDGS() as ddgs:
                results = list(ddgs.news(
                    person["search_query"],
                    max_results=max_per_entity,
                    timelimit="d",   # 過去 24 小時
                ))
            count = 0
            for r in results:
                url = r.get("url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                articles.append({
                    "title":       _clean(r.get("title", ""), 300),
                    "url":         url,
                    "summary":     _clean(r.get("body", ""), 400),
                    "category":    "人物動態",
                    "source":      r.get("source", ""),
                    "entity_name": person["name"],
                    "entity_zh":   person["name_zh"],
                    "entity_type": "person",
                    "entity_role": person["role"],
                })
                count += 1
            if count:
                print(f"    ✅ {person['name']}：{count} 則")
            else:
                print(f"    ─  {person['name']}：無最新消息")
        except Exception as e:
            print(f"    ⚠️ {person['name']} 搜尋失敗：{e}")

    # ── 搜尋追蹤企業 ──────────────────────────────────────────
    print(f"  🏢 搜尋追蹤企業動態（{len(watch_list.COMPANIES)} 家）...")
    for company in watch_list.COMPANIES:
        if len(articles) >= config.TOP_ENTITY_ARTICLES:
            break
        try:
            with DDGS() as ddgs:
                results = list(ddgs.news(
                    company["search_query"],
                    max_results=max_per_entity,
                    timelimit="d",
                ))
            count = 0
            for r in results:
                url = r.get("url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                articles.append({
                    "title":       _clean(r.get("title", ""), 300),
                    "url":         url,
                    "summary":     _clean(r.get("body", ""), 400),
                    "category":    "企業動態",
                    "source":      r.get("source", ""),
                    "entity_name": company["name"],
                    "entity_zh":   company["name_zh"],
                    "entity_type": "company",
                    "entity_role": "",
                })
                count += 1
            if count:
                print(f"    ✅ {company['name']}：{count} 則")
            else:
                print(f"    ─  {company['name']}：無最新消息")
        except Exception as e:
            print(f"    ⚠️ {company['name']} 搜尋失敗：{e}")

    # 整體上限
    articles = articles[:config.TOP_ENTITY_ARTICLES]
    print(f"  📋 追蹤動態合計：{len(articles)} 篇")
    return articles
