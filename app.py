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

# 1. 行程代碼登入（支援網址參數記憶，手機下拉重新整理不跑掉）
query_trip = st.query_params.get("trip", "okinawa_trip")

col_code, col_sync = st.columns([4, 1])
with col_code:
    trip_code_input = st.text_input("🔑 行程代碼（同行好友輸入相同代碼即可同步）", value=query_trip)
    trip_code = trip_code_input.strip()
    # 同步更新瀏覽器網址參數
    if trip_code != query_trip:
        st.query_params["trip"] = trip_code

with col_sync:
    st.write("") # 排版對齊
    st.write("")
    if st.button("🔄 同步最新資料", use_container_width=True, type="primary"):
        st.rerun()

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

# 讀取成員資料（每次執行直接抓取雲端最新）
def get_members(code):
    res = supabase.table("members").select("name").eq("trip_code", code).execute()
    return [r["name"] for r in res.data]

# 讀取費用資料（每次執行直接抓取雲端最新）
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

# ==================== 側邊欄：成員管理與自動更新 ====================
with st.sidebar:
    st.header("⚙️ 設定與管理")
    st.write(f"目前行程代碼：`{trip_code}`")
    
    # 共同編輯分享連結
    st.info("💡 **好友分享捷徑**：直接將當前網頁網址傳給好友，他們點開就會自動進入這個行程！")

    # 自動同步開關（適合大家坐在一起對帳時開啟）
    auto_sync = st.toggle("⏱️ 開啟自動定時同步", value=False, help="開啟後網頁將每隔數秒自動載入雲端最新資料")
    refresh_rate = 10
    if auto_sync:
        refresh_rate = st.slider("自動同步頻率 (秒)", min_value=5, max_value=30, value=10, step=5)
        st.caption(f"已啟用：每 {refresh_rate} 秒自動更新一次")

    st.divider()

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
                    format_func=lambda x: f"ID {x}: {[e['item'] for e in expenses if e['id']==x][0]} (${[e['amount'] for e in expenses if e['id']==x][0]})",
                    key="select_edit_id"
                )
                target_exp = [e for e in expenses if e["id"] == edit_id][0]
                current_split = [m.strip() for m in target_exp["split_members"].split(",") if m.strip() in members]
                
                with st.form("edit_form"):
                    new_item = st.text_input("修改品項名稱", value=target_exp["item"])
                    new_amount = st.number_input("修改金額", min_value=1.0, value=float(target_exp["amount"]), step=10.0)
                    paid_index = members.index(target_exp["paid_by"]) if target_exp["paid_by"] in members else 0
                    new_paid_by = st.selectbox("修改代墊人", options=members, index=paid_index)
                    new_split = st.multiselect("修改分攤對象", options=members, default=current_split)
                    
                    save_edit = st.form_submit_button("💾 更新帳目資料")
                    if save_edit:
                        if not new_item.strip():
                            st.error("品項名稱不可為空！")
                        elif not new_split:
                            st.error("分攤對象不可為空！")
                        else:
                            supabase.table("expenses").update({
                                "item": new_item.strip(),
                                "amount": new_amount,
                                "paid_by": new_paid_by,
                                "split_members": ",".join(new_split)
                            }).eq("id", edit_id).execute()
                            st.success("帳目已成功更新！")
                            st.rerun()

        # 功能：刪除記帳
        with col_del:
            with st.expander("🗑️ 刪除已記錄的帳目"):
                del_id = st.selectbox(
                    "選擇要刪除的紀錄：",
                    options=[e["id"] for e in expenses],
                    format_func=lambda x: f"ID {x}: {[e['item'] for e in expenses if e['id']==x][0]} (${[e['amount'] for e in expenses if e['id']==x][0]})",
                    key="select_del_id"
                )
                if st.button("確認刪除該筆帳目", type="primary"):
                    supabase.table("expenses").delete().eq("id", del_id).execute()
                    st.success("已成功刪除！")
                    st.rerun()
    else:
        st.info("目前還沒有任何消費記錄。")

