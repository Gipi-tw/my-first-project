"""
watch_list.py – 追蹤的特定人物與企業清單
可依需求修改 PEOPLE / COMPANIES 清單。
"""

# ── 追蹤人物 ──────────────────────────────────────────────────
PEOPLE = [
    {
        "name":         "Sam Altman",
        "name_zh":      "山姆·奧特曼",
        "role":         "OpenAI CEO",
        "search_query": '"Sam Altman" OpenAI news',
    },
    {
        "name":         "Jensen Huang",
        "name_zh":      "黃仁勳",
        "role":         "NVIDIA CEO",
        "search_query": '"Jensen Huang" OR "黃仁勳" NVIDIA',
    },
    {
        "name":         "Dario Amodei",
        "name_zh":      "達里奧·阿莫迪",
        "role":         "Anthropic CEO",
        "search_query": '"Dario Amodei" OR "Anthropic CEO"',
    },
    {
        "name":         "Andrew Ng",
        "name_zh":      "吳恩達",
        "role":         "DeepLearning.AI founder",
        "search_query": '"Andrew Ng" OR "吳恩達" AI',
    },
]

# ── 追蹤企業 ──────────────────────────────────────────────────
COMPANIES = [
    {
        "name":         "OpenAI",
        "name_zh":      "OpenAI",
        "search_query": "OpenAI news announcement product",
    },
    {
        "name":         "Anthropic",
        "name_zh":      "Anthropic",
        "search_query": "Anthropic Claude AI news",
    },
    {
        "name":         "Google DeepMind",
        "name_zh":      "Google AI",
        "search_query": "Google DeepMind Gemini AI news",
    },
    {
        "name":         "Microsoft",
        "name_zh":      "微軟",
        "search_query": "Microsoft AI Copilot Azure news",
    },
    {
        "name":         "NVIDIA",
        "name_zh":      "英偉達",
        "search_query": "NVIDIA GPU AI chip Blackwell news",
    },
    {
        "name":         "Salesforce",
        "name_zh":      "Salesforce",
        "search_query": "Salesforce Einstein AI CRM news",
    },
    {
        "name":         "HubSpot",
        "name_zh":      "HubSpot",
        "search_query": "HubSpot B2B marketing CRM news",
    },
    {
        "name":         "台積電",
        "name_zh":      "台積電",
        "search_query": "TSMC 台積電 semiconductor news 2026",
    },
    {
        "name":         "鴻海",
        "name_zh":      "鴻海",
        "search_query": "Foxconn 鴻海 EV AI news 2026",
    },
    {
        "name":         "聯發科",
        "name_zh":      "聯發科",
        "search_query": "MediaTek 聯發科 AI chip news 2026",
    },
]

# ── 動態偵測提示（供 Claude 評分 prompt 使用）─────────────────
DYNAMIC_ENTITY_HINT = (
    "AI 公司執行長/高管（如 CEO、CTO、VP Product）、"
    "全球五百大企業執行長（Fortune 500 CEO）、"
    "知名高科技產業 Podcast 主持人或 YouTuber"
)

# ── 快速存取：人物/企業名稱清單（供 prompt 插入）────────────
PEOPLE_NAMES    = [p["name"] for p in PEOPLE]
COMPANY_NAMES   = [c["name"] for c in COMPANIES]
