import streamlit as st
from supabase import create_client, Client
import pandas as pd
import urllib.request
import csv
import io
import time
import random
import string
import re
import hashlib
from datetime import datetime, date

# 頁面標題與佈局
st.set_page_config(
    page_title="個人/共同分帳記事簿",
    page_icon="📒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== 5 種現代高奢配色主題 ====================
THEMES = {
    "🌿 青嵐鼠尾草": {
        "primary": "#2D6A4F",
        "primary_dark": "#1B4332",
        "gradient": "linear-gradient(135deg, #2D6A4F 0%, #40916C 100%)",
        "hero_bg": "linear-gradient(135deg, #1B4332 0%, #2D6A4F 100%)",
        "tag_bg": "#E8F5E9",
        "tag_border": "#A3D9A5",
        "tag_text": "#1B4332",
        "glow": "rgba(45, 106, 79, 0.22)",
        "badge": "#D8F3DC"
    },
    "🍂 赤曜暖陶": {
        "primary": "#C84B31",
        "primary_dark": "#8F2D18",
        "gradient": "linear-gradient(135deg, #C84B31 0%, #E26D5C 100%)",
        "hero_bg": "linear-gradient(135deg, #7A2412 0%, #C84B31 100%)",
        "tag_bg": "#FBEAE7",
        "tag_border": "#F2A699",
        "tag_text": "#671A0B",
        "glow": "rgba(200, 75, 49, 0.22)",
        "badge": "#FCD5CE"
    },
    "🌊 暮靄深海藍": {
        "primary": "#1E5F74",
        "primary_dark": "#133B49",
        "gradient": "linear-gradient(135deg, #1E5F74 0%, #2D82B7 100%)",
        "hero_bg": "linear-gradient(135deg, #0E2933 0%, #1E5F74 100%)",
        "tag_bg": "#E5F4F8",
        "tag_border": "#9FD1E1",
        "tag_text": "#0C2E38",
        "glow": "rgba(30, 95, 116, 0.22)",
        "badge": "#CCE8F0"
    },
    "🌸 暮光煙粉": {
        "primary": "#A24857",
        "primary_dark": "#6D2935",
        "gradient": "linear-gradient(135deg, #A24857 0%, #C76B7C 100%)",
        "hero_bg": "linear-gradient(135deg, #581C26 0%, #A24857 100%)",
        "tag_bg": "#FCECEF",
        "tag_border": "#EAA4B1",
        "tag_text": "#4F1620",
        "glow": "rgba(162, 72, 87, 0.22)",
        "badge": "#F8D4DC"
    },
    "🌑 黑曜玄武岩": {
        "primary": "#2B2D42",
        "primary_dark": "#181926",
        "gradient": "linear-gradient(135deg, #2B2D42 0%, #474A6B 100%)",
        "hero_bg": "linear-gradient(135deg, #141520 0%, #2B2D42 100%)",
        "tag_bg": "#EDEEF2",
        "tag_border": "#B5B8C7",
        "tag_text": "#161722",
        "glow": "rgba(43, 45, 66, 0.22)",
        "badge": "#DFE0E8"
    }
}

if "theme_name" not in st.session_state:
    st.session_state["theme_name"] = "🌿 青嵐鼠尾草"

current_theme = THEMES[st.session_state["theme_name"]]

# ==================== 行動端頂級美學 CSS 注入 ====================
st.markdown(f"""
<style>
/* 1. 核心字體與全景畫布 */
html, body, [class*="css"] {{
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "PingFang TC", "Noto Sans TC", sans-serif;
    color: #0F172A;
    background-color: #F8FAFC !important;
    -webkit-font-smoothing: antialiased;
}}

.block-container {{
    padding-top: 3.2rem !important;
    padding-bottom: 3.5rem !important;
    max-width: 760px !important;
    margin: 0 auto;
}}

@media (max-width: 768px) {{
    .block-container {{
        padding-top: 4.6rem !important;
        padding-left: 0.95rem !important;
        padding-right: 0.95rem !important;
        padding-bottom: 3.5rem !important;
    }}
}}

/* 2. 移除原生物理厚框線，升級為懸浮白島卡片 */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius: 20px !important;
    border: 1px solid rgba(226, 232, 240, 0.8) !important;
    background-color: #FFFFFF !important;
    padding: 1.25rem 1.15rem !important;
    box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.04), 0 1px 3px rgba(15, 23, 42, 0.02) !important;
    margin-bottom: 0.9rem !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
}}

/* 3. 仿 iOS 錢包的懸浮膠囊分頁籤 (Segmented Bar) */
div[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    background: #E2E8F0 !important;
    padding: 4px !important;
    border-radius: 16px !important;
    gap: 4px !important;
    border: none !important;
    margin-bottom: 1rem !important;
}}
div[data-testid="stTabs"] button[data-testid="stTab"] {{
    border-radius: 13px !important;
    border: none !important;
    padding: 10px 14px !important;
    font-size: 0.96rem !important;
    font-weight: 700 !important;
    color: #64748B !important;
    background: transparent !important;
    transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1) !important;
    flex: 1 1 0px !important;
    text-align: center !important;
}}
div[data-testid="stTabs"] button[data-testid="stTab"][aria-selected="true"] {{
    background-color: #FFFFFF !important;
    color: {current_theme['primary']} !important;
    box-shadow: 0 3px 12px rgba(15, 23, 42, 0.08) !important;
}}
div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{
    display: none !important;
}}

/* 4. 手機專屬 Hero 看板卡片 */
.hero-card {{
    background: {current_theme['hero_bg']};
    color: #FFFFFF;
    border-radius: 22px;
    padding: 1.4rem 1.3rem;
    box-shadow: 0 10px 30px -4px {current_theme['glow']};
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
}}
.hero-card::after {{
    content: "";
    position: absolute;
    bottom: -20px;
    right: -20px;
    width: 130px;
    height: 130px;
    background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0) 70%);
    border-radius: 50%;
}}
.hero-card .label {{
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.78);
    font-weight: 500;
    margin-bottom: 4px;
}}
.hero-card .amount {{
    font-size: clamp(2rem, 8vw, 2.6rem);
    font-weight: 800;
    letter-spacing: -0.03em;
    line-height: 1.1;
    margin-bottom: 14px;
}}
.hero-card .pill-group {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}}
.hero-card .pill {{
    background: rgba(255, 255, 255, 0.16);
    backdrop-filter: blur(8px);
    border-radius: 12px;
    padding: 6px 12px;
    font-size: 0.82rem;
    font-weight: 600;
}}

/* 5. 交易流水卡片 (Transaction Item Card) */
.tx-item {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 14px;
    background: #FFFFFF;
    border-radius: 16px;
    border: 1px solid #F1F5F9;
    margin-bottom: 8px;
    box-shadow: 0 1px 4px rgba(15, 23, 42, 0.02);
}}
.tx-left {{
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
    min-width: 0;
}}
.tx-avatar {{
    width: 42px;
    height: 42px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    background-color: {current_theme['badge']};
    flex-shrink: 0;
}}
.tx-info {{
    min-width: 0;
    flex: 1;
}}
.tx-title {{
    font-weight: 700;
    font-size: 0.98rem;
    color: #1E293B;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.tx-subtitle {{
    font-size: 0.78rem;
    color: #64748B;
    margin-top: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.tx-amount {{
    font-size: 1.12rem;
    font-weight: 800;
    letter-spacing: -0.01em;
    text-align: right;
    margin-left: 12px;
    flex-shrink: 0;
}}

/* 6. 手機大拇指專用立體大按鈕 */
html body button[data-testid*="primary"],
html body button[data-testid="baseButton-primary"],
html body button[kind="primary"],
html body .stButton > button[kind="primary"],
html body div[data-testid="stFormSubmitButton"] > button {{
    background: {current_theme['gradient']} !important;
    border: none !important;
    color: #FFFFFF !important;
    border-radius: 15px !important;
    font-weight: 700 !important;
    font-size: 1.02rem !important;
    min-height: 48px !important;
    box-shadow: 0 4px 14px {current_theme['glow']} !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}}
html body button[data-testid*="primary"]:active,
html body div[data-testid="stFormSubmitButton"] > button:active {{
    transform: scale(0.97) !important;
}}

html body button[data-testid*="secondary"],
html body button[data-testid="baseButton-secondary"] {{
    border-radius: 13px !important;
    border: 1px solid #E2E8F0 !important;
    background: #FFFFFF !important;
    color: #334155 !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    min-height: 42px !important;
}}

/* 7. 表單元件微調 */
input[type="text"], input[type="password"], input[type="number"] {{
    border-radius: 13px !important;
    border: 1.5px solid #E2E8F0 !important;
    min-height: 46px !important;
    font-size: 1rem !important;
    padding: 9px 14px !important;
    background-color: #FAFAFA !important;
}}
input:focus {{
    background-color: #FFFFFF !important;
    border-color: {current_theme['primary']} !important;
    box-shadow: 0 0 0 3px {current_theme['glow']} !important;
}}

/* 8. 柔色選人標籤 */
div[data-testid="stMultiSelect"] {{
    --primary-color: {current_theme['tag_bg']} !important;
}}
html body div[data-testid="stMultiSelect"] [data-baseweb="tag"],
html body div[data-testid="stMultiSelect"] span:has(svg) {{
    background-color: {current_theme['tag_bg']} !important;
    border: 1.5px solid {current_theme['tag_border']} !important;
    border-radius: 10px !important;
    padding: 4px 10px !important;
}}
html body div[data-testid="stMultiSelect"] [data-baseweb="tag"] span {{
    color: {current_theme['tag_text']} !important;
    font-weight: 800 !important;
}}
html body div[data-testid="stMultiSelect"] [data-baseweb="tag"] svg {{
    fill: {current_theme['tag_text']} !important;
}}
</style>
""", unsafe_allow_html=True)

# ==================== 初始化 Supabase 連線 ====================
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception:
    st.error("資料庫連線失敗，請檢查 Streamlit Secrets 設定！")
    st.stop()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def generate_code(prefix=""):
    letters = ''.join(random.choices(string.ascii_uppercase, k=4))
    digits = ''.join(random.choices(string.digits, k=3))
    return f"{prefix}{letters}{digits}"

def format_time(ts_str):
    if not ts_str:
        return ""
    try:
        dt = pd.to_datetime(ts_str)
        if dt.tzinfo is None:
            dt = dt.tz_localize("UTC")
        return dt.tz_convert("Asia/Taipei").strftime("%m/%d %H:%M")
    except Exception:
        return str(ts_str)[5:16].replace("T", " ")

def log_activity(code, action, detail):
    try:
        supabase.table("activity_logs").insert({
            "trip_code": code,
            "action_type": action,
            "details": detail
        }).execute()
    except Exception:
        pass

def is_personal_only(expense):
    split_list = [m.strip() for m in expense.get("split_members", "").split(",") if m.strip()]
    return len(split_list) == 1 and split_list[0] == expense.get("paid_by")

def get_current_base_url():
    try:
        if hasattr(st, "context") and hasattr(st.context, "url") and st.context.url:
            raw_url = str(st.context.url)
            return raw_url.split("?")[0].rstrip("/")
    except Exception:
        pass
    try:
        if hasattr(st, "context") and hasattr(st.context, "headers") and st.context.headers:
            h = st.context.headers
            host = h.get("host") or h.get("x-forwarded-host")
            proto = h.get("x-forwarded-proto", "https")
            if host:
                return f"{proto}://{host}"
    except Exception:
        pass
    return "https://travel-expense-33.streamlit.app"

# ==================== 資料庫操作函式 ====================
def get_user_by_email(email):
    try:
        res = supabase.table("app_users").select("*").eq("email", email.strip().lower()).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

def get_user_books(email):
    try:
        res = supabase.table("user_books").select("*").eq("user_email", email.strip().lower()).order("id", desc=True).execute()
        return res.data
    except Exception:
        return []

def bind_book_to_user(email, b_type, b_code, b_name):
    try:
        supabase.table("user_books").upsert({
            "user_email": email.strip().lower(),
            "book_type": b_type,
            "book_code": b_code,
            "book_name": b_name
        }, on_conflict="user_email,book_code").execute()
    except Exception:
        pass

def get_trip_info(code):
    try:
        res = supabase.table("trips").select("*").eq("trip_code", code).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

def get_members(code):
    try:
        res = supabase.table("members").select("name").eq("trip_code", code).execute()
        return [r["name"] for r in res.data]
    except Exception:
        return []

def get_expenses(code):
    try:
        res = supabase.table("expenses").select("*").eq("trip_code", code).order("id", desc=True).execute()
        return res.data
    except Exception:
        return []

def get_logs(code):
    try:
        res = supabase.table("activity_logs").select("*").eq("trip_code", code).order("id", desc=True).limit(40).execute()
        return res.data
    except Exception:
        return []

def get_personal_records(book_code, r_type=None):
    try:
        query = supabase.table("personal_records").select("*").eq("book_code", book_code)
        if r_type:
            query = query.eq("record_type", r_type)
        res = query.order("record_date", desc=True).order("id", desc=True).execute()
        return res.data
    except Exception:
        return []

def get_personal_categories(book_code, r_type):
    try:
        res = supabase.table("personal_categories").select("name").eq("book_code", book_code).eq("record_type", r_type).execute()
        return [r["name"] for r in res.data]
    except Exception:
        return []

# 類別圖示對應
CATEGORY_ICONS = {
    "食物": "🍔", "購物": "🛍️", "家用": "🏠", "交通": "🚗",
    "醫療": "💊", "娛樂": "🎮", "儲蓄": "💰", "保險": "🛡️",
    "其他": "📦", "薪水": "💼", "獎金": "🎁", "回饋": "💳", "股息": "📈"
}

def get_cat_icon(cat):
    return CATEGORY_ICONS.get(cat, "🔖")

DEFAULT_RATES = {
    "USD": {"name": "美金", "cash_sell": 32.50},
    "JPY": {"name": "日幣", "cash_sell": 0.2150},
    "THB": {"name": "泰銖", "cash_sell": 0.9800},
    "KRW": {"name": "韓元", "cash_sell": 0.0245},
    "CNY": {"name": "人民幣", "cash_sell": 4.5200}
}

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_bot_rates_lazy():
    rates = DEFAULT_RATES.copy()
    url = "https://rate.bot.com.tw/xrt/flcsv/0/day"
    target_currencies = {"USD": "美金", "JPY": "日幣", "THB": "泰銖", "KRW": "韓元", "CNY": "人民幣"}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=1.8) as response:
            content = response.read().decode("utf-8", errors="ignore")
            reader = csv.reader(io.StringIO(content))
            for row in reader:
                if not row or len(row) < 14:
                    continue
                code = row[0].strip()
                if code in target_currencies:
                    try:
                        val = float(row[12].strip())
                        if val > 0:
                            rates[code] = {"name": target_currencies[code], "cash_sell": val}
                    except Exception:
                        pass
    except Exception:
        pass
    return rates

