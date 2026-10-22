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

# ==================== 5 種精緻質感配色（主色按鈕 + 同色系柔霧標籤） ====================
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

# 確保主題狀態初始化
if "theme_name" not in st.session_state:
    st.session_state["theme_name"] = "🌿 莫蘭迪鼠尾草綠"

current_theme = THEMES[st.session_state["theme_name"]]

# 注入最高權重 CSS：全面覆蓋按鈕與人名標籤樣式
st.markdown(f"""
<style>
/* 1. 主按鈕（包含普通 primary 與 form_submit_button） */
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

/* 2. 次要按鈕樣式 */
html body button[data-testid*="secondary"],
html body button[data-testid="baseButton-secondary"],
html body button[data-testid="stBaseButton-secondary"] {{
    border-radius: 8px !important;
}}

/* 3. 分頁籤選取時的底線與文字顏色 */
html body button[data-testid="stTab"][aria-selected="true"] {{
    color: {current_theme['primary']} !important;
    border-bottom: 2px solid {current_theme['primary']} !important;
}}

/* 4. 卡片懸停高亮邊框 */
html body div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
    border-color: {current_theme['primary']} !important;
    box-shadow: 0 2px 8px {current_theme['light']} !important;
    transition: all 0.2s ease-in-out;
}}

/* 5. 人名標籤 (st.multiselect tags)：覆蓋所有可能標籤元件 */
div[data-testid="stMultiSelect"] {{
    --primary-color: {current_theme['tag_bg']} !important;
}}

html body div[data-testid="stMultiSelect"] [data-baseweb="tag"],
html body div[data-testid="stMultiSelect"] [data-testid*="tag"],
html body div[data-testid="stMultiSelect"] [data-testid*="Tag"],
html body div[data-testid="stMultiSelect"] span:has(svg),
html body div[data-testid="stMultiSelect"] div:has(> svg):has(span),
html body div[data-testid="stMultiSelect"] [class*="multiValue"],
html body div[data-testid="stMultiSelect"] [class*="MultiValue"] {{
    background-color: {current_theme['tag_bg']} !important;
    background: {current_theme['tag_bg']} !important;
    border: 1px solid {current_theme['tag_border']} !important;
    border-radius: 6px !important;
    padding: 2px 6px !important;
}}

/* 標籤文字顏色 */
html body div[data-testid="stMultiSelect"] [data-baseweb="tag"] span,
html body div[data-testid="stMultiSelect"] [data-testid*="tag"] span,
html body div[data-testid="stMultiSelect"] span:has(svg) span,
html body div[data-testid="stMultiSelect"] div:has(> svg):has(span) span {{
    color: {current_theme['tag_text']} !important;
    font-weight: 600 !important;
}}

/* 標籤關閉按鈕 (X) 圖示顏色 */
html body div[data-testid="stMultiSelect"] [data-baseweb="tag"] svg,
html body div[data-testid="stMultiSelect"] [data-testid*="tag"] svg,
html body div[data-testid="stMultiSelect"] span:has(svg) svg,
html body div[data-testid="stMultiSelect"] div:has(> svg):has(span) svg,
html body div[data-testid="stMultiSelect"] span:has(svg) svg path,
html body div[data-testid="stMultiSelect"] div:has(> svg):has(span) svg path {{
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

# 判斷是否為「個人全額付款且無分攤」的自費項目
def is_personal_only(expense):
    split_list = [m.strip() for m in expense.get("split_members", "").split(",") if m.strip()]
    return len(split_list) == 1 and split_list[0] == expense.get("paid_by")

# 讀取資料
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
    st.metric("💵 全團累積總花費", f"${total_trip_expense:,.0f} 元")

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

    # 區塊 2：明細清單（只篩選顯示團體分攤項目，純個人自費自動隱藏）
    shared_expenses = [e for e in expenses if not is_personal_only(e)]

    with st.container(border=True):
        st.markdown("#### 📋 團體分攤記錄清單")
        st.caption("💡 提示：若消費僅由代墊人自己全額負擔（無他人分攤），已自動分類至「👤 個人帳務分析」中顯示，確保第一頁公帳簡潔！")
        
        if shared_expenses:
            exp_data = []
            for e in shared_expenses:
                exp_data.append({
                    "ID": e["id"],
                    "記帳時間": format_time(e.get("created_at")),
                    "消費項目": e["item"],
                    "總金額": f"${float(e['amount']):,.0f}",
                    "代墊付款人": e["paid_by"],
                    "分攤成員": e["split_members"]
                })
            df_exp = pd.DataFrame(exp_data)
            st.dataframe(df_exp, use_container_width=True, hide_index=True)

            # 下方獨立操作區塊：修改與刪除
            col_edit_card, col_del_card = st.columns(2)
            
            with col_edit_card:
                with st.expander("✏️ 修改已記錄的內容"):
                    edit_id = st.selectbox(
                        "選擇欲修改的項目：",
                        options=[e["id"] for e in shared_expenses],
                        format_func=lambda x: f"ID {x}: {[e['item'] for e in shared_expenses if e['id']==x][0]} (${float([e['amount'] for e in shared_expenses if e['id']==x][0]):,.0f})",
                        key="select_edit_id"
                    )
                    target_exp = [e for e in shared_expenses if e["id"] == edit_id][0]
                    current_split = [m.strip() for m in target_exp["split_members"].split(",") if m.strip() in members]
                    
                    with st.form("edit_form"):
                        new_item = st.text_input("項目名稱", value=target_exp["item"])
                        new_amount = st.number_input("金額", min_value=1.0, value=float(target_exp["amount"]), step=50.0)
                        paid_index = members.index(target_exp["paid_by"]) if target_exp["paid_by"] in members else 0
                        new_paid_by = st.selectbox("代墊人", options=members, index=paid_index)
                        new_split = st.multiselect("分攤名單", options=members, default=current_split)
                        
                        save_edit = st.form_submit_button("💾 儲存修改", type="primary", use_container_width=True)
                        if save_edit:
                            if not new_item.strip():
                                st.error("項目名稱不可為空！")
                            elif not new_split:
                                st.error("分攤名單不可為空！")
                            else:
                                supabase.table("expenses").update({
                                    "item": new_item.strip(),
                                    "amount": new_amount,
                                    "paid_by": new_paid_by,
                                    "split_members": ",".join(new_split)
                                }).eq("id", edit_id).execute()
                                st.success("帳目已更新！")
                                st.rerun()

            with col_del_card:
                with st.expander("🗑️ 刪除已記錄的帳目"):
                    del_id = st.selectbox(
                        "選擇欲刪除的項目：",
                        options=[e["id"] for e in shared_expenses],
                        format_func=lambda x: f"ID {x}: {[e['item'] for e in shared_expenses if e['id']==x][0]} (${float([e['amount'] for e in shared_expenses if e['id']==x][0]):,.0f})",
                        key="select_del_id"
                    )
                    if st.button("確認刪除該筆記錄", type="primary", use_container_width=True):
                        supabase.table("expenses").delete().eq("id", del_id).execute()
                        st.success("已成功刪除！")
                        st.rerun()
        else:
            st.info("目前尚無團體分攤紀錄。")

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
            
            group_expenses_list = []      # 團體分攤明細
            personal_expenses_list = []   # 純個人自費明細

            for e in expenses:
                amt = float(e["amount"])
                split_list = [m.strip() for m in e["split_members"].split(",") if m.strip()]
                share = amt / len(split_list) if split_list else 0

                # 若是當事人付款
                if e["paid_by"] == selected_user:
                    total_paid_by_user += amt

                # 若當事人有分攤
                if selected_user in split_list:
                    total_consumed_by_user += share

                # 分流判斷：純個人自費 vs 團體分攤
                if is_personal_only(e):
                    if e["paid_by"] == selected_user:
                        personal_expenses_list.append({
                            "ID": e["id"],
                            "記帳時間": format_time(e.get("created_at")),
                            "項目名稱": e["item"],
                            "自費金額": f"${amt:,.0f}"
                        })
                else:
                    if selected_user in split_list or e["paid_by"] == selected_user:
                        group_expenses_list.append({
                            "記帳時間": format_time(e.get("created_at")),
                            "項目": e["item"],
                            "整筆金額": f"${amt:,.0f}",
                            "分攤人數": f"{len(split_list)} 人",
                            "我應負擔": f"${share:,.2f}" if selected_user in split_list else "$0.00",
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

        # 區塊 A：個人專屬自費項目（第一頁不顯示，直接在此呈現）
        with st.container(border=True):
            st.markdown(f"#### 🛍️ **{selected_user}** 的個人自費清單（無他人分攤）")
            if personal_expenses_list:
                df_personal = pd.DataFrame(personal_expenses_list)
                st.dataframe(df_personal.drop(columns=["ID"]), use_container_width=True, hide_index=True)
                
                # 個人自費修改與刪除
                col_p_edit, col_p_del = st.columns(2)
                with col_p_edit:
                    with st.expander("✏️ 修改個人自費項目"):
                        p_edit_id = st.selectbox(
                            "選取要修改的個人項目：",
                            options=[p["ID"] for p in personal_expenses_list],
                            format_func=lambda x: f"{[p['項目名稱'] for p in personal_expenses_list if p['ID']==x][0]} ({[p['自費金額'] for p in personal_expenses_list if p['ID']==x][0]})",
                            key="p_edit_select"
                        )
                        target_p = [e for e in expenses if e["id"] == p_edit_id][0]
                        with st.form("personal_edit_form"):
                            p_new_item = st.text_input("修改名稱", value=target_p["item"])
                            p_new_amt = st.number_input("修改金額", min_value=1.0, value=float(target_p["amount"]), step=50.0)
                            if st.form_submit_button("儲存修改", type="primary", use_container_width=True):
                                if p_new_item.strip():
                                    supabase.table("expenses").update({"item": p_new_item.strip(), "amount": p_new_amt}).eq("id", p_edit_id).execute()
                                    st.success("已更新！")
                                    st.rerun()
                with col_p_del:
                    with st.expander("🗑️ 刪除個人自費項目"):
                        p_del_id = st.selectbox(
                            "選取要刪除的個人項目：",
                            options=[p["ID"] for p in personal_expenses_list],
                            format_func=lambda x: f"{[p['項目名稱'] for p in personal_expenses_list if p['ID']==x][0]} ({[p['自費金額'] for p in personal_expenses_list if p['ID']==x][0]})",
                            key="p_del_select"
                        )
                        if st.button("確認刪除此個人項目", type="primary", use_container_width=True):
                            supabase.table("expenses").delete().eq("id", p_del_id).execute()
                            st.success("已成功刪除！")
                            st.rerun()
            else:
                st.info(f"目前尚無 {selected_user} 的個人純自費項目。")

        # 區塊 B：參與的團體分攤明細
        with st.container(border=True):
            st.markdown(f"#### 👥 與 **{selected_user}** 相關的團體分攤明細")
            if group_expenses_list:
                st.dataframe(pd.DataFrame(group_expenses_list), use_container_width=True, hide_index=True)
            else:
                st.info("目前沒有與您相關的團體分攤明細。")

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

# ==================== 自動每 5 秒靜默刷新 ====================
time.sleep(5)
st.rerun()
