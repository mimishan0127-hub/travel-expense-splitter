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
st.set_page_config(page_title="旅遊即時分帳系統", page_icon="✈️", layout="wide")

# ==================== 5 種精緻質感配色 ====================
THEMES = {
    "🌿 莫蘭迪鼠尾草綠": {
        "primary": "#4A6B5D",
        "hover": "#385246",
        "tag_bg": "#E2ECE7",
        "tag_border": "#B8CECA",
        "tag_text": "#284438",
        "light": "rgba(74, 107, 93, 0.15)"
    },
    "🍂 暖陽焦糖陶土": {
        "primary": "#C86D51",
        "hover": "#A5543A",
        "tag_bg": "#F7ECE6",
        "tag_border": "#E5C6B8",
        "tag_text": "#783622",
        "light": "rgba(200, 109, 81, 0.15)"
    },
    "🌊 深海暮靄靛藍": {
        "primary": "#2E5B82",
        "hover": "#1F3E5A",
        "tag_bg": "#E3EDF6",
        "tag_border": "#B7D0E6",
        "tag_text": "#163A5C",
        "light": "rgba(46, 91, 130, 0.15)"
    },
    "🌸 霧面煙燻胭粉": {
        "primary": "#B05A6F",
        "hover": "#924456",
        "tag_bg": "#F9E9ED",
        "tag_border": "#E8C4CE",
        "tag_text": "#6E2837",
        "light": "rgba(176, 90, 111, 0.15)"
    },
    "🌑 黑曜玄武岩灰": {
        "primary": "#2D3139",
        "hover": "#1A1D23",
        "tag_bg": "#EBECEE",
        "tag_border": "#CDD0D5",
        "tag_text": "#1E2229",
        "light": "rgba(45, 49, 57, 0.15)"
    }
}

if "theme_name" not in st.session_state:
    st.session_state["theme_name"] = "🌿 莫蘭迪鼠尾草綠"

current_theme = THEMES[st.session_state["theme_name"]]