# 狀態管理
if "auth_user" not in st.session_state:
    st.session_state["auth_user"] = None
if "current_book_type" not in st.session_state:
    st.session_state["current_book_type"] = None
if "current_code" not in st.session_state:
    st.session_state["current_code"] = None
if "confirm_del_p_active" not in st.session_state:
    st.session_state["confirm_del_p_active"] = False
if "confirm_del_group_active" not in st.session_state:
    st.session_state["confirm_del_group_active"] = False

# ==================== URL 快速免登入檢查 ====================
url_trip = st.query_params.get("trip", "").strip().upper()
url_book = st.query_params.get("book", "").strip().upper()

if url_trip and st.session_state["current_code"] != url_trip:
    t_check = get_trip_info(url_trip)
    if t_check:
        st.session_state["current_book_type"] = "group"
        st.session_state["current_code"] = url_trip
    else:
        st.toast("⚠️ 邀請連結無效或該行程已被刪除！")
        st.query_params.clear()

elif url_book and st.session_state["current_code"] != url_book and st.session_state["auth_user"]:
    b_check = get_trip_info(url_book)
    if b_check:
        st.session_state["current_book_type"] = "personal"
        st.session_state["current_code"] = url_book


# ==============================================================================
# 第一層：身分認證（現代原生感登入卡）
# ==============================================================================
if st.session_state["current_code"] is None and st.session_state["auth_user"] is None:
    st.markdown("""
    <div style='text-align: center; margin-top: 10px; margin-bottom: 24px;'>
        <div style='font-size: 40px; margin-bottom: 6px;'>📒</div>
        <h2 style='margin:0; font-weight:800; font-size:1.65rem; color:#0F172A;'>個人 / 共同分帳記事簿</h2>
        <p style='color:#64748B; font-size:0.92rem; margin-top:6px;'>點擊好友連結免登入直達；管理私帳請由此登入</p>
    </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        tab_login, tab_signup = st.tabs(["🔑 會員登入", "✨ 免費註冊"])

        with tab_login:
            with st.form("login_form"):
                l_email = st.text_input("電子信箱", placeholder="name@example.com").strip().lower()
                l_pwd = st.text_input("登入密碼", type="password", placeholder="請輸入密碼")
                
                st.write("")
                if st.form_submit_button("登入我的帳本 ➔", type="primary", use_container_width=True):
                    if not l_email or not l_pwd:
                        st.toast("❌ 請填寫完整 Email 與密碼！")
                    else:
                        user = get_user_by_email(l_email)
                        if not user:
                            st.toast("❌ 查無此 Email，請先註冊！")
                        elif user.get("password_hash") != hash_password(l_pwd):
                            st.toast("❌ 密碼錯誤！")
                        else:
                            st.session_state["auth_user"] = {"email": user["email"], "name": user["name"]}
                            st.toast(f"🎉 歡迎回來，{user['name']}！")
                            st.rerun()

        with tab_signup:
            with st.form("signup_form"):
                s_name = st.text_input("您的姓名", placeholder="例如：小明")
                s_email = st.text_input("電子信箱", placeholder="name@example.com").strip().lower()
                s_pwd = st.text_input("設定密碼", type="password", placeholder="4 位以上密碼")
                
                st.write("")
                if st.form_submit_button("建立新帳號 ➔", type="primary", use_container_width=True):
                    clean_name = re.sub(r'[,，]', '', s_name.strip())
                    clean_email = s_email.strip()
                    if not clean_name:
                        st.toast("❌ 請填寫姓名！")
                    elif not clean_email or "@" not in clean_email:
                        st.toast("❌ 請填寫有效 Email！")
                    elif len(s_pwd) < 4:
                        st.toast("❌ 密碼長度需至少 4 位！")
                    elif get_user_by_email(clean_email):
                        st.toast("⚠️ 此 Email 已被註冊，請直接登入！")
                    else:
                        supabase.table("app_users").insert({
                            "email": clean_email,
                            "password_hash": hash_password(s_pwd),
                            "name": clean_name
                        }).execute()
                        st.session_state["auth_user"] = {"email": clean_email, "name": clean_name}
                        st.toast(f"🎉 註冊成功，{clean_name}！")
                        st.rerun()

    # 快捷邀請碼
    with st.container(border=True):
        st.markdown("**⚡ 手邊有 7 碼邀請碼？（免登入直接進入）**")
        c_quick1, c_quick2 = st.columns([2.4, 1.3])
        with c_quick1:
            quick_code_in = st.text_input("邀請代碼", placeholder="例如：TRIP888", label_visibility="collapsed").strip().upper()
        with c_quick2:
            if st.button("秒進 ➔", type="secondary", use_container_width=True):
                if quick_code_in and get_trip_info(quick_code_in):
                    st.query_params["trip"] = quick_code_in
                    st.rerun()
                else:
                    st.toast("❌ 查無此代碼！")

    st.stop()


# ==============================================================================
# 第二層：主揪 / 會員「個人帳本與行程大廳」（卡片清單）
# ==============================================================================
if st.session_state["current_code"] is None and st.session_state["auth_user"] is not None:
    current_user = st.session_state["auth_user"]
    user_email = current_user["email"]
    user_name = current_user["name"]

    col_u1, col_u2 = st.columns([3.6, 1.4])
    with col_u1:
        st.markdown(f"### 👋 哈囉，{user_name}")
        st.caption(f"`{user_email}` ｜ 雲端已連線")
    with col_u2:
        st.write("")
        if st.button("🚪 登出", use_container_width=True):
            st.session_state["auth_user"] = None
            st.session_state["current_book_type"] = None
            st.session_state["current_code"] = None
            st.session_state["confirm_del_p_active"] = False
            st.session_state["confirm_del_group_active"] = False
            st.query_params.clear()
            st.rerun()

    user_saved_books = get_user_books(user_email)
    personal_books = [b for b in user_saved_books if b["book_type"] == "personal"]
    group_books = [b for b in user_saved_books if b["book_type"] == "group"]

    # 區塊 1：個人帳本
    with st.container(border=True):
        st.markdown("#### 👤 個人獨立帳本")
        st.caption("專屬於您的日常私密收支，無他人分攤。")
        
        if personal_books:
            for b in personal_books:
                with st.container(border=True):
                    c_bname, c_bact = st.columns([3, 1.3])
                    with c_bname:
                        st.markdown(f"**📖 {b['book_name']}**")
                        st.caption(f"代碼：`{b['book_code']}`")
                    with c_bact:
                        if st.button("開啟 ➔", key=f"open_p_{b['book_code']}", use_container_width=True, type="primary"):
                            st.session_state["current_book_type"] = "personal"
                            st.session_state["current_code"] = b["book_code"]
                            st.query_params["book"] = b["book_code"]
                            st.rerun()
        else:
            st.info("尚無個人帳本，點擊下方立即建立！")

        c_p_op1, c_p_op2 = st.columns(2)
        with c_p_op1:
            with st.expander("➕ 建立新帳本"):
                with st.form("create_new_personal_book"):
                    nb_name = st.text_input("帳本名稱", placeholder="例如：2026日常開銷")
                    if st.form_submit_button("建立", type="primary", use_container_width=True):
                        c_nb_name = nb_name.strip()
                        if not c_nb_name:
                            st.toast("❌ 請填寫名稱！")
                        else:
                            nb_code = generate_code(prefix="P")
                            supabase.table("trips").insert({
                                "trip_code": nb_code,
                                "trip_name": c_nb_name,
                                "admin_pin": "0000"
                            }).execute()
                            bind_book_to_user(user_email, "personal", nb_code, c_nb_name)
                            st.session_state["current_book_type"] = "personal"
                            st.session_state["current_code"] = nb_code
                            st.query_params["book"] = nb_code
                            st.rerun()

        with c_p_op2:
            if personal_books:
                with st.expander("🛠️ 管理帳本"):
                    target_p_mng = st.selectbox(
                        "選取帳本：",
                        options=[b["book_code"] for b in personal_books],
                        format_func=lambda x: [b["book_name"] for b in personal_books if b["book_code"]==x][0],
                        key="lobby_p_mng_sel"
                    )
                    curr_b_obj = [b for b in personal_books if b["book_code"]==target_p_mng][0]
                    with st.form(f"rename_p_form_{target_p_mng}"):
                        new_bname_input = st.text_input("修改名稱", value=curr_b_obj["book_name"])
                        if st.form_submit_button("儲存新名稱", type="primary", use_container_width=True):
                            if new_bname_input.strip():
                                supabase.table("trips").update({"trip_name": new_bname_input.strip()}).eq("trip_code", target_p_mng).execute()
                                supabase.table("user_books").update({"book_name": new_bname_input.strip()}).eq("book_code", target_p_mng).execute()
                                st.toast("✏️ 已更新！")
                                st.rerun()

                    if st.button("🗑️ 刪除此帳本", key=f"lobby_del_p_{target_p_mng}", type="secondary", use_container_width=True):
                        supabase.table("personal_records").delete().eq("book_code", target_p_mng).execute()
                        supabase.table("personal_categories").delete().eq("book_code", target_p_mng).execute()
                        supabase.table("trips").delete().eq("trip_code", target_p_mng).execute()
                        supabase.table("user_books").delete().eq("book_code", target_p_mng).execute()
                        st.toast("🗑️ 已刪除！")
                        st.rerun()

    # 區塊 2：共同分帳行程
    with st.container(border=True):
        st.markdown("#### 👥 共同旅遊分帳")
        st.caption("同行好友記帳、結算還款與分享直達網址。")
        
        if group_books:
            for b in group_books:
                with st.container(border=True):
                    c_gname, c_gact = st.columns([3, 1.3])
                    with c_gname:
                        st.markdown(f"**✈️ {b['book_name']}**")
                        st.caption(f"邀請碼：`{b['book_code']}`")
                    with c_gact:
                        if st.button("進入 ➔", key=f"open_g_{b['book_code']}", use_container_width=True, type="primary"):
                            st.session_state["current_book_type"] = "group"
                            st.session_state["current_code"] = b["book_code"]
                            st.query_params["trip"] = b["book_code"]
                            st.rerun()
        else:
            st.info("尚無共同分帳，可發起新旅程！")

        c_g_op1, c_g_op2 = st.columns(2)
        with c_g_op1:
            with st.expander("➕ 發起新旅程"):
                with st.form("create_new_group_trip"):
                    ng_name = st.text_input("旅程名稱", placeholder="例如：沖繩五天四夜")
                    ng_pin = st.text_input("管理密碼 (4~6位)", type="password", max_chars=6)
                    if st.form_submit_button("建立旅程", type="primary", use_container_width=True):
                        c_ng_name = ng_name.strip()
                        if not c_ng_name:
                            st.toast("❌ 請填寫名稱！")
                        elif not re.fullmatch(r"^\d{4,6}$", ng_pin.strip()):
                            st.toast("❌ 密碼需為 4 ~ 6 位純數字！")
                        else:
                            ng_code = generate_code()
                            supabase.table("trips").insert({
                                "trip_code": ng_code,
                                "trip_name": c_ng_name,
                                "admin_pin": ng_pin.strip()
                            }).execute()
                            supabase.table("members").insert({
                                "trip_code": ng_code,
                                "name": user_name
                            }).execute()
                            bind_book_to_user(user_email, "group", ng_code, c_ng_name)
                            log_activity(ng_code, "建立行程", f"{user_name} 建立了「{c_ng_name}」")
                            st.session_state["current_book_type"] = "group"
                            st.session_state["current_code"] = ng_code
                            st.query_params["trip"] = ng_code
                            st.rerun()

        with c_g_op2:
            if group_books:
                with st.expander("🛠️ 管理共同行程"):
                    target_g_mng = st.selectbox(
                        "選取行程：",
                        options=[b["book_code"] for b in group_books],
                        format_func=lambda x: [b["book_name"] for b in group_books if b["book_code"]==x][0],
                        key="lobby_g_mng_sel"
                    )
                    curr_g_obj = [b for b in group_books if b["book_code"]==target_g_mng][0]
                    g_info = get_trip_info(target_g_mng)
                    g_admin_pin = g_info.get("admin_pin", "") if g_info else ""

                    with st.form(f"rename_g_form_{target_g_mng}"):
                        new_gname_input = st.text_input("修改名稱", value=curr_g_obj["book_name"])
                        if st.form_submit_button("儲存新名稱", type="primary", use_container_width=True):
                            if new_gname_input.strip():
                                supabase.table("trips").update({"trip_name": new_gname_input.strip()}).eq("trip_code", target_g_mng).execute()
                                supabase.table("user_books").update({"book_name": new_gname_input.strip()}).eq("book_code", target_g_mng).execute()
                                st.toast("✏️ 已更新！")
                                st.rerun()

                    del_g_pin_input = st.text_input("管理員密碼", type="password", key=f"del_g_pin_{target_g_mng}", placeholder="4~6位密碼")
                    if st.button("🗑️ 永久刪除此行程", key=f"lobby_del_g_{target_g_mng}", type="secondary", use_container_width=True):
                        if not del_g_pin_input.strip():
                            st.toast("❌ 請輸入密碼！")
                        elif g_admin_pin and del_g_pin_input.strip() != g_admin_pin:
                            st.toast("❌ 密碼錯誤！")
                        else:
                            supabase.table("expenses").delete().eq("trip_code", target_g_mng).execute()
                            supabase.table("members").delete().eq("trip_code", target_g_mng).execute()
                            supabase.table("activity_logs").delete().eq("trip_code", target_g_mng).execute()
                            supabase.table("trips").delete().eq("trip_code", target_g_mng).execute()
                            supabase.table("user_books").delete().eq("book_code", target_g_mng).execute()
                            st.toast("🗑️ 已銷毀行程！")
                            st.rerun()

    st.stop()


# ==============================================================================
# 第三層 A：個人獨立記帳主畫面 (Personal Book)
# ==============================================================================
if st.session_state["current_book_type"] == "personal":
    book_code = st.session_state["current_code"]
    book_info = get_trip_info(book_code)
    book_name = book_info["trip_name"] if book_info else "個人記帳本"
    
    current_u = st.session_state.get("auth_user")
    u_display = current_u["name"] if current_u else "個人"
    if current_u:
        bind_book_to_user(current_u["email"], "personal", book_code, book_name)

    p_records = get_personal_records(book_code)
    total_income = sum(int(round(float(r["amount"]))) for r in p_records if r["record_type"] == "income")
    total_expense = sum(int(round(float(r["amount"]))) for r in p_records if r["record_type"] == "expense")
    net_surplus = total_income - total_expense

    # 頂部行動專屬導航
    col_pb1, col_pb2 = st.columns([3.8, 1.4])
    with col_pb1:
        st.markdown(f"### 📖 {book_name}")
        st.caption(f"👤 `{u_display}` ｜ 代碼：`{book_code}`")
    with col_pb2:
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            if st.button("🔄", help="重新載入", use_container_width=True):
                st.toast("🔄 已同步最新資料")
                st.rerun()
        with c_p2:
            if st.button("⬅️", help="返回大廳", use_container_width=True):
                st.session_state["current_code"] = None
                st.session_state["current_book_type"] = None
                st.session_state["confirm_del_p_active"] = False
                st.query_params.clear()
                st.rerun()

    # 現代 Hero 看板卡片
    surplus_color = "#22C55E" if net_surplus >= 0 else "#F43F5E"
    surplus_sign = "+" if net_surplus > 0 else ""
    st.markdown(f"""
    <div class="hero-card">
        <div class="label">本帳本累積淨盈餘</div>
        <div class="amount" style="color:{surplus_color};">{surplus_sign}${net_surplus:,}</div>
        <div class="pill-group">
            <div class="pill">💰 總收入 ${total_income:,}</div>
            <div class="pill">💸 總支出 ${total_expense:,}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 側邊欄設定
    with st.sidebar:
        st.markdown("### ⚙️ 個人帳本設定")
        with st.container(border=True):
            st.markdown("**🎨 介面主題色**")
            def on_theme_change():
                st.session_state["theme_name"] = st.session_state["theme_selector"]
            st.selectbox("選擇主題色調：", options=list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state["theme_name"]), key="theme_selector", on_change=on_theme_change, label_visibility="collapsed")

        with st.container(border=True):
            st.markdown("**📖 帳本設定與管理**")
            with st.expander("✏️ 修改帳本名稱"):
                with st.form("rename_active_p_form"):
                    new_active_pname = st.text_input("帳本名稱", value=book_name)
                    if st.form_submit_button("儲存新名稱", type="primary", use_container_width=True):
                        if new_active_pname.strip():
                            supabase.table("trips").update({"trip_name": new_active_pname.strip()}).eq("trip_code", book_code).execute()
                            if current_u:
                                supabase.table("user_books").update({"book_name": new_active_pname.strip()}).eq("book_code", book_code).execute()
                            st.toast("✏️ 已更新！")
                            st.rerun()

            with st.expander("🗑️ 刪除此帳本"):
                if st.session_state["confirm_del_p_active"]:
                    st.error("⚠️ 確定要永久銷毀此個人帳本嗎？")
                    c_pdel_y, c_pdel_n = st.columns(2)
                    with c_pdel_y:
                        if st.button("🚨 確認刪除", type="primary", use_container_width=True):
                            supabase.table("personal_records").delete().eq("book_code", book_code).execute()
                            supabase.table("personal_categories").delete().eq("book_code", book_code).execute()
                            supabase.table("trips").delete().eq("trip_code", book_code).execute()
                            if current_u:
                                supabase.table("user_books").delete().eq("book_code", book_code).execute()
                            st.session_state["current_code"] = None
                            st.session_state["current_book_type"] = None
                            st.session_state["confirm_del_p_active"] = False
                            st.query_params.clear()
                            st.rerun()
                    with c_pdel_n:
                        if st.button("取消", use_container_width=True):
                            st.session_state["confirm_del_p_active"] = False
                            st.rerun()
                else:
                    if st.button("前往確認刪除", type="secondary", use_container_width=True):
                        st.session_state["confirm_del_p_active"] = True
                        st.rerun()

    default_expense_cats = ["食物", "購物", "家用", "交通", "醫療", "娛樂", "儲蓄", "保險", "其他"]
    default_income_cats = ["薪水", "獎金", "回饋", "股息"]
    custom_exp_cats = get_personal_categories(book_code, "expense")
    custom_inc_cats = get_personal_categories(book_code, "income")
    all_exp_cats = default_expense_cats + [c for c in custom_exp_cats if c not in default_expense_cats]
    all_inc_cats = default_income_cats + [c for c in custom_inc_cats if c not in default_income_cats]

    p_tab1, p_tab2 = st.tabs(["💸 支出記帳", "💰 收入記帳"])

    # 支出記帳
    with p_tab1:
        with st.container(border=True):
            st.markdown("##### ➕ 新增支出消費")
            with st.form("add_personal_expense_form", clear_on_submit=True):
                exp_item = st.text_input("消費名稱", placeholder="例如：午餐便當、家樂福、高鐵票")
                exp_amt = st.number_input("金額 (NTD)", min_value=1, step=50, format="%d")

                r2_c1, r2_c2 = st.columns(2)
                with r2_c1:
                    exp_cat = st.selectbox("支出類別", options=all_exp_cats)
                with r2_c2:
                    exp_date = st.date_input("消費日期", value=date.today())

                st.write("")
                if st.form_submit_button("記下一筆支出 ➔", type="primary", use_container_width=True):
                    if not exp_item.strip():
                        st.toast("❌ 請填寫消費名稱！")
                    else:
                        supabase.table("personal_records").insert({
                            "book_code": book_code,
                            "record_type": "expense",
                            "category": exp_cat,
                            "item": exp_item.strip(),
                            "amount": int(round(exp_amt)),
                            "record_date": str(exp_date)
                        }).execute()
                        st.toast(f"💸 支出已記錄：{exp_item.strip()}！")
                        st.rerun()

        with st.expander("🏷️ 管理支出類別"):
            c_add_ec1, c_add_ec2 = st.columns([2.5, 1.2])
            with c_add_ec1:
                new_ecat = st.text_input("新增自訂類別", placeholder="例如：寵物、健身", key="new_ecat_input")
            with c_add_ec2:
                st.write("")
                if st.button("➕ 新增", key="btn_add_ecat", use_container_width=True):
                    clean_ec = new_ecat.strip()
                    if clean_ec and clean_ec not in all_exp_cats:
                        supabase.table("personal_categories").insert({"book_code": book_code, "record_type": "expense", "name": clean_ec}).execute()
                        st.toast(f"✅ 已新增：{clean_ec}")
                        st.rerun()

            if custom_exp_cats:
                del_ecat_target = st.selectbox("選擇要刪除的類別：", options=custom_exp_cats, key="sel_del_ecat")
                if st.button("🗑️ 刪除類別", key="btn_del_ecat"):
                    supabase.table("personal_categories").delete().eq("book_code", book_code).eq("record_type", "expense").eq("name", del_ecat_target).execute()
                    st.toast(f"🗑️ 已刪除：{del_ecat_target}")
                    st.rerun()

        # 支出交易流水卡片流
        exp_list = [r for r in p_records if r["record_type"] == "expense"]
        with st.container(border=True):
            st.markdown("##### 📋 支出明細清單")
            if exp_list:
                for r in exp_list[:30]:
                    icon = get_cat_icon(r['category'])
                    amt_str = f"-${int(round(float(r['amount']))):,}"
                    st.markdown(f"""
                    <div class="tx-item">
                        <div class="tx-left">
                            <div class="tx-avatar">{icon}</div>
                            <div class="tx-info">
                                <div class="tx-title">{r['item']}</div>
                                <div class="tx-subtitle">{r['category']} · {r.get('record_date')}</div>
                            </div>
                        </div>
                        <div class="tx-amount" style="color:#EF4444;">{amt_str}</div>
                    </div>
                    """, unsafe_allow_html=True)

                with st.expander("🛠️ 管理或修改特定支出"):
                    target_pe_id = st.selectbox(
                        "選擇項目：",
                        options=[r["id"] for r in exp_list],
                        format_func=lambda x: f"{[r['record_date'] for r in exp_list if r['id']==x][0]} - {[r['item'] for r in exp_list if r['id']==x][0]} (${int(round(float([r['amount'] for r in exp_list if r['id']==x][0]))):,})"
                    )
                    curr_pe = [r for r in exp_list if r["id"] == target_pe_id][0]
                    with st.form("edit_pe_form"):
                        pe_n_item = st.text_input("名稱", value=curr_pe["item"])
                        pe_n_amt = st.number_input("金額", min_value=1, value=int(round(float(curr_pe["amount"]))), step=50, format="%d")
                        pe_n_cat = st.selectbox("類別", options=all_exp_cats, index=all_exp_cats.index(curr_pe["category"]) if curr_pe["category"] in all_exp_cats else 0)
                        pe_n_date = st.date_input("日期", value=pd.to_datetime(curr_pe["record_date"]).date())

                        if st.form_submit_button("💾 儲存修改", type="primary", use_container_width=True):
                            if pe_n_item.strip():
                                supabase.table("personal_records").update({"item": pe_n_item.strip(), "amount": int(round(pe_n_amt)), "category": pe_n_cat, "record_date": str(pe_n_date)}).eq("id", target_pe_id).execute()
                                st.toast("✏️ 已更新！")
                                st.rerun()

                    if st.button("🗑️ 刪除此筆支出", type="secondary", use_container_width=True, key="del_pe_btn"):
                        supabase.table("personal_records").delete().eq("id", target_pe_id).execute()
                        st.toast("🗑️ 已成功刪除！")
                        st.rerun()
            else:
                st.caption("尚無任何支出記錄。")

    # 收入記帳
    with p_tab2:
        with st.container(border=True):
            st.markdown("##### ➕ 新增收入項目")
            with st.form("add_personal_income_form", clear_on_submit=True):
                inc_item = st.text_input("收入名稱", placeholder="例如：薪水、獎金、發票中獎")
                inc_amt = st.number_input("金額 (NTD)", min_value=1, step=100, format="%d")

                r2_c1, r2_c2 = st.columns(2)
                with r2_c1:
                    inc_cat = st.selectbox("收入類別", options=all_inc_cats)
                with r2_c2:
                    inc_date = st.date_input("入帳日期", value=date.today())

                st.write("")
                if st.form_submit_button("記下一筆收入 ➔", type="primary", use_container_width=True):
                    if not inc_item.strip():
                        st.toast("❌ 請填寫收入名稱！")
                    else:
                        supabase.table("personal_records").insert({
                            "book_code": book_code,
                            "record_type": "income",
                            "category": inc_cat,
                            "item": inc_item.strip(),
                            "amount": int(round(inc_amt)),
                            "record_date": str(inc_date)
                        }).execute()
                        st.toast(f"💰 收入已記錄：{inc_item.strip()}！")
                        st.rerun()

        with st.expander("🏷️ 管理收入類別"):
            c_add_ic1, c_add_ic2 = st.columns([2.5, 1.2])
            with c_add_ic1:
                new_icat = st.text_input("新增自訂類別", placeholder="例如：兼職、租金", key="new_icat_input")
            with c_add_ic2:
                st.write("")
                if st.button("➕ 新增", key="btn_add_icat", use_container_width=True):
                    clean_ic = new_icat.strip()
                    if clean_ic and clean_ic not in all_inc_cats:
                        supabase.table("personal_categories").insert({"book_code": book_code, "record_type": "income", "name": clean_ic}).execute()
                        st.toast(f"✅ 已新增：{clean_ic}")
                        st.rerun()

            if custom_inc_cats:
                del_icat_target = st.selectbox("選擇要刪除的類別：", options=custom_inc_cats, key="sel_del_icat")
                if st.button("🗑️ 刪除類別", key="btn_del_icat"):
                    supabase.table("personal_categories").delete().eq("book_code", book_code).eq("record_type", "income").eq("name", del_icat_target).execute()
                    st.toast(f"🗑️ 已刪除：{del_icat_target}")
                    st.rerun()

        inc_list = [r for r in p_records if r["record_type"] == "income"]
        with st.container(border=True):
            st.markdown("##### 📋 收入明細清單")
            if inc_list:
                for r in inc_list[:30]:
                    icon = get_cat_icon(r['category'])
                    amt_str = f"+${int(round(float(r['amount']))):,}"
                    st.markdown(f"""
                    <div class="tx-item">
                        <div class="tx-left">
                            <div class="tx-avatar">{icon}</div>
                            <div class="tx-info">
                                <div class="tx-title">{r['item']}</div>
                                <div class="tx-subtitle">{r['category']} · {r.get('record_date')}</div>
                            </div>
                        </div>
                        <div class="tx-amount" style="color:#10B981;">{amt_str}</div>
                    </div>
                    """, unsafe_allow_html=True)

                with st.expander("🛠️ 管理或修改特定收入"):
                    target_pi_id = st.selectbox(
                        "選擇項目：",
                        options=[r["id"] for r in inc_list],
                        format_func=lambda x: f"{[r['record_date'] for r in inc_list if r['id']==x][0]} - {[r['item'] for r in inc_list if r['id']==x][0]} (${int(round(float([r['amount'] for r in inc_list if r['id']==x][0]))):,})"
                    )
                    curr_pi = [r for r in inc_list if r["id"] == target_pi_id][0]
                    with st.form("edit_pi_form"):
                        pi_n_item = st.text_input("名稱", value=curr_pi["item"])
                        pi_n_amt = st.number_input("金額", min_value=1, value=int(round(float(curr_pi["amount"]))), step=100, format="%d")
                        pi_n_cat = st.selectbox("類別", options=all_inc_cats, index=all_inc_cats.index(curr_pi["category"]) if curr_pi["category"] in all_inc_cats else 0)
                        pi_n_date = st.date_input("日期", value=pd.to_datetime(curr_pi["record_date"]).date())

                        if st.form_submit_button("💾 儲存修改", type="primary", use_container_width=True):
                            if pi_n_item.strip():
                                supabase.table("personal_records").update({"item": pi_n_item.strip(), "amount": int(round(pi_n_amt)), "category": pi_n_cat, "record_date": str(pi_n_date)}).eq("id", target_pi_id).execute()
                                st.toast("✏️ 已更新！")
                                st.rerun()

                    if st.button("🗑️ 刪除此筆收入", type="secondary", use_container_width=True, key="del_pi_btn"):
                        supabase.table("personal_records").delete().eq("id", target_pi_id).execute()
                        st.toast("🗑️ 已成功刪除！")
                        st.rerun()
            else:
                st.caption("尚無任何收入記錄。")

    st.stop()


