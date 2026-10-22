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
    initial_sidebar_state="auto"
)

# ==================== 5 種極簡莫蘭迪風格配色 ====================
THEMES = {
    "🌿 鼠尾草綠": {
        "primary": "#385A48",
        "hover": "#2B4537",
        "tag_bg": "#E1EDE6",
        "tag_border": "#9EC3AE",
        "tag_text": "#1A3525",
        "accent": "#4A7A60",
        "light_glow": "rgba(56, 90, 72, 0.12)"
    },
    "🍂 暖陶土橘": {
        "primary": "#BA5738",
        "hover": "#984227",
        "tag_bg": "#FAECE6",
        "tag_border": "#E5A894",
        "tag_text": "#612210",
        "accent": "#D46E4E",
        "light_glow": "rgba(186, 87, 56, 0.12)"
    },
    "🌊 暮靄靛藍": {
        "primary": "#274E6F",
        "hover": "#1A3750",
        "tag_bg": "#E3EDF6",
        "tag_border": "#96BCDE",
        "tag_text": "#0F2840",
        "accent": "#3B6D99",
        "light_glow": "rgba(39, 78, 111, 0.12)"
    },
    "🌸 煙燻胭粉": {
        "primary": "#9E475B",
        "hover": "#7D3243",
        "tag_bg": "#FAE8ED",
        "tag_border": "#DC9CB0",
        "tag_text": "#501725",
        "accent": "#BA5F76",
        "light_glow": "rgba(158, 71, 91, 0.12)"
    },
    "🌑 簡約冷灰": {
        "primary": "#2B333E",
        "hover": "#1B2027",
        "tag_bg": "#EAECEF",
        "tag_border": "#A8B1BD",
        "tag_text": "#111418",
        "accent": "#455060",
        "light_glow": "rgba(43, 51, 62, 0.12)"
    }
}

if "theme_name" not in st.session_state:
    st.session_state["theme_name"] = "🌿 鼠尾草綠"

current_theme = THEMES[st.session_state["theme_name"]]

