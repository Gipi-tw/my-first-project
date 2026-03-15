"""
main.py – Interest Agent 主程式

用法：
  python main.py              # 執行並發送 Email
  python main.py --dry-run    # 僅產生 HTML 預覽，不寄信
"""

import argparse
import sys

# 強制 UTF-8 輸出，避免 Windows CP950 編碼錯誤
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

import config
from fetcher        import fetch_all
from entity_fetcher import fetch_entity_news
from analyzer       import score_and_filter, generate_digest
from emailer        import send_digest


def check_config(dry_run: bool) -> None:
    errors = []
    if not config.ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY 未設定")
    if not dry_run:
        if not config.EMAIL_SENDER:
            errors.append("EMAIL_SENDER 未設定")
        if not config.EMAIL_PASSWORD:
            errors.append("EMAIL_PASSWORD 未設定")
        if not config.EMAIL_RECIPIENT:
            errors.append("EMAIL_RECIPIENT 未設定")
    if errors:
        print("❌ 設定錯誤，請檢查 .env 檔案：")
        for e in errors:
            print(f"   • {e}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Interest Agent – 每日興趣內容摘要")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="不發送 Email，改將 HTML 儲存到本地檔案供預覽",
    )
    args = parser.parse_args()

    print("\n🤖 Interest Agent 啟動中...\n")
    check_config(args.dry_run)

    # ── Step 1：抓取一般內容 ──────────────────────────────────
    print("【Step 1】抓取 RSS / HN / 網路搜尋內容")
    articles = fetch_all()

    if not articles:
        print("❌ 未抓到任何文章，請檢查網路連線或 RSS Feeds 設定。")
        sys.exit(1)

    # ── Step 2：抓取追蹤人物/企業動態 ────────────────────────
    print("\n【Step 2】抓取追蹤人物 & 企業動態")
    entity_articles = fetch_entity_news()
    print(f"  ✅ 追蹤動態：{len(entity_articles)} 篇")

    # ── Step 3：AI 評分篩選（一般文章）───────────────────────
    print("\n【Step 3】Claude AI 評分篩選")
    top_regular = score_and_filter(articles)
    print(f"  ✅ 一般精選：{len(top_regular)} 篇")

    if not top_regular and not entity_articles:
        print("❌ 沒有文章通過篩選門檻，請嘗試降低 MIN_SCORE 或增加來源。")
        sys.exit(1)

    # ── 合併：追蹤動態在前，一般精選在後 ────────────────────
    final_articles = entity_articles + top_regular

    # ── Step 4：產生個人化摘要 ───────────────────────────────
    print("\n【Step 4】Claude AI 產生個人化摘要（含為何值得關注）")
    digest = generate_digest(final_articles)
    print("  ✅ 摘要完成")

    # ── Step 5：發送 Email / Dry Run ──────────────────────────
    mode = "Dry Run 預覽" if args.dry_run else "發送 Email"
    print(f"\n【Step 5】{mode}")
    send_digest(final_articles, digest, dry_run=args.dry_run)

    print("\n✅ 全部完成！\n")


if __name__ == "__main__":
    main()