# ==============================================================================
# 第三層 B：共同旅遊分帳主畫面 (全卡片流極簡美學)
# ==============================================================================
trip_code = st.session_state["current_code"]
trip_info = get_trip_info(trip_code)
trip_name = trip_info["trip_name"] if trip_info else trip_code
admin_pin = trip_info["admin_pin"] if trip_info else ""

current_logged_user = st.session_state.get("auth_user")
if current_logged_user:
    bind_book_to_user(current_logged_user["email"], "group", trip_code, trip_name)

members = get_members(trip_code)

if current_logged_user:
    active_operator_name = current_logged_user["name"]
    if active_operator_name not in members:
        supabase.table("members").insert({"trip_code": trip_code, "name": active_operator_name}).execute()
        members = get_members(trip_code)
else:
    if "guest_operator_name" not in st.session_state or not st.session_state["guest_operator_name"]:
        st.session_state["guest_operator_name"] = members[0] if members else ""
    active_operator_name = st.session_state["guest_operator_name"]

expenses = get_expenses(trip_code)
logs = get_logs(trip_code)
total_trip_expense = sum(int(round(float(e["amount"]))) for e in expenses)
id_to_exp = {e["id"]: e for e in expenses}

# 頂部導航
col_h1, col_h2 = st.columns([3.6, 1.4])
with col_h1:
    st.markdown(f"### ✈️ {trip_name}")
    st.caption(f"🔑 `{trip_code}` ｜ 👤 `{active_operator_name if active_operator_name else '訪客'}`")