# ==================== 頂級現代 UI / UX CSS 樣式系統 ====================
st.markdown(f"""
<style>
/* 1. 字體與基礎排版 */
html, body, [class*="css"] {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans TC", "PingFang TC", sans-serif;
    color: #1e293b;
    letter-spacing: -0.012em;
}}

/* 電腦端頂部安全留白 */
.block-container {{
    padding-top: 3.5rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 1040px !important;
}}

/* 2. 手機端安全邊距 (防遮擋) */
@media (max-width: 768px) {{
    .block-container {{
        padding-top: 4.8rem !important;
        padding-left: 0.85rem !important;
        padding-right: 0.85rem !important;
        padding-bottom: 2rem !important;
    }}
    div[data-testid="stMetricValue"] {{
        font-size: clamp(1.2rem, 4.5vw, 1.55rem) !important;
    }}
}}

/* 3. 膠囊分頁滑塊導航 (iOS Segmented Tabs) */
div[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    background-color: #f1f5f9 !important;
    padding: 4px !important;
    border-radius: 12px !important;
    gap: 4px !important;
    border: 1px solid #e2e8f0 !important;
}}
div[data-testid="stTabs"] button[data-testid="stTab"] {{
    border-radius: 9px !important;
    border: none !important;
    padding: 8px 18px !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    color: #64748b !important;
    background: transparent !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}}
div[data-testid="stTabs"] button[data-testid="stTab"]:hover {{
    color: {current_theme['primary']} !important;
}}
div[data-testid="stTabs"] button[data-testid="stTab"][aria-selected="true"] {{
    background-color: #ffffff !important;
    color: {current_theme['primary']} !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.07), 0 1px 1px rgba(0, 0, 0, 0.04) !important;
}}
div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{
    display: none !important;
}}

/* 4. 現代微景深卡片 */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius: 14px !important;
    border: 1px solid #eef2f6 !important;
    background-color: #ffffff !important;
    padding: 1.1rem !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02) !important;
    transition: all 0.2s ease !important;
}}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
    border-color: {current_theme['tag_border']} !important;
    box-shadow: 0 6px 18px {current_theme['light_glow']} !important;
}}

/* 5. 數據指標卡 */
div[data-testid="stMetric"] {{
    background: #ffffff !important;
    border: 1px solid #eef2f6 !important;
    border-radius: 13px !important;
    padding: 12px 16px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
    position: relative !important;
    overflow: hidden !important;
}}
div[data-testid="stMetric"]::before {{
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3.5px;
    background-color: {current_theme['primary']};
}}
div[data-testid="stMetricLabel"] p {{
    font-size: 0.82rem !important;
    color: #64748b !important;
    font-weight: 600 !important;
}}
div[data-testid="stMetricValue"] {{
    font-size: clamp(1.35rem, 2.3vw, 1.7rem) !important;
    font-weight: 700 !important;
    color: #0f172a !important;
}}

/* 6. 按鈕系統 */
html body button[data-testid*="primary"],
html body button[data-testid="baseButton-primary"],
html body button[kind="primary"],
html body .stButton > button[kind="primary"],
html body div[data-testid="stFormSubmitButton"] > button {{
    background-color: {current_theme['primary']} !important;
    border: none !important;
    color: #ffffff !important;
    border-radius: 9px !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    min-height: 40px !important;
    box-shadow: 0 2px 5px {current_theme['light_glow']} !important;
    transition: all 0.18s ease !important;
}}
html body button[data-testid*="primary"]:hover,
html body div[data-testid="stFormSubmitButton"] > button:hover {{
    background-color: {current_theme['hover']} !important;
    box-shadow: 0 4px 10px {current_theme['light_glow']} !important;
    transform: translateY(-0.5px);
}}
html body button[data-testid*="primary"]:active,
html body div[data-testid="stFormSubmitButton"] > button:active {{
    transform: scale(0.99);
}}

html body button[data-testid*="secondary"],
html body button[data-testid="baseButton-secondary"] {{
    border-radius: 9px !important;
    border: 1px solid #cbd5e1 !important;
    background: #ffffff !important;
    color: #475569 !important;
    font-size: 0.9rem !important;
    min-height: 38px !important;
}}
html body button[data-testid*="secondary"]:hover {{
    border-color: #94a3b8 !important;
    background: #f8fafc !important;
}}

/* 7. 分攤角色標籤高辨識度 */
div[data-testid="stMultiSelect"] {{
    --primary-color: {current_theme['tag_bg']} !important;
}}
html body div[data-testid="stMultiSelect"] [data-baseweb="tag"],
html body div[data-testid="stMultiSelect"] span:has(svg) {{
    background-color: {current_theme['tag_bg']} !important;
    border: 1.5px solid {current_theme['tag_border']} !important;
    border-radius: 7px !important;
    padding: 3px 9px !important;
}}
html body div[data-testid="stMultiSelect"] [data-baseweb="tag"] span,
html body div[data-testid="stMultiSelect"] span:has(svg) span {{
    color: {current_theme['tag_text']} !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
}}
html body div[data-testid="stMultiSelect"] [data-baseweb="tag"] svg,
html body div[data-testid="stMultiSelect"] span:has(svg) svg path {{
    fill: {current_theme['tag_text']} !important;
    color: {current_theme['tag_text']} !important;
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

# ==================== 資料庫高效操作函式 ====================
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
        res = supabase.table("activity_logs").select("*").eq("trip_code", code).order("id", desc=True).limit(50).execute()
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

# 【效能核心優化】即時基準匯率 + 極速快取（絕不拖慢主網頁載入）
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
# 第一層：身分認證（未登入 且 未透過免登入連結進入）
# ==============================================================================
if st.session_state["current_code"] is None and st.session_state["auth_user"] is None:
    st.markdown("<h2 style='text-align: center; margin-bottom: 0.3rem; font-weight: 800;'>📒 個人/共同分帳記事簿</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b; margin-bottom: 1.8rem; font-size: 0.95rem;'>點擊好友專屬連結免登入直達；管理私密帳本或發起旅程請由此登入</p>", unsafe_allow_html=True)

    with st.container(border=True):
        tab_login, tab_signup = st.tabs(["🔑 會員登入 / 帳本管理", "✨ 免費註冊新帳號"])

        with tab_login:
            with st.form("login_form"):
                l_email = st.text_input("電子信箱 (Email)", placeholder="name@example.com").strip().lower()
                l_pwd = st.text_input("密碼", type="password", placeholder="輸入登入密碼")
                
                if st.form_submit_button("立即登入", type="primary", use_container_width=True):
                    if not l_email or not l_pwd:
                        st.toast("❌ 請填寫 Email 與密碼！")
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
                s_name = st.text_input("您的姓名 / 暱稱", placeholder="例如：小明")
                s_email = st.text_input("電子信箱 (Email)", placeholder="name@example.com").strip().lower()
                s_pwd = st.text_input("設定密碼", type="password", placeholder="建議 6 位以上英數字")
                
                if st.form_submit_button("確認註冊並登入", type="primary", use_container_width=True):
                    clean_name = re.sub(r'[,，]', '', s_name.strip())
                    clean_email = s_email.strip()
                    if not clean_name:
                        st.toast("❌ 請填寫姓名！")
                    elif not clean_email or "@" not in clean_email:
                        st.toast("❌ 請填寫有效的 Email！")
                    elif len(s_pwd) < 4:
                        st.toast("❌ 密碼長度至少需 4 位！")
                    elif get_user_by_email(clean_email):
                        st.toast("⚠️ 此 Email 已被註冊，請直接登入！")
                    else:
                        supabase.table("app_users").insert({
                            "email": clean_email,
                            "password_hash": hash_password(s_pwd),
                            "name": clean_name
                        }).execute()
                        st.session_state["auth_user"] = {"email": clean_email, "name": clean_name}
                        st.toast(f"🎉 註冊成功！歡迎使用，{clean_name}！")
                        st.rerun()

    with st.container(border=True):
        st.markdown("##### 🚀 手邊有好友的邀請代號？（免登入直接進入）")
        c_quick1, c_quick2 = st.columns([3, 1])
        with c_quick1:
            quick_code_in = st.text_input("輸入 7 碼邀請碼", placeholder="例如：TRIP888", label_visibility="collapsed").strip().upper()
        with c_quick2:
            if st.button("直接進入", type="secondary", use_container_width=True):
                if quick_code_in and get_trip_info(quick_code_in):
                    st.query_params["trip"] = quick_code_in
                    st.rerun()
                else:
                    st.toast("❌ 查無此邀請碼！")

    st.stop()


# ==============================================================================
# 第二層：主揪 / 會員「個人帳本與行程總覽大廳」
# ==============================================================================
if st.session_state["current_code"] is None and st.session_state["auth_user"] is not None:
    current_user = st.session_state["auth_user"]
    user_email = current_user["email"]
    user_name = current_user["name"]

    col_u1, col_u2 = st.columns([4, 1.2])
    with col_u1:
        st.markdown(f"### 👋 哈囉，{user_name}！")
        st.caption(f"📧 帳號：`{user_email}` ｜ 您的所有個人與共同帳本均在此自動同步")
    with col_u2:
        st.write("")
        if st.button("🚪 登出帳號", use_container_width=True):
            st.session_state["auth_user"] = None
            st.session_state["current_book_type"] = None
            st.session_state["current_code"] = None
            st.session_state["confirm_del_p_active"] = False
            st.session_state["confirm_del_group_active"] = False
            st.query_params.clear()
            st.toast("👋 已安全登出！")
            st.rerun()

    st.divider()

    user_saved_books = get_user_books(user_email)
    personal_books = [b for b in user_saved_books if b["book_type"] == "personal"]
    group_books = [b for b in user_saved_books if b["book_type"] == "group"]

    col_lobby_p, col_lobby_g = st.columns(2)

    # 個人帳本
    with col_lobby_p:
        with st.container(border=True):
            st.markdown("#### 👤 我的個人帳本")
            st.caption("專屬的日常收支管家，無其他人分攤。")
            
            if personal_books:
                for b in personal_books:
                    c_bname, c_bact = st.columns([3, 1.2])
                    with c_bname:
                        st.markdown(f"**📖 {b['book_name']}**")
                        st.caption(f"代碼：`{b['book_code']}`")
                    with c_bact:
                        if st.button("開啟", key=f"open_p_{b['book_code']}", use_container_width=True, type="primary"):
                            st.session_state["current_book_type"] = "personal"
                            st.session_state["current_code"] = b["book_code"]
                            st.query_params["book"] = b["book_code"]
                            st.rerun()
                    st.markdown("<hr style='margin: 6px 0; border: none; border-top: 1px dashed #e2e8f0;'>", unsafe_allow_html=True)
            else:
                st.info("尚無個人帳本，點擊下方立即建立！")

            c_p_op1, c_p_op2 = st.columns(2)
            with c_p_op1:
                with st.expander("➕ 建立新個人帳本"):
                    with st.form("create_new_personal_book"):
                        nb_name = st.text_input("記事本名稱", placeholder="例如：2026日常開銷")
                        if st.form_submit_button("確認建立", type="primary", use_container_width=True):
                            c_nb_name = nb_name.strip()
                            if not c_nb_name:
                                st.toast("❌ 請填寫帳本名稱！")
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
                                st.toast(f"🎉 成功建立「{c_nb_name}」！")
                                st.rerun()

            with c_p_op2:
                if personal_books:
                    with st.expander("🛠️ 管理個人帳本"):
                        target_p_mng = st.selectbox(
                            "選取欲管理的帳本：",
                            options=[b["book_code"] for b in personal_books],
                            format_func=lambda x: [b["book_name"] for b in personal_books if b["book_code"]==x][0],
                            key="lobby_p_mng_sel"
                        )
                        curr_b_obj = [b for b in personal_books if b["book_code"]==target_p_mng][0]
                        with st.form(f"rename_p_form_{target_p_mng}"):
                            new_bname_input = st.text_input("修改名稱", value=curr_b_obj["book_name"])
                            if st.form_submit_button("💾 儲存新名稱", type="primary", use_container_width=True):
                                if new_bname_input.strip():
                                    supabase.table("trips").update({"trip_name": new_bname_input.strip()}).eq("trip_code", target_p_mng).execute()
                                    supabase.table("user_books").update({"book_name": new_bname_input.strip()}).eq("book_code", target_p_mng).execute()
                                    st.toast("✏️ 帳本名稱已更新！")
                                    st.rerun()

                        if st.button("🗑️ 刪除此帳本", key=f"lobby_del_p_{target_p_mng}", type="secondary", use_container_width=True):
                            supabase.table("personal_records").delete().eq("book_code", target_p_mng).execute()
                            supabase.table("personal_categories").delete().eq("book_code", target_p_mng).execute()
                            supabase.table("trips").delete().eq("trip_code", target_p_mng).execute()
                            supabase.table("user_books").delete().eq("book_code", target_p_mng).execute()
                            st.toast("🗑️ 已成功刪除該個人帳本！")
                            st.rerun()

    # 共同旅遊分帳
    with col_lobby_g:
        with st.container(border=True):
            st.markdown("#### 👥 我的共同分帳行程")
            st.caption("出遊記帳、即時結算還款與直接分享網址。")
            
            if group_books:
                for b in group_books:
                    c_gname, c_gact = st.columns([3, 1.2])
                    with c_gname:
                        st.markdown(f"**✈️ {b['book_name']}**")
                        st.caption(f"邀請碼：`{b['book_code']}`")
                    with c_gact:
                        if st.button("進入", key=f"open_g_{b['book_code']}", use_container_width=True, type="primary"):
                            st.session_state["current_book_type"] = "group"
                            st.session_state["current_code"] = b["book_code"]
                            st.query_params["trip"] = b["book_code"]
                            st.rerun()
                    st.markdown("<hr style='margin: 6px 0; border: none; border-top: 1px dashed #e2e8f0;'>", unsafe_allow_html=True)
            else:
                st.info("尚無共同分帳，可發起新旅程！")

            c_g_op1, c_g_op2 = st.columns(2)
            with c_g_op1:
                with st.expander("➕ 發起新旅程"):
                    with st.form("create_new_group_trip"):
                        ng_name = st.text_input("旅程名稱", placeholder="例如：沖繩五天四夜")
                        ng_pin = st.text_input("管理密碼 (4~6位)", type="password", max_chars=6)
                        if st.form_submit_button("建立行程", type="primary", use_container_width=True):
                            c_ng_name = ng_name.strip()
                            if not c_ng_name:
                                st.toast("❌ 請填寫旅程名稱！")
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
                                st.toast(f"🎉 成功建立！邀請碼：{ng_code}")
                                st.rerun()

            with c_g_op2:
                if group_books:
                    with st.expander("🛠️ 管理共同行程"):
                        target_g_mng = st.selectbox(
                            "選取欲管理的行程：",
                            options=[b["book_code"] for b in group_books],
                            format_func=lambda x: [b["book_name"] for b in group_books if b["book_code"]==x][0],
                            key="lobby_g_mng_sel"
                        )
                        curr_g_obj = [b for b in group_books if b["book_code"]==target_g_mng][0]
                        g_info = get_trip_info(target_g_mng)
                        g_admin_pin = g_info.get("admin_pin", "") if g_info else ""

                        with st.form(f"rename_g_form_{target_g_mng}"):
                            new_gname_input = st.text_input("修改名稱", value=curr_g_obj["book_name"])
                            if st.form_submit_button("💾 儲存新名稱", type="primary", use_container_width=True):
                                if new_gname_input.strip():
                                    supabase.table("trips").update({"trip_name": new_gname_input.strip()}).eq("trip_code", target_g_mng).execute()
                                    supabase.table("user_books").update({"book_name": new_gname_input.strip()}).eq("book_code", target_g_mng).execute()
                                    st.toast("✏️ 行程名稱已更新！")
                                    st.rerun()

                        del_g_pin_input = st.text_input("管理員密碼 (4~6位)", type="password", key=f"del_g_pin_{target_g_mng}", placeholder="4~6位密碼")
                        if st.button("🗑️ 驗證並永久刪除此行程", key=f"lobby_del_g_{target_g_mng}", type="secondary", use_container_width=True):
                            if not del_g_pin_input.strip():
                                st.toast("❌ 請輸入管理員密碼！")
                            elif g_admin_pin and del_g_pin_input.strip() != g_admin_pin:
                                st.toast("❌ 管理員密碼錯誤，拒絕刪除！")
                            else:
                                supabase.table("expenses").delete().eq("trip_code", target_g_mng).execute()
                                supabase.table("members").delete().eq("trip_code", target_g_mng).execute()
                                supabase.table("activity_logs").delete().eq("trip_code", target_g_mng).execute()
                                supabase.table("trips").delete().eq("trip_code", target_g_mng).execute()
                                supabase.table("user
