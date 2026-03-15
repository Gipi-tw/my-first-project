"""
profile_collector.py – 從個人來源收集內容
  1. 個人部落格（RSS 優先，Fallback 到 BeautifulSoup 爬取）
  2. Google Drive（指定資料夾遞迴列出所有檔案，OAuth2）
"""

import os
import re
import requests
import feedparser
from bs4 import BeautifulSoup

import config

_HEADERS = {"User-Agent": "ProfileBuilder/1.0 (personal interest analyzer)"}


# ────────────────────────────────────────────────────────────
# 部落格文章抓取
# ────────────────────────────────────────────────────────────

def _try_rss(base_url: str) -> list[dict]:
    """嘗試常見 RSS 路徑，成功則回傳文章清單"""
    candidates = [
        f"{base_url.rstrip('/')}/feed",
        f"{base_url.rstrip('/')}/rss",
        f"{base_url.rstrip('/')}/feed.xml",
        f"{base_url.rstrip('/')}/atom.xml",
        f"{base_url.rstrip('/')}/rss.xml",
    ]
    for rss_url in candidates:
        try:
            parsed = feedparser.parse(rss_url, request_headers=_HEADERS)
            if parsed.entries:
                print(f"  ✅ RSS 找到：{rss_url}（{len(parsed.entries)} 篇）")
                articles = []
                for entry in parsed.entries[: config.BLOG_MAX_POSTS]:
                    title = (entry.get("title") or "").strip()
                    url = entry.get("link", "")
                    excerpt = " ".join(
                        (entry.get("summary") or entry.get("description") or "").split()
                    )[:500]
                    date = entry.get("published", entry.get("updated", ""))
                    if title:
                        articles.append({
                            "title":   title,
                            "url":     url,
                            "excerpt": excerpt,
                            "date":    date,
                            "source":  "blog",
                        })
                return articles
        except Exception:
            continue
    return []


def _scrape_blog(base_url: str) -> list[dict]:
    """
    Fallback：用 BeautifulSoup 爬取部落格首頁，
    找所有 <article> 或 <h2>/<h3> 內的連結作為文章標題。
    """
    try:
        resp = requests.get(base_url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        articles = []
        seen_urls: set[str] = set()

        # 優先找 <article> 標籤
        for article in soup.find_all("article")[: config.BLOG_MAX_POSTS]:
            title_tag = article.find(["h1", "h2", "h3", "h4"])
            link_tag = title_tag.find("a") if title_tag else article.find("a")
            if not title_tag or not link_tag:
                continue
            title = title_tag.get_text(strip=True)
            href = link_tag.get("href", "")
            if not href.startswith("http"):
                href = base_url.rstrip("/") + "/" + href.lstrip("/")
            excerpt_tag = article.find("p")
            excerpt = excerpt_tag.get_text(strip=True)[:500] if excerpt_tag else ""
            if href not in seen_urls and title:
                seen_urls.add(href)
                articles.append({
                    "title":   title,
                    "url":     href,
                    "excerpt": excerpt,
                    "date":    "",
                    "source":  "blog",
                })

        # 若 <article> 不夠，再找 <h2>/<h3> 內的連結
        if len(articles) < 5:
            for heading in soup.find_all(["h2", "h3"])[: config.BLOG_MAX_POSTS]:
                link = heading.find("a")
                if not link:
                    continue
                title = link.get_text(strip=True)
                href = link.get("href", "")
                if not href.startswith("http"):
                    href = base_url.rstrip("/") + "/" + href.lstrip("/")
                if href not in seen_urls and title:
                    seen_urls.add(href)
                    articles.append({
                        "title":   title,
                        "url":     href,
                        "excerpt": "",
                        "date":    "",
                        "source":  "blog",
                    })

        print(f"  ✅ 爬取部落格首頁：{len(articles)} 篇")
        return articles
    except Exception as e:
        print(f"  ⚠️ 部落格爬取失敗：{e}")
        return []


def fetch_blog_posts(base_url: str | None = None) -> list[dict]:
    """
    抓取部落格文章（RSS 優先，Fallback 爬取首頁）
    """
    url = base_url or config.PERSONAL_BLOG_URL
    print(f"  🌐 部落格：{url}")
    articles = _try_rss(url)
    if not articles:
        print("  ℹ️ 未找到 RSS，改為爬取首頁")
        articles = _scrape_blog(url)
    return articles


# ────────────────────────────────────────────────────────────
# Google Drive 抓取
# ────────────────────────────────────────────────────────────

def _get_drive_service():
    """建立並回傳 Google Drive API 服務物件（OAuth2）"""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
    creds_file = config.GOOGLE_CREDENTIALS_FILE
    token_file = config.GOOGLE_TOKEN_FILE

    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_file):
                raise FileNotFoundError(
                    f"找不到 {creds_file}，請先至 Google Cloud Console 下載 OAuth2 憑證。\n"
                    "步驟：Console → APIs & Services → Credentials → OAuth 2.0 Client IDs → 下載 JSON"
                )
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as f:
            f.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


