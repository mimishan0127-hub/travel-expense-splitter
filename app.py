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

# ==================== 頂部行程導航與狀態儀表板 ====================
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
    st.metric("💵 全團總累積花費", f"${total_trip_expense:,.0f} 元")

st.write("")

# ==================== 側邊欄：成員管理 ====================
with st.sidebar:
    st.markdown("### 👥 成員管理")
    st.caption(f"目前行程：`{trip_code}`")

    # 新增成員卡片
    with st.container(border=True):
        st.markdown("**➕ 新增夥伴**")
        with st.form("add_member_form", clear_on_submit=True):
            new_member = st.text_input("姓名", placeholder="例如：小明")
            add_btn = st.form_submit_button("確認加入", use_container_width=True)
            if add_btn:
                if new_member.strip() and new_member.strip() not in members:
                    supabase.table("members").insert({"trip_code": trip_code, "name": new_member.strip()}).execute()
                    st.success(f"已加入：{new_member}")
                    st.rerun()
                elif new_member.strip() in members:
                    st.warning("此成員已存在！")
                else:
                    st.error("姓名不能為空白！")

    # 成員名單與刪除卡片
    with st.container(border=True):
        st.markdown("**📋 現有成員清單**")
        if members:
            st.info("、".join(members))
            member_to_delete = st.selectbox("選取要刪除的成員：", options=members)
            if st.button("🗑️ 刪除成員", type="secondary", use_container_width=True):
                supabase.table("members").delete().eq("trip_code", trip_code).eq("name", member_to_delete).execute()
                st.success(f"已刪除：{member_to_delete}")
                st.rerun()
        else:
            st.warning("尚未新增任何成員，請先在上方加入！")

# ==================== 橫列功能分頁籤 ====================
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
                    item_name = st.text_input("消費項目", placeholder="例如：第一天晚餐、藥妝店購物")
                with col_price:
                    amount = st.number_input("金額 (NTD / 當地幣別)", min_value=1.0, step=50.0)

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

    # 區塊 2：明細清單卡片
    with st.container(border=True):
        st.markdown("#### 📋 帳目記錄清單")
        if expenses:
            exp_data = []
            for e in expenses:
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

            # 操作卡片：修改與刪除
            col_edit_card, col_del_card = st.columns(2)
            with col_edit_card:
                with st.expander("✏️ 修改已記錄的內容"):
                    edit_id = st.selectbox(
                        "選擇欲修改的項目：",
                        options=[e["id"] for e in expenses],
                        format_func=lambda x: f"ID {x}: {[e['item'] for e in expenses if e['id']==x][0]} (${float([e['amount'] for e in expenses if e['id']==x][0]):,.0f})",
                        key="select_edit_id"
                    )
                    target_exp = [e for e in expenses if e["id"] == edit_id][0]
                    current_split = [m.strip() for m in target_exp["split_members"].split(",") if m.strip() in members]
                    
                    with st.form("edit_form"):
                        new_item = st.text_input("項目名稱", value=target_exp["item"])
                        new_amount = st.number_input("金額", min_value=1.0, value=float(target_exp["amount"]), step=50.0)
                        paid_index = members.index(target_exp["paid_by"]) if target_exp["paid_by"] in members else 0
                        new_paid_by = st.selectbox("代墊人", options=members, index=paid_index)
                        new_split = st.multiselect("分攤名單", options=members, default=current_split)
                        
                        save_edit = st.form_submit_button("儲存修改", use_container_width=True)
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
                with st.expander("🗑️ 刪除帳目"):
                    del_id = st.selectbox(
                        "選擇欲刪除的項目：",
                        options=[e["id"] for e in expenses],
                        format_func=lambda x: f"ID {x}: {[e['item'] for e in expenses if e['id']==x][0]} (${float([e['amount'] for e in expenses if e['id']==x][0]):,.0f})",
                        key="select_del_id"
                    )
                    if st.button("確認刪除該筆記錄", type="primary", use_container_width=True):
                        supabase.table("expenses").delete().eq("id", del_id).execute()
                        st.success("已成功刪除！")
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
        "TWD": "新台幣 (TWD)",
        "USD": "美金 (USD)",
        "JPY": "日幣 (JPY)",
        "THB": "泰銖 (THB)",
        "KRW": "韓元 (KRW)",
        "CNY": "人民幣 (CNY)"
    }

    # 換算計算機卡片
    with st.container(border=True):
        st.markdown("#### 🔄 雙向即時匯率換算")
        col_amt, col_from, col_to = st.columns([2, 2, 2])
        
        with col_amt:
            input_amount = st.number_input("金額：", min_value=0.0, value=1000.0, step=100.0)
        with col_from:
            from_cur = st.selectbox(
                "幣別 (From)：",
                options=list(currency_labels.keys()),
                format_func=lambda x: currency_labels[x],
                index=0
            )
        with col_to:
            to_cur = st.selectbox(
                "換算為 (To)：",
                options=list(currency_labels.keys()),
                format_func=lambda x: currency_labels[x],
                index=2
            )

        twd_amount = input_amount * currency_rates_to_twd[from_cur]
        converted_amount = twd_amount / currency_rates_to_twd[to_cur]

        st.success(
            f"💰 **換算結果：** `{input_amount:,.2f}` {currency_labels[from_cur]} ≈ "
            f"**`{converted_amount:,.2f}` {currency_labels[to_cur]}**"
        )

        if from_cur != to_cur:
            unit_rate = currency_rates_to_twd[from_cur] / currency_rates_to_twd[to_cur]
            st.caption(f"ℹ️ 參考匯率：1 {from_cur} ≈ {unit_rate:.4f} {to_cur}")

    # 台灣銀行牌告資料卡片
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

# ==================== 每 5 秒自動靜默刷新 ====================
time.sleep(5)
st.rerun()
