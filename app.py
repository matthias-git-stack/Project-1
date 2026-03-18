import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from calendar import monthrange

st.set_page_config(page_title="Account Ledger", layout="wide")

# ── Default Chart of Accounts ───────────────────────────────────────────────
DEFAULT_ACCOUNTS = [
    # Assets
    {"id": "a1000", "number": "1000", "name": "Cash",                        "type": "Asset",     "normal": "Debit"},
    {"id": "a1010", "number": "1010", "name": "Petty Cash",                  "type": "Asset",     "normal": "Debit"},
    {"id": "a1200", "number": "1200", "name": "Accounts Receivable",         "type": "Asset",     "normal": "Debit"},
    {"id": "a1300", "number": "1300", "name": "Inventory",                   "type": "Asset",     "normal": "Debit"},
    {"id": "a1400", "number": "1400", "name": "Prepaid Expenses",            "type": "Asset",     "normal": "Debit"},
    {"id": "a1500", "number": "1500", "name": "Property, Plant & Equipment", "type": "Asset",     "normal": "Debit"},
    {"id": "a1600", "number": "1600", "name": "Accumulated Depreciation",    "type": "Asset",     "normal": "Credit"},
    # Liabilities
    {"id": "l2000", "number": "2000", "name": "Accounts Payable",            "type": "Liability", "normal": "Credit"},
    {"id": "l2100", "number": "2100", "name": "Accrued Liabilities",         "type": "Liability", "normal": "Credit"},
    {"id": "l2200", "number": "2200", "name": "Notes Payable",               "type": "Liability", "normal": "Credit"},
    {"id": "l2300", "number": "2300", "name": "Deferred Revenue",            "type": "Liability", "normal": "Credit"},
    {"id": "l2400", "number": "2400", "name": "Income Tax Payable",          "type": "Liability", "normal": "Credit"},
    # Equity
    {"id": "e3000", "number": "3000", "name": "Common Stock",                "type": "Equity",    "normal": "Credit"},
    {"id": "e3100", "number": "3100", "name": "Additional Paid-In Capital",  "type": "Equity",    "normal": "Credit"},
    {"id": "e3200", "number": "3200", "name": "Retained Earnings",           "type": "Equity",    "normal": "Credit"},
    {"id": "e3300", "number": "3300", "name": "Dividends Paid",              "type": "Equity",    "normal": "Debit"},
    # Revenue
    {"id": "r4000", "number": "4000", "name": "Sales Revenue",               "type": "Revenue",   "normal": "Credit"},
    {"id": "r4100", "number": "4100", "name": "Service Revenue",             "type": "Revenue",   "normal": "Credit"},
    {"id": "r4200", "number": "4200", "name": "Interest Income",             "type": "Revenue",   "normal": "Credit"},
    {"id": "r4300", "number": "4300", "name": "Other Income",                "type": "Revenue",   "normal": "Credit"},
    # Expenses
    {"id": "x5000", "number": "5000", "name": "Cost of Goods Sold",          "type": "Expense",   "normal": "Debit"},
    {"id": "x5100", "number": "5100", "name": "Salaries & Wages Expense",    "type": "Expense",   "normal": "Debit"},
    {"id": "x5200", "number": "5200", "name": "Rent Expense",                "type": "Expense",   "normal": "Debit"},
    {"id": "x5300", "number": "5300", "name": "Utilities Expense",           "type": "Expense",   "normal": "Debit"},
    {"id": "x5400", "number": "5400", "name": "Depreciation Expense",        "type": "Expense",   "normal": "Debit"},
    {"id": "x5500", "number": "5500", "name": "Insurance Expense",           "type": "Expense",   "normal": "Debit"},
    {"id": "x5600", "number": "5600", "name": "Office Supplies Expense",     "type": "Expense",   "normal": "Debit"},
    {"id": "x5700", "number": "5700", "name": "Advertising Expense",         "type": "Expense",   "normal": "Debit"},
    {"id": "x5800", "number": "5800", "name": "Interest Expense",            "type": "Expense",   "normal": "Debit"},
    {"id": "x5900", "number": "5900", "name": "Income Tax Expense",          "type": "Expense",   "normal": "Debit"},
]

# ── Session State Init ──────────────────────────────────────────────────────
def init_state():
    if "accounts" not in st.session_state:
        st.session_state.accounts = [a.copy() for a in DEFAULT_ACCOUNTS]
    if "entries" not in st.session_state:
        st.session_state.entries = []
    if "next_entry_id" not in st.session_state:
        st.session_state.next_entry_id = 1
    if "show_entry_form" not in st.session_state:
        st.session_state.show_entry_form = False
    if "editing_entry_id" not in st.session_state:
        st.session_state.editing_entry_id = None
    if "form_date" not in st.session_state:
        st.session_state.form_date = date.today()
    if "form_ref" not in st.session_state:
        st.session_state.form_ref = ""
    if "form_memo" not in st.session_state:
        st.session_state.form_memo = ""
    if "form_lines" not in st.session_state:
        st.session_state.form_lines = []
    if "view_entry_id" not in st.session_state:
        st.session_state.view_entry_id = None
    if "show_account_form" not in st.session_state:
        st.session_state.show_account_form = False

init_state()

# ── Helpers ─────────────────────────────────────────────────────────────────
def fmt(n):
    return f"{float(n):,.2f}"

def account_by_id(account_id):
    return next((a for a in st.session_state.accounts if a["id"] == account_id), None)

def account_label(acct):
    if not acct:
        return ""
    return f"{acct['number']} — {acct['name']}"

def get_account_options():
    sorted_accts = sorted(st.session_state.accounts, key=lambda x: x["number"])
    return [account_label(a) for a in sorted_accts]

def label_to_account(label):
    for a in st.session_state.accounts:
        if account_label(a) == label:
            return a
    return None

def compute_balances():
    balances = {a["id"]: 0.0 for a in st.session_state.accounts}
    for entry in st.session_state.entries:
        for line in entry["lines"]:
            acct = account_by_id(line["account_id"])
            if not acct:
                continue
            delta = line.get("debit", 0.0) - line.get("credit", 0.0)
            if acct["normal"] == "Credit":
                delta = -delta
            balances[line["account_id"]] = balances.get(line["account_id"], 0.0) + delta
    return balances

