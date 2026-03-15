"""
profile_main.py – 個人興趣輪廓分析主程式

用法：
  python profile_main.py              # 分析 + 更新 config.py TOPICS + 儲存報告
  python profile_main.py --dry-run    # 只產生報告，不修改 config.py
"""

import argparse
import sys
import os
from datetime import date

# 強制 UTF-8 輸出
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

import config
from profile_collector  import collect_all
from interest_profiler  import analyze_profile, generate_report, update_config_topics
from fetcher            import fetch_all
from analyzer           import score_and_filter


def check_config() -> None:
    if not config.ANTHROPIC_API_KEY:
        print("❌ ANTHROPIC_API_KEY 未設定，請檢查 .env 檔案。")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interest Profile Builder – 分析個人興趣輪廓"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只產生報告，不修改 config.py TOPICS",
    )
    parser.add_argument(
        "--skip-external",
        action="store_true",
        help="跳過外部文章抓取（加快速度，但分析資料較少）",
    )
    args = parser.parse_args()

    print("\n🔍 Interest Profile Builder 啟動中...\n")
    check_config()

    # ── Step 1：收集個人內容 ──────────────────────────────────
    print("【Step 1】收集個人來源內容")
    personal_data = collect_all()
    blog_posts  = personal_data["blog_posts"]
    drive_files = personal_data["drive_files"]

    print(f"\n  📊 個人資料彙整：")
    print(f"     部落格文章：{len(blog_posts)} 篇")
    print(f"     Drive 檔案：{len(drive_files)} 個")

    if not blog_posts and not drive_files:
        print("\n⚠️ 未收集到任何個人內容，請檢查網路連線或 Google Drive 設定。")
        print("   仍可繼續使用外部文章進行分析...\n")

    # ── Step 2：抓取外部高分文章（可選）────────────────────────
    external_articles = []
    if not args.skip_external:
        print("\n【Step 2】抓取外部 RSS 文章（供分析參考）")
        print("  （提示：若只想分析個人內容，可加上 --skip-external）")
        all_articles = fetch_all()
        if all_articles:
            print("\n  🤖 AI 評分篩選外部文章...")
            external_articles = score_and_filter(all_articles)
            print(f"  ✅ 精選出 {len(external_articles)} 篇外部文章")
    else:
        print("\n【Step 2】跳過外部文章抓取（--skip-external）")

    # ── Step 3：Claude AI 分析興趣輪廓 ───────────────────────
    print("\n【Step 3】Claude AI 分析個人興趣輪廓")
    profile = analyze_profile(
        blog_posts=blog_posts,
        drive_files=drive_files,
        external_articles=external_articles,
    )

    clusters  = profile.get("topic_clusters", [])
    suggested = profile.get("suggested_topics", [])
    print(f"  ✅ 發現 {len(clusters)} 個興趣主題 cluster")
    print(f"  ✅ 建議 TOPICS：{suggested}")

    # ── Step 4：產生 Markdown 報告 ────────────────────────────
    print("\n【Step 4】產生分析報告")
    report_md = generate_report(profile, blog_posts, drive_files)

    today = date.today().strftime("%Y-%m-%d")
    report_filename = f"interest_profile_{today}.md"
    report_path = os.path.join(os.path.dirname(__file__), report_filename)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"  ✅ 報告已儲存：{report_filename}")

    # ── Step 5：更新 config.py TOPICS ─────────────────────────
    if args.dry_run:
        print("\n【Step 5】Dry Run 模式 – 跳過更新 config.py")
        print("\n  建議的新 TOPICS 清單：")
        for t in suggested:
            print(f"    - {t}")
    else:
        print("\n【Step 5】更新 config.py TOPICS")
        if suggested:
            update_config_topics(suggested)
        else:
            print("  ⚠️ 未取得建議 TOPICS，config.py 未修改")

    print(f"\n✅ 全部完成！報告位置：{report_path}\n")


if __name__ == "__main__":
    main()
