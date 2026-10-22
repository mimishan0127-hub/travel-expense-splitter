import streamlit as st
from supabase import create_client, Client
import pandas as pd

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
st.markdown("輸入同一組 **行程代碼**，即可與同行好友即時共同編輯與結算！")

# 1. 行程代碼登入
trip_code_input = st.text_input("🔑 請輸入行程代碼（例如：tokyo2026 或 澎湖三天兩夜）", value="okinawa_trip")
trip_code = trip_code_input.strip()

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

members = get_members(trip_code)
expenses = get_expenses(trip_code)

# ==================== 側邊欄：成員管理（新增 & 刪除） ====================
with st.sidebar:
    st.header("👥 成員名單管理")
    st.write(f"目前行程代碼：`{trip_code}`")
    
    # 1. 新增成員
    st.subheader("➕ 新增成員")
    new_member = st.text_input("成員姓名", key="add_member_input")
    if st.button("確認新增"):
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
        st.info("尚無成員，請先新增成員才能開始記帳！")

# 分頁籤
tab1, tab2, tab3 = st.tabs(["📝 記帳管理與明細", "👤 個人即時帳務", "📊 最終結算建議"])

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
                    st.error("分攤對象不能為空，至少要有一人分攤！")
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
        st.dataframe(df
