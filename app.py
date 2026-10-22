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
from datetime import datetime, date

# 頁面標題與佈局
st.set_page_config(page_title="個人/共同分帳記事簿", page_icon="📒", layout="wide", initial_sidebar_state="auto")

# ==================== 5 種極簡莫蘭迪風格配色 ====================
THEMES = {
    "🌿 鼠尾草綠": {
        "primary": "#3d5a4d",
        "hover": "#2f463b",
        "tag_bg": "#cfe3d7",
        "tag_border": "#8ab79e",
        "tag_text": "#123020"
    },
    "🍂 暖陶土橘": {
        "primary": "#b8563b",
        "hover": "#99432b",
        "tag_bg": "#f8cfbf",
        "tag_border": "#df9077",
        "tag_text": "#5c1b0c"
    },
    "🌊 暮靄靛藍": {
        "primary": "#2a4d6c",
        "hover": "#1d374e",
        "tag_bg": "#cce0f2",
        "tag_border": "#84b3dc",
        "tag_text": "#0a243d"
    },
    "🌸 煙燻胭粉": {
        "primary": "#9c485c",
        "hover": "#7f3546",
        "tag_bg": "#f7cad6",
        "tag_border": "#d48197",
        "tag_text": "#4d0d1d"
    },
    "🌑 簡約冷灰": {
        "primary": "#2d3748",
        "hover": "#1a202c",
        "tag_bg": "#d3d9e0",
        "tag_border": "#9aa5b3",
        "tag_text": "#0f141a"
    }
}

if "theme_name" not in st.session_state:
    st.session_state["theme_name"] = "🌿 鼠尾草綠"

current_theme = THEMES[st.session_state["theme_name"]]

# ==================== 極簡 CSS 樣式系統 ====================
st.markdown(f"""
<style>
html, body, [class*="css"] {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang TC", sans-serif;
    color: #1e293b;
}}

.block-container {{
    padding-top: 3.5rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 1050px !important;
}}

@media (max-width: 768px) {{
    .block-container {{
        padding-top: 4.8rem !important;
        padding-left: 0.85rem !important;
        padding-right: 0.85rem !important;
        padding-bottom: 2rem !important;
    }}
}}

div[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    background-color: #f1f5f9 !important;
    padding: 4px !important;
    border-radius: 12px !important;
    gap: 4px !important;
    border: none !important;
}}
div[data-testid="stTabs"] button[data-testid="stTab"] {{
    border-radius: 9px !important;
    border: none !important;
    padding: 8px 16px !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    color: #64748b !important;
    background: transparent !important;
    transition: all 0.2s ease !important;
}}
div[data-testid="stTabs"] button[data-testid="stTab"][aria-selected="true"] {{
    background-color: #ffffff !important;
    color: {current_theme['primary']} !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
}}
div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{
    display: none !important;
}}

div[data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius: 12px !important;
    border: 1px solid #e2e8f0 !important;
    background-color: #ffffff !important;
    padding: 1rem !important;
    box-shadow: none !important;
}}

div[data-testid="stMetric"] {{
    background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
}}
div[data-testid="stMetricLabel"] p {{
    font-size: 0.82rem !important;
    color: #64748b !important;
    font-weight: 500 !important;
}}
div[data-testid="stMetricValue"] {{
    font-size: clamp(1.35rem, 2.5vw, 1.7rem) !important;
    font-weight: 700 !important;
    color: #0f172a !important;
}}

html body button[data-testid*="primary"],
html body button[data-testid="baseButton-primary"],
html body button[kind="primary"],
html body .stButton > button[kind="primary"],
html body div[data-testid="stFormSubmitButton"] > button {{
    background-color: {current_theme['primary']} !important;
    border: none !important;
    color: #ffffff !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    min-height: 40px !important;
    transition: all 0.15s ease !important;
}}
html body button[data-testid*="primary"]:hover,
html body div[data-testid="stFormSubmitButton"] > button:hover {{
    background-color: {current_theme['hover']} !important;
    opacity: 0.95 !important;
}}

html body button[data-testid*="secondary"],
html body button[data-testid="baseButton-secondary"] {{
    border-radius: 8px !important;
    border: 1px solid #cbd5e1 !important;
    background: #ffffff !important;
    color: #475569 !important;
    font-size: 0.9rem !important;
    min-height: 38px !important;
}}

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
}}
html body div[data-testid="stMultiSelect"] [data-baseweb="tag"] svg,
html body div[data-testid="stMultiSelect"] span:has(svg) svg path {{
    fill: {current_theme['tag_text']} !important;
    color: {current_theme['tag_text']} !important;
}}
</style>
""", unsafe_allow_html=True)

# 初始化 Supabase 連線
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error("資料庫連線失敗，請檢查 Streamlit Secrets 設定！")
    st.stop()