# ==================== Tab 2: 個人即時帳務 ====================
with tab2:
    st.subheader("👤 查看個人的即時帳務狀況")
    if not members:
        st.info("請先新增成員。")
    else:
        selected_user = st.selectbox("請選擇你是誰：", options=members)
        
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
                    "時間": format_time(e.get("created_at")),
                    "品項": e["item"],
                    "整筆總額": amt,
                    "分攤人數": len(split_list),
                    "我的負擔份額": round(share, 2),
                    "由誰代墊": e["paid_by"]
                })

        net_balance = total_paid_by_user - total_consumed_by_user

        c1, c2, c3 = st.columns(3)
        c1.metric("💰 我先代墊的全額總支出", f"${total_paid_by_user:,.2f}")
        c2.metric("🍽️ 我實際個人的總消費", f"${total_consumed_by_user:,.2f}")
        if net_balance >= 0:
            c3.metric("🟢 我目前應收回（淨額）", f"+${net_balance:,.2f}")
        else:
            c3.metric("🔴 我目前應補繳（淨額）", f"-${abs(net_balance):,.2f}")

        st.markdown("#### 🔍 與我有關係的消費清單：")
        if user_detailed_expenses:
            st.dataframe(pd.DataFrame(user_detailed_expenses), use_container_width=True)
        else:
            st.info("目前尚無與您相關的消費。")

# ==================== Tab 3: 最終結算建議 ====================
with tab3:
    st.subheader("📊 結算總覽與最簡還款指引")
    if not expenses or not members:
        st.info("資料不足，尚無法結算。")
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

        df_bal = pd.DataFrame([
            {"成員": k, "應收 / 應付 (淨額)": f"+{round(v, 2)}" if v >= 0 else f"{round(v, 2)}"}
            for k, v in balances.items()
        ])
        st.dataframe(df_bal, use_container_width=True)

        st.markdown("#### 💡 最簡轉帳還款方案（誰該給誰多少錢）：")
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
            
            settlements.append(f"👉 **{deb_name}** 應給 **{cred_name}**：`${trans_amt:,.2f}` 元")
            
            debtors[i][1] -= trans_amt
            creditors[j][1] -= trans_amt
            
            if round(debtors[i][1], 2) <= 0.01:
                i += 1
            if round(creditors[j][1], 2) <= 0.01:
                j += 1

        if settlements:
            for s in settlements:
                st.markdown(s)
        else:
            st.success("🎉 目前帳目已完全平衡，大家互不相欠！")

# ==================== Tab 4: 匯率換算 (台灣銀行) ====================
with tab4:
    st.subheader("💱 台灣銀行即時匯率換算")
    bot_rates, bot_status = fetch_bot_rates()
    st.caption(f"📡 資料狀態：{bot_status}（牌告賣出價）")

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

    st.markdown("#### 🔄 雙向即時換算")
    col_amt, col_from, col_to = st.columns([2, 2, 2])
    
    with col_amt:
        input_amount = st.number_input("輸入欲換算金額：", min_value=0.0, value=1000.0, step=100.0)
    with col_from:
        from_cur = st.selectbox(
            "從幣別 (From)：",
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
        st.info(f"ℹ️ 換算參考：1 {from_cur} ≈ {unit_rate:.4f} {to_cur}")

    st.divider()

    st.markdown("#### 📋 台灣銀行最新牌告匯率一覽表")
    table_rows = []
    for code, info in bot_rates.items():
        table_rows.append({
            "幣別代碼": code,
            "幣別名稱": info["name"],
            "現金賣出價 (換現鈔)": f"{info['cash_sell']:.4f} TWD",
            "即期賣出價 (刷卡/轉帳)": f"{info['spot_sell']:.4f} TWD"
        })
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True)

    st.markdown("#### ✈️ 出國血拼常見金額快速對照 (折合台幣)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🇯🇵 10,000 日圓", f"≈ ${10000 * currency_rates_to_twd['JPY']:,.0f} 台幣")
    c2.metric("🇺🇸 100 美元", f"≈ ${100 * currency_rates_to_twd['USD']:,.0f} 台幣")
    c3.metric("🇹🇭 1,000 泰銖", f"≈ ${1000 * currency_rates_to_twd['THB']:,.0f} 台幣")
    c4.metric("🇰🇷 50,000 韓元", f"≈ ${50000 * currency_rates_to_twd['KRW']:,.0f} 台幣")

# ==================== 自動定時同步執行邏輯 ====================
if auto_sync:
    time.sleep(refresh_rate)
    st.rerun()