with col_h2:
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        if st.button("🔄", help="手動更新", use_container_width=True):
            st.toast("🔄 已同步最新資料")
            st.rerun()
    with col_btn2:
        with st.popover("🔗", help="分享行程邀請連結", use_container_width=True):
            st.markdown(f"**📤 分享【{trip_name}】**")
            st.caption("好友點擊即可**免登入直接進入**：")
            
            base_url = get_current_base_url()
            full_share_url = f"{base_url}/?trip={trip_code}"

            st.code(full_share_url, language="text")

            st.components.v1.html(f"""
            <div style="display:flex; flex-direction:column; gap:6px; font-family:-apple-system,BlinkMacSystemFont,sans-serif;">
                <input type="text" id="shareUrlBox" value="{full_share_url}" readonly style="
                    width: 100%; padding: 8px 10px; border: 1.5px solid #cbd5e1; border-radius: 8px; font-size: 13px; background-color: #f8fafc; color: #334155; box-sizing: border-box;
                " />
                <button id="copyBtn" style="
                    background: {current_theme['gradient']}; color: white; border: none; padding: 10px 12px; border-radius: 8px; font-size: 13px; font-weight: 700; cursor: pointer; width: 100%;
                ">📋 一鍵複製專屬直達網址</button>
                <div id="copyNotice" style="font-size:12px; color:#16a34a; font-weight:700; display:none; text-align:center; margin-top:2px;">
                    ✅ 專屬網址已複製至剪貼簿！
                </div>
            </div>
            <script>
                try {{
                    if (window.parent && window.parent.location && window.parent.location.origin) {{
                        const origin = window.parent.location.origin;
                        const pathname = window.parent.location.pathname;
                        document.getElementById('shareUrlBox').value = origin + pathname + '?trip={trip_code}';
                    }}
                }} catch(e) {{}}

                document.getElementById('copyBtn').addEventListener('click', function() {{
                    const inputEl = document.getElementById('shareUrlBox');
                    inputEl.select();
                    inputEl.setSelectionRange(0, 99999);
                    function showSuccess() {{
                        const btn = document.getElementById('copyBtn');
                        const notice = document.getElementById('copyNotice');
                        btn.innerText = '✅ 複製成功！';
                        notice.style.display = 'block';
                        setTimeout(() => {{
                            btn.innerText = '📋 點擊一鍵複製直達網址';
                            notice.style.display = 'none';
                        }}, 2500);
                    }}
                    if (navigator.clipboard && window.isSecureContext) {{
                        navigator.clipboard.writeText(inputEl.value).then(showSuccess).catch(function() {{
                            try {{ document.execCommand('copy'); showSuccess(); }} catch(err) {{ alert('複製失敗，請手動選取網址！'); }}
                        }});
                    }} else {{
                        try {{ document.execCommand('copy'); showSuccess(); }} catch(err) {{ alert('複製失敗，請手動選取網址！'); }}
                    }}
                }});
            </script>
            """, height=115)

            st.caption(f"🔑 7 碼邀請代碼：`{trip_code}`")

    with col_btn3:
        if st.button("⬅️", help="返回大廳", use_container_width=True):
            st.session_state["current_code"] = None
            st.session_state["current_book_type"] = None
            st.session_state["confirm_del_group_active"] = False
            st.query_params.clear()
            st.rerun()