# 產生邀請碼
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

# 資料庫查詢：行程 / 帳簿
def get_trip_info(code):
    try:
        res = supabase.table("trips").select("*").eq("trip_code", code).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

def get_members(code):
    res = supabase.table("members").select("name").eq("trip_code", code).execute()
    return [r["name"] for r in res.data]

def get_expenses(code):
    res = supabase.table("expenses").select("*").eq("trip_code", code).order("id", desc=True).execute()
    return res.data

def get_logs(code):
    try:
        res = supabase.table("activity_logs").select("*").eq("trip_code", code).order("id", desc=True).limit(60).execute()
        return res.data
    except Exception:
        return []

# 資料庫查詢：個人記帳專用
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

# 抓取台銀匯率
@st.cache_data(ttl=1800)
def fetch_bot_rates():
    url = "https://rate.bot.com.tw/xrt/flcsv/0/day"
    target_currencies = {"USD": "美金", "JPY": "日幣", "THB": "泰銖", "KRW": "韓元", "CNY": "人民幣"}
    rates = {"USD": {"name": "美金", "cash_sell": 32.50}, "JPY": {"name": "日幣", "cash_sell": 0.2150},
             "THB": {"name": "泰銖", "cash_sell": 0.9800}, "KRW": {"name": "韓元", "cash_sell": 0.0245},
             "CNY": {"name": "人民幣", "cash_sell": 4.5200}}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
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
if "app_mode" not in st.session_state:
    st.session_state["app_mode"] = None  # None (首頁二選一), 'personal' (個人記帳), 'group' (共同記帳)
if "current_trip" not in st.session_state:
    st.session_state["current_trip"] = None
if "current_book" not in st.session_state:
    st.session_state["current_book"] = None

# URL 導向檢查
q_trip = st.query_params.get("trip", "").strip().upper()
q_book = st.query_params.get("book", "").strip().upper()

if q_trip and not st.session_state["current_trip"]:
    st.session_state["app_mode"] = "group"
    st.session_state["current_trip"] = q_trip
elif q_book and not st.session_state["current_book"]:
    st.session_state["app_mode"] = "personal"
    st.session_state["current_book"] = q_book


# ==============================================================================
# 第一個畫面：首頁選擇（個人記帳 vs 共同記帳）
# ==============================================================================
if st.session_state["app_mode"] is None:
    st.markdown("<h2 style='text-align: center; margin-bottom: 0.3rem; font-weight: 800;'>📒 個人/共同分帳記事簿</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b; margin-bottom: 2rem; font-size: 0.95rem;'>請選擇您要使用的記帳模式，隨時切換、雲端即時保存</p>", unsafe_allow_html=True)

    col_m1, col_m2 = st.columns(2)

    with col_m1:
        with st.container(border=True):
            st.markdown("### 👤 個人獨立記帳")
            st.caption("專屬於自己的日常收支管家，精細分類、記錄私房錢與生活預算，無分攤還款干擾。")
            st.markdown("""
            * 📊 即時統計：收入 / 支出 / 淨盈餘
            * 🏷️ 支援自訂分類（飲食、交通、薪水、回饋等）
            * 🔒 專屬 6~8 位密碼保護獨立帳本
            """)
            if st.button("👉 進入個人記帳", type="primary", use_container_width=True):
                st.session_state["app_mode"] = "personal"
                st.rerun()

    with col_m2:
        with st.container(border=True):
            st.markdown("### 👥 共同旅遊分帳")
            st.caption("專為好友同行出遊設計，多人代墊記帳、自選分攤對象，並自動算出最簡轉帳指引。")
            st.markdown("""
            * ✈️ 輸入代號與好友即時多人共同編輯
            * 💡 最簡還款轉帳建議（一鍵複製 LINE 催款）
            * 💱 內建台灣銀行即時牌告匯率換算
            """)
            if st.button("👉 進入共同記帳", type="primary", use_container_width=True):
                st.session_state["app_mode"] = "group"
                st.rerun()

    st.stop()


