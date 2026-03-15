"""
emailer.py – 將精選文章格式化為 HTML Email 並發送
"""

import html
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

import config


def _safe_text(text: str) -> str:
    """移除 HTML 標籤並 escape 特殊字元，確保純文字安全插入 HTML 模板"""
    # 移除所有 HTML 標籤
    text = re.sub(r"<[^>]+>", " ", text or "")
    # 合併多餘空白
    text = " ".join(text.split())
    # Escape HTML 特殊字元（< > & " 等）
    return html.escape(text)


# ────────────────────────────────────────────────────────────
# HTML 樣板
# ────────────────────────────────────────────────────────────

_CATEGORY_COLORS = {
    "AI/ML":        "#7c3aed",
    "Software Dev": "#0284c7",
    "Tech/Dev":     "#0369a1",
    "Tech News":    "#0891b2",
    "Product":      "#059669",
    "Web Search":   "#6b7280",
    "人物動態":     "#dc2626",
    "企業動態":     "#ea580c",
}

_ENTITY_TYPE_ICON = {
    "person":  "👤",
    "company": "🏢",
}


def _category_badge(category: str) -> str:
    color = _CATEGORY_COLORS.get(category, "#6b7280")
    return (
        f'<span style="background:{color};color:#fff;'
        f'padding:2px 9px;border-radius:12px;font-size:11px;'
        f'font-weight:600;margin-left:8px;">{category}</span>'
    )


def _entity_badge(entity_name: str, entity_type: str) -> str:
    icon = _ENTITY_TYPE_ICON.get(entity_type, "🔖")
    return (
        f'<span style="background:#fff3cd;color:#856404;border:1px solid #ffc107;'
        f'padding:2px 9px;border-radius:12px;font-size:11px;'
        f'font-weight:600;margin-left:6px;">{icon} {html.escape(entity_name)}</span>'
    )


def _build_article_row(i: int, a: dict, summary_map: dict) -> str:
    """產生單篇文章的 HTML 區塊（含摘要與「為何值得關注」）"""
    raw_summary = summary_map.get(i, {})
    summary          = _safe_text(raw_summary.get("summary", a.get("summary", "")))
    relevance_reason = _safe_text(raw_summary.get("relevance_reason", ""))
    title   = _safe_text(a["title"])
    source  = _safe_text(a.get("source", ""))
    url     = html.escape(a.get("url", "#"), quote=True)
    badge   = _category_badge(a["category"])

    # 追蹤人物/企業 badge
    entity_html = ""
    if a.get("entity_name"):
        entity_html = _entity_badge(a["entity_name"], a.get("entity_type", ""))

    # 「為何值得關注」區塊（有內容才顯示）
    relevance_html = ""
    if relevance_reason:
        relevance_html = f"""
          <div style="background:#f0f7ff;border-radius:8px;padding:12px 14px;margin-top:10px;">
            <div style="color:#1d4ed8;font-size:12px;font-weight:600;margin-bottom:4px;">
              💡 為何值得關注
            </div>
            <div style="color:#374151;line-height:1.65;font-size:13px;">{relevance_reason}</div>
          </div>"""

    return f"""
        <div style="margin-bottom:28px;border-left:4px solid #e94560;padding-left:16px;">
          <h2 style="margin:0 0 4px 0;font-size:17px;line-height:1.4;">
            <a href="{url}" style="color:#1a1a2e;text-decoration:none;">{title}</a>
            {badge}{entity_html}
          </h2>
          <div style="color:#888;font-size:12px;margin-bottom:8px;">來源：{source}</div>
          <div style="color:#444;line-height:1.7;font-size:14px;">{summary}</div>
          {relevance_html}
        </div>"""