def auto_ref():
    return f"JE-{st.session_state.next_entry_id:04d}"

def open_entry_form(entry=None):
    st.session_state.show_entry_form = True
    st.session_state.view_entry_id = None
    st.session_state.editing_entry_id = entry["id"] if entry else None
    if entry:
        st.session_state.form_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
        st.session_state.form_ref = entry["reference"]
        st.session_state.form_memo = entry["memo"]
        st.session_state.form_lines = [
            {
                "account": account_label(account_by_id(l["account_id"])),
                "description": l.get("description", ""),
                "debit": l.get("debit", 0.0),
                "credit": l.get("credit", 0.0),
            }
            for l in entry["lines"]
        ]
    else:
        st.session_state.form_date = date.today()
        st.session_state.form_ref = auto_ref()
        st.session_state.form_memo = ""
        st.session_state.form_lines = [
            {"account": "", "description": "", "debit": 0.0, "credit": 0.0},
            {"account": "", "description": "", "debit": 0.0, "credit": 0.0},
        ]

def close_entry_form():
    st.session_state.show_entry_form = False
    st.session_state.editing_entry_id = None
    st.session_state.form_lines = []

# ── Report Formatting ───────────────────────────────────────────────────────
def fmt_acct(n):
    """CPA-style: negatives in parentheses, zero as dash."""
    if n is None:
        return ""
    n = float(n)
    if abs(n) < 0.005:
        return "—"
    if n < 0:
        return f"({abs(n):,.2f})"
    return f"{n:,.2f}"

# ── Cash Flow Account Classification ───────────────────────────────────────
CASH_ACCOUNT_IDS = {"a1000", "a1010"}
OPERATING_WC_ASSETS = {"a1200", "a1300", "a1400"}
OPERATING_WC_LIABILITIES = {"l2000", "l2100", "l2300", "l2400"}
DEPRECIATION_EXPENSE_ID = "x5400"
ACCUM_DEPRECIATION_ID = "a1600"
INVESTING_ACCOUNT_IDS = {"a1500"}
FINANCING_ACCOUNT_IDS = {"l2200", "e3000", "e3100", "e3300"}

def classify_for_cashflow(acct):
    """Classify an account for cash flow statement purposes."""
    aid = acct["id"]
    if aid in CASH_ACCOUNT_IDS:
        return "cash"
    if aid == DEPRECIATION_EXPENSE_ID:
        return "depr_expense"
    if aid == ACCUM_DEPRECIATION_ID:
        return "accum_depr"
    if acct["type"] in ("Revenue", "Expense"):
        return "net_income"
    if aid in OPERATING_WC_ASSETS:
        return "operating_asset"
    if aid in OPERATING_WC_LIABILITIES:
        return "operating_liability"
    if aid in INVESTING_ACCOUNT_IDS:
        return "investing"
    if aid in FINANCING_ACCOUNT_IDS:
        return "financing"
    # Custom accounts: classify by type
    if acct["type"] == "Asset":
        return "investing"
    if acct["type"] == "Liability":
        return "operating_liability"
    if acct["type"] == "Equity":
        return "financing"
    return "operating_liability"

