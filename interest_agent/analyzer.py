"""
analyzer.py – 使用 Claude API 進行兩步驟分析
  Step 1: score_and_filter  → 對所有文章評分，選出最相關的 TOP_N 篇
  Step 2: generate_digest   → 為精選文章產生繁體中文摘要與導言
"""

import json
import re

import anthropic

import config
import watch_list

_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def _extract_json(text: str) -> str:
    """從 Claude 回覆中取出 JSON（處理可能有 ```json ... ``` 包裹的情況）"""
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1)
    return text.strip()


# ────────────────────────────────────────────────────────────
# Step 1 – 評分篩選
# ────────────────────────────────────────────────────────────

def score_and_filter(articles: list[dict]) -> list[dict]:
    """
    把文章清單送給 Claude，要求依相關性評分（0-10），
    回傳分數 >= MIN_SCORE 的前 TOP_ARTICLES_COUNT 篇。
    """
    candidates = articles[: config.MAX_ARTICLES_TO_SCORE]
    topics_str = "、".join(config.TOPICS)

    lines = []
    for i, a in enumerate(candidates):
        lines.append(
            f"{i}. [{a['source']}] {a['title'][:120]}\n"
            f"   {a['summary'][:200]}"
        )
    articles_block = "\n".join(lines)

    people_str   = "、".join(watch_list.PEOPLE_NAMES)
    companies_str = "、".join(watch_list.COMPANY_NAMES)

    prompt = f"""你是一位內容策展人，負責為一位對以下主題感興趣的讀者挑選文章：
{topics_str}

【讀者特別追蹤的人物】：{people_str}
【讀者特別追蹤的企業】：{companies_str}
【其他需留意的人物類型】：{watch_list.DYNAMIC_ENTITY_HINT}

請對下列 {len(candidates)} 篇文章的相關性進行評分（0 = 完全無關，10 = 極度相關）。
只回傳分數 >= {config.MIN_SCORE} 的文章。

【額外加分規則】：
- 文章直接報導上述追蹤人物的近期言論、訪談或決策 → +2 分（上限 10 分）
- 文章報導上述追蹤企業的產品發布、戰略調整或重大消息 → +2 分（上限 10 分）
- 文章提及其他 AI 高管、Fortune 500 CEO 或知名科技 Podcaster → +1 分

文章清單：
{articles_block}

**只回傳 JSON 陣列，不要其他文字**，格式如下：
[{{"index": 0, "score": 8.5, "entities_mentioned": ["Sam Altman", "OpenAI"]}}, {{"index": 3, "score": 7.0, "entities_mentioned": []}}, ...]
（entities_mentioned 填入文章中提及的追蹤人物/企業名稱，未提及則填空陣列）"""

    response = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        raw = _extract_json(response.content[0].text)
        scored: list[dict] = json.loads(raw)
        scored.sort(key=lambda x: x["score"], reverse=True)
        result = []
        for s in scored[: config.TOP_ARTICLES_COUNT]:
            idx = s["index"]
            if 0 <= idx < len(candidates):
                article = dict(candidates[idx])
                article["entities_mentioned"] = s.get("entities_mentioned", [])
                result.append(article)
        return result
    except Exception as e:
        print(f"  [Analyzer] 評分解析失敗: {e}")
        return candidates[: config.TOP_ARTICLES_COUNT]


# ────────────────────────────────────────────────────────────
# Step 2 – 產生繁體中文摘要
# ────────────────────────────────────────────────────────────

def generate_digest(articles: list[dict]) -> dict:
    """
    為精選文章生成繁體中文摘要，並撰寫一段導言。
    回傳格式：{"intro": "...", "summaries": [{"index": 0, "summary": "..."}, ...]}
    """
    topics_str = "、".join(config.TOPICS)

    items = []
    for i, a in enumerate(articles):
        items.append(
            f"{i}. 標題: {a['title']}\n"
            f"   來源: {a['source']}\n"
            f"   說明: {a['summary'][:350]}"
        )
    articles_block = "\n\n".join(items)

    people_str    = "、".join(watch_list.PEOPLE_NAMES)
    companies_str = "、".join(watch_list.COMPANY_NAMES)

    prompt = f"""請用繁體中文為以下精選文章撰寫個人化每日摘要。

【讀者背景】：資深科技業管理者，負責 AI 產品策略與 B2B 業務開發，持續關注 AI 商業應用、組織管理與高科技產業趨勢。
【讀者興趣主題】：{topics_str}
【讀者追蹤人物】：{people_str}
【讀者追蹤企業】：{companies_str}

任務：
1. 撰寫一段 2-3 句的導言，總結今日最值得關注的人物/企業動態或趨勢。
2. 為每篇文章各完成以下兩個欄位（每欄位限 2 句，簡潔有力）：
   - summary：2 句，說明文章核心內容
   - relevance_reason：2 句「為何值得關注」，說明：與讀者追蹤的人物/企業或興趣主題的連結，以及對讀者工作的啟示或行動建議

文章：
{articles_block}

**只回傳 JSON，不要其他文字**，格式：
{{
  "intro": "今日導言...",
  "summaries": [
    {{"index": 0, "summary": "...", "relevance_reason": "..."}},
    ...
  ]
}}"""

    response = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        raw = _extract_json(response.content[0].text)
        return json.loads(raw)
    except Exception as e:
        resp_text = response.content[0].text if response.content else ""
        stop_reason = response.stop_reason
        print(f"  [Analyzer] 摘要解析失敗: {e}")
        print(f"  [Analyzer] stop_reason={stop_reason}, 回應長度={len(resp_text)} 字元")
        if resp_text:
            print(f"  [Analyzer] 回應前 300 字：{resp_text[:300]}")
        return {
            "intro": "今日精選來自 AI、軟體開發、科技新聞與產品管理的優質文章。",
            "summaries": [
                {"index": i, "summary": a.get("summary", ""), "relevance_reason": ""}
                for i, a in enumerate(articles)
            ],
        }
