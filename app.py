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
from datetime import datetime

# 頁面標題與佈局
st.set_page_config(page_title="旅遊即時分帳系統", page_icon="✈️", layout="wide", initial_sidebar_state="auto")

# ==================== 5 種極簡莫蘭迪風格配色 ====================
THEMES = {
    "🌿 鼠尾草綠": {
        "primary": "#3d5a4d",
        "hover": "#2f463b",
        "tag_bg": "#edf4f0",
        "tag_border": "#cde0d5",
        "tag_text": "#234033"
    },
    "🍂 暖陶土橘": {
        "primary": "#b8563b",
        "hover": "#99432b",
        "tag_bg": "#faeee9",
        "tag_border": "#ecc9bc",
        "tag_text": "#752e1d"
    },
    "🌊 暮靄靛藍": {
        "primary": "#2a4d6c",
        "hover": "#1d374e",
        "tag_bg": "#edf3f8",
        "tag_border": "#c4d8e8",
        "tag_text": "#15334d"
    },
    "🌸 煙燻胭粉": {
        "primary": "#9c485c",
        "hover": "#7f3546",
        "tag_bg": "#faecf0",
        "tag_border": "#ebc5cf",
        "tag_text": "#691f30"
    },
    "🌑 簡約冷灰": {
        "primary": "#2d3748",
        "hover": "#1a202c",
        "tag_bg": "#edf2f7",
        "tag_border": "#cbd5e0",
        "tag_text": "#1a202c"
    }
}

if "theme_name" not in st.session_state:
    st.session_state["theme_name"] = "🌿 鼠尾草綠"

current_theme = THEMES[st.session_state["theme_name"]]