def build_html(articles: list[dict], digest: dict) -> str:
    date_str = datetime.now().strftime("%Y 年 %m 月 %d 日")
    intro = _safe_text(digest.get("intro", ""))

    # 將 summaries 轉成 index → {summary, relevance_reason} 的 map
    summary_map = {
        s["index"]: s
        for s in digest.get("summaries", [])
    }

    # 分組：追蹤動態（entity_name 欄位）vs 一般精選
    entity_articles  = [(i, a) for i, a in enumerate(articles) if a.get("entity_name")]
    regular_articles = [(i, a) for i, a in enumerate(articles) if not a.get("entity_name")]

    # ── 追蹤動態 section ──────────────────────────────────────
    entity_rows = ""
    if entity_articles:
        rows_html = "".join(_build_article_row(i, a, summary_map) for i, a in entity_articles)
        entity_rows = f"""
    <!-- 今日追蹤動態 -->
    <div style="padding:20px 32px 0;">
      <div style="font-size:16px;font-weight:700;color:#1a1a2e;margin-bottom:16px;
                  padding-bottom:8px;border-bottom:2px solid #e94560;">
        🔔 今日追蹤動態
      </div>
      {rows_html}
    </div>"""

    # ── 今日精選 section ──────────────────────────────────────
    regular_rows = ""
    if regular_articles:
        rows_html = "".join(_build_article_row(i, a, summary_map) for i, a in regular_articles)
        regular_rows = f"""
    <!-- 今日精選 -->
    <div style="padding:20px 32px 0;">
      <div style="font-size:16px;font-weight:700;color:#1a1a2e;margin-bottom:16px;
                  padding-bottom:8px;border-bottom:2px solid #94a3b8;">
        📚 今日精選
      </div>
      {rows_html}
    </div>"""

    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>每日興趣摘要</title>
</head>
<body style="margin:0;padding:0;background:#f4f5f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:680px;margin:30px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08);">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);padding:28px 32px;">
      <h1 style="margin:0;color:#fff;font-size:22px;font-weight:700;">📰 每日興趣摘要</h1>
      <p style="margin:6px 0 0;color:#94a3b8;font-size:13px;">{date_str} · 由 Claude AI 精選</p>
    </div>

    <!-- Intro -->
    <div style="background:#f8f9fb;padding:20px 32px;border-bottom:1px solid #e9ecef;">
      <p style="margin:0;color:#374151;line-height:1.7;font-size:14px;">{intro}</p>
    </div>

    <!-- 追蹤動態 + 今日精選 -->
    {entity_rows}
    {regular_rows}

    <!-- Footer -->
    <div style="background:#f8f9fb;padding:16px 32px;text-align:center;border-top:1px solid #e9ecef;margin-top:24px;">
      <p style="margin:0;color:#9ca3af;font-size:11px;">
        由 Interest Agent 自動生成 · Claude AI 驅動 · 如需調整請修改 config.py 與 watch_list.py
      </p>
    </div>
  </div>
</body>
</html>"""


# ────────────────────────────────────────────────────────────
# 發送 Email
# ────────────────────────────────────────────────────────────

def send_digest(articles: list[dict], digest: dict, dry_run: bool = False) -> None:
    html_content = build_html(articles, digest)
    date_str = datetime.now().strftime("%Y-%m-%d")
    entity_count  = sum(1 for a in articles if a.get("entity_name"))
    regular_count = len(articles) - entity_count
    subject = f"📰 每日興趣摘要 – {date_str}（追蹤動態 {entity_count} 篇 · 精選 {regular_count} 篇）"

    if dry_run:
        # Dry run：將 HTML 存到檔案供預覽
        preview_path = f"digest_preview_{date_str}.html"
        with open(preview_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"  [Dry Run] HTML 已儲存至 {preview_path}，請用瀏覽器開啟預覽。")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = config.EMAIL_SENDER
    msg["To"]      = config.EMAIL_RECIPIENT
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(config.EMAIL_SENDER, config.EMAIL_PASSWORD)
        server.sendmail(
            config.EMAIL_SENDER,
            config.EMAIL_RECIPIENT,
            msg.as_bytes(),
        )

    print(f"  ✅ Email 已發送至 {config.EMAIL_RECIPIENT}")
