import streamlit as st
from supabase import create_client, Client
import pandas as pd
import urllib.request
import csv
import io
import time
from datetime import datetime

# 頁面標題與佈局
st.set_page_config(page_title="旅遊即時分帳系統", page_icon="✈️", layout="wide")

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

# 標題
st.title("✈️ 旅遊分帳與帳務管理系統")

# 1. 行程代碼登入（簡約單列設計，支援網址參數記憶）
query_trip = st.query_params.get("trip", "okinawa_trip")
trip_code_input = st.text_input("🔑 行程代碼（同行好友輸入相同代碼即可同步）", value=query_trip)
trip_code = trip_code_input.strip()

if trip_code != query_trip:
    st.query_params["trip"] = trip_code

if not trip_code:
    st.warning("請先輸入行程代碼以載入資料。")
    st.stop()

# 輔助函式：時間轉換為台灣時間字串
def format_time(ts_str):
    if not ts_str:
        return ""
    try:
        dt = pd.to_datetime(ts_str)
        if dt.tzinfo is None:
            dt = dt.tz_localize("UTC")
        return dt.tz_convert("Asia/Taipei").strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(ts_str)[:16].replace("T", " ")

# 讀取成員資料
def get_members(code):
    res = supabase.table("members").select("name").eq("trip_code", code).execute()
    return [r["name"] for r in res.data]

# 讀取費用資料
def get_expenses(code):
    res = supabase.table("expenses").select("*").eq("trip_code", code).order("id", desc=True).execute()
    return res.data

# 抓取台灣銀行牌告匯率
@st.cache_data(ttl=1800)
def fetch_bot_rates():
    url = "https://rate.bot.com.tw/xrt/flcsv/0/day"
    target_currencies = {
        "USD": "美金 (USD)",
        "JPY": "日幣 (JPY)",
        "THB": "泰銖 (THB)",
        "KRW": "韓元 (KRW)",
        "CNY": "人民幣 (CNY)"
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
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
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

members = get_members(trip_code)
expenses = get_expenses(trip_code)

# ==================== 側邊欄：成員管理 ====================
with st.sidebar:
    st.header("👥 成員管理")
    st.caption(f"目前行程代碼：`{trip_code}`")
    st.caption("⚡ 系統已啟動每 5 秒自動靜默同步")

    # 1. 新增成員（表單包裝，防止定時刷新中斷打字）
    st.subheader("➕ 新增成員")
    with st.form("add_member_form", clear_on_submit=True):
        new_member = st.text_input("成員姓名")
        add_btn = st.form_submit_button("確認新增")
        if add_btn:
            if new_member.strip() and new_member.strip() not in members:
                supabase.table("members").insert({"trip_code": trip_code, "name": new_member.strip()}).execute()
                st.success(f"已加入：{new_member}")
                st.rerun()
            elif new_member.strip() in members:
                st.warning("此成員已存在！")
            else:
                st.error("姓名不能為空白！")

    st.divider()

    # 2. 目前成員與刪除成員
    st.subheader("📋 目前成員")
    if members:
        st.write("、".join(members))
        member_to_delete = st.selectbox("選擇要刪除的成員：", options=members)
        if st.button("🗑️ 刪除該成員", type="secondary"):
            supabase.table("members").delete().eq("trip_code", trip_code).eq("name", member_to_delete).execute()
            st.success(f"已刪除成員：{member_to_delete}")
            st.rerun()
    else:
        st.info("尚無成員，請先新增成員！")

# ==================== 橫列式功能選單 (Tabs) ====================
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 記帳管理與明細",
    "👤 個人即時帳務",
    "📊 最終結算建議",
    "💱 匯率換算 (台灣銀行)"
])

# ==================== Tab 1: 記帳管理與明細 ====================
with tab1:
    st.subheader("新增一筆消費")
    if len(members) < 1:
        st.warning("請先在左側選單新增至少一位成員！")
    else:
        with st.form("add_expense_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                item_name = st.text_input("品項名稱（如：第一天晚餐、包車費）")
                amount = st.number_input("金額 (NTD / 結算幣別)", min_value=1.0, step=10.0)
            with col2:
                paid_by = st.selectbox("誰先全額墊付？", options=members)
                split_with = st.multiselect("這筆錢由誰分攤？", options=members, default=members)

            submitted = st.form_submit_button("💾 儲存這筆帳目")
            if submitted:
                if not item_name.strip():
                    st.error("請填寫品項名稱！")
                elif not split_with:
                    st.error("分攤對象不能為空！")
                else:
                    supabase.table("expenses").insert({
                        "trip_code": trip_code,
                        "item": item_name.strip(),
                        "amount": amount,
                        "paid_by": paid_by,
                        "split_members": ",".join(split_with)
                    }).execute()
                    st.success("記帳成功！")
                    st.rerun()

    st.divider()
    st.subheader("📋 記帳明細清單")
    if expenses:
        exp_data = []
        for e in expenses:
            exp_data.append({
                "ID": e["id"],
                "記帳時間": format_time(e.get("created_at")),
                "消費品項": e["item"],
                "總金額": e["amount"],
                "代墊人": e["paid_by"],
                "分攤對象": e["split_members"]
            })
        df_exp = pd.DataFrame(exp_data)
        st.dataframe(df_exp, use_container_width=True)

        col_edit, col_del = st.columns(2)

        # 功能：修改記帳
        with col_edit:
            with st.expander("✏️ 修改已記錄的帳目內容"):
                edit_id = st.selectbox(
                    "選擇要修改的紀錄：",
                    options=[e["id"] for e in expenses],
                    format_func=lambda x: f
