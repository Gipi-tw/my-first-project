import os
from dotenv import load_dotenv

load_dotenv()

# ── 使用者興趣設定 ──────────────────────────────────────────
TOPICS = [
    "AI 應用與 LLM 技術發展",
    "商業策略與企業經營管理",
    "軟體研發流程與產品管理",
    "職涯發展與個人學習成長",
    "業務銷售與 B2B 商業模式",
    "組織管理與人才培育",
]

# ── RSS Feeds ────────────────────────────────────────────────
RSS_FEEDS = [
    # AI / ML
    {"url": "https://www.reddit.com/r/MachineLearning/.rss",    "category": "AI/ML"},
    {"url": "https://www.reddit.com/r/LocalLLaMA/.rss",         "category": "AI/ML"},
    # Software Dev
    {"url": "https://hnrss.org/frontpage",                      "category": "Tech/Dev"},
    {"url": "https://dev.to/feed",                              "category": "Software Dev"},
    {"url": "https://www.reddit.com/r/programming/.rss",        "category": "Software Dev"},
    # Tech News
    {"url": "https://techcrunch.com/feed/",                     "category": "Tech News"},
    {"url": "https://www.theverge.com/rss/index.xml",           "category": "Tech News"},
    # Product / Business
    {"url": "https://www.producthunt.com/feed",                 "category": "Product"},

    # ── 中文科技 ──────────────────────────────────────────────
    {"url": "https://36kr.com/feed",                            "category": "中文科技"},   # 36氪
    {"url": "https://www.woshipm.com/feed",                     "category": "中文科技"},   # 人人都是產品經理
    {"url": "https://rsshub.app/zhihu/hotlist",                 "category": "中文科技"},   # 知乎熱榜
    {"url": "https://www.huxiu.com/rss/0.xml",                  "category": "中文科技"},   # 虎嗅網
    {"url": "https://inside.com.tw/feed",                       "category": "中文科技"},   # Inside
    {"url": "https://buzzorange.com/techorange/feed/",          "category": "中文科技"},   # TechOrange 科技橘報
    {"url": "https://sspai.com/feed",                           "category": "中文科技"},   # 少數派

    # ── AI 中文資訊 ───────────────────────────────────────────
    {"url": "https://www.jiqizhixin.com/rss",                   "category": "AI/ML"},      # 機器之心
    {"url": "https://rsshub.app/wechat/xinzhiyuan",             "category": "AI/ML"},      # 新智元（透過 RSSHub）
    {"url": "https://www.geekpark.net/rss",                     "category": "中文科技"},   # 極客公園

    # ── Tech News ─────────────────────────────────────────────
    {"url": "https://feeds.bloomberg.com/technology/news.rss",  "category": "Tech News"},  # Bloomberg Technology
    {"url": "https://gizmodo.com/rss",                          "category": "Tech News"},  # Gizmodo
    {"url": "https://www.infoq.com/feed/",                      "category": "Tech News"},  # InfoQ
    {"url": "https://www.ithome.com.tw/rss",                    "category": "Tech News"},  # iThome（台灣）
    {"url": "https://rss.slashdot.org/Slashdot/slashdotMain",   "category": "Tech News"},  # Slashdot
    {"url": "https://venturebeat.com/feed/",                    "category": "Tech News"},  # VentureBeat
    {"url": "https://www.wired.com/feed/rss",                   "category": "Tech News"},  # Wired

    # ── Work / Business ───────────────────────────────────────
    {"url": "https://www.fastcompany.com/latest/rss",           "category": "Work"},       # Fast Company
    {"url": "https://feeds.hbr.org/harvardbusiness",            "category": "Work"},       # HBR.org
    {"url": "https://lifehacker.com/rss",                       "category": "Work"},       # Lifehacker
]

# Web search queries（每週最新內容）
SEARCH_QUERIES = [
    "AI LLM breakthrough latest 2026",
    "software engineering developer tools 2026",
    "tech startup product launch 2026",
    "machine learning research paper 2026",
]

# ── API 金鑰 ────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# ── Email 設定 ───────────────────────────────────────────────
EMAIL_SENDER    = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD  = os.getenv("EMAIL_PASSWORD")   # Gmail App Password
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")
SMTP_SERVER     = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT       = int(os.getenv("SMTP_PORT", "587"))

# ── Agent 參數 ───────────────────────────────────────────────
MAX_ARTICLES_PER_FEED   = 10   # 每個 Feed 最多抓幾篇
MAX_ARTICLES_TO_SCORE   = 60   # 送給 Claude 評分的上限
TOP_ARTICLES_COUNT      = 15   # 一般文章最終選出篇數（減少以保留空間給追蹤動態）
TOP_ENTITY_ARTICLES     = 10   # 追蹤人物/企業動態最多納入篇數
MIN_SCORE               = 6.0  # 低於此分數的文章直接排除

# ── Profile Builder 設定 ─────────────────────────────────────
PERSONAL_BLOG_URL       = os.getenv("PERSONAL_BLOG_URL", "https://gipi.tw")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
GOOGLE_TOKEN_FILE       = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
GOOGLE_DRIVE_FOLDER_ID  = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "1wlYnXZrXipOQc5AcQGWtZnSMNXavEfC-")
GOOGLE_DRIVE_MAX_FILES  = 500   # 最多抓取的 Drive 檔案數（含子資料夾遞迴）
BLOG_MAX_POSTS          = 50    # 最多抓取的部落格文章數