# ── Period Boundary Computation ─────────────────────────────────────────────
def get_period_boundaries(start_dt, end_dt, grouping):
    """Return list of (label, period_start, period_end) tuples."""
    if grouping == "None":
        label = f"{start_dt.strftime('%b %d, %Y')} – {end_dt.strftime('%b %d, %Y')}"
        return [(label, start_dt, end_dt)]

    periods = []
    if grouping == "Monthly":
        cursor = start_dt.replace(day=1)
        while cursor <= end_dt:
            _, last_day = monthrange(cursor.year, cursor.month)
            p_end = cursor.replace(day=last_day)
            p_start = max(cursor, start_dt)
            p_end = min(p_end, end_dt)
            label = cursor.strftime("%b %Y")
            periods.append((label, p_start, p_end))
            # Advance to next month
            if cursor.month == 12:
                cursor = cursor.replace(year=cursor.year + 1, month=1, day=1)
            else:
                cursor = cursor.replace(month=cursor.month + 1, day=1)
    elif grouping == "Quarterly":
        # Find start of quarter containing start_dt
        q_month = ((start_dt.month - 1) // 3) * 3 + 1
        cursor = start_dt.replace(month=q_month, day=1)
        while cursor <= end_dt:
            q_end_month = cursor.month + 2
            q_end_year = cursor.year
            if q_end_month > 12:
                q_end_month -= 12
                q_end_year += 1
            _, last_day = monthrange(q_end_year, q_end_month)
            p_end = date(q_end_year, q_end_month, last_day)
            p_start = max(cursor, start_dt)
            p_end_clamped = min(p_end, end_dt)
            q_num = (cursor.month - 1) // 3 + 1
            label = f"Q{q_num} {cursor.year}"
            periods.append((label, p_start, p_end_clamped))
            # Advance to next quarter
            next_month = cursor.month + 3
            next_year = cursor.year
            if next_month > 12:
                next_month -= 12
                next_year += 1
            cursor = date(next_year, next_month, 1)
    elif grouping == "Yearly":
        cursor = start_dt.replace(month=1, day=1)
        while cursor <= end_dt:
            p_end = cursor.replace(month=12, day=31)
            p_start = max(cursor, start_dt)
            p_end_clamped = min(p_end, end_dt)
            label = str(cursor.year)
            periods.append((label, p_start, p_end_clamped))
            cursor = cursor.replace(year=cursor.year + 1)

    return periods

# ── Entry Filtering & Activity Computation ──────────────────────────────────
def entries_in_range(start_dt, end_dt):
    """Return entries whose date falls within [start_dt, end_dt]."""
    s = start_dt.strftime("%Y-%m-%d")
    e = end_dt.strftime("%Y-%m-%d")
    return [
        entry for entry in st.session_state.entries
        if s <= entry["date"] <= e
    ]

def compute_activity(start_dt, end_dt):
    """
    Compute net activity per account for entries in [start_dt, end_dt].
    Returns dict: account_id -> activity in normal-balance direction.
    Positive = balance increased in normal direction.
    """
    activity = {}
    for entry in entries_in_range(start_dt, end_dt):
        for line in entry["lines"]:
            aid = line["account_id"]
            acct = account_by_id(aid)
            if not acct:
                continue
            dr = line.get("debit", 0.0)
            cr = line.get("credit", 0.0)
            if acct["normal"] == "Debit":
                delta = dr - cr
            else:
                delta = cr - dr
            activity[aid] = activity.get(aid, 0.0) + delta
    return activity

def compute_cumulative_balances_as_of(as_of_date):
    """Compute cumulative balances for all accounts through as_of_date."""
    d = as_of_date.strftime("%Y-%m-%d")
    balances = {a["id"]: 0.0 for a in st.session_state.accounts}
    for entry in st.session_state.entries:
        if entry["date"] > d:
            continue
        for line in entry["lines"]:
            acct = account_by_id(line["account_id"])
            if not acct:
                continue
            dr = line.get("debit", 0.0)
            cr = line.get("credit", 0.0)
            if acct["normal"] == "Debit":
                balances[line["account_id"]] += dr - cr
            else:
                balances[line["account_id"]] += cr - dr
    return balances

def compute_raw_activity(start_dt, end_dt):
    """
    Compute raw debit-minus-credit per account (not normal-adjusted).
    Positive = net debit, Negative = net credit.
    """
    activity = {}
    for entry in entries_in_range(start_dt, end_dt):
        for line in entry["lines"]:
            aid = line["account_id"]
            dr = line.get("debit", 0.0)
            cr = line.get("credit", 0.0)
            activity[aid] = activity.get(aid, 0.0) + (dr - cr)
    return activity

# ── Report Generators ───────────────────────────────────────────────────────

def generate_trial_balance(start_dt, end_dt, grouping):
    """Generate Trial Balance: cumulative balances as of each period end."""
    periods = get_period_boundaries(start_dt, end_dt, grouping)
    type_order = ["Asset", "Liability", "Equity", "Revenue", "Expense"]
    sorted_accts = sorted(st.session_state.accounts, key=lambda a: a["number"])

    rows = []
    period_totals_dr = {p[0]: 0.0 for p in periods}
    period_totals_cr = {p[0]: 0.0 for p in periods}

    for acct_type in type_order:
        accts = [a for a in sorted_accts if a["type"] == acct_type]
        if not accts:
            continue
        # Section header
        row = {"Account #": "", "Account Name": f"── {acct_type}s ──"}
        for label, _, _ in periods:
            row[f"{label} Dr"] = ""
            row[f"{label} Cr"] = ""
        rows.append(row)

        for acct in accts:
            row = {"Account #": acct["number"], "Account Name": acct["name"]}
            for label, _, p_end in periods:
                bal = compute_cumulative_balances_as_of(p_end).get(acct["id"], 0.0)
                if acct["normal"] == "Debit":
                    if bal >= 0:
                        row[f"{label} Dr"] = fmt_acct(bal)
                        row[f"{label} Cr"] = ""
                        period_totals_dr[label] += bal
                    else:
                        row[f"{label} Dr"] = ""
                        row[f"{label} Cr"] = fmt_acct(abs(bal))
                        period_totals_cr[label] += abs(bal)
                else:
                    if bal >= 0:
                        row[f"{label} Dr"] = ""
                        row[f"{label} Cr"] = fmt_acct(bal)
                        period_totals_cr[label] += bal
                    else:
                        row[f"{label} Dr"] = fmt_acct(abs(bal))
                        row[f"{label} Cr"] = ""
                        period_totals_dr[label] += abs(bal)
            rows.append(row)

    # Totals row
    totals_row = {"Account #": "", "Account Name": "TOTALS"}
    for label, _, _ in periods:
        totals_row[f"{label} Dr"] = fmt_acct(period_totals_dr[label])
        totals_row[f"{label} Cr"] = fmt_acct(period_totals_cr[label])
    rows.append(totals_row)

    return pd.DataFrame(rows)


def generate_income_statement(start_dt, end_dt, grouping):
    """Generate multi-step Income Statement for each period."""
    periods = get_period_boundaries(start_dt, end_dt, grouping)
    sorted_accts = sorted(st.session_state.accounts, key=lambda a: a["number"])
    show_total = len(periods) > 1

    revenue_accts = [a for a in sorted_accts if a["type"] == "Revenue"]
    cogs_accts = [a for a in sorted_accts if a["id"] == "x5000"]
    opex_accts = [a for a in sorted_accts if a["type"] == "Expense" and a["id"] != "x5000"]

    rows = []

    def make_row(label, values, bold=False):
        prefix = "**" if bold else ""
        suffix = "**" if bold else ""
        row = {"": f"{prefix}{label}{suffix}"}
        for i, (plabel, _, _) in enumerate(periods):
            row[plabel] = fmt_acct(values[i]) if values[i] is not None else ""
        if show_total:
            total = sum(v for v in values if v is not None)
            row["Total"] = fmt_acct(total)
        return row

    def blank_row():
        row = {"": ""}
        for plabel, _, _ in periods:
            row[plabel] = ""
        if show_total:
            row["Total"] = ""
        return row

    # Compute activity for each period
    period_activities = []
    for _, p_start, p_end in periods:
        period_activities.append(compute_activity(p_start, p_end))

    # ── Revenue Section ──
    rows.append(make_row("REVENUE", [None] * len(periods)))
    revenue_totals = [0.0] * len(periods)
    for acct in revenue_accts:
        values = []
        for i, act in enumerate(period_activities):
            val = act.get(acct["id"], 0.0)
            values.append(val)
            revenue_totals[i] += val
        rows.append(make_row(f"  {acct['number']} {acct['name']}", values))
    rows.append(make_row("Total Revenue", revenue_totals, bold=True))
    rows.append(blank_row())

    # ── COGS Section ──
    cogs_totals = [0.0] * len(periods)
    if cogs_accts:
        rows.append(make_row("COST OF GOODS SOLD", [None] * len(periods)))
        for acct in cogs_accts:
            values = []
            for i, act in enumerate(period_activities):
                val = act.get(acct["id"], 0.0)
                values.append(val)
                cogs_totals[i] += val
            rows.append(make_row(f"  {acct['number']} {acct['name']}", values))
        rows.append(make_row("Total COGS", cogs_totals, bold=True))
        rows.append(blank_row())

    # ── Gross Profit ──
    gross_profit = [revenue_totals[i] - cogs_totals[i] for i in range(len(periods))]
    rows.append(make_row("GROSS PROFIT", gross_profit, bold=True))
    rows.append(blank_row())

    # ── Operating Expenses ──
    rows.append(make_row("OPERATING EXPENSES", [None] * len(periods)))
    opex_totals = [0.0] * len(periods)
    for acct in opex_accts:
        values = []
        for i, act in enumerate(period_activities):
            val = act.get(acct["id"], 0.0)
            values.append(val)
            opex_totals[i] += val
        rows.append(make_row(f"  {acct['number']} {acct['name']}", values))
    rows.append(make_row("Total Operating Expenses", opex_totals, bold=True))
    rows.append(blank_row())

    # ── Net Income ──
    net_income = [gross_profit[i] - opex_totals[i] for i in range(len(periods))]
    rows.append(make_row("NET INCOME (LOSS)", net_income, bold=True))

    return pd.DataFrame(rows)


def generate_balance_sheet(start_dt, end_dt, grouping):
    """Generate Balance Sheet: cumulative balances as of each period end."""
    periods = get_period_boundaries(start_dt, end_dt, grouping)
    sorted_accts = sorted(st.session_state.accounts, key=lambda a: a["number"])

    asset_accts = [a for a in sorted_accts if a["type"] == "Asset"]
    liability_accts = [a for a in sorted_accts if a["type"] == "Liability"]
    equity_accts = [a for a in sorted_accts if a["type"] == "Equity"]
    revenue_accts = [a for a in sorted_accts if a["type"] == "Revenue"]
    expense_accts = [a for a in sorted_accts if a["type"] == "Expense"]

    # Pre-compute cumulative balances for each period end
    period_balances = []
    for _, _, p_end in periods:
        period_balances.append(compute_cumulative_balances_as_of(p_end))

    rows = []

    def make_row(label, values, bold=False):
        prefix = "**" if bold else ""
        suffix = "**" if bold else ""
        row = {"": f"{prefix}{label}{suffix}"}
        for i, (plabel, _, _) in enumerate(periods):
            as_of = periods[i][2].strftime("%m/%d/%Y")
            col = f"As of {as_of}" if len(periods) == 1 else plabel
            row[col] = fmt_acct(values[i]) if values[i] is not None else ""
        return row

    def blank_row():
        row = {"": ""}
        for i, (plabel, _, _) in enumerate(periods):
            as_of = periods[i][2].strftime("%m/%d/%Y")
            col = f"As of {as_of}" if len(periods) == 1 else plabel
            row[col] = ""
        return row

    # ── Assets ──
    rows.append(make_row("ASSETS", [None] * len(periods)))
    asset_totals = [0.0] * len(periods)
    for acct in asset_accts:
        values = []
        for i, bals in enumerate(period_balances):
            val = bals.get(acct["id"], 0.0)
            # Accumulated Depreciation is contra-asset, show as negative
            if acct["normal"] == "Credit":
                val = -val
            values.append(val)
            asset_totals[i] += val
        rows.append(make_row(f"  {acct['number']} {acct['name']}", values))
    rows.append(make_row("Total Assets", asset_totals, bold=True))
    rows.append(blank_row())

    # ── Liabilities ──
    rows.append(make_row("LIABILITIES", [None] * len(periods)))
    liability_totals = [0.0] * len(periods)
    for acct in liability_accts:
        values = []
        for i, bals in enumerate(period_balances):
            val = bals.get(acct["id"], 0.0)
            values.append(val)
            liability_totals[i] += val
        rows.append(make_row(f"  {acct['number']} {acct['name']}", values))
    rows.append(make_row("Total Liabilities", liability_totals, bold=True))
    rows.append(blank_row())

    # ── Equity ──
    rows.append(make_row("EQUITY", [None] * len(periods)))
    equity_totals = [0.0] * len(periods)
    for acct in equity_accts:
        values = []
        for i, bals in enumerate(period_balances):
            val = bals.get(acct["id"], 0.0)
            if acct["normal"] == "Debit":
                val = -val  # Dividends reduce equity
            values.append(val)
            equity_totals[i] += val
        rows.append(make_row(f"  {acct['number']} {acct['name']}", values))

    # Net Income (cumulative Revenue - Expenses through period end)
    net_income_values = []
    for i, bals in enumerate(period_balances):
        rev = sum(bals.get(a["id"], 0.0) for a in revenue_accts)
        exp = sum(bals.get(a["id"], 0.0) for a in expense_accts)
        ni = rev - exp
        net_income_values.append(ni)
        equity_totals[i] += ni
    rows.append(make_row("  Net Income (Current Period)", net_income_values))
    rows.append(make_row("Total Equity", equity_totals, bold=True))
    rows.append(blank_row())

    # ── Total L&E ──
    total_le = [liability_totals[i] + equity_totals[i] for i in range(len(periods))]
    rows.append(make_row("TOTAL LIABILITIES & EQUITY", total_le, bold=True))

    return pd.DataFrame(rows)


def generate_cash_flow_statement(start_dt, end_dt, grouping):
    """Generate Statement of Cash Flows using the indirect method."""
    periods = get_period_boundaries(start_dt, end_dt, grouping)
    sorted_accts = sorted(st.session_state.accounts, key=lambda a: a["number"])
    show_total = len(periods) > 1

    rows = []

    def make_row(label, values, bold=False):
        prefix = "**" if bold else ""
        suffix = "**" if bold else ""
        row = {"": f"{prefix}{label}{suffix}"}
        for i, (plabel, _, _) in enumerate(periods):
            row[plabel] = fmt_acct(values[i]) if values[i] is not None else ""
        if show_total:
            total = sum(v for v in values if v is not None)
            row["Total"] = fmt_acct(total)
        return row

    def blank_row():
        row = {"": ""}
        for plabel, _, _ in periods:
            row[plabel] = ""
        if show_total:
            row["Total"] = ""
        return row

    # Pre-compute raw activity (debit - credit) for each period
    period_raw = []
    for _, p_start, p_end in periods:
        period_raw.append(compute_raw_activity(p_start, p_end))

    # Pre-compute normal-direction activity for each period
    period_normal = []
    for _, p_start, p_end in periods:
        period_normal.append(compute_activity(p_start, p_end))

    revenue_accts = [a for a in sorted_accts if a["type"] == "Revenue"]
    expense_accts = [a for a in sorted_accts if a["type"] == "Expense"]

    # ── Net Income ──
    net_income = []
    for i, act in enumerate(period_normal):
        rev = sum(act.get(a["id"], 0.0) for a in revenue_accts)
        exp = sum(act.get(a["id"], 0.0) for a in expense_accts)
        net_income.append(rev - exp)

    # ══ OPERATING ACTIVITIES ══
    rows.append(make_row("OPERATING ACTIVITIES", [None] * len(periods)))
    rows.append(make_row("  Net Income", net_income))

    # Adjustments for non-cash items
    rows.append(make_row("  Adjustments for non-cash items:", [None] * len(periods)))

    # Depreciation add-back
    depr_values = []
    for i, act in enumerate(period_normal):
        depr_values.append(act.get(DEPRECIATION_EXPENSE_ID, 0.0))
    if any(abs(v) > 0.005 for v in depr_values):
        rows.append(make_row("    Depreciation & Amortization", depr_values))

    # Changes in working capital
    rows.append(make_row("  Changes in working capital:", [None] * len(periods)))

    operating_adjustments = [0.0] * len(periods)
    for v in depr_values:
        for i in range(len(periods)):
            pass
    # Track total depreciation
    total_depr = list(depr_values)

    # Operating assets (increase = cash outflow = negative)
    op_asset_ids = set()
    for acct in sorted_accts:
        cf_class = classify_for_cashflow(acct)
        if cf_class == "operating_asset":
            op_asset_ids.add(acct["id"])
            values = []
            for i, raw in enumerate(period_raw):
                # Raw activity is debit - credit. For assets, increase is debit.
                # Increase in asset = used cash = negative for cash flow
                change = -(raw.get(acct["id"], 0.0))
                values.append(change)
                operating_adjustments[i] += change
            if any(abs(v) > 0.005 for v in values):
                rows.append(make_row(f"    {acct['name']}", values))

    # Operating liabilities (increase = cash inflow = positive)
    for acct in sorted_accts:
        cf_class = classify_for_cashflow(acct)
        if cf_class == "operating_liability":
            values = []
            for i, raw in enumerate(period_raw):
                # Raw activity is debit - credit. For liabilities, increase is credit (negative raw).
                # Increase in liability = source of cash = positive
                change = -(raw.get(acct["id"], 0.0))
                values.append(change)
                operating_adjustments[i] += change
            if any(abs(v) > 0.005 for v in values):
                rows.append(make_row(f"    {acct['name']}", values))

    # Accum depreciation change (already handled via depreciation add-back, but
    # the balance sheet change in accum depr needs to net out if tracked separately)
    # For indirect method: depr expense add-back covers the non-cash portion.
    # Accum depr changes that aren't from depr expense (e.g., asset disposal) would
    # show here, but we'll keep it simple.

    net_cash_operating = [
        net_income[i] + total_depr[i] + operating_adjustments[i]
        for i in range(len(periods))
    ]
    rows.append(blank_row())
    rows.append(make_row("Net Cash from Operating Activities", net_cash_operating, bold=True))
    rows.append(blank_row())

    # ══ INVESTING ACTIVITIES ══
    rows.append(make_row("INVESTING ACTIVITIES", [None] * len(periods)))
    investing_total = [0.0] * len(periods)
    for acct in sorted_accts:
        cf_class = classify_for_cashflow(acct)
        if cf_class == "investing":
            values = []
            for i, raw in enumerate(period_raw):
                # Increase in PP&E (debit) = cash outflow = negative
                change = -(raw.get(acct["id"], 0.0))
                values.append(change)
                investing_total[i] += change
            if any(abs(v) > 0.005 for v in values):
                rows.append(make_row(f"  {acct['name']}", values))

    rows.append(make_row("Net Cash from Investing Activities", investing_total, bold=True))
    rows.append(blank_row())

    # ══ FINANCING ACTIVITIES ══
    rows.append(make_row("FINANCING ACTIVITIES", [None] * len(periods)))
    financing_total = [0.0] * len(periods)
    for acct in sorted_accts:
        cf_class = classify_for_cashflow(acct)
        if cf_class == "financing":
            values = []
            for i, raw in enumerate(period_raw):
                if acct["normal"] == "Debit":
                    # Debit-normal equity (e.g., Dividends Paid): increase = outflow
                    change = -(raw.get(acct["id"], 0.0))
                else:
                    # Credit-normal: increase (credit) = inflow
                    change = -(raw.get(acct["id"], 0.0))
                values.append(change)
                financing_total[i] += change
            if any(abs(v) > 0.005 for v in values):
                rows.append(make_row(f"  {acct['name']}", values))

    rows.append(make_row("Net Cash from Financing Activities", financing_total, bold=True))
    rows.append(blank_row())

    # ══ SUMMARY ══
    net_change = [
        net_cash_operating[i] + investing_total[i] + financing_total[i]
        for i in range(len(periods))
    ]
    rows.append(make_row("NET CHANGE IN CASH", net_change, bold=True))

    # Beginning and ending cash
    beginning_cash = []
    ending_cash = []
    for i, (_, p_start, p_end) in enumerate(periods):
        # Beginning cash = cumulative cash balance before period start
        day_before = p_start - timedelta(days=1)
        beg_bals = compute_cumulative_balances_as_of(day_before)
        beg = sum(beg_bals.get(cid, 0.0) for cid in CASH_ACCOUNT_IDS)
        beginning_cash.append(beg)

        end_bals = compute_cumulative_balances_as_of(p_end)
        end = sum(end_bals.get(cid, 0.0) for cid in CASH_ACCOUNT_IDS)
        ending_cash.append(end)

    rows.append(make_row("Beginning Cash Balance", beginning_cash))
    rows.append(make_row("ENDING CASH BALANCE", ending_cash, bold=True))

    return pd.DataFrame(rows)


# ── App Header ──────────────────────────────────────────────────────────────
st.title("Account Ledger")

# ── Tabs ────────────────────────────────────────────────────────────────────
tab_journal, tab_ledger, tab_accounts, tab_reports = st.tabs(
    ["Journal Entries", "General Ledger", "Chart of Accounts", "Reports"]
)

# ══════════════════════════════════════════════════════════════════════
# JOURNAL ENTRIES TAB
# ══════════════════════════════════════════════════════════════════════
with tab_journal:
    hdr_col, btn_col = st.columns([5, 1])
    with hdr_col:
        st.subheader("Journal Entries")
    with btn_col:
        if st.button("+ New Entry", type="primary", use_container_width=True):
            open_entry_form()
            st.rerun()

    # ── Entry Form ────────────────────────────────────────────────────
    if st.session_state.show_entry_form:
        editing = st.session_state.editing_entry_id is not None
        form_title = (
            f"Edit Entry — {st.session_state.form_ref}" if editing else "New Journal Entry"
        )

        with st.container(border=True):
            st.subheader(form_title)

            col_date, col_ref, col_memo = st.columns([1, 1, 2])
            with col_date:
                form_date = st.date_input("Date", value=st.session_state.form_date)
            with col_ref:
                form_ref = st.text_input("Reference #", value=st.session_state.form_ref)
            with col_memo:
                form_memo = st.text_input("Memo / Description", value=st.session_state.form_memo)

            st.markdown("**Line Items** — use the table below to add/edit lines. You can add rows with the ＋ at the bottom or delete rows with the trash icon.")

            account_options = get_account_options()
            lines_df = pd.DataFrame(
                st.session_state.form_lines,
                columns=["account", "description", "debit", "credit"],
            )

            edited_df = st.data_editor(
                lines_df,
                column_config={
                    "account": st.column_config.SelectboxColumn(
                        "GL Account",
                        options=account_options,
                        width="large",
                    ),
                    "description": st.column_config.TextColumn("Description", width="medium"),
                    "debit": st.column_config.NumberColumn(
                        "Debit", min_value=0.0, format="%.2f", width="small"
                    ),
                    "credit": st.column_config.NumberColumn(
                        "Credit", min_value=0.0, format="%.2f", width="small"
                    ),
                },
                num_rows="dynamic",
                hide_index=True,
                use_container_width=True,
            )

            total_debit = float(edited_df["debit"].fillna(0).sum())
            total_credit = float(edited_df["credit"].fillna(0).sum())
            diff = abs(total_debit - total_credit)

            tot_col, bal_col = st.columns([2, 2])
            with tot_col:
                st.markdown(
                    f"**Total Debits:** {fmt(total_debit)} &nbsp;|&nbsp; **Total Credits:** {fmt(total_credit)}"
                )
            with bal_col:
                if diff < 0.005:
                    st.success("Entry is balanced ✓")
                else:
                    st.error(f"Out of balance by {fmt(diff)}")

            cancel_col, _, save_col = st.columns([1, 4, 1])
            with cancel_col:
                if st.button("Cancel", use_container_width=True):
                    close_entry_form()
                    st.rerun()
            with save_col:
                if st.button("Post Entry", type="primary", use_container_width=True):
                    errors = []
                    if not form_ref.strip():
                        errors.append("Please enter a reference number.")

                    valid_lines = edited_df[
                        edited_df["account"].notna() & (edited_df["account"] != "")
                    ]
                    if len(valid_lines) < 2:
                        errors.append("A journal entry must have at least 2 lines with accounts selected.")

                    if diff >= 0.005:
                        errors.append(
                            f"Entry is out of balance by {fmt(diff)}. Debits must equal credits."
                        )
                    if total_debit == 0:
                        errors.append("Entry has no amounts. Please enter debit or credit values.")

                    if errors:
                        for err in errors:
                            st.error(err)
                    else:
                        lines_internal = []
                        for _, row in valid_lines.iterrows():
                            acct = label_to_account(row["account"])
                            if acct:
                                lines_internal.append({
                                    "account_id": acct["id"],
                                    "description": str(row.get("description") or ""),
                                    "debit": float(row.get("debit") or 0),
                                    "credit": float(row.get("credit") or 0),
                                })

                        if st.session_state.editing_entry_id is not None:
                            idx = next(
                                (i for i, e in enumerate(st.session_state.entries)
                                 if e["id"] == st.session_state.editing_entry_id),
                                None,
                            )
                            if idx is not None:
                                st.session_state.entries[idx] = {
                                    **st.session_state.entries[idx],
                                    "date": form_date.strftime("%Y-%m-%d"),
                                    "reference": form_ref.strip(),
                                    "memo": form_memo.strip(),
                                    "lines": lines_internal,
                                }
                        else:
                            st.session_state.entries.append({
                                "id": st.session_state.next_entry_id,
                                "date": form_date.strftime("%Y-%m-%d"),
                                "reference": form_ref.strip(),
                                "memo": form_memo.strip(),
                                "lines": lines_internal,
                            })
                            st.session_state.next_entry_id += 1

                        close_entry_form()
                        st.rerun()

    # ── Entry Detail View ─────────────────────────────────────────────
    if st.session_state.view_entry_id is not None:
        entry = next(
            (e for e in st.session_state.entries if e["id"] == st.session_state.view_entry_id),
            None,
        )
        if entry:
            with st.container(border=True):
                title_col, close_col = st.columns([5, 1])
                with title_col:
                    st.subheader(f"Journal Entry — {entry['reference']}")
                with close_col:
                    if st.button("Close", use_container_width=True):
                        st.session_state.view_entry_id = None
                        st.rerun()

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Date", entry["date"])
                m2.metric("Reference", entry["reference"])
                m3.metric("Memo", entry["memo"] or "—")
                m4.metric("Total", fmt(sum(l.get("debit", 0) for l in entry["lines"])))

                detail_rows = []
                for i, line in enumerate(entry["lines"]):
                    acct = account_by_id(line["account_id"])
                    detail_rows.append({
                        "#": i + 1,
                        "Account": account_label(acct) if acct else "Unknown",
                        "Description": line.get("description", ""),
                        "Debit": fmt(line["debit"]) if line.get("debit", 0) > 0 else "",
                        "Credit": fmt(line["credit"]) if line.get("credit", 0) > 0 else "",
                    })

                total_d = sum(l.get("debit", 0) for l in entry["lines"])
                total_c = sum(l.get("credit", 0) for l in entry["lines"])
                detail_rows.append({
                    "#": "",
                    "Account": "**Totals**",
                    "Description": "",
                    "Debit": fmt(total_d),
                    "Credit": fmt(total_c),
                })

                st.dataframe(
                    pd.DataFrame(detail_rows),
                    hide_index=True,
                    use_container_width=True,
                )

    # ── Entries List ──────────────────────────────────────────────────
    if not st.session_state.entries:
        st.info("No journal entries yet. Click **+ New Entry** to get started.")
    else:
        sorted_entries = sorted(
            st.session_state.entries, key=lambda e: (e["date"], e["id"])
        )

        # Header
        h1, h2, h3, h4, h5, h6 = st.columns([1.2, 1.2, 3, 1.2, 1.2, 2])
        h1.markdown("**Date**")
        h2.markdown("**Reference**")
        h3.markdown("**Memo**")
        h4.markdown("**Debits**")
        h5.markdown("**Credits**")
        h6.markdown("**Actions**")
        st.divider()

        for entry in sorted_entries:
            total_d = sum(l.get("debit", 0) for l in entry["lines"])
            total_c = sum(l.get("credit", 0) for l in entry["lines"])

            c1, c2, c3, c4, c5, c6 = st.columns([1.2, 1.2, 3, 1.2, 1.2, 2])
            c1.write(entry["date"])
            c2.code(entry["reference"])
            c3.write(entry["memo"])
            c4.write(fmt(total_d))
            c5.write(fmt(total_c))

            with c6:
                a1, a2, a3 = st.columns(3)
                with a1:
                    if st.button("View", key=f"view_{entry['id']}"):
                        st.session_state.view_entry_id = entry["id"]
                        st.session_state.show_entry_form = False
                        st.rerun()
                with a2:
                    if st.button("Edit", key=f"edit_{entry['id']}"):
                        e = next((x for x in st.session_state.entries if x["id"] == entry["id"]), None)
                        if e:
                            open_entry_form(e)
                            st.rerun()
                with a3:
                    if st.button("Del", key=f"del_{entry['id']}"):
                        st.session_state.entries = [
                            x for x in st.session_state.entries if x["id"] != entry["id"]
                        ]
                        if st.session_state.view_entry_id == entry["id"]:
                            st.session_state.view_entry_id = None
                        st.rerun()

# ══════════════════════════════════════════════════════════════════════
# GENERAL LEDGER TAB
# ══════════════════════════════════════════════════════════════════════
with tab_ledger:
    st.subheader("General Ledger")

    # Account filter
    account_options_all = ["— All Accounts —"] + get_account_options()
    filter_label = st.selectbox("Filter by Account", options=account_options_all)
    filter_acct = label_to_account(filter_label) if filter_label != "— All Accounts —" else None

    if not st.session_state.entries:
        st.info("Post journal entries to see ledger activity.")
    else:
        sorted_entries = sorted(
            st.session_state.entries, key=lambda e: (e["date"], e["id"])
        )

        all_lines = []
        for entry in sorted_entries:
            for line in entry["lines"]:
                if filter_acct and line["account_id"] != filter_acct["id"]:
                    continue
                all_lines.append({
                    **line,
                    "date": entry["date"],
                    "reference": entry["reference"],
                    "entry_memo": entry["memo"],
                })

        if not all_lines:
            st.info("No transactions for the selected account.")
        else:
            rows = []
            running_balance = 0.0
            current_account_id = None

            for line in all_lines:
                acct = account_by_id(line["account_id"])
                acct_label = account_label(acct) if acct else "Unknown"

                # Insert account group header when viewing all accounts
                if not filter_acct and line["account_id"] != current_account_id:
                    current_account_id = line["account_id"]
                    running_balance = 0.0
                    rows.append({
                        "Date": "",
                        "Reference": "",
                        "Account": f"── {acct_label} ──",
                        "Memo": "",
                        "Debit": "",
                        "Credit": "",
                        "Balance": "",
                    })

                if acct:
                    if acct["normal"] == "Debit":
                        running_balance += line.get("debit", 0) - line.get("credit", 0)
                    else:
                        running_balance += line.get("credit", 0) - line.get("debit", 0)

                bal_str = fmt(abs(running_balance))
                if running_balance < 0:
                    bal_str += " Cr"

                rows.append({
                    "Date": line["date"],
                    "Reference": line["reference"],
                    "Account": acct_label if filter_acct else "",
                    "Memo": line.get("description") or line.get("entry_memo", ""),
                    "Debit": fmt(line["debit"]) if line.get("debit", 0) > 0 else "",
                    "Credit": fmt(line["credit"]) if line.get("credit", 0) > 0 else "",
                    "Balance": bal_str,
                })

            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# CHART OF ACCOUNTS TAB
# ══════════════════════════════════════════════════════════════════════
with tab_accounts:
    hdr_col, btn_col = st.columns([5, 1])
    with hdr_col:
        st.subheader("Chart of Accounts")
    with btn_col:
        if st.button("+ Add Account", type="primary", use_container_width=True):
            st.session_state.show_account_form = not st.session_state.show_account_form
            st.rerun()

    # ── Add Account Form ──────────────────────────────────────────────
    if st.session_state.show_account_form:
        with st.container(border=True):
            st.subheader("New GL Account")

            fc1, fc2, fc3, fc4 = st.columns([1, 2, 1, 1])
            with fc1:
                new_number = st.text_input("Account #", placeholder="e.g. 1050")
            with fc2:
                new_name = st.text_input("Account Name", placeholder="e.g. Petty Cash")
            with fc3:
                new_type = st.selectbox(
                    "Type", ["Asset", "Liability", "Equity", "Revenue", "Expense"]
                )
            with fc4:
                default_normal = "Debit" if new_type in ("Asset", "Expense") else "Credit"
                new_normal = st.selectbox(
                    "Normal Balance",
                    ["Debit", "Credit"],
                    index=0 if default_normal == "Debit" else 1,
                )

            fa_cancel, _, fa_save = st.columns([1, 4, 1])
            with fa_cancel:
                if st.button("Cancel", key="cancel_acct", use_container_width=True):
                    st.session_state.show_account_form = False
                    st.rerun()
            with fa_save:
                if st.button("Save Account", type="primary", key="save_acct", use_container_width=True):
                    errors = []
                    if not new_number.strip():
                        errors.append("Please enter an account number.")
                    if not new_name.strip():
                        errors.append("Please enter an account name.")
                    if any(a["number"] == new_number.strip() for a in st.session_state.accounts):
                        errors.append(f"Account number {new_number.strip()} already exists.")

                    if errors:
                        for err in errors:
                            st.error(err)
                    else:
                        st.session_state.accounts.append({
                            "id": f"custom_{int(datetime.now().timestamp() * 1000)}",
                            "number": new_number.strip(),
                            "name": new_name.strip(),
                            "type": new_type,
                            "normal": new_normal,
                        })
                        st.session_state.accounts.sort(key=lambda a: a["number"])
                        st.session_state.show_account_form = False
                        st.rerun()

    # ── Accounts Table ────────────────────────────────────────────────
    balances = compute_balances()
    type_order = ["Asset", "Liability", "Equity", "Revenue", "Expense"]

    grouped = {}
    for acct in sorted(st.session_state.accounts, key=lambda a: a["number"]):
        grouped.setdefault(acct["type"], []).append(acct)

    rows = []
    for acct_type in type_order:
        if acct_type not in grouped or not grouped[acct_type]:
            continue
        rows.append({
            "Account #": f"── {acct_type}s ──",
            "Account Name": "",
            "Type": "",
            "Normal Balance": "",
            "Balance": "",
        })
        for acct in grouped[acct_type]:
            bal = balances.get(acct["id"], 0.0)
            rows.append({
                "Account #": acct["number"],
                "Account Name": acct["name"],
                "Type": acct["type"],
                "Normal Balance": acct["normal"],
                "Balance": fmt(abs(bal)),
            })

    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# REPORTS TAB
# ══════════════════════════════════════════════════════════════════════
with tab_reports:
    st.subheader("Financial Reports")

    # ── Report Controls ──────────────────────────────────────────────
    ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([2, 1.5, 1.5, 1.5])
    with ctrl1:
        report_type = st.selectbox(
            "Report",
            ["Income Statement", "Balance Sheet", "Trial Balance", "Statement of Cash Flows"],
        )
    with ctrl2:
        # Determine sensible date defaults from existing entries
        if st.session_state.entries:
            all_dates = [e["date"] for e in st.session_state.entries]
            min_date = datetime.strptime(min(all_dates), "%Y-%m-%d").date()
            max_date = datetime.strptime(max(all_dates), "%Y-%m-%d").date()
            default_start = min_date.replace(month=1, day=1)
            default_end = max_date.replace(month=12, day=31)
        else:
            default_start = date.today().replace(month=1, day=1)
            default_end = date.today().replace(month=12, day=31)

        report_start = st.date_input("From", value=default_start, key="rpt_start")
    with ctrl3:
        report_end = st.date_input("To", value=default_end, key="rpt_end")
    with ctrl4:
        grouping = st.selectbox("Group By", ["None", "Monthly", "Quarterly", "Yearly"])

    if report_start > report_end:
        st.error("Start date must be on or before end date.")
    elif not st.session_state.entries:
        st.info("Post journal entries to generate reports.")
    else:
        # ── Generate Report ──────────────────────────────────────────
        with st.spinner("Generating report..."):
            if report_type == "Trial Balance":
                report_df = generate_trial_balance(report_start, report_end, grouping)
            elif report_type == "Income Statement":
                report_df = generate_income_statement(report_start, report_end, grouping)
            elif report_type == "Balance Sheet":
                report_df = generate_balance_sheet(report_start, report_end, grouping)
            elif report_type == "Statement of Cash Flows":
                report_df = generate_cash_flow_statement(report_start, report_end, grouping)
            else:
                report_df = pd.DataFrame()

        if report_df.empty:
            st.info("No data for the selected report and date range.")
        else:
            # ── Report Header ────────────────────────────────────────
            if report_type in ("Income Statement", "Trial Balance", "Statement of Cash Flows"):
                period_desc = f"For the Period {report_start.strftime('%B %d, %Y')} through {report_end.strftime('%B %d, %Y')}"
            else:
                period_desc = f"As of {report_end.strftime('%B %d, %Y')}"
            st.caption(period_desc)

            # ── Display Report ───────────────────────────────────────
            st.dataframe(
                report_df,
                hide_index=True,
                use_container_width=True,
                height=min(len(report_df) * 38 + 40, 800),
            )

            # ── CSV Export ───────────────────────────────────────────
            csv_df = report_df.copy()
            for col in csv_df.columns:
                csv_df[col] = csv_df[col].astype(str).str.replace(r"\*\*", "", regex=True)
            csv_data = csv_df.to_csv(index=False)

            file_name = (
                report_type.lower().replace(" ", "_")
                + f"_{report_start.strftime('%Y%m%d')}_{report_end.strftime('%Y%m%d')}.csv"
            )

            st.download_button(
                label="Export to CSV",
                data=csv_data,
                file_name=file_name,
                mime="text/csv",
                type="secondary",
            )