# 注入全域 CSS 樣式
st.markdown(f"""
<style>
/* 主按鈕 */
html body button[data-testid*="primary"],
html body button[data-testid="baseButton-primary"],
html body button[data-testid="stBaseButton-primary"],
html body button[kind="primary"],
html body .stButton > button[kind="primary"],
html body div[data-testid="stFormSubmitButton"] > button {{
    background-color: {current_theme['primary']} !important;
    border: 1px solid {current_theme['primary']} !important;
    color: #ffffff !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease-in-out;
}}

html body button[data-testid*="primary"]:hover,
html body button[data-testid="baseButton-primary"]:hover,
html body button[data-testid="stBaseButton-primary"]:hover,
html body button[kind="primary"]:hover,
html body .stButton > button[kind="primary"]:hover,
html body div[data-testid="stFormSubmitButton"] > button:hover {{
    background-color: {current_theme['hover']} !important;
    border-color: {current_theme['hover']} !important;
    color: #ffffff !important;
}}

/* 次要按鈕 */
html body button[data-testid*="secondary"],
html body button[data-testid="baseButton-secondary"],
html body button[data-testid="stBaseButton-secondary"] {{
    border-radius: 8px !important;
}}

/* 分頁籤選取樣式 */
html body button[data-testid="stTab"][aria-selected="true"] {{
    color: {current_theme['primary']} !important;
    border-bottom: 2px solid {current_theme['primary']} !important;
}}

/* 卡片懸停效果 */
div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
    border-color: {current_theme['primary']} !important;
    box-shadow: 0 2px 8px {current_theme['light']} !important;
    transition: all 0.2s ease-in-out;
}}

/* 人名標籤 (多選標籤) 配色 */
div[data-testid="stMultiSelect"] {{
    --primary-color: {current_theme['tag_bg']} !important;
}}

html body div[data-testid="stMultiSelect"] [data-baseweb="tag"],
html body div[data-testid="stMultiSelect"] [data-testid*="tag"],
html body div[data-testid="stMultiSelect"] span:has(svg),
html body div[data-testid="stMultiSelect"] div:has(> svg):has(span) {{
    background-color: {current_theme['tag_bg']} !important;
    background: {current_theme['tag_bg']} !important;
    border: 1px solid {current_theme['tag_border']} !important;
    border-radius: 6px !important;
    padding: 2px 6px !important;
}}

html body div[data-testid="stMultiSelect"] [data-baseweb="tag"] span,
html body div[data-testid="stMultiSelect"] span:has(svg) span {{
    color: {current_theme['tag_text']} !important;
    font-weight: 600 !important;
}}

html body div[data-testid="stMultiSelect"] [data-baseweb="tag"] svg,
html body div[data-testid="stMultiSelect"] span:has(svg) svg path {{
    fill: {current_theme['tag_text']} !important;
    stroke: {current_theme['tag_text']} !important;
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

# 輔助函式：產生 4 位大寫英文 + 3 位數字的亂數邀請碼
def generate_invite_code():
    letters = ''.join(random.choices(string.ascii_uppercase, k=4))
    digits = ''.join(random.choices(string.digits, k=3))
    return f"{letters}{digits}"

# 輔助函式：時間轉換為台灣時間字串
def format_time(ts_str):
    if not ts_str:
        return ""
    try:
        dt = pd.to_datetime(ts_str)
        if dt.tzinfo is None:
            dt = dt.tz_localize("UTC")
        return dt.tz_convert("Asia/Taipei").strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(ts_str)[:19].replace("T", " ")

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

# 判斷是否為「個人自費（無他人分攤）」
def is_personal_only(expense):
    split_list = [m.strip() for m in expense.get("split_members", "").split(",") if m.strip()]
    return len(split_list) == 1 and split_list[0] == expense.get("paid_by")

# 資料庫讀取操作
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
        res = supabase.table("activity_logs").select("*").eq("trip_code", code).order("id", desc=True).limit(100).execute()
        return res.data
    except Exception:
        return []

# 抓取台銀牌告匯率
@st.cache_data(ttl=1800)
def fetch_bot_rates():
    url = "https://rate.bot.com.tw/xrt/flcsv/0/day"
    target_currencies = {
        "USD": "美金 (USD)", "JPY": "日幣 (JPY)", "THB": "泰銖 (THB)",
        "KRW": "韓元 (KRW)", "CNY": "人民幣 (CNY)"
    }
    rates = {
        "USD": {"name": "美金 (USD)", "cash_sell": 32.50, "spot_sell": 32.40},
        "JPY": {"name": "日幣 (JPY)", "cash_sell": 0.2150, "spot_sell": 0.2130},
        "THB": {"name": "泰銖 (THB)", "cash_sell": 0.9800, "spot_sell": 0.9500},
        "KRW": {"name": "韓元 (KRW)", "cash_sell": 0.0245, "spot_sell": 0.0240},
        "CNY": {"name": "人民幣 (CNY)", "cash_sell": 4.5200, "spot_sell": 4.4900}
    }
    status = "備用參考匯率（離線）"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as response:
            content = response.read().decode("utf-8", errors="ignore")
            reader = csv.reader(io.StringIO(content))
            for row in reader:
                if not row or len(row) < 14:
                    continue
                code = row[0].strip()
                if code in target_currencies:
                    def parse_val(v):
                        try:
                            val = float(v.strip())
                            return val if val > 0 else None
                        except Exception:
                            return None
                    cash_sell = parse_val(row[12])
                    spot_sell = parse_val(row[13])
                    c_val = cash_sell if cash_sell else spot_sell
                    s_val = spot_sell if spot_sell else cash_sell
                    if c_val:
                        rates[code] = {
                            "name": target_currencies[code],
                            "cash_sell": c_val,
                            "spot_sell": s_val if s_val else c_val
                        }
            status = f"台灣銀行即時牌告（更新於 {datetime.now().strftime('%H:%M')}）"
    except Exception:
        status = "連線逾時，已使用備用匯率"
    return rates, status

# 選單自動收合計數器
if "cnt_group_edit" not in st.session_state:
    st.session_state["cnt_group_edit"] = 0
if "cnt_group_del" not in st.session_state:
    st.session_state["cnt_group_del"] = 0
if "cnt_p_edit" not in st.session_state:
    st.session_state["cnt_p_edit"] = 0
if "cnt_p_del" not in st.session_state:
    st.session_state["cnt_p_del"] = 0

# ==============================================================================
# 狀態檢查：判斷使用者是否已進入特定行程
# ==============================================================================
query_trip = st.query_params.get("trip", "").strip().upper()
if "current_trip" not in st.session_state:
    st.session_state["current_trip"] = query_trip if query_trip else None

current_trip = st.session_state["current_trip"]

# ==============================================================================
# 畫面 A：大廳首頁（2 個方塊選項：新增分帳 vs 加入分帳）
# ==============================================================================
if not current_trip:
    st.markdown("<h2 style='text-align: center; margin-bottom: 2rem;'>✈️ 旅遊即時分帳系統</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6b7280; margin-top: -1.5rem;'>請選擇建立全新旅遊分帳，或輸入好友邀請碼加入！</p>", unsafe_allow_html=True)

    col_create, col_join = st.columns(2)

    # 方塊 1：新增分帳
    with col_create:
        with st.container(border=True):
            st.markdown("### ➕ 新增分帳行程")
            st.caption("由你擔任主揪發起行程，系統將自動產生 7 碼專屬邀請碼！")
            
            with st.form("create_trip_form"):
                new_trip_name = st.text_input("📍 旅程名稱", placeholder="例如：東京五天四夜、澎湖花火節")
                new_admin_pin = st.text_input("🔒 設定管理員密碼（4~6 位數字）", type="password", max_chars=6, help="刪除成員或刪除整本記帳簿需要驗證此密碼")
                creator_name = st.text_input("👤 你的名字（主揪）", placeholder="例如：小明")

                create_submit = st.form_submit_button("✨ 立即建立並產生邀請碼", type="primary", use_container_width=True)

                if create_submit:
                    clean_name = new_trip_name.strip()
                    clean_pin = new_admin_pin.strip()
                    clean_creator = creator_name.strip()

                    if not clean_name:
                        st.toast("❌ 請填寫旅程名稱！", icon="❌")
                    elif not re.fullmatch(r"^\d{4,6}$", clean_pin):
                        st.toast("❌ 管理員密碼必須為 4 ~ 6 位純數字！", icon="❌")
                    elif not clean_creator:
                        st.toast("❌ 請填寫主揪名字！", icon="❌")
                    else:
                        generated_code = generate_invite_code()
                        while get_trip_info(generated_code):
                            generated_code = generate_invite_code()

                        supabase.table("trips").insert({
                            "trip_code": generated_code,
                            "trip_name": clean_name,
                            "admin_pin": clean_pin
                        }).execute()

                        supabase.table("members").insert({
                            "trip_code": generated_code,
                            "name": clean_creator
                        }).execute()

                        log_activity(generated_code, "🚀 建立行程", f"主揪「{clean_creator}」建立了行程「{clean_name}」")

                        st.session_state["current_trip"] = generated_code
                        st.query_params["trip"] = generated_code
                        st.toast(f"🎉 建立成功！專屬邀請碼為：{generated_code}")
                        st.rerun()

    # 方塊 2：加入分帳
    with col_join:
        with st.container(border=True):
            st.markdown("### 🚀 加入現有分帳")
            st.caption("輸入好友分享的 7 碼邀請碼，即可參與共同記帳！")

            join_code_input = st.text_input("🔑 輸入邀請碼 (必填)", value=query_trip, placeholder="例如：ABCD123", max_chars=7).strip().upper()
            
            trip_info = None
            existing_members = []
            if join_code_input:
                trip_info = get_trip_info(join_code_input)
                if trip_info:
                    existing_members = get_members(join_code_input)
                    st.success(f"📍 **旅程：{trip_info['trip_name']}**")
                    if existing_members:
                        st.info(f"👥 **目前已加入的成員：** { '、'.join(existing_members) }")
                    else:
                        st.caption("👥 目前暫無成員。")
                else:
                    st.warning("⚠️ 查無此邀請碼，請確認後重新輸入！")

            with st.form("join_trip_form"):
                join_member_name = st.text_input(
                    "👤 你的成員名稱 (選填)",
                    placeholder="若上方名單已有你的名字，可免填直接進入",
                    help="如果已在上方成員名單中，免填即可直接進入；若為新夥伴，填入名稱將自動加入名單。"
                )
                join_submit = st.form_submit_button("進入分帳系統", type="primary", use_container_width=True)

                if join_submit:
                    if not join_code_input:
                        st.toast("❌ 請輸入邀請碼！", icon="❌")
                    elif not trip_info:
                        st.toast("❌ 邀請碼無效，無法進入！", icon="❌")
                    else:
                        clean_join_name = join_member_name.strip()
                        if clean_join_name and clean_join_name not in existing_members:
                            supabase.table("members").insert({
                                "trip_code": join_code_input,
                                "name": clean_join_name
                            }).execute()
                            log_activity(join_code_input, "➕ 成員加入", f"新成員「{clean_join_name}」加入行程")

                        st.session_state["current_trip"] = join_code_input
                        st.query_params["trip"] = join_code_input
                        st.toast(f"✅ 成功進入「{trip_info['trip_name']}」！")
                        st.rerun()

    st.stop()

# ==============================================================================
# 畫面 B：分帳系統主儀表板
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

# 頂部行程導航列
with st.container(border=True):
    col_t1, col_t2, col_t3 = st.columns([3, 1, 1])
    with col_t1:
        st.markdown(f"### ✈️ {trip_name}")
        st.caption(f"🔑 專屬邀請碼：`{trip_code}` ｜ ⚡ 按鈕執行完成即時更新（背景 30 秒自動同步）")
    with col_t2:
        st.write("")
        if st.button("🔄 立即重新整理", type="primary", use_container_width=True, help="點擊強制自雲端重新抓取最新資料"):
            st.toast("🔄 已即時同步最新帳目！")
            st.rerun()
    with col_t3:
        st.write("")
        if st.button("🚪 離開行程", use_container_width=True):
            st.session_state["current_trip"] = None
            st.session_state["confirm_del_trip"] = False
            st.query_params.clear()
            st.rerun()

# 頂部快捷概覽數據卡片（純整數）
c_metric1, c_metric2, c_metric3 = st.columns(3)
with c_metric1:
    st.metric("📋 行程邀請碼", trip_code)
with c_metric2:
    st.metric("👥 成員總數", f"{len(members)} 位")
with c_metric3:
    st.metric("💵 全團累積總花費", f"${total_trip_expense:,} 元")

st.write("")

# ==================== 側邊欄：配色與成員管理 ====================
with st.sidebar:
    st.markdown("### 🎨 介面與成員管理")
    
    # 1. 質感配色自訂區塊
    with st.container(border=True):
        st.markdown("**🎨 系統色彩主題**")
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

    # 2. 新增成員卡片
    with st.container(border=True):
        st.markdown("**➕ 新增成員**")
        with st.form("add_member_form", clear_on_submit=True):
            new_member = st.text_input("姓名", placeholder="例如：小華")
            add_btn = st.form_submit_button("確認加入", type="primary", use_container_width=True)
            if add_btn:
                clean_name = new_member.strip()
                if clean_name and clean_name not in members:
                    supabase.table("members").insert({"trip_code": trip_code, "name": clean_name}).execute()
                    log_activity(trip_code, "➕ 新增成員", f"新增行程成員「{clean_name}」")
                    st.toast(f"✅ 已成功加入成員：{clean_name}")
                    st.rerun()
                elif clean_name in members:
                    st.toast(f"⚠️ 成員「{clean_name}」已存在於名單中！", icon="⚠️")
                else:
                    st.toast("❌ 成員姓名不能為空白！", icon="❌")

    # 3. 現有成員名單與管理員密碼刪除
    with st.container(border=True):
        st.markdown("**📋 目前成員清單**")
        if members:
            st.info("、".join(members))
            member_to_delete = st.selectbox("選取要刪除的成員：", options=members)
            del_pin_input = st.text_input("🔒 輸入管理員密碼 (4~6位)", type="password", key="input_del_pin", placeholder="建立者設定的密碼")
            
            if st.button("🗑️ 驗證並刪除該成員", type="secondary", use_container_width=True):
                if not del_pin_input.strip():
                    st.toast("❌ 刪除成員需要輸入管理員密碼！", icon="❌")
                elif del_pin_input.strip() != admin_pin:
                    st.toast("❌ 管理員密碼錯誤，拒絕刪除！", icon="❌")
                else:
                    supabase.table("members").delete().eq("trip_code", trip_code).eq("name", member_to_delete).execute()
                    log_activity(trip_code, "🗑️ 刪除成員", f"管理員驗證成功，刪除成員「{member_to_delete}」")
                    st.toast(f"🗑️ 已成功刪除成員：{member_to_delete}")
                    st.rerun()
        else:
            st.warning("尚無成員，請在上方加入！")

    # 4. 刪除整本記帳簿
    with st.container(border=True):
        st.markdown("**⚠️ 危機管理：刪除記帳簿**")
        with st.expander("🚨 刪除此行程帳簿"):
            if st.session_state.get("confirm_del_trip", False):
                st.error("⚠️ **二次確認警告**：此動作將永久抹除本行程的所有成員、全部記帳紀錄與日誌，**絕對無法復原**！確定要刪除全部記帳資訊嗎？")
                c_del_yes, c_del_no = st.columns(2)
                with c_del_yes:
                    if st.button("🚨 確認刪除全部", type="primary", use_container_width=True):
                        supabase.table("expenses").delete().eq("trip_code", trip_code).execute()
                        supabase.table("members").delete().eq("trip_code", trip_code).execute()
                        supabase.table("activity_logs").delete().eq("trip_code", trip_code).execute()
                        supabase.table("trips").delete().eq("trip_code", trip_code).execute()
                        
                        st.session_state["confirm_del_trip"] = False
                        st.session_state["current_trip"] = None
                        st.query_params.clear()
                        st.toast("🗑️ 行程記帳簿已徹底刪除！")
                        st.rerun()
                with c_del_no:
                    if st.button("❌ 放棄取消", use_container_width=True):
                        st.session_state["confirm_del_trip"] = False
                        st.rerun()
            else:
                st.caption("刪除後將無法還原，需要驗證管理員密碼。")
                trip_pin_attempt = st.text_input("🔒 請輸入管理員密碼", type="password", key="del_trip_pin_input", placeholder="4~6位管理員密碼")
                if st.button("驗證密碼並前往下一步", type="secondary", use_container_width=True):
                    if not trip_pin_attempt.strip():
                        st.toast("❌ 請輸入管理員密碼！", icon="❌")
                    elif trip_pin_attempt.strip() != admin_pin:
                        st.toast("❌ 管理員密碼錯誤，拒絕操作！", icon="❌")
                    else:
                        st.session_state["confirm_del_trip"] = True
                        st.rerun()

# ==================== 橫列功能選單 ====================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 記帳明細管理",
    "👤 個人帳務分析",
    "📊 最終結算建議",
    "💱 即時匯率換算",
    "📜 操作紀錄明細"
])

# ==================== Tab 1: 記帳管理與明細 ====================
with tab1:
    with st.container(border=True):
        st.markdown("#### ➕ 快速新增記帳")
        if len(members) < 1:
            st.warning("請先在左側選單新增成員後再開始記帳！")
        else:
            with st.form("add_expense_form", clear_on_submit=True):
                col_name, col_price = st.columns(2)
                with col_name:
                    item_name = st.text_input("消費項目", placeholder="例如：第一天晚餐、包車費")
                with col_price:
                    amount = st.number_input("金額 (NTD / 結算幣別)", min_value=1, step=50, format="%d")

                col_payer, col_splitter = st.columns(2)
                with col_payer:
                    paid_by = st.selectbox("誰先代墊全額？", options=members)
                with col_splitter:
                    split_with = st.multiselect("這筆錢由誰分攤？", options=members, default=members)

                submitted = st.form_submit_button("💾 儲存並同步這筆記帳", type="primary", use_container_width=True)
                if submitted:
                    if not item_name.strip():
                        st.toast("❌ 請填寫消費項目名稱！", icon="❌")
                    elif not split_with:
                        st.toast("❌ 分攤對象不能為空！", icon="❌")
                    else:
                        supabase.table("expenses").insert({
                            "trip_code": trip_code,
                            "item": item_name.strip(),
                            "amount": int(round(amount)),
                            "paid_by": paid_by,
                            "split_members": ",".join(split_with)
                        }).execute()
                        
                        split_str = ", ".join(split_with)
                        log_detail = f"新增「{item_name.strip()}」金額 ${int(round(amount)):,} 元（代墊人：{paid_by}，分攤成員：{split_str}）"
                        log_activity(trip_code, "➕ 新增記帳", log_detail)
                        
                        st.toast(f"💾 記帳成功：{item_name.strip()}！")
                        st.rerun()

    # 明細清單（只篩選顯示團體分攤項目）
    shared_expenses = [e for e in expenses if not is_personal_only(e)]
    sorted_shared = sorted(shared_expenses, key=lambda x: x["id"])
    shared_id_to_seq = {e["id"]: idx + 1 for idx, e in enumerate(sorted_shared)}

    with st.container(border=True):
        st.markdown("#### 📋 團體分攤記錄清單")
        st.caption("💡 提示：若消費僅由代墊人自己全額負擔（無他人分攤），已自動分類至「👤 個人帳務分析」中顯示！")
        
        if shared_expenses:
            exp_data = []
            for e in shared_expenses:
                exp_data.append({
                    "ID": shared_id_to_seq[e["id"]],
                    "記帳時間": format_time(e.get("created_at")),
                    "消費項目": e["item"],
                    "總金額": f"${int(round(float(e['amount']))):,}",
                    "代墊付款人": e["paid_by"],
                    "分攤成員": e["split_members"]
                })
            df_exp = pd.DataFrame(exp_data)
            st.dataframe(df_exp, use_container_width=True, hide_index=True)

            col_edit_card, col_del_card = st.columns(2)
            
            with col_edit_card:
                with st.expander("✏️ 修改已記錄的內容", expanded=False, key=f"exp_group_edit_{st.session_state['cnt_group_edit']}"):
                    edit_id = st.selectbox(
                        "選擇欲修改的項目：",
                        options=[e["id"] for e in shared_expenses],
                        format_func=lambda x: f"編號 #{shared_id_to_seq[x]}：{id_to_exp[x]['item']} (${int(round(float(id_to_exp[x]['amount']))):,})",
                        key="select_edit_id"
                    )
                    target_exp = id_to_exp[edit_id]
                    current_split = [m.strip() for m in target_exp["split_members"].split(",") if m.strip() in members]
                    
                    with st.form("edit_form"):
                        new_item = st.text_input("項目名稱", value=target_exp["item"])
                        new_amount = st.number_input("金額", min_value=1, value=int(round(float(target_exp["amount"]))), step=50, format="%d")
                        paid_index = members.index(target_exp["paid_by"]) if target_exp["paid_by"] in members else 0
                        new_paid_by = st.selectbox("代墊人", options=members, index=paid_index)
                        new_split = st.multiselect("分攤名單", options=members, default=current_split)
                        
                        save_edit = st.form_submit_button("💾 儲存修改", type="primary", use_container_width=True)
                        if save_edit:
                            if not new_item.strip():
                                st.toast("❌ 項目名稱不可為空！", icon="❌")
                            elif not new_split:
                                st.toast("❌ 分攤名單不可為空！", icon="❌")
                            else:
                                supabase.table("expenses").update({
                                    "item": new_item.strip(),
                                    "amount": int(round(new_amount)),
                                    "paid_by": new_paid_by,
                                    "split_members": ",".join(new_split)
                                }).eq("id", edit_id).execute()
                                
                                seq_num = shared_id_to_seq[edit_id]
                                old_info = f"原「{target_exp['item']}」${int(round(float(target_exp['amount']))):,}(墊:{target_exp['paid_by']})"
                                new_info = f"改為「{new_item.strip()}」${int(round(new_amount)):,}(墊:{new_paid_by}，分攤:{', '.join(new_split)})"
                                log_activity(trip_code, "✏️ 修改記帳", f"修改編號 #{seq_num}：{old_info} ➔ {new_info}")
                                
                                st.toast("✏️ 帳目已成功更新！")
                                st.session_state["cnt_group_edit"] += 1
                                st.rerun()

            with col_del_card:
                with st.expander("🗑️ 刪除已記錄的帳目", expanded=False, key=f"exp_group_del_{st.session_state['cnt_group_del']}"):
                    del_id = st.selectbox(
                        "選擇欲刪除的項目：",
                        options=[e["id"] for e in shared_expenses],
                        format_func=lambda x: f"編號 #{shared_id_to_seq[x]}：{id_to_exp[x]['item']} (${int(round(float(id_to_exp[x]['amount']))):,})",
                        key="select_del_id"
                    )
                    if st.button("確認刪除該筆記錄", type="primary", use_container_width=True):
                        seq_num = shared_id_to_seq[del_id]
                        del_item_name = id_to_exp[del_id]['item']
                        del_amt = int(round(float(id_to_exp[del_id]['amount'])))
                        
                        supabase.table("expenses").delete().eq("id", del_id).execute()
                        log_activity(trip_code, "🗑️ 刪除記帳", f"刪除編號 #{seq_num}「{del_item_name}」，金額 ${del_amt:,} 元")
                        
                        st.toast("🗑️ 該筆帳目已成功刪除！")
                        st.session_state["cnt_group_del"] += 1
                        st.rerun()
        else:
            st.info("目前尚無團體分攤紀錄。")

# ==================== Tab 2: 個人即時帳務（全整數化計算） ====================
with tab2:
    if not members:
        st.info("請先新增成員。")
    else:
        with st.container(border=True):
            col_sel, _ = st.columns([1, 2])
            with col_sel:
                selected_user = st.selectbox("請切換你的名字查看：", options=members)
            
            total_paid_by_user = 0
            total_consumed_by_user = 0
            
            group_expenses_list = []
            personal_expenses_list = []

            for e in expenses:
                amt = int(round(float(e["amount"])))
                split_list = [m.strip() for m in e["split_members"].split(",") if m.strip()]
                # 四捨五入至整數，無小數點
                share = int(round(amt / len(split_list))) if split_list else 0

                if e["paid_by"] == selected_user:
                    total_paid_by_user += amt

                if selected_user in split_list:
                    total_consumed_by_user += share

                if is_personal_only(e):
                    if e["paid_by"] == selected_user:
                        personal_expenses_list.append({
                            "raw_id": e["id"],
                            "記帳時間": format_time(e.get("created_at")),
                            "項目名稱": e["item"],
                            "自費金額": f"${amt:,}"
                        })
                else:
                    if selected_user in split_list or e["paid_by"] == selected_user:
                        seq_display = shared_id_to_seq.get(e["id"], "-")
                        group_expenses_list.append({
                            "ID": seq_display,
                            "記帳時間": format_time(e.get("created_at")),
                            "項目": e["item"],
                            "整筆金額": f"${amt:,}",
                            "分攤人數": f"{len(split_list)} 人",
                            "我應負擔": f"${share:,}" if selected_user in split_list else "$0",
                            "代墊人": e["paid_by"]
                        })

            net_balance = total_paid_by_user - total_consumed_by_user

            st.divider()
            c_u1, c_u2, c_u3 = st.columns(3)
            with c_u1:
                st.metric("💰 我先代墊的全額總支出", f"${total_paid_by_user:,}")
            with c_u2:
                st.metric("🍽️ 我個人的實際總消費", f"${total_consumed_by_user:,}")
            with c_u3:
                if net_balance >= 0:
                    st.metric("🟢 我目前應收回（淨額）", f"+${net_balance:,}")
                else:
                    st.metric("🔴 我目前應補繳（淨額）", f"-${abs(net_balance):,}")

        # 個人專屬自費項目
        with st.container(border=True):
            st.markdown(f"#### 🛍️ **{selected_user}** 的個人自費清單（無他人分攤）")
            if personal_expenses_list:
                sorted_personal = sorted(personal_expenses_list, key=lambda x: x["raw_id"])
                p_id_to_seq = {p["raw_id"]: idx + 1 for idx, p in enumerate(sorted_personal)}
                for p in personal_expenses_list:
                    p["ID"] = p_id_to_seq[p["raw_id"]]

                df_personal = pd.DataFrame(personal_expenses_list)
                cols_order = ["ID", "記帳時間", "項目名稱", "自費金額"]
                st.dataframe(df_personal[cols_order], use_container_width=True, hide_index=True)
                
                col_p_edit, col_p_del = st.columns(2)
                with col_p_edit:
                    with st.expander("✏️ 修改個人自費項目", expanded=False, key=f"exp_p_edit_{st.session_state['cnt_p_edit']}"):
                        p_edit_id = st.selectbox(
                            "選取要修改的個人項目：",
                            options=[p["raw_id"] for p in personal_expenses_list],
                            format_func=lambda x: f"編號 #{p_id_to_seq[x]}：{id_to_exp[x]['item']} (${int(round(float(id_to_exp[x]['amount']))):,})",
                            key="p_edit_select"
                        )
                        target_p = id_to_exp[p_edit_id]
                        with st.form("personal_edit_form"):
                            p_new_item = st.text_input("修改名稱", value=target_p["item"])
                            p_new_amt = st.number_input("修改金額", min_value=1, value=int(round(float(target_p["amount"]))), step=50, format="%d")
                            if st.form_submit_button("💾 儲存修改", type="primary", use_container_width=True):
                                if p_new_item.strip():
                                    supabase.table("expenses").update({"item": p_new_item.strip(), "amount": int(round(p_new_amt))}).eq("id", p_edit_id).execute()
                                    seq_num = p_id_to_seq[p_edit_id]
                                    log_activity(trip_code, "✏️ 修改自費", f"{selected_user} 修改個人自費 #{seq_num} 原「{target_p['item']}」➔「{p_new_item.strip()}」${int(round(p_new_amt)):,} 元")
                                    st.toast("✏️ 個人項目已更新！")
                                    st.session_state["cnt_p_edit"] += 1
                                    st.rerun()
                with col_p_del:
                    with st.expander("🗑️ 刪除個人自費項目", expanded=False, key=f"exp_p_del_{st.session_state['cnt_p_del']}"):
                        p_del_id = st.selectbox(
                            "選取要刪除的個人項目：",
                            options=[p["raw_id"] for p in personal_expenses_list],
                            format_func=lambda x: f"編號 #{p_id_to_seq[x]}：{id_to_exp[x]['item']} (${int(round(float(id_to_exp[x]['amount']))):,})",
                            key="p_del_select"
                        )
                        if st.button("確認刪除此個人項目", type="primary", use_container_width=True):
                            seq_num = p_id_to_seq[p_del_id]
                            p_name = id_to_exp[p_del_id]['item']
                            supabase.table("expenses").delete().eq("id", p_del_id).execute()
                            log_activity(trip_code, "🗑️ 刪除自費", f"{selected_user} 刪除個人自費項目 #{seq_num}「{p_name}」")
                            st.toast("🗑️ 已成功刪除該個人項目！")
                            st.session_state["cnt_p_del"] += 1
                            st.rerun()
            else:
                st.info(f"目前尚無 {selected_user} 的個人純自費項目。")

        # 團體分攤明細
        with st.container(border=True):
            st.markdown(f"#### 👥 與 **{selected_user}** 相關的團體分攤明細")
            if group_expenses_list:
                st.dataframe(pd.DataFrame(group_expenses_list), use_container_width=True, hide_index=True)
            else:
                st.info("目前沒有與您相關的團體分攤明細。")

# ==================== Tab 3: 最終結算建議（四捨五入平帳） ====================
with tab3:
    if not expenses or not members:
        st.info("尚無足夠資料進行結算。")
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

        col_bal, col_guide = st.columns([1, 1])

        with col_bal:
            with st.container(border=True):
                st.markdown("#### 📋 各成員應收 / 應付淨額")
                bal_rows = []
                for k, v in balances.items():
                    bal_rows.append({
                        "成員": k,
                        "結算狀態": f"🟢 應收回 +${v:,}" if v >= 0 else f"🔴 應支付 -${abs(v):,}"
                    })
                st.dataframe(pd.DataFrame(bal_rows), use_container_width=True, hide_index=True)

        with col_guide:
            with st.container(border=True):
                st.markdown("#### 💡 最簡還款轉帳指南")
                # 篩選債務人與債權人（整數金額 >= 1）
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
                    st.success("🎉 目前帳目完全平衡，大家互不相欠！")

# ==================== Tab 4: 匯率換算 (台灣銀行) ====================
with tab4:
    bot_rates, bot_status = fetch_bot_rates()
    
    currency_rates_to_twd = {"TWD": 1.0}
    for code, info in bot_rates.items():
        currency_rates_to_twd[code] = info["cash_sell"]

    currency_labels = {
        "TWD": "新台幣 (TWD)", "USD": "美金 (USD)", "JPY": "日幣 (JPY)",
        "THB": "泰銖 (THB)", "KRW": "韓元 (KRW)", "CNY": "人民幣 (CNY)"
    }

    with st.container(border=True):
        st.markdown("#### 🔄 雙向即時匯率換算")
        col_amt, col_from, col_to = st.columns([2, 2, 2])
        
        with col_amt:
            input_amount = st.number_input("金額：", min_value=0, value=1000, step=100, format="%d")
        with col_from:
            from_cur = st.selectbox("幣別 (From)：", options=list(currency_labels.keys()), format_func=lambda x: currency_labels[x], index=0)
        with col_to:
            to_cur = st.selectbox("換算為 (To)：", options=list(currency_labels.keys()), format_func=lambda x: currency_labels[x], index=2)

        twd_amount = input_amount * currency_rates_to_twd[from_cur]
        converted_amount = twd_amount / currency_rates_to_twd[to_cur]

        if to_cur == "TWD":
            st.success(f"💰 **換算結果：** `{input_amount:,}` {currency_labels[from_cur]} ≈ **`{int(round(converted_amount)):,}` {currency_labels[to_cur]}**")
        else:
            st.success(f"💰 **換算結果：** `{input_amount:,}` {currency_labels[from_cur]} ≈ **`{converted_amount:,.2f}` {currency_labels[to_cur]}**")

        if from_cur != to_cur:
            unit_rate = currency_rates_to_twd[from_cur] / currency_rates_to_twd[to_cur]
            st.caption(f"ℹ️ 參考匯率：1 {from_cur} ≈ {unit_rate:.4f} {to_cur}")

    with st.container(border=True):
        st.markdown("#### 📋 台灣銀行牌告牌價")
        st.caption(f"📡 資料來源：{bot_status}")
        table_rows = []
        for code, info in bot_rates.items():
            table_rows.append({
                "幣別代碼": code,
                "幣別名稱": info["name"],
                "現金賣出價 (換現鈔)": f"{info['cash_sell']:.4f} TWD",
                "即期賣出價 (刷卡/轉帳)": f"{info['spot_sell']:.4f} TWD"
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

# ==================== Tab 5: 📜 操作紀錄明細 ====================
with tab5:
    with st.container(border=True):
        st.markdown("#### 📜 系統操作異動紀錄")
        st.caption(f"即時追蹤當前行程（邀請碼：`{trip_code}`）的所有操作行為。")
        
        if logs:
            log_records = []
            for l in logs:
                log_records.append({
                    "異動時間": format_time(l.get("created_at")),
                    "動作類型": l.get("action_type", ""),
                    "詳細異動內容": l.get("details", "")
                })
            df_logs = pd.DataFrame(log_records)
            st.dataframe(df_logs, use_container_width=True, hide_index=True)
            st.caption(f"📊 目前已紀錄最新 {len(log_records)} 筆異動日誌。")
        else:
            st.info("尚無任何操作紀錄。")

# ==================== 30 秒自動靜默同步 ====================
time.sleep(30)
st.rerun()
