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

# ==================== 5 種質感配色定義 ====================
THEMES = {
    "🌿 莫蘭迪鼠尾草綠": {
        "primary": "#4A6B5D",
        "hover": "#3B574A",
        "light": "#EBF2EE"
    },
    "🍂 暖陽焦糖陶土": {
        "primary": "#C86D51",
        "hover": "#A8543A",
        "light": "#FAF0EC"
    },
    "🌊 深海暮靄靛藍": {
        "primary": "#3B5A75",
        "hover": "#2C445A",
        "light": "#EDF3F7"
    },
    "🌸 霧面煙燻胭粉": {
        "primary": "#B35D67",
        "hover": "#964650",
        "light": "#F8ECEE"
    },
    "🌑 黑曜玄武岩灰": {
        "primary": "#2C302E",
        "hover": "#1A1C1B",
        "light": "#EFEFEF"
    }
}

# 預設主題
if "selected_theme" not in st.session_state:
    st.session_state["selected_theme"] = "🌿 莫蘭迪鼠尾草綠"

current_theme = THEMES[st.session_state["selected_theme"]]

# 動態注入自訂質感 CSS
st.markdown(f"""
<style>
/* 主按鈕顏色與圓角 */
button[kind="primary"], .stButton > button[kind="primary"] {{
    background-color: {current_theme['primary']} !important;
    border-color: {current_theme['primary']} !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease-in-out;
}}
button[kind="primary"]:hover {{
    background-color: {current_theme['hover']} !important;
    border-color: {current_theme['hover']} !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
}}

/* 次要按鈕樣式 */
button[kind="secondary"], .stButton > button[kind="secondary"] {{
    border-radius: 8px !important;
    font-weight: 500 !important;
}}

/* 滑鼠懸停卡片外框高亮 */
div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
    border-color: {current_theme['primary']} !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    transition: all 0.2s ease-in-out;
}}

/* 緊湊化表單與輸入框留白（縮減高度） */
div[data-testid="stForm"] {{
    padding: 0.6rem 0.9rem !important;
    border-radius: 10px !important;
}}
div[data-testid="stForm"] .stTextInput, 
div[data-testid="stForm"] .stNumberInput, 
div[data-testid="stForm"] .stSelectbox, 
div[data-testid="stForm"] .stMultiSelect {{
    margin-bottom: -0.3rem !important;
}}

/* 標籤小巧化 */
div[data-testid="stForm"] label {{
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: #4b5563 !important;
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

# 讀取資料函式
def get_members(code):
    res = supabase.table("members").select("name").eq("trip_code", code).execute()
    return [r["name"] for r in res.data]

def get_expenses(code):
    res = supabase.table("expenses").select("*").eq("trip_code", code).order("id", desc=True).execute()
    return res.data

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

# 狀態管理
if "edit_id" not in st.session_state:
    st.session_state["edit_id"] = None
if "delete_id" not in st.session_state:
    st.session_state["delete_id"] = None

# ==================== 確保存檔後 100% 消失的回呼函式 (Callbacks) ====================
def on_save_edit(exp_id):
    item = st.session_state.get(f"edit_item_{exp_id}", "").strip()
    amount = float(st.session_state.get(f"edit_amt_{exp_id}", 1.0))
    paid_by = st.session_state.get(f"edit_paid_{exp_id}")
    split_list = st.session_state.get(f"edit_split_{exp_id}", [])
    
    if item and split_list:
        supabase.table("expenses").update({
            "item": item,
            "amount": amount,
            "paid_by": paid_by,
            "split_members": ",".join(split_list)
        }).eq("id", exp_id).execute()
        # 強制在重新渲染前重設狀態
        st.session_state["edit_id"] = None

def on_cancel_edit():
    st.session_state["edit_id"] = None

def on_confirm_delete(exp_id):
    supabase.table("expenses").delete().eq("id", exp_id).execute()
    st.session_state["delete_id"] = None

def on_cancel_delete():
    st.session_state["delete_id"] = None

# ==================== 頂部行程導航與儀表板 ====================
query_trip = st.query_params.get("trip", "okinawa_trip")

with st.container(border=True):
    col_title, col_input = st.columns([2, 1])
    with col_title:
        st.markdown("### ✈️ 旅遊分帳系統")
        st.caption("⚡ 雲端資料庫已連線 ｜ 每 5 秒自動靜默同步")
    with col_input:
        trip_code_input = st.text_input("🔑 行程代碼", value=query_trip, label_visibility="collapsed", placeholder="輸入行程代碼")
        trip_code = trip_code_input.strip()

if trip_code != query_trip:
    st.query_params["trip"] = trip_code

if not trip_code:
    st.warning("請先輸入行程代碼以載入資料。")
    st.stop()

members = get_members(trip_code)
expenses = get_expenses(trip_code)
total_trip_expense = sum(float(e["amount"]) for e in expenses)

# 頂部快捷概覽卡片
c_metric1, c_metric2, c_metric3 = st.columns(3)
with c_metric1:
    st.metric("📋 行程代碼", trip_code)
with c_metric2:
    st.metric("👥 成員總數", f"{len(members)} 位")
with c_metric3:
    st.metric("💵 全團總花費", f"${total_trip_expense:,.0f} 元")

st.write("")

# ==================== 側邊欄：配色與成員管理 ====================
with st.sidebar:
    st.markdown("### 🎨 介面與成員管理")
    
    # 1. 質感配色自訂區塊
    with st.container(border=True):
        st.markdown("**🎨 系統按鈕配色**")
        chosen_theme = st.selectbox(
            "選擇主題色調：",
            options=list(THEMES.keys()),
            index=list(THEMES.keys()).index(st.session_state["selected_theme"]),
            label_visibility="collapsed"
        )
        if chosen_theme != st.session_state["selected_theme"]:
            st.session_state["selected_theme"] = chosen_theme
            st.rerun()

    # 2. 新增成員卡片
    with st.container(border=True):
        st.markdown("**➕ 新增成員**")
        with st.form("add_member_form", clear_on_submit=True):
            new_member = st.text_input("姓名", placeholder="例如：小明")
            add_btn = st.form_submit_button("確認加入", type="primary", use_container_width=True)
            if add_btn:
                if new_member.strip() and new_member.strip() not in members:
                    supabase.table("members").insert({"trip_code": trip_code, "name": new_member.strip()}).execute()
                    st.success(f"已加入：{new_member}")
                    st.rerun()
                elif new_member.strip() in members:
                    st.warning("此成員已存在！")
                else:
                    st.error("姓名不能為空白！")

    # 3. 現有成員名單與刪除
    with st.container(border=True):
        st.markdown("**📋 目前成員清單**")
        if members:
            st.info("、".join(members))
            member_to_delete = st.selectbox("選取要刪除的成員：", options=members)
            if st.button("🗑️ 刪除該成員", type="secondary", use_container_width=True):
                supabase.table("members").delete().eq("trip_code", trip_code).eq("name", member_to_delete).execute()
                st.success(f"已刪除：{member_to_delete}")
                st.rerun()
        else:
            st.warning("尚無成員，請在上方加入！")

# ==================== 橫列功能選單 ====================
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 記帳明細管理",
    "👤 個人帳務分析",
    "📊 最終結算建議",
    "💱 即時匯率換算"
])

# ==================== Tab 1: 記帳管理與明細 ====================
with tab1:
    # 區塊 1：新增記帳卡片
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
                    amount = st.number_input("金額 (NTD / 結算幣別)", min_value=1.0, step=50.0)

                col_payer, col_splitter = st.columns(2)
                with col_payer:
                    paid_by = st.selectbox("誰先代墊全額？", options=members)
                with col_splitter:
                    split_with = st.multiselect("這筆錢由誰分攤？", options=members, default=members)

                submitted = st.form_submit_button("💾 儲存並同步這筆記帳", type="primary", use_container_width=True)
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

    # 區塊 2：動態互動清單
    with st.container(border=True):
        st.markdown("#### 📋 帳目記錄清單（點擊右側 ✏️ 可直接原地修改）")
        if expenses:
            for e in expenses:
                # 情況 A：正在行內編輯該筆（2x2 緊湊雙列佈局，大幅減少高度）
                if st.session_state["edit_id"] == e["id"]:
                    with st.container(border=True):
                        st.markdown(f"✏️ **修改帳目：{e['item']}**")
                        current_split = [m.strip() for m in e["split_members"].split(",") if m.strip() in members]
                        paid_idx = members.index(e["paid_by"]) if e["paid_by"] in members else 0
                        
                        with st.form(f"inline_edit_{e['id']}"):
                            # 第 1 列：項目名稱 + 金額
                            r1_col1, r1_col2 = st.columns([3, 2])
                            with r1_col1:
                                st.text_input("項目名稱", value=e["item"], key=f"edit_item_{e['id']}")
                            with r1_col2:
                                st.number_input("金額", min_value=1.0, value=float(e["amount"]), step=50.0, key=f"edit_amt_{e['id']}")
                            
                            # 第 2 列：代墊人 + 分攤成員
                            r2_col1, r2_col2 = st.columns([2, 3])
                            with r2_col1:
                                st.selectbox("代墊人", options=members, index=paid_idx, key=f"edit_paid_{e['id']}")
                            with r2_col2:
                                st.multiselect("分攤名單", options=members, default=current_split, key=f"edit_split_{e['id']}")
                            
                            # 第 3 列：按鈕
                            st.write("")
                            c_sv, c_cl = st.columns(2)
                            with c_sv:
                                st.form_submit_button(
                                    "💾 儲存更新",
                                    type="primary",
                                    use_container_width=True,
                                    on_click=on_save_edit,
                                    args=(e["id"],)
                                )
                            with c_cl:
                                st.form_submit_button(
                                    "❌ 取消",
                                    use_container_width=True,
                                    on_click=on_cancel_edit
                                )

                # 情況 B：正在確認刪除該筆
                elif st.session_state["delete_id"] == e["id"]:
                    with st.container(border=True):
                        st.warning(f"⚠️ 確定要刪除 **{e['item']}**（金額：${float(e['amount']):,.0f} 元）嗎？")
                        c_yes, c_no = st.columns(2)
                        with c_yes:
                            st.button(
                                "🗑️ 確認永久刪除",
                                key=f"conf_del_{e['id']}",
                                type="primary",
                                use_container_width=True,
                                on_click=on_confirm_delete,
                                args=(e["id"],)
                            )
                        with c_no:
                            st.button(
                                "取消",
                                key=f"cancel_del_{e['id']}",
                                use_container_width=True,
                                on_click=on_cancel_delete
                            )

                # 情況 C：平時正常顯示的卡片
                else:
                    with st.container(border=True):
                        col_info, col_price, col_actions = st.columns([4, 1.5, 1.1])
                        with col_info:
                            st.markdown(f"**{e['item']}**")
                            st.caption(f"🕒 {format_time(e.get('created_at'))} ｜ 墊付：**{e['paid_by']}** ｜ 分攤：{e['split_members']}")
                        with col_price:
                            st.markdown(f"### ${float(e['amount']):,.0f}")
                        with col_actions:
                            b1, b2 = st.columns(2)
                            with b1:
                                if st.button("✏️", key=f"btn_edit_{e['id']}", help="修改此筆", use_container_width=True):
                                    st.session_state["edit_id"] = e["id"]
                                    st.session_state["delete_id"] = None
                                    st.rerun()
                            with b2:
                                if st.button("🗑️", key=f"btn_del_{e['id']}", help="刪除此筆", use_container_width=True):
                                    st.session_state["delete_id"] = e["id"]
                                    st.session_state["edit_id"] = None
                                    st.rerun()
        else:
            st.info("目前尚無消費紀錄。")

# ==================== Tab 2: 個人即時帳務 ====================
with tab2:
    if not members:
        st.info("請先新增成員。")
    else:
        with st.container(border=True):
            col_sel, _ = st.columns([1, 2])
            with col_sel:
                selected_user = st.selectbox("請切換你的名字查看：", options=members)
            
            total_paid_by_user = 0.0
            total_consumed_by_user = 0.0
            user_detailed_expenses = []

            for e in expenses:
                amt = float(e["amount"])
                split_list = [m.strip() for m in e["split_members"].split(",") if m.strip()]
                share = amt / len(split_list) if split_list else 0

                if e["paid_by"] == selected_user:
                    total_paid_by_user += amt

                if selected_user in split_list:
                    total_consumed_by_user += share
                    user_detailed_expenses.append({
                        "記帳時間": format_time(e.get("created_at")),
                        "項目": e["item"],
                        "整筆金額": f"${amt:,.0f}",
                        "分攤人數": f"{len(split_list)} 人",
                        "我應負擔": f"${share:,.2f}",
                        "代墊人": e["paid_by"]
                    })

            net_balance = total_paid_by_user - total_consumed_by_user

            st.divider()
            c_u1, c_u2, c_u3 = st.columns(3)
            with c_u1:
                st.metric("💰 我先代墊的全額總支出", f"${total_paid_by_user:,.2f}")
            with c_u2:
                st.metric("🍽️ 我個人的實際總消費", f"${total_consumed_by_user:,.2f}")
            with c_u3:
                if net_balance >= 0:
                    st.metric("🟢 我目前應收回（淨額）", f"+${net_balance:,.2f}")
                else:
                    st.metric("🔴 我目前應補繳（淨額）", f"-${abs(net_balance):,.2f}")

        with st.container(border=True):
            st.markdown(f"#### 🔍 與 **{selected_user}** 相關的消費明細")
            if user_detailed_expenses:
                st.dataframe(pd.DataFrame(user_detailed_expenses), use_container_width=True, hide_index=True)
            else:
                st.info("目前沒有與您相關的消費明細。")

# ==================== Tab 3: 最終結算建議 ====================
with tab3:
    if not expenses or not members:
        st.info("尚無足夠資料進行結算。")
    else:
        balances = {m: 0.0 for m in members}
        for e in expenses:
            amt = float(e["amount"])
            split_list = [m.strip() for m in e["split_members"].split(",") if m.strip()]
            share = amt / len(split_list) if split_list else 0
            
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
                        "結算狀態": f"🟢 應收回 +${v:,.2f}" if v >= 0 else f"🔴 應支付 -${abs(v):,.2f}"
                    })
                st.dataframe(pd.DataFrame(bal_rows), use_container_width=True, hide_index=True)

        with col_guide:
            with st.container(border=True):
                st.markdown("#### 💡 最簡還款轉帳指南")
                debtors = []
                creditors = []
                for m, b in balances.items():
                    if round(b, 2) < -0.01:
                        debtors.append([m, -b])
                    elif round(b, 2) > 0.01:
                        creditors.append([m, b])

                settlements = []
                i, j = 0, 0
                while i < len(debtors) and j < len(creditors):
                    deb_name, deb_amt = debtors[i]
                    cred_name, cred_amt = creditors[j]
                    trans_amt = min(deb_amt, cred_amt)
                    
                    settlements.append(f"👉 **{deb_name}** 轉帳給 **{cred_name}**：`{trans_amt:,.2f}` 元")
                    
                    debtors[i][1] -= trans_amt
                    creditors[j][1] -= trans_amt
                    
                    if round(debtors[i][1], 2) <= 0.01:
                        i += 1
                    if round(creditors[j][1], 2) <= 0.01:
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
            input_amount = st.number_input("金額：", min_value=0.0, value=1000.0, step=100.0)
        with col_from:
            from_cur = st.selectbox("幣別 (From)：", options=list(currency_labels.keys()), format_func=lambda x: currency_labels[x], index=0)
        with col_to:
            to_cur = st.selectbox("換算為 (To)：", options=list(currency_labels.keys()), format_func=lambda x: currency_labels[x], index=2)

        twd_amount = input_amount * currency_rates_to_twd[from_cur]
        converted_amount = twd_amount / currency_rates_to_twd[to_cur]

        st.success(f"💰 **換算結果：** `{input_amount:,.2f}` {currency_labels[from_cur]} ≈ **`{converted_amount:,.2f}` {currency_labels[to_cur]}**")

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

# ==================== 自動定時靜默同步 ====================
# 當使用者正在進行行內編輯或確認刪除時，自動暫停定時重整，避免打字被中斷
is_user_busy = (st.session_state["edit_id"] is not None) or (st.session_state["delete_id"] is not None)
if not is_user_busy:
    time.sleep(5)
    st.rerun()
