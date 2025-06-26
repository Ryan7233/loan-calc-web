# streamlit_app.py
import streamlit as st
import math
import re
from datetime import datetime, timedelta

# -------------------------
# Loan Calculation Logic
# -------------------------

def add_months(source_date, months):
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = source_date.day
    try:
        new_date = datetime(year, month, day)
    except ValueError:
        new_date = datetime(year, month + 1, 1) - timedelta(days=1)
    return new_date

def calculate_repayment_plan(principal_cents, annual_rate_percent, total_periods, start_date_str, interest_only_periods=0):
    plan = []
    daily_rate = (annual_rate_percent / 100) / 360
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    last_repayment_date = start_date
    remaining_principal_cents = principal_cents

    for i in range(1, interest_only_periods + 1):
        current_repayment_date = add_months(start_date, i)
        days_in_period = (current_repayment_date - last_repayment_date).days
        interest_per_period = round(principal_cents * daily_rate * days_in_period)
        plan.append({
            "period": i,
            "repayment_date": current_repayment_date.strftime('%Y-%m-%d'),
            "principal": 0,
            "interest": interest_per_period,
            "remaining_principal": principal_cents
        })
        last_repayment_date = current_repayment_date

    equal_periods = total_periods - interest_only_periods
    if equal_periods <= 0:
        return plan

    monthly_rate = (annual_rate_percent / 100) / 12
    power_val = (1 + monthly_rate) ** equal_periods
    monthly_payment = round(remaining_principal_cents * (monthly_rate * power_val) / (power_val - 1))

    for i in range(1, equal_periods + 1):
        current_repayment_date = add_months(last_repayment_date, i - 1)
        next_repayment_date = add_months(last_repayment_date, i)
        days_in_period = (next_repayment_date - current_repayment_date).days

        current_interest_cents = round(remaining_principal_cents * daily_rate * days_in_period)
        current_principal_cents = monthly_payment - current_interest_cents

        if i == equal_periods or remaining_principal_cents < current_principal_cents:
            current_principal_cents = remaining_principal_cents

        remaining_principal_cents -= current_principal_cents

        plan.append({
            "period": i + interest_only_periods,
            "repayment_date": next_repayment_date.strftime('%Y-%m-%d'),
            "principal": current_principal_cents,
            "interest": current_interest_cents,
            "remaining_principal": max(0, remaining_principal_cents)
        })

    return plan

def parse_repayment_method(method_str):
    method_str = method_str.strip()
    match_equal = re.match(r'(\d+)期等额本息', method_str)
    if match_equal:
        return int(match_equal.group(1)), 0
    match_hybrid = re.match(r'前(\d+)后(\d+)', method_str)
    if match_hybrid:
        interest_only = int(match_hybrid.group(1))
        equal = int(match_hybrid.group(2))
        return interest_only + equal, interest_only
    return 0, 0

# -------------------------
# Streamlit UI
# -------------------------

st.set_page_config(page_title="贷款试算工具", layout="wide")
st.title("📊 分期还款计划试算工具")

col1, col2 = st.columns(2)
with col1:
    amount = st.number_input("贷款金额（元）", min_value=1000.0, step=1000.0, value=987000.0)
    rate = st.number_input("年化利率（%）", min_value=0.0, step=0.1, value=7.2)
    method = st.selectbox("还款方式", ["24期等额本息", "前3后21", "前3后12", "前3后3"], index=1)
with col2:
    start_date = st.date_input("起息日", value=datetime.today())

if st.button("📅 开始计算"):
    try:
        total_periods, interest_only_periods = parse_repayment_method(method)
        if total_periods == 0:
            st.error(f"无法解析还款方式: {method}")
        else:
            principal_cents = int(amount * 100)
            plan = calculate_repayment_plan(principal_cents, rate, total_periods, start_date.strftime('%Y-%m-%d'), interest_only_periods)

            if not plan:
                st.warning("计算失败，请检查输入参数")
            else:
                st.success("还款计划如下：")
                st.table([
                    {
                        "期数": p["period"],
                        "还款日": p["repayment_date"],
                        "本金(元)": p["principal"] / 100,
                        "利息(元)": p["interest"] / 100,
                        "剩余本金(元)": p["remaining_principal"] / 100
                    } for p in plan
                ])
    except Exception as e:
        st.error(f"出错了: {e}")