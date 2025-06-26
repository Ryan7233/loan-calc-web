import tkinter as tk
from tkinter import ttk, messagebox
import math
import re
from datetime import datetime, timedelta

# ==============================================================================
# --- 核心计算函数 (逻辑与之前版本保持一致) ---
# ==============================================================================

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

    # 1. 计算先息后本阶段
    for i in range(1, interest_only_periods + 1):
        current_repayment_date = add_months(start_date, i)
        days_in_period = (current_repayment_date - last_repayment_date).days
        interest_per_period = round(principal_cents * daily_rate * days_in_period)
        plan.append({
            "period": i, "repayment_date": current_repayment_date,
            "principal": 0, "interest": interest_per_period,
            "remaining_principal": principal_cents
        })
        last_repayment_date = current_repayment_date

    # 2. 计算等额本息阶段
    equal_periods = total_periods - interest_only_periods
    if equal_periods <= 0:
        return plan

    monthly_rate = (annual_rate_percent / 100) / 12
    try:
        power_val = (1 + monthly_rate)**equal_periods
        monthly_payment = round(remaining_principal_cents * (monthly_rate * power_val) / (power_val - 1))
    except (OverflowError, ValueError):
        return None # Return None on calculation error

    for i in range(1, equal_periods + 1):
        current_repayment_date = add_months(last_repayment_date, i-1) # Bug fix: should be i-1
        next_repayment_date = add_months(last_repayment_date, i)
        days_in_period = (next_repayment_date - current_repayment_date).days

        current_interest_cents = round(remaining_principal_cents * daily_rate * days_in_period)
        current_principal_cents = monthly_payment - current_interest_cents

        if i == equal_periods:
            current_principal_cents = remaining_principal_cents

        if remaining_principal_cents < current_principal_cents:
            current_principal_cents = remaining_principal_cents

        remaining_principal_cents -= current_principal_cents

        plan.append({
            "period": i + interest_only_periods, "repayment_date": next_repayment_date,
            "principal": current_principal_cents, "interest": current_interest_cents,
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

# ==============================================================================
# --- 图形用户界面 (GUI) 实现 ---
# ==============================================================================
class LoanCalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("分期还款计划试算工具")
        self.geometry("800x600")

        # --- 输入区 ---
        input_frame = ttk.Frame(self, padding="20")
        input_frame.pack(fill=tk.X)

        ttk.Label(input_frame, text="贷款金额 (元):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.amount_var = tk.StringVar(value="987000")
        ttk.Entry(input_frame, textvariable=self.amount_var, width=20).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="年化利率 (%):").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.rate_var = tk.StringVar(value="7.2")
        ttk.Entry(input_frame, textvariable=self.rate_var, width=20).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(input_frame, text="还款方式:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.method_var = tk.StringVar()
        method_options = ["24期等额本息", "前3后21", "前3后12", "前3后3"]
        self.method_menu = ttk.Combobox(input_frame, textvariable=self.method_var, values=method_options, width=18)
        self.method_menu.set("前3后21")
        self.method_menu.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="起息日 (YYYY-MM-DD):").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.date_var = tk.StringVar(value="2025-06-17")
        ttk.Entry(input_frame, textvariable=self.date_var, width=20).grid(row=1, column=3, padx=5, pady=5)

        ttk.Button(input_frame, text="开始计算", command=self.run_calculation).grid(row=2, column=0, columnspan=4, pady=20)

        # --- 输出区 ---
        output_frame = ttk.Frame(self, padding="0 10 10 10")
        output_frame.pack(expand=True, fill=tk.BOTH)

        self.result_text = tk.Text(output_frame, wrap=tk.WORD, font=("Menlo", 10), borderwidth=0)

        # Add scrollbars
        yscroll = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        xscroll = ttk.Scrollbar(output_frame, orient=tk.HORIZONTAL, command=self.result_text.xview)
        self.result_text.config(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.result_text.pack(expand=True, fill=tk.BOTH)

    def run_calculation(self):
        try:
            loan_amount = float(self.amount_var.get())
            annual_rate = float(self.rate_var.get())
            repayment_method = self.method_var.get()
            start_date = self.date_var.get()

            # Validate date format
            datetime.strptime(start_date, '%Y-%m-%d')

            loan_amount_cents = int(loan_amount * 100)
            total_periods, interest_only_periods = parse_repayment_method(repayment_method)

            if total_periods == 0:
                messagebox.showerror("错误", f"无法解析还款方式: {repayment_method}")
                return

            final_plan = calculate_repayment_plan(loan_amount_cents, annual_rate, total_periods, start_date, interest_only_periods)

            self.display_results(final_plan)

        except (ValueError, TypeError) as e:
            messagebox.showerror("输入错误", f"请输入有效的数字和日期格式 (YYYY-MM-DD)。\n错误详情: {e}")

    def display_results(self, plan):
        self.result_text.delete('1.0', tk.END)
        if not plan:
            self.result_text.insert(tk.END, "计算失败，请检查输入参数。")
            return

        header = f"{'期数':<5} | {'还款日':<12} | {'应还本金(元)':<15} | {'应还利息(元)':<15} | {'剩余本金(元)':<15}\n"
        separator = "-" * 80 + "\n"

        self.result_text.insert(tk.END, header)
        self.result_text.insert(tk.END, separator)

        for p in plan:
            line = (f"{p['period']:<6} | "
                    f"{p['repayment_date'].strftime('%Y-%m-%d'):<12} | "
                    f"{p['principal'] / 100:<15.2f} | "
                    f"{p['interest'] / 100:<15.2f} | "
                    f"{p['remaining_principal'] / 100:<15.2f}\n")
            self.result_text.insert(tk.END, line)

if __name__ == "__main__":
    app = LoanCalculatorApp()
    app.mainloop()