# ==============================================================================
# 模式一：個人獨立記帳系統 (Personal Accounting)
# ==============================================================================
if st.session_state["app_mode"] == "personal":
    book_code = st.session_state.get("current_book")

    # 1. 未載入個人記事簿時的入口畫面（建立新帳本 vs 開啟現有帳本）
    if not book_code:
        col_nav_l, col_nav_r = st.columns([4, 1.2])
        with col_nav_l:
            st.markdown("### 👤 個人獨立記帳")
            st.caption("請建立專屬個人帳簿，或輸入帳本代碼與密碼開啟")
        with col_nav_r:
            if st.button("🏠 返回首頁選單", use_container_width=True):
                st.session_state["app_mode"] = None
                st.query_params.clear()
                st.rerun()

        col_p_create, col_p_open = st.columns(2)

        with col_p_create:
            with st.container(border=True):
                st.markdown("#### ➕ 建立個人帳簿")
                st.caption("建立專屬獨立帳本，系統將為您生成個人代號")
                with st.form("create_personal_book_form"):
                    p_name = st.text_input("記事本名稱", placeholder="例如：我的日常收支、2026年度帳本")
                    p_pin = st.text_input("設定密碼（6~8 位數字）", type="password", max_chars=8, help="開啟與保護此帳本需要此密碼")
                    
                    if st.form_submit_button("✨ 立即建立帳本", type="primary", use_container_width=True):
                        clean_p_name = p_name.strip()
                        clean_p_pin = p_pin.strip()
                        if not clean_p_name:
                            st.toast("❌ 請填寫記事本名稱！")
                        elif not re.fullmatch(r"^\d{6,8}$", clean_p_pin):
                            st.toast("❌ 密碼必須為 6 ~ 8 位純數字！")
                        else:
                            new_bcode = generate_code(prefix="P")
                            while get_trip_info(new_bcode):
                                new_bcode = generate_code(prefix="P")

                            supabase.table("trips").insert({
                                "trip_code": new_bcode,
                                "trip_name": clean_p_name,
                                "admin_pin": clean_p_pin
                            }).execute()

                            st.session_state["current_book"] = new_bcode
                            st.query_params["book"] = new_bcode
                            st.toast(f"🎉 建立成功！個人代號：{new_bcode}")
                            st.rerun()

        with col_p_open:
            with st.container(border=True):
                st.markdown("#### 🔑 開啟個人帳簿")
                st.caption("輸入您的專屬個人代碼與密碼進入")
                with st.form("open_personal_book_form"):
                    open_bcode = st.text_input("個人帳簿代碼", placeholder="例如：PABC123").strip().upper()
                    open_pin = st.text_input("請輸入密碼（6~8 位數字）", type="password", max_chars=8)

                    if st.form_submit_button("進入我的帳本", type="primary", use_container_width=True):
                        if not open_bcode:
                            st.toast("❌ 請輸入帳本代碼！")
                        else:
                            book_info = get_trip_info(open_bcode)
                            if not book_info:
                                st.toast("❌ 查無此個人帳簿代碼！")
                            elif book_info.get("admin_pin") != open_pin.strip():
                                st.toast("❌ 密碼錯誤，拒絕存取！")
                            else:
                                st.session_state["current_book"] = open_bcode
                                st.query_params["book"] = open_bcode
                                st.toast(f"✅ 成功開啟「{book_info['trip_name']}」！")
                                st.rerun()

        st.stop()

    # 2. 已載入個人記事簿的主畫面
    book_info = get_trip_info(book_code)
    book_name = book_info["trip_name"] if book_info else "個人記帳本"
    book_pin = book_info["admin_pin"] if book_info else ""

    # 讀取個人收支資料
    p_records = get_personal_records(book_code)
    total_income = sum(int(round(float(r["amount"]))) for r in p_records if r["record_type"] == "income")
    total_expense = sum(int(round(float(r["amount"]))) for r in p_records if r["record_type"] == "expense")
    net_surplus = total_income - total_expense

    # 頂部導航
    col_pb1, col_pb2 = st.columns([3.8, 1.5])
    with col_pb1:
        st.markdown(f"### 👤 {book_name}")
        st.caption(f"🔑 帳本代碼：**`{book_code}`**（個人專屬私密帳簿，無成員分攤）")
    with col_pb2:
        col_pbtn1, col_pbtn2 = st.columns(2)
        with col_pbtn1:
            if st.button("🔄", help="重新載入", use_container_width=True):
                st.toast("🔄 資料已更新！")
                st.rerun()
        with col_pbtn2:
            if st.button("🚪", help="關閉離開此帳本", use_container_width=True):
                st.session_state["current_book"] = None
                st.query_params.clear()
                st.rerun()

    # 畫面正上方：總收入 / 總支出 / 淨盈餘
    c_inc, c_exp, c_sur = st.columns(3)
    with c_inc:
        st.metric("💰 總收入", f"${total_income:,}")
    with c_exp:
        st.metric("💸 總支出", f"${total_expense:,}")
    with c_sur:
        if net_surplus > 0:
            st.metric("⚖️ 淨盈餘", f"+${net_surplus:,}")
        elif net_surplus < 0:
            st.metric("⚖️ 淨透支", f"-${abs(net_surplus):,}")
        else:
            st.metric("⚖️ 收支平衡", "$0")

    st.write("")

    # 側邊欄：色彩主題、匯率工具與刪除帳本
    with st.sidebar:
        st.markdown("### ⚙️ 個人帳本工具")
        
        # 主題色彩
        with st.container(border=True):
            st.markdown("**🎨 介面主題色**")
            def on_theme_change():
                st.session_state["theme_name"] = st.session_state["theme_selector"]

            st.selectbox("選擇主題色調：", options=list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state["theme_name"]), key="theme_selector", on_change=on_theme_change, label_visibility="collapsed")

        # 匯率換算
        with st.container(border=True):
            st.markdown("**💱 台灣銀行牌告匯率**")
            bot_rates = fetch_bot_rates()
            fx_amt = st.number_input("換算金額", min_value=0, value=1000, step=100, format="%d", key="p_fx_amt")
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                fx_from = st.selectbox("從", options=["TWD", "JPY", "USD", "THB", "KRW", "CNY"], index=0, key="p_fx_from")
            with c_f2:
                fx_to = st.selectbox("換為", options=["TWD", "JPY", "USD", "THB", "KRW", "CNY"], index=1, key="p_fx_to")
            
            rates_to_twd = {"TWD": 1.0}
            for c, info in bot_rates.items():
                rates_to_twd[c] = info["cash_sell"]
            res_amt = (fx_amt * rates_to_twd.get(fx_from, 1.0)) / rates_to_twd.get(fx_to, 1.0)
            st.info(f"≈ **${int(round(res_amt)):,}** 台幣" if fx_to == "TWD" else f"≈ **{res_amt:,.2f}** {fx_to}")

        # 刪除個人帳本
        with st.container(border=True):
            st.markdown("**⚠️ 帳本危機管理**")
            with st.expander("🚨 永久刪除此帳本"):
                del_p_pin = st.text_input("輸入帳本密碼 (6~8位)", type="password", key="del_p_pin_input")
                if st.button("確認永久刪除帳本", type="primary", use_container_width=True):
                    if del_p_pin.strip() != book_pin:
                        st.toast("❌ 密碼錯誤！")
                    else:
                        supabase.table("personal_records").delete().eq("book_code", book_code).execute()
                        supabase.table("personal_categories").delete().eq("book_code", book_code).execute()
                        supabase.table("trips").delete().eq("trip_code", book_code).execute()
                        st.session_state["current_book"] = None
                        st.query_params.clear()
                        st.toast("🗑️ 個人帳本已刪除！")
                        st.rerun()

    # 讀取預設與自訂類別
    default_expense_cats = ["食物", "購物", "家用", "交通", "醫療", "娛樂", "儲蓄", "保險", "其他"]
    default_income_cats = ["薪水", "獎金", "回饋", "股息"]
    
    custom_exp_cats = get_personal_categories(book_code, "expense")
    custom_inc_cats = get_personal_categories(book_code, "income")
    
    all_exp_cats = default_expense_cats + [c for c in custom_exp_cats if c not in default_expense_cats]
    all_inc_cats = default_income_cats + [c for c in custom_inc_cats if c not in default_income_cats]

    # 分頁籤：支出記帳 vs 收入記帳
    p_tab1, p_tab2 = st.tabs(["💸 支出記帳", "💰 收入記帳"])

    # ---------- 分頁 1：支出記帳 ----------
    with p_tab1:
        with st.container(border=True):
            st.markdown("##### ➕ 新增支出消費")
            with st.form("add_personal_expense_form", clear_on_submit=True):
                r1_c1, r1_c2 = st.columns([3, 2])
                with r1_c1:
                    exp_item = st.text_input("消費名稱", placeholder="例如：午餐便當、家樂福採買、高鐵票")
                with r1_c2:
                    exp_amt = st.number_input("金額 (NTD)", min_value=1, step=50, format="%d")

                r2_c1, r2_c2 = st.columns(2)
                with r2_c1:
                    exp_cat = st.selectbox("支出類別", options=all_exp_cats)
                with r2_c2:
                    exp_date = st.date_input("消費日期", value=date.today())

                if st.form_submit_button("記下一筆支出", type="primary", use_container_width=True):
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
                        st.toast(f"💸 支出已記錄：{exp_item.strip()} ${int(round(exp_amt)):,}！")
                        st.rerun()

        # 類別管理（新增自訂類別）
        with st.expander("🏷️ 管理支出類別 (新增或刪除自訂類別)"):
            c_add_ec1, c_add_ec2 = st.columns([3, 1])
            with c_add_ec1:
                new_ecat = st.text_input("新增自訂支出類別", placeholder="例如：寵物、健身、訂閱", key="new_ecat_input")
            with c_add_ec2:
                st.write("")
                if st.button("➕ 新增類別", key="btn_add_ecat", use_container_width=True):
                    clean_ec = new_ecat.strip()
                    if clean_ec and clean_ec not in all_exp_cats:
                        supabase.table("personal_categories").insert({
                            "book_code": book_code,
                            "record_type": "expense",
                            "name": clean_ec
                        }).execute()
                        st.toast(f"✅ 已新增類別：{clean_ec}")
                        st.rerun()

            if custom_exp_cats:
                st.caption("自訂類別列表（可刪除）：")
                del_ecat_target = st.selectbox("選擇要刪除的自訂類別：", options=custom_exp_cats, key="sel_del_ecat")
                if st.button("🗑️ 刪除該自訂類別", key="btn_del_ecat"):
                    supabase.table("personal_categories").delete().eq("book_code", book_code).eq("record_type", "expense").eq("name", del_ecat_target).execute()
                    st.toast(f"🗑️ 已刪除類別：{del_ecat_target}")
                    st.rerun()

        # 支出明細列表
        exp_list = [r for r in p_records if r["record_type"] == "expense"]
        with st.container(border=True):
            st.markdown("##### 📋 支出明細清單")
            if exp_list:
                st.dataframe(pd.DataFrame([{
                    "日期": str(r.get("record_date", "")),
                    "類別": r["category"],
                    "項目": r["item"],
                    "金額": f"${int(round(float(r['amount']))):,}"
                } for r in exp_list]), use_container_width=True, hide_index=True)

                with st.expander("🛠️ 管理或修改支出項目"):
                    target_pe_id = st.selectbox(
                        "選擇欲調整的支出：",
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
                                supabase.table("personal_records").update({
                                    "item": pe_n_item.strip(),
                                    "amount": int(round(pe_n_amt)),
                                    "category": pe_n_cat,
                                    "record_date": str(pe_n_date)
                                }).eq("id", target_pe_id).execute()
                                st.toast("✏️ 支出已更新！")
                                st.rerun()

                    if st.button("🗑️ 刪除此筆支出", type="secondary", use_container_width=True, key="del_pe_btn"):
                        supabase.table("personal_records").delete().eq("id", target_pe_id).execute()
                        st.toast("🗑️ 已成功刪除！")
                        st.rerun()
            else:
                st.caption("尚無任何支出記錄。")

    # ---------- 分頁 2：收入記帳 ----------
    with p_tab2:
        with st.container(border=True):
            st.markdown("##### ➕ 新增收入項目")
            with st.form("add_personal_income_form", clear_on_submit=True):
                r1_c1, r1_c2 = st.columns([3, 2])
                with r1_c1:
                    inc_item = st.text_input("收入名稱", placeholder="例如：十月份薪資、業績獎金、發票中獎")
                with r1_c2:
                    inc_amt = st.number_input("金額 (NTD)", min_value=1, step=100, format="%d")

                r2_c1, r2_c2 = st.columns(2)
                with r2_c1:
                    inc_cat = st.selectbox("收入類別", options=all_inc_cats)
                with r2_c2:
                    inc_date = st.date_input("入帳日期", value=date.today())

                if st.form_submit_button("記下一筆收入", type="primary", use_container_width=True):
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
                        st.toast(f"💰 收入已記錄：{inc_item.strip()} ${int(round(inc_amt)):,}！")
                        st.rerun()

        # 類別管理（新增自訂收入類別）
        with st.expander("🏷️ 管理收入類別 (新增或刪除自訂類別)"):
            c_add_ic1, c_add_ic2 = st.columns([3, 1])
            with c_add_ic1:
                new_icat = st.text_input("新增自訂收入類別", placeholder="例如：兼職、租金、外快", key="new_icat_input")
            with c_add_ic2:
                st.write("")
                if st.button("➕ 新增類別", key="btn_add_icat", use_container_width=True):
                    clean_ic = new_icat.strip()
                    if clean_ic and clean_ic not in all_inc_cats:
                        supabase.table("personal_categories").insert({
                            "book_code": book_code,
                            "record_type": "income",
                            "name": clean_ic
                        }).execute()
                        st.toast(f"✅ 已新增類別：{clean_ic}")
                        st.rerun()

            if custom_inc_cats:
                st.caption("自訂收入類別列表：")
                del_icat_target = st.selectbox("選擇要刪除的類別：", options=custom_inc_cats, key="sel_del_icat")
                if st.button("🗑️ 刪除該自訂類別", key="btn_del_icat"):
                    supabase.table("personal_categories").delete().eq("book_code", book_code).eq("record_type", "income").eq("name", del_icat_target).execute()
                    st.toast(f"🗑️ 已刪除類別：{del_icat_target}")
                    st.rerun()

        # 收入明細列表
        inc_list = [r for r in p_records if r["record_type"] == "income"]
        with st.container(border=True):
            st.markdown("##### 📋 收入明細清單")
            if inc_list:
                st.dataframe(pd.DataFrame([{
                    "日期": str(r.get("record_date", "")),
                    "類別": r["category"],
                    "項目": r["item"],
                    "金額": f"${int(round(float(r['amount']))):,}"
                } for r in inc_list]), use_container_width=True, hide_index=True)

                with st.expander("🛠️ 管理或修改收入項目"):
                    target_pi_id = st.selectbox(
                        "選擇欲調整的收入：",
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
                                supabase.table("personal_records").update({
                                    "item": pi_n_item.strip(),
                                    "amount": int(round(pi_n_amt)),
                                    "category": pi_n_cat,
                                    "record_date": str(pi_n_date)
                                }).eq("id", target_pi_id).execute()
                                st.toast("✏️ 收入已更新！")
                                st.rerun()

                    if st.button("🗑️ 刪除此筆收入", type="secondary", use_container_width=True, key="del_pi_btn"):
                        supabase.table("personal_records").delete().eq("id", target_pi_id).execute()
                        st.toast("🗑️ 已成功刪除！")
                        st.rerun()
            else:
                st.caption("尚無任何收入記錄。")

    st.stop()


# ==============================================================================
# 模式二：共同旅遊分帳系統 (Group Expense Splitter)
# ==============================================================================
trip_code = st.session_state.get("current_trip")

# 1. 共同分帳入口大廳
if not trip_code:
    col_nav_gl, col_nav_gr = st.columns([4, 1.2])
    with col_nav_gl:
        st.markdown("### 👥 共同旅遊分帳")
        st.caption("簡單、直覺的同行出遊記帳與即時結算工具")
    with col_nav_gr:
        if st.button("🏠 返回首頁選單", use_container_width=True):
            st.session_state["app_mode"] = None
            st.query_params.clear()
            st.rerun()

    col_create, col_join = st.columns(2)

    with col_create:
        with st.container(border=True):
            st.markdown("#### ➕ 建立新行程")
            st.caption("由你發起旅程，系統將自動產生 7 碼邀請碼")
            with st.form("create_trip_form"):
                new_trip_name = st.text_input("旅程名稱", placeholder="例如：日本東京五日遊")
                new_admin_pin = st.text_input("管理密碼（4~6 位數字）", type="password", max_chars=6, help="刪除成員或帳簿時驗證用")
                creator_name = st.text_input("主揪姓名", placeholder="例如：小明")

                if st.form_submit_button("建立行程並取得邀請碼", type="primary", use_container_width=True):
                    clean_name = new_trip_name.strip()
                    clean_pin = new_admin_pin.strip()
                    clean_creator = re.sub(r'[,，]', '', creator_name.strip())

                    if not clean_name:
                        st.toast("❌ 請填寫旅程名稱！")
                    elif not re.fullmatch(r"^\d{4,6}$", clean_pin):
                        st.toast("❌ 管理密碼需為 4 ~ 6 位純數字！")
                    elif not clean_creator:
                        st.toast("❌ 請填寫主揪姓名！")
                    else:
                        code = generate_code()
                        while get_trip_info(code):
                            code = generate_code()

                        supabase.table("trips").insert({
                            "trip_code": code,
                            "trip_name": clean_name,
                            "admin_pin": clean_pin
                        }).execute()

                        supabase.table("members").insert({
                            "trip_code": code,
                            "name": clean_creator
                        }).execute()

                        log_activity(code, "建立行程", f"主揪「{clean_creator}」建立了「{clean_name}」")

                        st.session_state["current_trip"] = code
                        st.session_state["user_name"] = clean_creator
                        st.query_params["trip"] = code
                        st.toast(f"🎉 建立成功！邀請碼為：{code}")
                        st.rerun()

    with col_join:
        with st.container(border=True):
            st.markdown("#### 🚀 加入現有行程")
            st.caption("輸入好友分享的 7 碼邀請代號即可加入")

            join_code_input = st.text_input("邀請碼 (必填)", value=q_trip, placeholder="例如：TRIP888", max_chars=7).strip().upper()
            
            trip_info = None
            existing_members = []
            if join_code_input:
                trip_info = get_trip_info(join_code_input)
                if trip_info:
                    existing_members = get_members(join_code_input)
                    st.success(f"📍 **{trip_info['trip_name']}**")
                    st.caption(f"現有夥伴：{ '、'.join(existing_members) if existing_members else '暫無成員' }")
                else:
                    st.warning("⚠️ 查無此邀請碼，請確認後重試！")

            with st.form("join_trip_form"):
                join_member_name = st.text_input("你的姓名 (選填)", placeholder="名單已有名字者免填，新夥伴請填寫")
                if st.form_submit_button("進入分帳帳簿", type="primary", use_container_width=True):
                    if not join_code_input:
                        st.toast("❌ 請輸入邀請碼！")
                    elif not trip_info:
                        st.toast("❌ 邀請碼無效！")
                    else:
                        clean_join_name = re.sub(r'[,，]', '', join_member_name.strip())
                        if clean_join_name and clean_join_name not in existing_members:
                            supabase.table("members").insert({
                                "trip_code": join_code_input,
                                "name": clean_join_name
                            }).execute()
                            log_activity(join_code_input, "成員加入", f"新成員「{clean_join_name}」加入行程")
                            st.session_state["user_name"] = clean_join_name
                        elif clean_join_name:
                            st.session_state["user_name"] = clean_join_name

                        st.session_state["current_trip"] = join_code_input
                        st.query_params["trip"] = join_code_input
                        st.toast(f"✅ 成功進入「{trip_info['trip_name']}」！")
                        st.rerun()

    st.stop()

# 2. 共同分帳主儀表板
trip_info = get_trip_info(trip_code)
trip_name = trip_info["trip_name"] if trip_info else trip_code
admin_pin = trip_info["admin_pin"] if trip_info else ""

members = get_members(trip_code)
expenses = get_expenses(trip_code)
logs = get_logs(trip_code)
total_trip_expense = sum(int(round(float(e["amount"]))) for e in expenses)
id_to_exp = {e["id"]: e for e in expenses}

# 頂部行程橫幅
col_h1, col_h2 = st.columns([3.5, 1.8])
with col_h1:
    st.markdown(f"### {trip_name}")
    st.caption(f"🔑 邀請碼：**`{trip_code}`** ｜ 30 秒自動同步")
with col_h2:
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        if st.button("🔄", help="手動更新", use_container_width=True):
            st.toast("🔄 已同步最新資料")
            st.rerun()
    with col_btn2:
        with st.popover("🔗", help="分享行程邀請碼", use_container_width=True):
            st.markdown(f"**📤 分享【{trip_name}】**")
            st.caption("邀請碼：")
            st.code(trip_code, language="text")
    with col_btn3:
        if st.button("🚪", help="離開切換行程", use_container_width=True):
            st.session_state["current_trip"] = None
            st.query_params.clear()
            st.rerun()

# 頂部三大指標卡
c_m1, c_m2, c_m3 = st.columns(3)
avg_expense = int(round(total_trip_expense / len(members))) if members else 0
with c_m1:
    st.metric("全團總花費", f"${total_trip_expense:,}")
with c_m2:
    st.metric("成員人數", f"{len(members)} 人")
with c_m3:
    st.metric("每人平均約", f"${avg_expense:,}")

st.write("")

# 側邊欄
with st.sidebar:
    st.markdown("### ⚙️ 工具與成員管理")
    
    with st.container(border=True):
        st.markdown("**👤 我的身分**")
        default_user_idx = 0
        if "user_name" in st.session_state and st.session_state["user_name"] in members:
            default_user_idx = members.index(st.session_state["user_name"])
        active_user = st.selectbox("當前使用成員：", options=members if members else ["無成員"], index=default_user_idx if members else 0)
        if members and active_user != st.session_state.get("user_name"):
            st.session_state["user_name"] = active_user

    with st.container(border=True):
        st.markdown("**🎨 介面主題色**")
        def on_theme_change():
            st.session_state["theme_name"] = st.session_state["theme_selector"]
        st.selectbox("選擇主題色調：", options=list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state["theme_name"]), key="theme_selector", on_change=on_theme_change, label_visibility="collapsed")

    with st.container(border=True):
        st.markdown("**👥 行程成員管理**")
        with st.form("add_member_form", clear_on_submit=True):
            new_member = st.text_input("新增姓名", placeholder="例如：阿山", label_visibility="collapsed")
            if st.form_submit_button("➕ 加入成員", type="primary", use_container_width=True):
                clean_name = re.sub(r'[,，]', '', new_member.strip())
                if clean_name and clean_name not in members:
                    supabase.table("members").insert({"trip_code": trip_code, "name": clean_name}).execute()
                    log_activity(trip_code, "新增成員", f"新增成員「{clean_name}」")
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
        bot_rates = fetch_bot_rates()
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
        st.markdown("**⚠️ 危機管理**")
        with st.expander("🚨 永久刪除此帳簿"):
            tp_pin = st.text_input("輸入管理密碼", type="password", key="tp_pin_del")
            if st.button("確認永久刪除", type="primary", use_container_width=True):
                if not admin_pin or tp_pin.strip() != admin_pin:
                    st.toast("❌ 密碼錯誤！")
                else:
                    supabase.table("expenses").delete().eq("trip_code", trip_code).execute()
                    supabase.table("members").delete().eq("trip_code", trip_code).execute()
                    supabase.table("activity_logs").delete().eq("trip_code", trip_code).execute()
                    supabase.table("trips").delete().eq("trip_code", trip_code).execute()
                    st.session_state["current_trip"] = None
                    st.query_params.clear()
                    st.toast("🗑️ 行程已刪除！")
                    st.rerun()

# 共同分帳三頁籤
tab1, tab2, tab3 = st.tabs(["📝 新增消費", "👤 個人帳務", "📊 結算還款"])

# Tab 1: 新增消費與分攤明細
with tab1:
    with st.container(border=True):
        st.markdown("##### ➕ 新增消費")
        if len(members) < 1:
            st.warning("請先在左側選單新增成員！")
        else:
            with st.form("add_expense_form", clear_on_submit=True):
                c_item, c_amt = st.columns(2)
                with c_item:
                    item_name = st.text_input("項目名稱", placeholder="例如：晚餐、計程車、門票")
                with c_amt:
                    amount = st.number_input("金額 (NTD / 幣別)", min_value=1, step=50, format="%d")

                c_payer, c_split = st.columns(2)
                with c_payer:
                    current_idx = members.index(st.session_state.get("user_name")) if st.session_state.get("user_name") in members else 0
                    paid_by = st.selectbox("誰先付錢？", options=members, index=current_idx)
                with c_split:
                    split_with = st.multiselect("誰要分攤？", options=members, default=members)

                if st.form_submit_button("記下一筆", type="primary", use_container_width=True):
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
        st.markdown("##### 📋 分攤明細")
        if shared_expenses:
            st.dataframe(pd.DataFrame([{
                "#": shared_id_to_seq[e["id"]],
                "時間": format_time(e.get("created_at")),
                "項目": e["item"],
                "金額": f"${int(round(float(e['amount']))):,}",
                "代墊人": e["paid_by"],
                "分攤名單": e["split_members"]
            } for e in shared_expenses]), use_container_width=True, hide_index=True)

            with st.expander("🛠️ 管理或修改帳目"):
                target_id = st.selectbox(
                    "選擇欲調整的帳目：",
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
                            st.toast("✏️ 帳目已更新！")
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

# Tab 2: 個人帳務（自費清單/分攤清單）
with tab2:
    if not members:
        st.info("請先新增成員！")
    else:
        with st.container(border=True):
            col_u_sel, _ = st.columns([1.5, 2])
            with col_u_sel:
                default_sel_idx = members.index(st.session_state.get("user_name")) if st.session_state.get("user_name") in members else 0
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

            st.divider()
            c_p1, c_p2, c_p3 = st.columns(3)
            with c_p1:
                st.metric("我代墊的支出", f"${total_paid_by_user:,}")
            with c_p2:
                st.metric("我個人的消費", f"${total_consumed_by_user:,}")
            with c_p3:
                if net_balance > 0:
                    st.metric("🟢 目前應收回", f"+${net_balance:,}")
                elif net_balance < 0:
                    st.metric("🔴 目前應補繳", f"-${abs(net_balance):,}")
                else:
                    st.metric("⚖️ 帳目平衡", "$0")

        with st.container(border=True):
            st.markdown(f"##### 🛍️ 自費清單 ({selected_user})")
            if personal_list:
                sorted_p = sorted(personal_list, key=lambda x: x["raw_id"])
                p_id_seq = {p["raw_id"]: idx + 1 for idx, p in enumerate(sorted_p)}
                for p in personal_list:
                    p["#"] = p_id_seq[p["raw_id"]]

                st.dataframe(pd.DataFrame(personal_list)[["#", "時間", "項目", "自費金額"]], use_container_width=True, hide_index=True)

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
                                log_activity(trip_code, "修改自費", f"{selected_user} 修改自費為「{pn_item.strip()}」${int(round(pn_amt)):,}")
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
                st.dataframe(pd.DataFrame(group_list), use_container_width=True, hide_index=True)
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

        col_b_list, col_b_guide = st.columns([1, 1.2])

        with col_b_list:
            with st.container(border=True):
                st.markdown("##### 📋 每人結算淨額")
                st.dataframe(pd.DataFrame([{
                    "成員": k,
                    "狀態": f"🟢 應收回 +${v:,}" if v > 0 else (f"🔴 應支付 -${abs(v):,}" if v < 0 else "⚖️ 結清 $0")
                } for k, v in balances.items()]), use_container_width=True, hide_index=True)

        with col_b_guide:
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
                        line_messages.append(f"• {deb_name} 轉帳給 {cred_name}：${trans_amt:,} 元")
                    
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
                    st.markdown("**📋 LINE 群組催款懶人包**")
                    share_text = f"✈️【{trip_name}】費用結算清單\n全團總累積花費：${total_trip_expense:,} 元\n" + "-"*20 + "\n"
                    share_text += "\n".join(line_messages)
                    share_text += "\n" + "-"*20 + "\n大家確認無誤後即可直接轉帳結清囉！"
                    st.code(share_text, language="text")
                else:
                    st.success("🎉 目前帳目完全平衡，大家互不相欠！")

# ==================== 30 秒自動靜默同步 ====================
time.sleep(30)
st.rerun()
