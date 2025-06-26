import csv
import io
import math
import re
from datetime import datetime, timedelta

# ==============================================================================
# --- 贷款试算输入区 ---
# 您每次需要试算时，只需修改下面的参数即可。
# ==============================================================================

# 请输入贷款金额 (单位：元)
LOAN_AMOUNT_YUAN = 550000.00

# 请输入年化利率 (例如: 9.0, 7.2 等)
ANNUAL_RATE_PERCENT = 9.0

# 请输入还款方式 (格式: "24期等额本息" 或 "前3后21", "前3后12" 等)
REPAYMENT_METHOD_STR = "24期等额本息"

# 请输入起息日 (格式: "YYYYMMDD")
START_DATE_STR = "20250611"


# ==============================================================================
# --- 核心计算函数 (无需修改) ---
# ==============================================================================

def add_months(source_date, months):
    """
    精准地给一个日期增加月份，处理月末日期问题。
    """
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = source_date.day
    try:
        new_date = datetime(year, month, day)
    except ValueError:
        new_date = datetime(year, month + 1, 1) - timedelta(days=1)
    return new_date


def calculate_repayment_plan(principal_cents, annual_rate_percent, total_periods, start_date_str,
                             interest_only_periods=0):
    """
    一个统一的还款计划计算函数，用于生成分期计划。
    """
    plan = []
    daily_rate = (annual_rate_percent / 100) / 360
    start_date = datetime.strptime(start_date_str, '%Y%m%d')
    last_repayment_date = start_date
    remaining_principal_cents = principal_cents

    # --- 1. 计算先息后本阶段 (如果存在) ---
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

    # --- 2. 计算等额本息阶段 ---
    equal_periods = total_periods - interest_only_periods
    if equal_periods <= 0:
        return plan

    monthly_rate = (annual_rate_percent / 100) / 12

    try:
        power_val = (1 + monthly_rate) ** equal_periods
        # 使用行业标准的向上取整方式计算月供
        monthly_payment = math.ceil(remaining_principal_cents * (monthly_rate * power_val) / (power_val - 1))
    except OverflowError:
        print("计算月供时发生错误，请检查输入参数。")
        return []

    for i in range(1, equal_periods + 1):
        current_repayment_date = add_months(last_repayment_date, i)
        current_period_start_date = add_months(last_repayment_date, i - 1)
        days_in_period = (current_repayment_date - current_period_start_date).days

        current_interest_cents = round(remaining_principal_cents * daily_rate * days_in_period)
        current_principal_cents = monthly_payment - current_interest_cents

        if i == equal_periods:
            current_principal_cents = remaining_principal_cents

        # 确保剩余本金不会变成负数
        if remaining_principal_cents < current_principal_cents:
            current_principal_cents = remaining_principal_cents

        remaining_principal_cents -= current_principal_cents

        plan.append({
            "period": i + interest_only_periods,
            "repayment_date": current_repayment_date.strftime('%Y-%m-%d'),
            "principal": current_principal_cents,
            "interest": current_interest_cents,
            "remaining_principal": remaining_principal_cents
        })

    return plan


def parse_repayment_method(method_str):
    """
    智能解析还款方式字符串。
    """
    method_str = method_str.strip()
    match_equal = re.match(r'(\d+)期等额本息', method_str)
    if match_equal:
        return int(match_equal.group(1)), 0
    match_hybrid = re.match(r'前(\d+)后(\d+)', method_str)
    if match_hybrid:
        interest_only = int(match_hybrid.group(1))
        equal = int(match_hybrid.group(2))
        return interest_only + equal, interest_only
    print(f"警告: 无法解析还款方式 '{method_str}'。")
    return 0, 0


# --- 主程序 ---
def run_trial_calculation():
    """
    执行试算并打印结果。
    """
    loan_amount_cents = int(LOAN_AMOUNT_YUAN * 100)
    total_periods, interest_only_periods = parse_repayment_method(REPAYMENT_METHOD_STR)

    if total_periods == 0:
        return

    print("-" * 80)
    print(f"借款金额: {loan_amount_cents / 100:.2f} 元")
    print(f"年化利率: {ANNUAL_RATE_PERCENT}%")
    print(f"还款方式: {REPAYMENT_METHOD_STR}")
    print("-" * 80)
    header = f"{'期数':<5} | {'还款日':<12} | {'应还本金(元)':<15} | {'应还利息(元)':<15} | {'剩余本金(元)':<15}"
    print(header)
    print("-" * 80)

    final_plan = calculate_repayment_plan(
        loan_amount_cents,
        ANNUAL_RATE_PERCENT,
        total_periods,
        START_DATE_STR,
        interest_only_periods
    )

    if final_plan:
        for p in final_plan:
            print(
                f"{p['period']:<6} | {p['repayment_date']:<12} | {p['principal'] / 100:<15.2f} | {p['interest'] / 100:<15.2f} | {p['remaining_principal'] / 100:<15.2f}")

    print("\n")


# 执行试算
if __name__ == "__main__":
    run_trial_calculation()