# 支援的 MIME 類型對應顯示名稱與 export 格式
_EXPORTABLE_MIME = {
    "application/vnd.google-apps.document":     ("Google Docs",   "text/plain"),
    "application/vnd.google-apps.presentation": ("Google Slides", "text/plain"),
    "application/vnd.google-apps.spreadsheet":  ("Google Sheets", "text/csv"),
}
# 可直接下載的 MIME 類型（非 Google 原生格式）
_DOWNLOADABLE_MIME = {
    "application/pdf":  "PDF",
    "text/plain":       "Text",
    "text/markdown":    "Markdown",
}


def _export_file_content(service, file_id: str, mime_type: str) -> str:
    """
    匯出或下載檔案內容，回傳前 2000 字純文字。
    - Google 原生格式（Docs/Slides/Sheets）：用 export API
    - 其他（PDF/txt 等）：用 get_media 下載
    """
    try:
        if mime_type in _EXPORTABLE_MIME:
            _, export_mime = _EXPORTABLE_MIME[mime_type]
            content = service.files().export(
                fileId=file_id, mimeType=export_mime
            ).execute()
        else:
            import io
            from googleapiclient.http import MediaIoBaseDownload
            buf = io.BytesIO()
            downloader = MediaIoBaseDownload(
                buf, service.files().get_media(fileId=file_id)
            )
            done = False
            while not done:
                _, done = downloader.next_chunk()
            content = buf.getvalue()

        text = content.decode("utf-8", errors="ignore") if isinstance(content, bytes) else str(content)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        return text[:2000]
    except Exception:
        return ""


def _list_files_in_folder(service, folder_id: str, collected: list, depth: int = 0) -> None:
    """
    遞迴列出指定資料夾（含子資料夾）的所有檔案，
    結果 append 進 collected 清單。
    """
    if len(collected) >= config.GOOGLE_DRIVE_MAX_FILES:
        return

    supported_mimes = list(_EXPORTABLE_MIME.keys()) + list(_DOWNLOADABLE_MIME.keys())
    mime_filter = " or ".join(f"mimeType='{m}'" for m in supported_mimes)
    folder_mime = "application/vnd.google-apps.folder"

    page_token = None
    while True:
        if len(collected) >= config.GOOGLE_DRIVE_MAX_FILES:
            break
        try:
            resp = service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                pageSize=100,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
                pageToken=page_token,
            ).execute()
        except Exception as e:
            print(f"  ⚠️ 列出資料夾內容失敗（depth={depth}）：{e}")
            break

        for f in resp.get("files", []):
            if f["mimeType"] == folder_mime:
                # 遞迴進入子資料夾
                _list_files_in_folder(service, f["id"], collected, depth + 1)
            elif f["mimeType"] in _EXPORTABLE_MIME or f["mimeType"] in _DOWNLOADABLE_MIME:
                if len(collected) < config.GOOGLE_DRIVE_MAX_FILES:
                    collected.append(f)

        page_token = resp.get("nextPageToken")
        if not page_token:
            break


def fetch_google_drive_files() -> list[dict]:
    """
    遞迴列出指定 Google Drive 資料夾下的所有檔案
    （Docs、Slides、Sheets、PDF、txt 等），並 export 部分內容。
    資料夾 ID 從 config.GOOGLE_DRIVE_FOLDER_ID 讀取。
    """
    try:
        service = _get_drive_service()
    except FileNotFoundError as e:
        print(f"  ⚠️ Google Drive 跳過：{e}")
        return []
    except Exception as e:
        print(f"  ⚠️ Google Drive 授權失敗：{e}")
        return []

    folder_id = config.GOOGLE_DRIVE_FOLDER_ID
    print(f"  📂 資料夾 ID：{folder_id}（遞迴掃描中...）")

    raw_files: list[dict] = []
    _list_files_in_folder(service, folder_id, raw_files)

    # 統計各類型數量
    type_counts: dict[str, int] = {}
    for f in raw_files:
        label = (
            _EXPORTABLE_MIME.get(f["mimeType"], (None,))[0]
            or _DOWNLOADABLE_MIME.get(f["mimeType"], f["mimeType"])
        )
        type_counts[label] = type_counts.get(label, 0) + 1
    summary = "、".join(f"{k} {v} 個" for k, v in type_counts.items())
    print(f"  📁 Drive 共找到 {len(raw_files)} 個檔案（{summary}）")

    results = []
    for f in raw_files:
        ftype = (
            _EXPORTABLE_MIME.get(f["mimeType"], (None,))[0]
            or _DOWNLOADABLE_MIME.get(f["mimeType"], "其他")
        )
        content_snippet = _export_file_content(service, f["id"], f["mimeType"])
        results.append({
            "title":           f["name"],
            "content_snippet": content_snippet,
            "file_type":       ftype,
            "modified_date":   f.get("modifiedTime", ""),
            "source":          "google_drive",
        })

    return results


# ────────────────────────────────────────────────────────────
# 統一入口
# ────────────────────────────────────────────────────────────

def collect_all() -> dict:
    """
    收集所有個人來源資料，回傳：
    {
        "blog_posts":   [...],
        "drive_files":  [...],
    }
    """
    print("\n  📡 抓取部落格文章...")
    blog_posts = fetch_blog_posts()

    print("\n  📡 抓取 Google Drive 檔案...")
    drive_files = fetch_google_drive_files()

    return {
        "blog_posts":  blog_posts,
        "drive_files": drive_files,
    }