# ==================== 極簡無干擾 CSS 樣式系統 ====================
st.markdown(f"""
<style>
/* 1. 現代字體與背景邊距 */
html, body, [class*="css"] {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang TC", sans-serif;
    color: #1e293b;
}}

/* 電腦端頂部安全留白 */
.block-container {{
    padding-top: 3.5rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 1050px !important;
}}

/* 2. 手機端安全間距：保證不被工具列遮擋 */
@media (max-width: 768px) {{
    .block-container {{
        padding-top: 4.8rem !important;
        padding-left: 0.85rem !important;
        padding-right: 0.85rem !important;
        padding-bottom: 2rem !important;
    }}
}}

/* 3. 極簡膠囊分頁導航 (Tabs) */
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

/* 4. 極簡扁平卡片（極細框線、無多餘大陰影） */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius: 12px !important;
    border: 1px solid #e2e8f0 !important;
    background-color: #ffffff !important;
    padding: 1rem !important;
    box-shadow: none !important;
}}

/* 5. 簡約指標卡 */
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

/* 6. 按鈕樣式：圓角、簡約無厚重陰影 */
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

/* 7. 人名標籤 (多選標籤) 扁平淡色 */
div[data-testid="stMultiSelect"] {{
    --primary-color: {current_theme['tag_bg']} !important;
}}
html body div[data-testid="stMultiSelect"] [data-baseweb="tag"],
html body div[data-testid="stMultiSelect"] span:has(svg) {{
    background-color: {current_theme['tag_bg']} !important;
    border: 1px solid {current_theme['tag_border']} !important;
    border-radius: 6px !important;
    padding: 2px 7px !important;
}}
html body div[data-testid="stMultiSelect"] [data-baseweb="tag"] span {{
    color: {current_theme['tag_text']} !important;
    font-weight: 600 !important;
}}
html body div[data-testid="stMultiSelect"] [data-baseweb="tag"] svg {{
    fill: {current_theme['tag_text']} !important;
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

# 輔助函式：產生 7 碼邀請碼
def generate_invite_code():
    letters = ''.join(random.choices(string.ascii_uppercase, k=4))
    digits = ''.join(random.choices(string.digits, k=3))
    return f"{letters}{digits}"

# 輔助函式：時間轉換
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

# 寫入操作紀錄
def log_activity(code, action, detail):
    try:
        supabase.table("activity_logs").insert({
            "trip_code": code,
            "action_type": action,
            "details": detail
        }).execute()
    except Exception:
        pass

# 判斷是否為「個人純自費」
def is_personal_only(expense):
    split_list = [m.strip() for m in expense.get("split_members", "").split(",") if m.strip()]
    return len(split_list) == 1 and split_list[0] == expense.get("paid_by")

# 資料庫讀取
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

# 抓取台銀牌告匯率
@st.cache_data(ttl=1800)
def fetch_bot_rates():
    url = "https://rate.bot.com.tw/xrt/flcsv/0/day"
    target_currencies = {
        "USD": "美金", "JPY": "日幣", "THB": "泰銖",
        "KRW": "韓元", "CNY": "人民幣"
    }
    rates = {
        "USD": {"name": "美金", "cash_sell": 32.50},
        "JPY": {"name": "日幣", "cash_sell": 0.2150},
        "THB": {"name": "泰銖", "cash_sell": 0.9800},
        "KRW": {"name": "韓元", "cash_sell": 0.0245},
        "CNY": {"name": "人民幣", "cash_sell": 4.5200}
    }
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

# 狀態計數器
if "cnt_manage_exp" not in st.session_state:
    st.session_state["cnt_manage_exp"] = 0
if "cnt_manage_p" not in st.session_state:
    st.session_state["cnt_manage_p"] = 0

# ==============================================================================
# 狀態檢查：判斷是否已登入特定行程
# ==============================================================================
query_trip = st.query_params.get("trip", "").strip().upper()
if "current_trip" not in st.session_state:
    st.session_state["current_trip"] = query_trip if query_trip else None

current_trip = st.session_state["current_trip"]

# ==============================================================================
# 畫面 A：極簡大廳首頁（雙方塊清晰入口）
# ==============================================================================
if not current_trip:
    st.markdown("<h2 style='text-align: center; margin-bottom: 0.3rem; font-weight: 700;'>✈️ 旅遊分帳系統</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b; margin-bottom: 1.8rem; font-size: 0.95rem;'>簡單、直覺的同行出遊記帳與即時結算工具</p>", unsafe_allow_html=True)

    col_create, col_join = st.columns(2)

    with col_create:
        with st.container(border=True):
            st.markdown("#### ➕ 建立新行程")
            st.caption("由你發起旅程，系統將自動產生 7 碼邀請碼")
            
            with st.form("create_trip_form"):
                new_trip_name = st.text_input("旅程名稱", placeholder="例如：日本東京五日遊")
                new_admin_pin = st.text_input("管理密碼（4~6 位數字）", type="password", max_chars=6, help="刪除成員或帳簿時驗證用")
                creator_name = st.text_input("主揪姓名", placeholder="例如：小明")

                create_submit = st.form_submit_button("建立行程並取得邀請碼", type="primary", use_container_width=True)

                if create_submit:
                    clean_name = new_trip_name.strip()
                    clean_pin = new_admin_pin.strip()
                    clean_creator = creator_name.strip()

                    if not clean_name:
                        st.toast("❌ 請填寫旅程名稱！")
                    elif not re.fullmatch(r"^\d{4,6}$", clean_pin):
                        st.toast("❌ 管理密碼需為 4 ~ 6 位純數字！")
                    elif not clean_creator:
                        st.toast("❌ 請填寫主揪姓名！")
                    else:
                        code = generate_invite_code()
                        while get_trip_info(code):
                            code = generate_invite_code()

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
                        st.query_params["trip"] = code
                        st.toast(f"🎉 建立成功！邀請碼為：{code}")
                        st.rerun()

    with col_join:
        with st.container(border=True):
            st.markdown("#### 🚀 加入現有行程")
            st.caption("輸入好友分享的 7 碼邀請代號即可加入")

            join_code_input = st.text_input("邀請碼 (必填)", value=query_trip, placeholder="例如：TRIP888", max_chars=7).strip().upper()
            
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
                join_member_name = st.text_input(
                    "你的姓名 (選填)",
                    placeholder="名單已有名字者免填，新夥伴請填寫"
                )
                join_submit = st.form_submit_button("進入分帳帳簿", type="primary", use_container_width=True)

                if join_submit:
                    if not join_code_input:
                        st.toast("❌ 請輸入邀請碼！")
                    elif not trip_info:
                        st.toast("❌ 邀請碼無效！")
                    else:
                        clean_join_name = join_member_name.strip()
                        if clean_join_name and clean_join_name not in existing_members:
                            supabase.table("members").insert({
                                "trip_code": join_code_input,
                                "name": clean_join_name
                            }).execute()
                            log_activity(join_code_input, "成員加入", f"新成員「{clean_join_name}」加入行程")

                        st.session_state["current_trip"] = join_code_input
                        st.query_params["trip"] = join_code_input
                        st.toast(f"✅ 成功進入「{trip_info['trip_name']}」！")
                        st.rerun()

    st.stop()

# ==============================================================================
# 畫面 B：主分帳系統
# ==============================================================================
trip_code = current_trip
trip_info = get_trip_info(trip_code)
trip_name = trip_info["trip_name"] if trip_info else trip_code
admin_pin = trip_info["admin_pin"] if trip_info else "0000"

members = get_members(trip_code)
expenses = get_expenses(trip_code)
logs = get_logs(trip_code)
total_trip_expense = sum(int(round(float(e["amount"]))) for e in expenses)

id_to_exp = {e["id"]: e for e in expenses}

# 頂部行程橫幅
col_h1, col_h2 = st.columns([4, 1.2])
with col_h1:
    st.markdown(f"### {trip_name}")
    st.caption(f"🔑 邀請碼：**`{trip_code}`** ｜ 30 秒自動同步")
with col_h2:
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄", help="手動更新最新資料", use_container_width=True):
            st.toast("🔄 已同步最新資料")
            st.rerun()
    with col_btn2:
        if st.button("🚪", help="離開切換行程", use_container_width=True):
            st.session_state["current_trip"] = None
            st.session_state["confirm_del_trip"] = False
            st.query_params.clear()
            st.rerun()

# 頂部三大直覺指標卡（總支出、成員數、每人平均負擔）
c_m1, c_m2, c_m3 = st.columns(3)
avg_expense = int(round(total_trip_expense / len(members))) if members else 0

with c_m1:
    st.metric("全團總花費", f"${total_trip_expense:,}")
with c_m2:
    st.metric("成員人數", f"{len(members)} 人")
with c_m3:
    st.metric("每人平均約", f"${avg_expense:,}")

st.write("")

# ==============================================================================
# 側邊欄：工具與管理
# ==============================================================================
with st.sidebar:
    st.markdown("### ⚙️ 工具與成員管理")
    
    # 1. 色彩主題
    with st.container(border=True):
        st.markdown("**🎨 介面主題色**")
        def on_theme_change():
            st.session_state["theme_name"] = st.session_state["theme_selector"]

        st.selectbox(
            "選擇主題色調：",
            options=list(THEMES.keys()),
            index=list(THEMES.keys()).index(st.session_state["theme_name"]),
            key="theme_selector",
            on_change=on_theme_change,
            label_visibility="collapsed"
        )

    # 2. 成員管理
    with st.container(border=True):
        st.markdown("**👥 行程成員**")
        with st.form("add_member_form", clear_on_submit=True):
            new_member = st.text_input("新增姓名", placeholder="例如：阿山", label_visibility="collapsed")
            add_btn = st.form_submit_button("➕ 加入成員", type="primary", use_container_width=True)
            if add_btn:
                clean_name = new_member.strip()
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
                    if not del_pin_input.strip():
                        st.toast("❌ 請輸入密碼！")
                    elif del_pin_input.strip() != admin_pin:
                        st.toast("❌ 密碼錯誤！")
                    else:
                        supabase.table("members").delete().eq("trip_code", trip_code).eq("name", member_to_delete).execute()
                        log_activity(trip_code, "刪除成員", f"管理員刪除成員「{member_to_delete}」")
                        st.toast(f"🗑️ 已刪除：{member_to_delete}")
                        st.rerun()

    # 3. 匯率工具
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

        res_amt = (fx_amt * rates_to_twd[fx_from]) / rates_to_twd[fx_to]
        if fx_to == "TWD":
            st.info(f"≈ **${int(round(res_amt)):,}** 台幣")
        else:
            st.info(f"≈ **{res_amt:,.2f}** {fx_to}")

    # 4. 操作日誌
    with st.container(border=True):
        st.markdown("**📜 異動紀錄**")
        with st.expander(f"查看最新日誌 ({len(logs)} 筆)"):
            if logs:
                st.dataframe(pd.DataFrame([{
                    "時間": format_time(l.get("created_at")),
                    "動作": l.get("action_type", ""),
                    "內容": l.get("details", "")
                } for l in logs]), use_container_width=True, hide_index=True)
            else:
                st.caption("尚無紀錄。")

    # 5. 危機管理：刪除帳簿
    with st.container(border=True):
        st.markdown("**⚠️ 危機管理**")
        with st.expander("🚨 永久刪除此帳簿"):
            if st.session_state.get("confirm_del_trip", False):
                st.error("警告：將永久抹除所有資料！")
                c_dy, c_dn = st.columns(2)
                with c_dy:
                    if st.button("確認刪除", type="primary", use_container_width=True):
                        supabase.table("expenses").delete().eq("trip_code", trip_code).execute()
                        supabase.table("members").delete().eq("trip_code", trip_code).execute()
                        supabase.table("activity_logs").delete().eq("trip_code", trip_code).execute()
                        supabase.table("trips").delete().eq("trip_code", trip_code).execute()
                        st.session_state["confirm_del_trip"] = False
                        st.session_state["current_trip"] = None
                        st.query_params.clear()
                        st.toast("🗑️ 行程已刪除！")
                        st.rerun()
                with c_dn:
                    if st.button("取消", use_container_width=True):
                        st.session_state["confirm_del_trip"] = False
                        st.rerun()
            else:
                tp_pin = st.text_input("輸入管理密碼", type="password", key="tp_pin_del")
                if st.button("驗證並繼續", type="secondary", use_container_width=True):
                    if tp_pin.strip() != admin_pin:
                        st.toast("❌ 密碼錯誤！")
                    else:
                        st.session_state["confirm_del_trip"] = True
                        st.rerun()

# ==============================================================================
# 橫列主功能選單（3 膠囊標籤）
# ==============================================================================
tab1, tab2, tab3 = st.tabs([
    "📝 記帳明細",
    "👤 個人帳務",
    "📊 結算還款"
])

# ==================== Tab 1: 記帳明細 ====================
with tab1:
    # 快速記帳
    with st.container(border=True):
        st.markdown("##### ➕ 新增一筆消費")
        if len(members) < 1:
            st.warning("請先在左側選單新增成員！")
        else:
            with st.form("add_expense_form", clear_on_submit=True):
                c_item, c_amt = st.columns([3, 2])
                with c_item:
                    item_name = st.text_input("項目名稱", placeholder="例如：晚餐、計程車、門票")
                with c_amt:
                    amount = st.number_input("金額 (NTD / 幣別)", min_value=1, step=50, format="%d")

                c_payer, c_split = st.columns(2)
                with c_payer:
                    paid_by = st.selectbox("誰先付錢？", options=members)
                with c_split:
                    split_with = st.multiselect("誰要分攤？", options=members, default=members)

                submit_btn = st.form_submit_button("記下一筆", type="primary", use_container_width=True)
                if submit_btn:
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

    # 團體明細清單
    shared_expenses = [e for e in expenses if not is_personal_only(e)]
    sorted_shared = sorted(shared_expenses, key=lambda x: x["id"])
    shared_id_to_seq = {e["id"]: idx + 1 for idx, e in enumerate(sorted_shared)}

    with st.container(border=True):
        st.markdown("##### 📋 團體分攤明細清單")
        if shared_expenses:
            st.dataframe(pd.DataFrame([{
                "#": shared_id_to_seq[e["id"]],
                "時間": format_time(e.get("created_at")),
                "項目": e["item"],
                "金額": f"${int(round(float(e['amount']))):,}",
                "代墊人": e["paid_by"],
                "分攤名單": e["split_members"]
            } for e in shared_expenses]), use_container_width=True, hide_index=True)

            # 【極簡整合】：編輯與刪除合為一體，直覺流暢
            with st.expander("🛠️ 管理或修改帳目", expanded=False, key=f"exp_mng_{st.session_state['cnt_manage_exp']}"):
                target_id = st.selectbox(
                    "選擇欲調整的帳目：",
                    options=[e["id"] for e in shared_expenses],
                    format_func=lambda x: f"#{shared_id_to_seq[x]} {id_to_exp[x]['item']} (${int(round(float(id_to_exp[x]['amount']))):,})",
                    key="sel_mng_exp"
                )
                curr_exp = id_to_exp[target_id]
                curr_split = [m.strip() for m in curr_exp["split_members"].split(",") if m.strip() in members]

                with st.form("unified_edit_form"):
                    e_name = st.text_input("項目名稱", value=curr_exp["item"])
                    e_amt = st.number_input("金額", min_value=1, value=int(round(float(curr_exp["amount"]))), step=50, format="%d")
                    p_idx = members.index(curr_exp["paid_by"]) if curr_exp["paid_by"] in members else 0
                    e_paid = st.selectbox("代墊人", options=members, index=p_idx)
                    e_split = st.multiselect("分攤名單", options=members, default=curr_split)

                    c_save, c_empty = st.columns([1, 1])
                    with c_save:
                        save_btn = st.form_submit_button("💾 儲存修改", type="primary", use_container_width=True)
                    if save_btn:
                        if e_name.strip() and e_split:
                            supabase.table("expenses").update({
                                "item": e_name.strip(),
                                "amount": int(round(e_amt)),
                                "paid_by": e_paid,
                                "split_members": ",".join(e_split)
                            }).eq("id", target_id).execute()
                            log_activity(trip_code, "修改記帳", f"修改 #{shared_id_to_seq[target_id]} 為「{e_name.strip()}」${int(round(e_amt)):,}")
                            st.toast("✏️ 帳目已更新！")
                            st.session_state["cnt_manage_exp"] += 1
                            st.rerun()

                # 刪除按鈕直接放在下方，不需分開找兩次
                if st.button("🗑️ 刪除這筆帳目", type="secondary", use_container_width=True, key="del_mng_btn"):
                    seq_num = shared_id_to_seq[target_id]
                    d_name = curr_exp['item']
                    supabase.table("expenses").delete().eq("id", target_id).execute()
                    log_activity(trip_code, "刪除記帳", f"刪除 #{seq_num}「{d_name}」")
                    st.toast("🗑️ 已成功刪除該筆帳目！")
                    st.session_state["cnt_manage_exp"] += 1
                    st.rerun()
        else:
            st.caption("尚無團體分攤紀錄。")

# ==================== Tab 2: 個人帳務 ====================
with tab2:
    if not members:
        st.info("請先新增成員！")
    else:
        with st.container(border=True):
            col_u_sel, _ = st.columns([1.5, 2])
            with col_u_sel:
                selected_user = st.selectbox("切換查看成員：", options=members)

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

            # 大字號清晰狀態看板
            st.divider()
            c_p1, c_p2, c_p3 = st.columns(3)
            with c_p1:
                st.metric("我代墊的支出", f"${total_paid_by_user:,}")
            with c_p2:
                st.metric("我個人的消費", f"${total_consumed_by_user:,}")
            with c_p3:
                if net_balance >= 0:
                    st.metric("🟢 目前應收回", f"+${net_balance:,}")
                else:
                    st.metric("🔴 目前應補繳", f"-${abs(net_balance):,}")

        # 個人純自費清單
        with st.container(border=True):
            st.markdown(f"##### 🛍️ **{selected_user}** 的個人自費清單")
            if personal_list:
                sorted_p = sorted(personal_list, key=lambda x: x["raw_id"])
                p_id_seq = {p["raw_id"]: idx + 1 for idx, p in enumerate(sorted_p)}
                for p in personal_list:
                    p["#"] = p_id_seq[p["raw_id"]]

                st.dataframe(pd.DataFrame(personal_list)[["#", "時間", "項目", "自費金額"]], use_container_width=True, hide_index=True)

                with st.expander("🛠️ 管理個人自費項目", expanded=False, key=f"exp_p_mng_{st.session_state['cnt_manage_p']}"):
                    p_sel_id = st.selectbox(
                        "選擇自費項目：",
                        options=[p["raw_id"] for p in personal_list],
                        format_func=lambda x: f"#{p_id_seq[x]} {id_to_exp[x]['item']} (${int(round(float(id_to_exp[x]['amount']))):,})",
                        key="sel_p_mng"
                    )
                    curr_p = id_to_exp[p_sel_id]
                    with st.form("edit_p_form"):
                        pn_item = st.text_input("名稱", value=curr_p["item"])
                        pn_amt = st.number_input("金額", min_value=1, value=int(round(float(curr_p["amount"]))), step=50, format="%d")
                        if st.form_submit_button("💾 儲存修改", type="primary", use_container_width=True):
                            if pn_item.strip():
                                supabase.table("expenses").update({"item": pn_item.strip(), "amount": int(round(pn_amt))}).eq("id", p_sel_id).execute()
                                log_activity(trip_code, "修改自費", f"{selected_user} 修改自費為「{pn_item.strip()}」${int(round(pn_amt)):,}")
                                st.toast("✏️ 已更新！")
                                st.session_state["cnt_manage_p"] += 1
                                st.rerun()

                    if st.button("🗑️ 刪除此自費項目", type="secondary", use_container_width=True, key="del_p_mng_btn"):
                        supabase.table("expenses").delete().eq("id", p_sel_id).execute()
                        log_activity(trip_code, "刪除自費", f"{selected_user} 刪除自費「{curr_p['item']}」")
                        st.toast("🗑️ 已成功刪除！")
                        st.session_state["cnt_manage_p"] += 1
                        st.rerun()
            else:
                st.caption(f"目前尚無 {selected_user} 的個人純自費項目。")

        # 參與的團體分攤明細
        with st.container(border=True):
            st.markdown(f"##### 👥 與 **{selected_user}** 相關的分攤明細")
            if group_list:
                st.dataframe(pd.DataFrame(group_list), use_container_width=True, hide_index=True)
            else:
                st.caption("尚無相關分攤明細。")

# ==================== Tab 3: 結算還款 ====================
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
                    "狀態": f"🟢 應收回 +${v:,}" if v >= 0 else f"🔴 應支付 -${abs(v):,}"
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
                i, j = 0, 0
                while i < len(debtors) and j < len(creditors):
                    deb_name, deb_amt = debtors[i]
                    cred_name, cred_amt = creditors[j]
                    trans_amt = min(deb_amt, cred_amt)
                    
                    if trans_amt >= 1:
                        settlements.append(f"👉 **{deb_name}** 轉帳給 **{cred_name}**：`{trans_amt:,}` 元")
                    
                    debtors[i][1] -= trans_amt
                    creditors[j][1] -= trans_amt
                    
                    if debtors[i][1] == 0:
                        i += 1
                    if creditors[j][1] == 0:
                        j += 1

                if settlements:
                    for s in settlements:
                        st.info(s)
                else:
                    st.success("🎉 目前帳目已完全平衡，大家互不相欠！")

# ==================== 30 秒自動靜默同步 ====================
time.sleep(30)
st.rerun()