# 現代 Hero 看板卡片
avg_expense = int(round(total_trip_expense / len(members))) if members else 0
st.markdown(f"""
<div class="hero-card">
    <div class="label">全團累積總花費</div>
    <div class="amount">${total_trip_expense:,}</div>
    <div class="pill-group">
        <div class="pill">👥 成員共 {len(members)} 位</div>
        <div class="pill">💳 每人平均約 ${avg_expense:,}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 側邊欄
with st.sidebar:
    st.markdown("### ⚙️ 工具與成員管理")
    
    with st.container(border=True):
        st.markdown("**👤 目前操作者（我是誰）**")
        if members:
            cur_idx = members.index(active_operator_name) if active_operator_name in members else 0
            sel_op = st.selectbox("選取我的姓名：", options=members, index=cur_idx, help="記帳時會自動將代墊人預設為您")
            if sel_op != active_operator_name:
                st.session_state["guest_operator_name"] = sel_op
                st.rerun()
        else:
            st.caption("尚未有成員，請在下方加入。")

    with st.container(border=True):
        st.markdown("**🎨 介面主題色**")
        def on_theme_change():
            st.session_state["theme_name"] = st.session_state["theme_selector"]
        st.selectbox("選擇主題色調：", options=list(THEMES.keys()), index=list(THEMES.keys()), key="theme_selector", on_change=on_theme_change, label_visibility="collapsed")

    with st.container(border=True):
        st.markdown("**👥 行程成員管理**")
        with st.form("add_member_form", clear_on_submit=True):
            new_member = st.text_input("新增姓名", placeholder="例如：阿山", label_visibility="collapsed")
            if st.form_submit_button("➕ 加入成員", type="primary", use_container_width=True):
                clean_name = re.sub(r'[,，]', '', new_member.strip())
                if clean_name and clean_name not in members:
                    supabase.table("members").insert({"trip_code": trip_code, "name": clean_name}).execute()
                    log_activity(trip_code, "新增成員", f"新增成員「{clean_name}」")
                    st.session_state["guest_operator_name"] = clean_name
                    st.toast(f"✅ 已加入成員：{clean_name}")
                    st.rerun()
                elif clean_name in members:
                    st.toast(f"⚠️ 成員「{clean_name}」已存在！")
                else:
                    st.toast("❌ 姓名不能空白！")

        if members:
            st.caption("成員名單：" + "、".join(members))
            with st.expander("刪除成員"):
                member_to_delete = st.selectbox("選擇欲刪除成員", options=members)
                del_pin_input = st.text_input("管理密碼", type="password", key="input_del_pin", placeholder="輸入管理密碼")
                if st.button("確認刪除", type="secondary", use_container_width=True):
                    is_payer = any(e.get("paid_by") == member_to_delete for e in expenses)
                    is_in_split = any(member_to_delete in [m.strip() for m in e.get("split_members", "").split(",")] for e in expenses)
                    if not del_pin_input.strip():
                        st.toast("❌ 請輸入密碼！")
                    elif not admin_pin or del_pin_input.strip() != admin_pin:
                        st.toast("❌ 密碼錯誤！")
                    elif is_payer or is_in_split:
                        st.error(f"⚠️ 無法刪除「{member_to_delete}」！已有代墊或分攤紀錄。")
                    else:
                        supabase.table("members").delete().eq("trip_code", trip_code).eq("name", member_to_delete).execute()
                        log_activity(trip_code, "刪除成員", f"管理員刪除成員「{member_to_delete}」")
                        st.toast(f"🗑️ 已刪除：{member_to_delete}")
                        st.rerun()

    with st.container(border=True):
        st.markdown("**💱 台灣銀行牌告匯率**")
        with st.expander("展開匯率計算機", expanded=False):
            bot_rates = fetch_bot_rates_lazy()
            fx_amt = st.number_input("金額", min_value=0, value=1000, step=100, format="%d", key="fx_amt_sb")
            c_fx1, c_fx2 = st.columns(2)
            with c_fx1:
                fx_from = st.selectbox("從", options=["TWD", "JPY", "USD", "THB", "KRW", "CNY"], index=0, key="fx_from_sb")
            with c_fx2:
                fx_to = st.selectbox("換為", options=["TWD", "JPY", "USD", "THB", "KRW", "CNY"], index=1, key="fx_to_sb")

            rates_to_twd = {"TWD": 1.0}
            for c, info in bot_rates.items():
                rates_to_twd[c] = info["cash_sell"]
            res_amt = (fx_amt * rates_to_twd.get(fx_from, 1.0)) / rates_to_twd.get(fx_to, 1.0)
            st.info(f"≈ **${int(round(res_amt)):,}** 台幣" if fx_to == "TWD" else f"≈ **{res_amt:,.2f}** {fx_to}")

    with st.container(border=True):
        st.markdown("**📜 異動紀錄**")
        with st.expander(f"查看日誌 ({len(logs)} 筆)"):
            if logs:
                st.dataframe(pd.DataFrame([{"時間": format_time(l.get("created_at")), "動作": l.get("action_type", ""), "內容": l.get("details", "")} for l in logs]), use_container_width=True, hide_index=True)
            else:
                st.caption("尚無紀錄。")

    with st.container(border=True):
        st.markdown("**⚠️ 危機管理：刪除行程**")
        with st.expander("🚨 永久刪除此共同行程"):
            if st.session_state["confirm_del_group_active"]:
                st.error(f"⚠️ **再次警告**：將永久銷毀【{trip_name}】的所有消費、成員名單、操作日誌，無法復原！確定要刪除？")
                c_gdel_y, c_gdel_n = st.columns(2)
                with c_gdel_y:
                    if st.button("🚨 確認刪除全部", type="primary", use_container_width=True, key="act_g_del_conf"):
                        supabase.table("expenses").delete().eq("trip_code", trip_code).execute()
                        supabase.table("members").delete().eq("trip_code", trip_code).execute()
                        supabase.table("activity_logs").delete().eq("trip_code", trip_code).execute()
                        supabase.table("trips").delete().eq("trip_code", trip_code).execute()
                        supabase.table("user_books").delete().eq("book_code", trip_code).execute()
                        st.session_state["current_code"] = None
                        st.session_state["current_book_type"] = None
                        st.session_state["confirm_del_group_active"] = False
                        st.query_params.clear()
                        st.toast("🗑️ 共同行程帳本已徹底銷毀！")
                        st.rerun()
                with c_gdel_n:
                    if st.button("取消", use_container_width=True, key="act_g_del_canc"):
                        st.session_state["confirm_del_group_active"] = False
                        st.rerun()
            else:
                st.caption("銷毀後無法還原，需驗證管理員密碼。")
                pin_try = st.text_input("輸入管理員密碼", type="password", key="active_del_g_pin", placeholder="4~6位密碼")
                if st.button("驗證密碼並前往刪除", type="secondary", use_container_width=True):
                    if not pin_try.strip():
                        st.toast("❌ 請輸入管理員密碼！")
                    elif admin_pin and pin_try.strip() != admin_pin:
                        st.toast("❌ 管理員密碼錯誤，拒絕操作！")
                    else:
                        st.session_state["confirm_del_group_active"] = True
                        st.rerun()

# 共同分帳三膠囊分頁
tab1, tab2, tab3 = st.tabs(["📝 新增消費", "👤 個人帳務", "📊 結算還款"])

# Tab 1: 新增消費與分攤明細
with tab1:
    with st.container(border=True):
        st.markdown("##### ➕ 新增消費")
        if len(members) < 1:
            st.warning("請先在左側選單新增成員！")
        else:
            with st.form("add_expense_form", clear_on_submit=True):
                item_name = st.text_input("項目名稱", placeholder="例如：晚餐、計程車、門票")
                amount = st.number_input("金額 (NTD / 結算幣別)", min_value=1, step=50, format="%d")

                c_payer, c_split = st.columns(2)
                with c_payer:
                    payer_def_idx = members.index(active_operator_name) if active_operator_name in members else 0
                    paid_by = st.selectbox("誰先代墊全額？", options=members, index=payer_def_idx)
                with c_split:
                    split_with = st.multiselect("這筆由誰分攤？", options=members, default=members)

                st.write("")
                if st.form_submit_button("記下一筆消費 ➔", type="primary", use_container_width=True):
                    if not item_name.strip():
                        st.toast("❌ 請填寫消費項目！")
                    elif not split_with:
                        st.toast("❌ 分攤對象不能為空！")
                    else:
                        supabase.table("expenses").insert({
                            "trip_code": trip_code,
                            "item": item_name.strip(),
                            "amount": int(round(amount)),
                            "paid_by": paid_by,
                            "split_members": ",".join(split_with)
                        }).execute()
                        log_activity(trip_code, "新增記帳", f"「{item_name.strip()}」${int(round(amount)):,} 元 (由 {paid_by} 代墊)")
                        st.toast(f"💾 記帳成功：{item_name.strip()}！")
                        st.rerun()

    shared_expenses = [e for e in expenses if not is_personal_only(e)]
    sorted_shared = sorted(shared_expenses, key=lambda x: x["id"])
    shared_id_to_seq = {e["id"]: idx + 1 for idx, e in enumerate(sorted_shared)}

    with st.container(border=True):
        st.markdown("##### 📋 團體分攤明細清單")
        if shared_expenses:
            for e in shared_expenses[:30]:
                amt_str = f"${int(round(float(e['amount']))):,}"
                st.markdown(f"""
                <div class="tx-item">
                    <div class="tx-left">
                        <div class="tx-avatar">✈️</div>
                        <div class="tx-info">
                            <div class="tx-title">#{shared_id_to_seq[e['id']]} {e['item']}</div>
                            <div class="tx-subtitle">由 <b>{e['paid_by']}</b> 代墊 · {format_time(e.get('created_at'))}</div>
                        </div>
                    </div>
                    <div class="tx-amount" style="color:{current_theme['primary']};">{amt_str}</div>
                </div>
                """, unsafe_allow_html=True)

            with st.expander("🛠️ 管理或修改特定帳目"):
                target_id = st.selectbox(
                    "選擇項目：",
                    options=[e["id"] for e in shared_expenses],
                    format_func=lambda x: f"#{shared_id_to_seq[x]} {id_to_exp.get(x, {}).get('item', '')} (${int(round(float(id_to_exp.get(x, {}).get('amount', 0)))):,})"
                )
                curr_exp = id_to_exp.get(target_id, {})
                curr_split = [m.strip() for m in curr_exp.get("split_members", "").split(",") if m.strip() in members]

                with st.form("unified_edit_form"):
                    e_name = st.text_input("項目名稱", value=curr_exp.get("item", ""))
                    e_amt = st.number_input("金額", min_value=1, value=int(round(float(curr_exp.get("amount", 1)))), step=50, format="%d")
                    p_idx = members.index(curr_exp.get("paid_by")) if curr_exp.get("paid_by") in members else 0
                    e_paid = st.selectbox("代墊人", options=members, index=p_idx)
                    e_split = st.multiselect("分攤名單", options=members, default=curr_split)

                    if st.form_submit_button("💾 儲存修改", type="primary", use_container_width=True):
                        if e_name.strip() and e_split:
                            supabase.table("expenses").update({
                                "item": e_name.strip(),
                                "amount": int(round(e_amt)),
                                "paid_by": e_paid,
                                "split_members": ",".join(e_split)
                            }).eq("id", target_id).execute()
                            log_activity(trip_code, "修改記帳", f"修改 #{shared_id_to_seq[target_id]} 為「{e_name.strip()}」${int(round(e_amt)):,}")
                            st.toast("✏️ 已更新！")
                            st.rerun()

                if st.button("🗑️ 刪除這筆帳目", type="secondary", use_container_width=True, key="del_mng_btn"):
                    seq_num = shared_id_to_seq[target_id]
                    d_name = curr_exp.get('item')
                    supabase.table("expenses").delete().eq("id", target_id).execute()
                    log_activity(trip_code, "刪除記帳", f"刪除 #{seq_num}「{d_name}」")
                    st.toast("🗑️ 已成功刪除！")
                    st.rerun()
        else:
            st.caption("尚無分攤明細紀錄。")

# Tab 2: 個人帳務
with tab2:
    if not members:
        st.info("請先新增成員！")
    else:
        with st.container(border=True):
            col_u_sel, _ = st.columns([1.5, 2])
            with col_u_sel:
                default_sel_idx = members.index(active_operator_name) if active_operator_name in members else 0
                selected_user = st.selectbox("切換查看成員：", options=members, index=default_sel_idx)

            total_paid_by_user = 0
            total_consumed_by_user = 0
            group_list = []
            personal_list = []

            for e in expenses:
                amt = int(round(float(e["amount"])))
                split_list = [m.strip() for m in e["split_members"].split(",") if m.strip()]
                share = int(round(amt / len(split_list))) if split_list else 0

                if e["paid_by"] == selected_user:
                    total_paid_by_user += amt

                if selected_user in split_list:
                    total_consumed_by_user += share

                if is_personal_only(e):
                    if e["paid_by"] == selected_user:
                        personal_list.append({
                            "raw_id": e["id"],
                            "時間": format_time(e.get("created_at")),
                            "項目": e["item"],
                            "自費金額": f"${amt:,}"
                        })
                else:
                    if selected_user in split_list or e["paid_by"] == selected_user:
                        group_list.append({
                            "#": shared_id_to_seq.get(e["id"], "-"),
                            "時間": format_time(e.get("created_at")),
                            "項目": e["item"],
                            "總額": f"${amt:,}",
                            "人數": f"{len(split_list)}人",
                            "我的份額": f"${share:,}" if selected_user in split_list else "$0",
                            "代墊人": e["paid_by"]
                        })

            net_balance = total_paid_by_user - total_consumed_by_user

            # 簡潔小看板
            c_p1, c_p2, c_p3 = st.columns(3)
            with c_p1:
                st.metric("代墊支出", f"${total_paid_by_user:,}")
            with c_p2:
                st.metric("個人消費", f"${total_consumed_by_user:,}")
            with c_p3:
                if net_balance > 0:
                    st.metric("應收回", f"+${net_balance:,}")
                elif net_balance < 0:
                    st.metric("應補繳", f"-${abs(net_balance):,}")
                else:
                    st.metric("帳目平衡", "$0")

        with st.container(border=True):
            st.markdown(f"##### 🛍️ 自費清單 ({selected_user})")
            if personal_list:
                sorted_p = sorted(personal_list, key=lambda x: x["raw_id"])
                p_id_seq = {p["raw_id"]: idx + 1 for idx, p in enumerate(sorted_p)}
                for p in personal_list:
                    p["#"] = p_id_seq[p["raw_id"]]

                for p in personal_list:
                    st.markdown(f"""
                    <div class="tx-item">
                        <div class="tx-left">
                            <div class="tx-avatar">🛍️</div>
                            <div class="tx-info">
                                <div class="tx-title">#{p['#']} {p['項目']}</div>
                                <div class="tx-subtitle">個人自費 · {p['時間']}</div>
                            </div>
                        </div>
                        <div class="tx-amount" style="color:#EF4444;">{p['自費金額']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                with st.expander("🛠️ 管理自費項目"):
                    p_sel_id = st.selectbox(
                        "選擇自費項目：",
                        options=[p["raw_id"] for p in personal_list],
                        format_func=lambda x: f"#{p_id_seq[x]} {id_to_exp.get(x, {}).get('item', '')} (${int(round(float(id_to_exp.get(x, {}).get('amount', 0)))):,})"
                    )
                    curr_p = id_to_exp.get(p_sel_id, {})
                    with st.form("edit_p_form"):
                        pn_item = st.text_input("名稱", value=curr_p.get("item", ""))
                        pn_amt = st.number_input("金額", min_value=1, value=int(round(float(curr_p.get("amount", 1)))), step=50, format="%d")
                        if st.form_submit_button("💾 儲存修改", type="primary", use_container_width=True):
                            if pn_item.strip():
                                supabase.table("expenses").update({"item": pn_item.strip(), "amount": int(round(pn_amt))}).eq("id", p_sel_id).execute()
                                log_activity(trip_code, "修改自費", f"{selected_user} 修改自費為「{pn_item.strip()}」${int(round(pn_amt)):,} 元")
                                st.toast("✏️ 已更新！")
                                st.rerun()

                    if st.button("🗑️ 刪除此自費項目", type="secondary", use_container_width=True, key="del_p_mng_btn"):
                        supabase.table("expenses").delete().eq("id", p_sel_id).execute()
                        log_activity(trip_code, "刪除自費", f"{selected_user} 刪除自費「{curr_p.get('item')}」")
                        st.toast("🗑️ 已成功刪除！")
                        st.rerun()
            else:
                st.caption(f"目前尚無 {selected_user} 的個人自費項目。")

        with st.container(border=True):
            st.markdown(f"##### 👥 分攤清單 ({selected_user})")
            if group_list:
                for g in group_list[:30]:
                    st.markdown(f"""
                    <div class="tx-item">
                        <div class="tx-left">
                            <div class="tx-avatar">👥</div>
                            <div class="tx-info">
                                <div class="tx-title">#{g['#']} {g['項目']}</div>
                                <div class="tx-subtitle">由 <b>{g['代墊人']}</b> 代墊 · 共{g['人數']}分攤</div>
                            </div>
                        </div>
                        <div class="tx-amount" style="color:{current_theme['primary']};">{g['我的份額']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("尚無相關分攤明細。")

# Tab 3: 結算還款
with tab3:
    if not expenses or not members:
        st.info("尚無足夠資料進行結算！")
    else:
        balances = {m: 0 for m in members}
        for e in expenses:
            amt = int(round(float(e["amount"])))
            split_list = [m.strip() for m in e["split_members"].split(",") if m.strip()]
            share = int(round(amt / len(split_list))) if split_list else 0
            
            if e["paid_by"] in balances:
                balances[e["paid_by"]] += amt
            for sm in split_list:
                if sm in balances:
                    balances[sm] -= share

        with st.container(border=True):
            st.markdown("##### 📋 每人結算淨額")
            for k, v in balances.items():
                if v > 0:
                    status_badge = f"<span style='color:#10B981; font-weight:800; font-size:1.1rem;'>應收回 +${v:,}</span>"
                elif v < 0:
                    status_badge = f"<span style='color:#EF4444; font-weight:800; font-size:1.1rem;'>應支付 -${abs(v):,}</span>"
                else:
                    status_badge = f"<span style='color:#64748B; font-weight:700;'>已結清 $0</span>"

                st.markdown(f"""
                <div class="tx-item">
                    <div class="tx-left">
                        <div class="tx-avatar">👤</div>
                        <div class="tx-info">
                            <div class="tx-title">{k}</div>
                        </div>
                    </div>
                    <div>{status_badge}</div>
                </div>
                """, unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("##### 💡 最簡轉帳還款指南")
            debtors = []
            creditors = []
            for m, b in balances.items():
                if b < 0:
                    debtors.append([m, -b])
                elif b > 0:
                    creditors.append([m, b])

            settlements = []
            line_messages = []
            i, j = 0, 0
            while i < len(debtors) and j < len(creditors):
                deb_name, deb_amt = debtors[i]
                cred_name, cred_amt = creditors[j]
                trans_amt = min(deb_amt, cred_amt)
                
                if trans_amt >= 1:
                    settlements.append(f"👉 **{deb_name}** 轉帳給 **{cred_name}**：`{trans_amt:,}` 元")
                    line_messages.append(f"• {deb_name} ➔ {cred_name}：${trans_amt:,} 元")
                
                debtors[i][1] -= trans_amt
                creditors[j][1] -= trans_amt
                
                if debtors[i][1] == 0:
                    i += 1
                if creditors[j][1] == 0:
                    j += 1

            if settlements:
                for s in settlements:
                    st.info(s)
                
                st.divider()
                st.markdown("**📋 LINE 催款懶人包** (點擊右上角複製)")
                share_text = f"✈️【{trip_name}】費用結算清單\n全團總累積花費：${total_trip_expense:,} 元\n" + "-"*20 + "\n"
                share_text += "\n".join(line_messages)
                share_text += "\n" + "-"*20 + "\n大家確認無誤後即可轉帳結清囉！"
                st.code(share_text, language="text")
            else:
                st.success("🎉 目前帳目完全平衡，大家互不相欠！")

# 共同分帳背景自動同步
time.sleep(30)
st.rerun()
