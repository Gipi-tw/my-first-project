"""
interest_profiler.py – 使用 Claude AI 分析個人興趣輪廓
  1. analyze_profile   → 整合三方資料，推導 topic clusters
  2. generate_report   → 輸出 Markdown 分析報告
  3. update_config_topics → 更新 config.py 的 TOPICS 清單
"""

import json
import re
import os
from datetime import date

import anthropic

import config

_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def _extract_json(text: str) -> str:
    """從 Claude 回覆中取出 JSON"""
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1)
    return text.strip()


# ────────────────────────────────────────────────────────────
# Step 1 – Claude AI 分析興趣輪廓
# ────────────────────────────────────────────────────────────

def analyze_profile(
    blog_posts: list[dict],
    drive_files: list[dict],
    external_articles: list[dict] | None = None,
) -> dict:
    """
    整合個人網站、Google Drive 與外部文章，
    讓 Claude 推導出興趣 topic clusters 與建議的 TOPICS 清單。

    回傳格式：
    {
        "topic_clusters": [
            {"topic": "...", "confidence": 0.9, "evidence": ["..."]}
        ],
        "suggested_topics": ["...", "..."],
        "insight": "整體興趣輪廓說明..."
    }
    """

    # ── 整理部落格資料 ───────────────────────────────────────
    blog_lines = []
    for p in blog_posts[:40]:
        line = f"- {p['title']}"
        if p.get("excerpt"):
            line += f"：{p['excerpt'][:150]}"
        blog_lines.append(line)
    blog_block = "\n".join(blog_lines) if blog_lines else "（無資料）"

    # ── 整理 Google Drive 資料 ───────────────────────────────
    drive_lines = []
    for f in drive_files[:60]:
        line = f"- [{f['file_type']}] {f['title']}"
        if f.get("content_snippet"):
            snippet = f["content_snippet"][:200].replace("\n", " ")
            line += f"：{snippet}"
        drive_lines.append(line)
    drive_block = "\n".join(drive_lines) if drive_lines else "（無資料）"

    # ── 整理外部文章分類統計 ─────────────────────────────────
    category_counts: dict[str, int] = {}
    if external_articles:
        for a in external_articles:
            cat = a.get("category", "其他")
            category_counts[cat] = category_counts.get(cat, 0) + 1
    ext_block = "\n".join(
        f"- {cat}：{cnt} 篇" for cat, cnt in
        sorted(category_counts.items(), key=lambda x: -x[1])
    ) if category_counts else "（未提供）"

    prompt = f"""你是一位個人興趣分析專家。請根據以下三個來源的資料，
分析這位使用者真正感興趣的主題領域。

## 來源一：個人部落格文章（共 {len(blog_posts)} 篇）
{blog_block}

## 來源二：Google Drive 文件（共 {len(drive_files)} 個）
{drive_block}

## 來源三：外部新聞閱讀習慣（interest_agent 抓取分類統計）
{ext_block}

---

請完成以下分析：
1. 識別 5-8 個主要興趣主題 cluster，每個 cluster 提供：
   - 主題名稱（繁體中文，簡潔描述，例如「AI 應用與 LLM 技術」）
   - 信心分數（0.0-1.0，基於三個來源的佐證強度）
   - 具體佐證（列舉 2-3 個代表性標題或類別）
2. 建議 4-6 個用於 interest_agent 的 TOPICS 條目（繁體中文，格式參考：「AI / 機器學習」）
3. 一段 100-150 字的整體興趣輪廓描述

**只回傳 JSON，不要其他文字**，格式：
{{
  "topic_clusters": [
    {{
      "topic": "主題名稱",
      "confidence": 0.85,
      "evidence": ["佐證1", "佐證2", "佐證3"]
    }}
  ],
  "suggested_topics": ["主題A", "主題B", "主題C", "主題D"],
  "insight": "整體輪廓說明..."
}}"""

    response = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        raw = _extract_json(response.content[0].text)
        return json.loads(raw)
    except Exception as e:
        print(f"  [Profiler] 分析結果解析失敗: {e}")
        return {
            "topic_clusters": [],
            "suggested_topics": config.TOPICS[:],
            "insight": "（分析失敗，保留現有 TOPICS）",
        }


# ────────────────────────────────────────────────────────────
# Step 2 – 產生 Markdown 報告
# ────────────────────────────────────────────────────────────

def generate_report(
    profile: dict,
    blog_posts: list[dict],
    drive_files: list[dict],
) -> str:
    today = date.today().strftime("%Y-%m-%d")
    clusters = profile.get("topic_clusters", [])
    suggested = profile.get("suggested_topics", [])
    insight = profile.get("insight", "")

    lines = [
        f"# 個人興趣輪廓分析報告",
        f"",
        f"> 分析日期：{today}",
        f"",
        f"## 資料來源統計",
        f"",
        f"| 來源 | 數量 |",
        f"|------|------|",
        f"| 個人部落格文章 | {len(blog_posts)} 篇 |",
        f"| Google Drive 文件 | {len(drive_files)} 個 |",
        f"",
        f"---",
        f"",
        f"## 整體興趣輪廓",
        f"",
        insight,
        f"",
        f"---",
        f"",
        f"## 發現的興趣主題 Clusters",
        f"",
    ]

    for i, cluster in enumerate(clusters, 1):
        topic = cluster.get("topic", "")
        confidence = cluster.get("confidence", 0.0)
        evidence = cluster.get("evidence", [])
        conf_bar = "█" * int(confidence * 10) + "░" * (10 - int(confidence * 10))
        lines.append(f"### {i}. {topic}")
        lines.append(f"")
        lines.append(f"信心分數：`{conf_bar}` {confidence:.0%}")
        lines.append(f"")
        lines.append(f"**佐證：**")
        for ev in evidence:
            lines.append(f"- {ev}")
        lines.append(f"")

    lines += [
        f"---",
        f"",
        f"## 建議更新的 TOPICS 清單",
        f"",
        f"以下為 Claude AI 建議的新 `TOPICS` 設定，可複製至 `config.py`：",
        f"",
        f"```python",
        f"TOPICS = [",
    ]
    for t in suggested:
        lines.append(f'    "{t}",')
    lines += [
        f"]",
        f"```",
        f"",
        f"---",
        f"",
        f"*由 Interest Agent Profile Builder 自動產生*",
    ]

    return "\n".join(lines)


# ────────────────────────────────────────────────────────────
# Step 3 – 更新 config.py TOPICS
# ────────────────────────────────────────────────────────────

def update_config_topics(new_topics: list[str]) -> None:
    """
    以正規表達式替換 config.py 中的 TOPICS = [...] 區塊。
    """
    config_path = os.path.join(os.path.dirname(__file__), "config.py")
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 建立新的 TOPICS 區塊
    items = "\n".join(f'    "{t}",' for t in new_topics)
    new_block = f"TOPICS = [\n{items}\n]"

    # 替換舊的 TOPICS = [...] 區塊（支援多行）
    updated = re.sub(
        r"TOPICS\s*=\s*\[.*?\]",
        new_block,
        content,
        flags=re.DOTALL,
    )

    if updated == content:
        print("  ⚠️ 未找到 TOPICS 區塊，config.py 未修改")
        return

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(updated)

    print(f"  ✅ config.py TOPICS 已更新（{len(new_topics)} 個主題）")
