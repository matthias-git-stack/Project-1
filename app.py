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

ENTITY_TYPES = [
    "Individual",
    "Joint Account",
    "Trust",
    "LLC",
    "Partnership",
    "S-Corp",
    "C-Corp",
    "IRA",
    "Roth IRA",
    "Foundation",
    "Other",
]

# ── Formatting ───────────────────────────────────────────────────────────────
def fmt(n):
    return f"{float(n):,.2f}"

def fmt_acct(n):
    """CPA-style: negatives in parentheses, zero as em-dash."""
    if n is None:
        return ""
    n = float(n)
    if abs(n) < 0.005:
        return "—"
    if n < 0:
        return f"({abs(n):,.2f})"
    return f"{n:,.2f}"

# ── Cash Flow Classification (by account NUMBER for consolidation safety) ────
# Using account numbers as canonical identifiers so classification works
# for both single-entity (id-based) and consolidated (number-as-id) contexts.
CASH_ACCOUNT_NUMBERS        = {"1000", "1010"}
OPERATING_WC_ASSET_NUMBERS  = {"1200", "1300", "1400"}
OPERATING_WC_LIAB_NUMBERS   = {"2000", "2100", "2300", "2400"}
DEPRECIATION_EXPENSE_NUMBER = "5400"
ACCUM_DEPRECIATION_NUMBER   = "1600"
INVESTING_ACCOUNT_NUMBERS   = {"1500"}
FINANCING_ACCOUNT_NUMBERS   = {"2200", "3000", "3100", "3300"}

def classify_for_cashflow(acct):
    num = acct["number"]
    if num in CASH_ACCOUNT_NUMBERS:        return "cash"
    if num == DEPRECIATION_EXPENSE_NUMBER: return "depr_expense"
    if num == ACCUM_DEPRECIATION_NUMBER:   return "accum_depr"
    if acct["type"] in ("Revenue", "Expense"): return "net_income"
    if num in OPERATING_WC_ASSET_NUMBERS:  return "operating_asset"
    if num in OPERATING_WC_LIAB_NUMBERS:   return "operating_liability"
    if num in INVESTING_ACCOUNT_NUMBERS:   return "investing"
    if num in FINANCING_ACCOUNT_NUMBERS:   return "financing"
    # Custom accounts: classify by type
    if acct["type"] == "Asset":     return "investing"
    if acct["type"] == "Liability": return "operating_liability"
    if acct["type"] == "Equity":    return "financing"
    return "operating_liability"

# ── State Init & Migration ───────────────────────────────────────────────────
def _new_entity_dict(name, entity_type, description="",
                     accounts=None, entries=None, next_entry_id=1, eid=None):
    if eid is None:
        eid = f"entity_{int(datetime.now().timestamp() * 1000)}"
    return {
        "id":            eid,
        "name":          name,
        "type":          entity_type,
        "description":   description,
        "accounts":      accounts if accounts is not None else [a.copy() for a in DEFAULT_ACCOUNTS],
        "entries":       entries  if entries  is not None else [],
        "next_entry_id": next_entry_id,
    }

def init_state():
    # ── Migrate legacy flat state (single-entity → multi-entity) ──
    if "accounts" in st.session_state and "entities" not in st.session_state:
        migrated = _new_entity_dict(
            "My Entity", "Other", "",
            accounts=st.session_state.pop("accounts"),
            entries=st.session_state.pop("entries", []),
            next_entry_id=st.session_state.pop("next_entry_id", 1),
            eid="entity_default",
        )
        st.session_state.entities = {"entity_default": migrated}
        st.session_state.active_entity_id = "entity_default"

    # ── Fresh initialisation ──
    if "entities" not in st.session_state:
        e = _new_entity_dict("Client 1", "Individual", eid="entity_001")
        st.session_state.entities = {"entity_001": e}
        st.session_state.active_entity_id = "entity_001"

    # ── Guard: active entity must exist ──
    if st.session_state.get("active_entity_id") not in st.session_state.entities:
        st.session_state.active_entity_id = next(iter(st.session_state.entities))

    # ── UI state defaults ──
    for key, default in [
        ("show_entry_form",    False),
        ("editing_entry_id",   None),
        ("form_date",          date.today()),
        ("form_ref",           ""),
        ("form_memo",          ""),
        ("form_lines",         []),
        ("view_entry_id",      None),
        ("show_account_form",  False),
        ("show_entity_form",   False),
        ("editing_entity_id",  None),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

init_state()

# ── Entity Accessors ─────────────────────────────────────────────────────────
def active_eid():
    return st.session_state.active_entity_id

def get_active_entity():
    return st.session_state.entities[active_eid()]

def get_accounts(entity_id=None):
    return st.session_state.entities[entity_id or active_eid()]["accounts"]

def get_entries(entity_id=None):
    return st.session_state.entities[entity_id or active_eid()]["entries"]

def get_next_id(entity_id=None):
    return st.session_state.entities[entity_id or active_eid()]["next_entry_id"]

def increment_next_id(entity_id=None):
    st.session_state.entities[entity_id or active_eid()]["next_entry_id"] += 1

def set_active_entity(eid):
    st.session_state.active_entity_id = eid
    close_entry_form()
    st.session_state.show_account_form = False
    st.session_state.view_entry_id = None

def create_entity(name, entity_type, description=""):
    e = _new_entity_dict(name, entity_type, description)
    st.session_state.entities[e["id"]] = e
    return e["id"]

def update_entity(eid, name, entity_type, description):
    e = st.session_state.entities[eid]
    e["name"] = name
    e["type"] = entity_type
    e["description"] = description

def delete_entity(eid):
    if len(st.session_state.entities) <= 1:
        return False
    del st.session_state.entities[eid]
    if active_eid() == eid:
        st.session_state.active_entity_id = next(iter(st.session_state.entities))
    return True

# ── Account Helpers (default to active entity) ───────────────────────────────
def account_by_id(account_id, accounts=None):
    if accounts is None:
        accounts = get_accounts()
    return next((a for a in accounts if a["id"] == account_id), None)

def account_label(acct):
    return f"{acct['number']} — {acct['name']}" if acct else ""

def get_account_options(accounts=None):
    if accounts is None:
        accounts = get_accounts()
    return [account_label(a) for a in sorted(accounts, key=lambda x: x["number"])]

def label_to_account(label, accounts=None):
    if accounts is None:
        accounts = get_accounts()
    return next((a for a in accounts if account_label(a) == label), None)

def compute_balances(accounts=None, entries=None):
    if accounts is None: accounts = get_accounts()
    if entries  is None: entries  = get_entries()
    balances = {a["id"]: 0.0 for a in accounts}
    for entry in entries:
        for line in entry["lines"]:
            acct = next((a for a in accounts if a["id"] == line["account_id"]), None)
            if not acct:
                continue
            dr, cr = line.get("debit", 0.0), line.get("credit", 0.0)
            delta = (dr - cr) if acct["normal"] == "Debit" else (cr - dr)
            balances[acct["id"]] = balances.get(acct["id"], 0.0) + delta
    return balances

# ── Consolidated Context Builder ─────────────────────────────────────────────
def build_report_context(entity_ids):
    """
    Merge accounts and entries from multiple entities for consolidated reporting.

    Merging rule: accounts with the same number are treated as the same GL
    account (first entity's metadata wins). Each entry's account_id lines are
    re-mapped so that the account's NUMBER becomes its canonical ID, ensuring
    cross-entity lookups resolve correctly.
    """
    acct_by_number = {}   # number → canonical account dict  (id = number)
    for eid in entity_ids:
        for acct in st.session_state.entities.get(eid, {}).get("accounts", []):
            if acct["number"] not in acct_by_number:
                acct_by_number[acct["number"]] = {**acct, "id": acct["number"]}

    merged_accounts = sorted(acct_by_number.values(), key=lambda a: a["number"])

    merged_entries = []
    for eid in entity_ids:
        entity = st.session_state.entities.get(eid, {})
        entity_name = entity.get("name", eid)
        id_to_number = {a["id"]: a["number"] for a in entity.get("accounts", [])}
        for entry in entity.get("entries", []):
            new_lines = []
            for line in entry["lines"]:
                num = id_to_number.get(line["account_id"])
                if num:
                    new_lines.append({**line, "account_id": num})
            if new_lines:
                merged_entries.append({
                    **entry,
                    "lines": new_lines,
                    "entity_name": entity_name,
                })

    return merged_accounts, merged_entries

# ── Period Boundaries ────────────────────────────────────────────────────────
def get_period_boundaries(start_dt, end_dt, grouping):
    """Return list of (label, period_start, period_end) tuples."""
    if grouping == "None":
        label = f"{start_dt.strftime('%b %d, %Y')} – {end_dt.strftime('%b %d, %Y')}"
        return [(label, start_dt, end_dt)]

    periods = []
    if grouping == "Monthly":
        cursor = start_dt.replace(day=1)
        while cursor <= end_dt:
            _, last = monthrange(cursor.year, cursor.month)
            periods.append((
                cursor.strftime("%b %Y"),
                max(cursor, start_dt),
                min(cursor.replace(day=last), end_dt),
            ))
            # Advance to first of next month
            cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)

    elif grouping == "Quarterly":
        q_month = ((start_dt.month - 1) // 3) * 3 + 1
        cursor = start_dt.replace(month=q_month, day=1)
        while cursor <= end_dt:
            em = cursor.month + 2
            ey = cursor.year + (em - 1) // 12
            em = (em - 1) % 12 + 1
            _, last = monthrange(ey, em)
            q = (cursor.month - 1) // 3 + 1
            periods.append((
                f"Q{q} {cursor.year}",
                max(cursor, start_dt),
                min(date(ey, em, last), end_dt),
            ))
            nm = cursor.month + 3
            cursor = date(cursor.year + (nm - 1) // 12, (nm - 1) % 12 + 1, 1)

    elif grouping == "Yearly":
        cursor = start_dt.replace(month=1, day=1)
        while cursor <= end_dt:
            periods.append((
                str(cursor.year),
                max(cursor, start_dt),
                min(cursor.replace(month=12, day=31), end_dt),
            ))
            cursor = cursor.replace(year=cursor.year + 1)

    return periods

# ── Core Computation (data-explicit; work for both single & consolidated) ────
def _filter_entries(entries, start_dt, end_dt):
    s, e = start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d")
    return [en for en in entries if s <= en["date"] <= e]

def compute_activity(start_dt, end_dt, accounts=None, entries=None):
    """Net activity per account in normal-balance direction for a date range."""
    if accounts is None: accounts = get_accounts()
    if entries  is None: entries  = get_entries()
    acct_map = {a["id"]: a for a in accounts}
    activity = {}
    for entry in _filter_entries(entries, start_dt, end_dt):
        for line in entry["lines"]:
            acct = acct_map.get(line["account_id"])
            if not acct:
                continue
            dr, cr = line.get("debit", 0.0), line.get("credit", 0.0)
            delta = (dr - cr) if acct["normal"] == "Debit" else (cr - dr)
            activity[line["account_id"]] = activity.get(line["account_id"], 0.0) + delta
    return activity

def compute_cumulative_balances_as_of(as_of_date, accounts=None, entries=None):
    """Cumulative normal-direction balance per account through as_of_date."""
    if accounts is None: accounts = get_accounts()
    if entries  is None: entries  = get_entries()
    d = as_of_date.strftime("%Y-%m-%d")
    acct_map = {a["id"]: a for a in accounts}
    balances = {a["id"]: 0.0 for a in accounts}
    for entry in entries:
        if entry["date"] > d:
            continue
        for line in entry["lines"]:
            acct = acct_map.get(line["account_id"])
            if not acct:
                continue
            dr, cr = line.get("debit", 0.0), line.get("credit", 0.0)
            delta = (dr - cr) if acct["normal"] == "Debit" else (cr - dr)
            balances[line["account_id"]] = balances.get(line["account_id"], 0.0) + delta
    return balances

def compute_raw_activity(start_dt, end_dt, entries=None):
    """Raw (debit − credit) per account for a date range; sign not adjusted."""
    if entries is None: entries = get_entries()
    activity = {}
    for entry in _filter_entries(entries, start_dt, end_dt):
        for line in entry["lines"]:
            aid = line["account_id"]
            dr, cr = line.get("debit", 0.0), line.get("credit", 0.0)
            activity[aid] = activity.get(aid, 0.0) + (dr - cr)
    return activity

# ── Report Generators ────────────────────────────────────────────────────────
def generate_trial_balance(start_dt, end_dt, grouping, accounts=None, entries=None):
    """Trial Balance: cumulative balances as of each period-end date."""
    if accounts is None: accounts = get_accounts()
    if entries  is None: entries  = get_entries()
    periods = get_period_boundaries(start_dt, end_dt, grouping)
    sorted_accts = sorted(accounts, key=lambda a: a["number"])
    type_order = ["Asset", "Liability", "Equity", "Revenue", "Expense"]

    rows = []
    totals_dr = {p[0]: 0.0 for p in periods}
    totals_cr = {p[0]: 0.0 for p in periods}

    for acct_type in type_order:
        accts = [a for a in sorted_accts if a["type"] == acct_type]
        if not accts:
            continue
        hdr = {"Account #": "", "Account Name": f"── {acct_type}s ──"}
        for lbl, _, _ in periods:
            hdr[f"{lbl} Dr"] = ""
            hdr[f"{lbl} Cr"] = ""
        rows.append(hdr)

        for acct in accts:
            row = {"Account #": acct["number"], "Account Name": acct["name"]}
            for lbl, _, p_end in periods:
                bal = compute_cumulative_balances_as_of(p_end, accounts, entries).get(acct["id"], 0.0)
                if acct["normal"] == "Debit":
                    if bal >= 0:
                        row[f"{lbl} Dr"] = fmt_acct(bal); row[f"{lbl} Cr"] = ""
                        totals_dr[lbl] += bal
                    else:
                        row[f"{lbl} Dr"] = ""; row[f"{lbl} Cr"] = fmt_acct(abs(bal))
                        totals_cr[lbl] += abs(bal)
                else:
                    if bal >= 0:
                        row[f"{lbl} Dr"] = ""; row[f"{lbl} Cr"] = fmt_acct(bal)
                        totals_cr[lbl] += bal
                    else:
                        row[f"{lbl} Dr"] = fmt_acct(abs(bal)); row[f"{lbl} Cr"] = ""
                        totals_dr[lbl] += abs(bal)
            rows.append(row)

    totals_row = {"Account #": "", "Account Name": "TOTALS"}
    for lbl, _, _ in periods:
        totals_row[f"{lbl} Dr"] = fmt_acct(totals_dr[lbl])
        totals_row[f"{lbl} Cr"] = fmt_acct(totals_cr[lbl])
    rows.append(totals_row)
    return pd.DataFrame(rows)


def generate_income_statement(start_dt, end_dt, grouping, accounts=None, entries=None):
    """Multi-step Income Statement with activity for each period."""
    if accounts is None: accounts = get_accounts()
    if entries  is None: entries  = get_entries()
    periods = get_period_boundaries(start_dt, end_dt, grouping)
    sorted_accts = sorted(accounts, key=lambda a: a["number"])
    show_total = len(periods) > 1

    revenue_accts = [a for a in sorted_accts if a["type"] == "Revenue"]
    cogs_accts    = [a for a in sorted_accts if a["number"] == "5000"]
    opex_accts    = [a for a in sorted_accts if a["type"] == "Expense" and a["number"] != "5000"]

    period_acts = [compute_activity(ps, pe, accounts, entries) for _, ps, pe in periods]

    rows = []

    def make_row(label, values, bold=False):
        p = "**" if bold else ""
        row = {"": f"{p}{label}{p}"}
        for i, (pl, _, _) in enumerate(periods):
            row[pl] = fmt_acct(values[i]) if values[i] is not None else ""
        if show_total:
            row["Total"] = fmt_acct(sum(v for v in values if v is not None))
        return row

    def blank():
        r = {"": ""}
        for pl, _, _ in periods: r[pl] = ""
        if show_total: r["Total"] = ""
        return r

    # Revenue
    rows.append(make_row("REVENUE", [None] * len(periods)))
    rev_tot = [0.0] * len(periods)
    for acct in revenue_accts:
        vals = [act.get(acct["id"], 0.0) for act in period_acts]
        for i, v in enumerate(vals): rev_tot[i] += v
        rows.append(make_row(f"  {acct['number']} {acct['name']}", vals))
    rows.append(make_row("Total Revenue", rev_tot, bold=True))
    rows.append(blank())

    # COGS
    cogs_tot = [0.0] * len(periods)
    if cogs_accts:
        rows.append(make_row("COST OF GOODS SOLD", [None] * len(periods)))
        for acct in cogs_accts:
            vals = [act.get(acct["id"], 0.0) for act in period_acts]
            for i, v in enumerate(vals): cogs_tot[i] += v
            rows.append(make_row(f"  {acct['number']} {acct['name']}", vals))
        rows.append(make_row("Total COGS", cogs_tot, bold=True))
        rows.append(blank())

    # Gross Profit
    gross = [rev_tot[i] - cogs_tot[i] for i in range(len(periods))]
    rows.append(make_row("GROSS PROFIT", gross, bold=True))
    rows.append(blank())

    # Operating Expenses
    rows.append(make_row("OPERATING EXPENSES", [None] * len(periods)))
    opex_tot = [0.0] * len(periods)
    for acct in opex_accts:
        vals = [act.get(acct["id"], 0.0) for act in period_acts]
        for i, v in enumerate(vals): opex_tot[i] += v
        rows.append(make_row(f"  {acct['number']} {acct['name']}", vals))
    rows.append(make_row("Total Operating Expenses", opex_tot, bold=True))
    rows.append(blank())

    net_income = [gross[i] - opex_tot[i] for i in range(len(periods))]
    rows.append(make_row("NET INCOME (LOSS)", net_income, bold=True))
    return pd.DataFrame(rows)


def generate_balance_sheet(start_dt, end_dt, grouping, accounts=None, entries=None):
    """Balance Sheet: cumulative balances as of each period-end date."""
    if accounts is None: accounts = get_accounts()
    if entries  is None: entries  = get_entries()
    periods = get_period_boundaries(start_dt, end_dt, grouping)
    sorted_accts = sorted(accounts, key=lambda a: a["number"])
    period_bals = [compute_cumulative_balances_as_of(pe, accounts, entries) for _, _, pe in periods]

    asset_accts   = [a for a in sorted_accts if a["type"] == "Asset"]
    liab_accts    = [a for a in sorted_accts if a["type"] == "Liability"]
    equity_accts  = [a for a in sorted_accts if a["type"] == "Equity"]
    revenue_accts = [a for a in sorted_accts if a["type"] == "Revenue"]
    expense_accts = [a for a in sorted_accts if a["type"] == "Expense"]

    rows = []

    def col(i):
        return f"As of {periods[i][2].strftime('%m/%d/%Y')}" if len(periods) == 1 else periods[i][0]

    def make_row(label, values, bold=False):
        p = "**" if bold else ""
        row = {"": f"{p}{label}{p}"}
        for i in range(len(periods)):
            row[col(i)] = fmt_acct(values[i]) if values[i] is not None else ""
        return row

    def blank():
        r = {"": ""}
        for i in range(len(periods)): r[col(i)] = ""
        return r

    # Assets
    rows.append(make_row("ASSETS", [None] * len(periods)))
    asset_tot = [0.0] * len(periods)
    for acct in asset_accts:
        vals = []
        for i, bals in enumerate(period_bals):
            v = bals.get(acct["id"], 0.0)
            if acct["normal"] == "Credit": v = -v   # contra-asset (Accum Depr)
            vals.append(v); asset_tot[i] += v
        rows.append(make_row(f"  {acct['number']} {acct['name']}", vals))
    rows.append(make_row("Total Assets", asset_tot, bold=True))
    rows.append(blank())

    # Liabilities
    rows.append(make_row("LIABILITIES", [None] * len(periods)))
    liab_tot = [0.0] * len(periods)
    for acct in liab_accts:
        vals = [bals.get(acct["id"], 0.0) for bals in period_bals]
        for i, v in enumerate(vals): liab_tot[i] += v
        rows.append(make_row(f"  {acct['number']} {acct['name']}", vals))
    rows.append(make_row("Total Liabilities", liab_tot, bold=True))
    rows.append(blank())

    # Equity
    rows.append(make_row("EQUITY", [None] * len(periods)))
    eq_tot = [0.0] * len(periods)
    for acct in equity_accts:
        vals = []
        for i, bals in enumerate(period_bals):
            v = bals.get(acct["id"], 0.0)
            if acct["normal"] == "Debit": v = -v   # dividends reduce equity
            vals.append(v); eq_tot[i] += v
        rows.append(make_row(f"  {acct['number']} {acct['name']}", vals))
    # Net income roll-up (cumulative revenue − expenses through period end)
    ni_vals = []
    for i, bals in enumerate(period_bals):
        rev = sum(bals.get(a["id"], 0.0) for a in revenue_accts)
        exp = sum(bals.get(a["id"], 0.0) for a in expense_accts)
        ni = rev - exp
        ni_vals.append(ni); eq_tot[i] += ni
    rows.append(make_row("  Net Income (Current Period)", ni_vals))
    rows.append(make_row("Total Equity", eq_tot, bold=True))
    rows.append(blank())

    total_le = [liab_tot[i] + eq_tot[i] for i in range(len(periods))]
    rows.append(make_row("TOTAL LIABILITIES & EQUITY", total_le, bold=True))
    return pd.DataFrame(rows)


def generate_cash_flow_statement(start_dt, end_dt, grouping, accounts=None, entries=None):
    """Statement of Cash Flows — indirect method."""
    if accounts is None: accounts = get_accounts()
    if entries  is None: entries  = get_entries()
    periods = get_period_boundaries(start_dt, end_dt, grouping)
    sorted_accts = sorted(accounts, key=lambda a: a["number"])
    show_total = len(periods) > 1

    revenue_accts = [a for a in sorted_accts if a["type"] == "Revenue"]
    expense_accts = [a for a in sorted_accts if a["type"] == "Expense"]

    period_act = [compute_activity(ps, pe, accounts, entries) for _, ps, pe in periods]
    period_raw = [compute_raw_activity(ps, pe, entries) for _, ps, pe in periods]

    rows = []

    def make_row(label, values, bold=False):
        p = "**" if bold else ""
        row = {"": f"{p}{label}{p}"}
        for i, (pl, _, _) in enumerate(periods):
            row[pl] = fmt_acct(values[i]) if values[i] is not None else ""
        if show_total:
            row["Total"] = fmt_acct(sum(v for v in values if v is not None))
        return row

    def blank():
        r = {"": ""}
        for pl, _, _ in periods: r[pl] = ""
        if show_total: r["Total"] = ""
        return r

    net_income = [
        sum(act.get(a["id"], 0.0) for a in revenue_accts)
        - sum(act.get(a["id"], 0.0) for a in expense_accts)
        for act in period_act
    ]

    # Locate depreciation expense account by number
    depr_acct_id = next((a["id"] for a in accounts if a["number"] == DEPRECIATION_EXPENSE_NUMBER), None)
    depr_vals = [act.get(depr_acct_id, 0.0) if depr_acct_id else 0.0 for act in period_act]

    # ── Operating ──
    rows.append(make_row("OPERATING ACTIVITIES", [None] * len(periods)))
    rows.append(make_row("  Net Income", net_income))
    rows.append(make_row("  Adjustments for non-cash items:", [None] * len(periods)))
    if any(abs(v) > 0.005 for v in depr_vals):
        rows.append(make_row("    Depreciation & Amortization", depr_vals))

    rows.append(make_row("  Changes in working capital:", [None] * len(periods)))
    op_adj = [0.0] * len(periods)
    for acct in sorted_accts:
        cf = classify_for_cashflow(acct)
        if cf in ("operating_asset", "operating_liability"):
            vals = [-(raw.get(acct["id"], 0.0)) for raw in period_raw]
            for i, v in enumerate(vals): op_adj[i] += v
            if any(abs(v) > 0.005 for v in vals):
                rows.append(make_row(f"    {acct['name']}", vals))

    net_ops = [net_income[i] + depr_vals[i] + op_adj[i] for i in range(len(periods))]
    rows.append(blank())
    rows.append(make_row("Net Cash from Operating Activities", net_ops, bold=True))
    rows.append(blank())

    # ── Investing ──
    rows.append(make_row("INVESTING ACTIVITIES", [None] * len(periods)))
    inv_tot = [0.0] * len(periods)
    for acct in sorted_accts:
        if classify_for_cashflow(acct) == "investing":
            vals = [-(raw.get(acct["id"], 0.0)) for raw in period_raw]
            for i, v in enumerate(vals): inv_tot[i] += v
            if any(abs(v) > 0.005 for v in vals):
                rows.append(make_row(f"  {acct['name']}", vals))
    rows.append(make_row("Net Cash from Investing Activities", inv_tot, bold=True))
    rows.append(blank())

    # ── Financing ──
    rows.append(make_row("FINANCING ACTIVITIES", [None] * len(periods)))
    fin_tot = [0.0] * len(periods)
    for acct in sorted_accts:
        if classify_for_cashflow(acct) == "financing":
            vals = [-(raw.get(acct["id"], 0.0)) for raw in period_raw]
            for i, v in enumerate(vals): fin_tot[i] += v
            if any(abs(v) > 0.005 for v in vals):
                rows.append(make_row(f"  {acct['name']}", vals))
    rows.append(make_row("Net Cash from Financing Activities", fin_tot, bold=True))
    rows.append(blank())

    # ── Summary ──
    net_change = [net_ops[i] + inv_tot[i] + fin_tot[i] for i in range(len(periods))]
    rows.append(make_row("NET CHANGE IN CASH", net_change, bold=True))

    cash_ids = {a["id"] for a in accounts if a["number"] in CASH_ACCOUNT_NUMBERS}
    beg_cash, end_cash = [], []
    for _, ps, pe in periods:
        beg_bals = compute_cumulative_balances_as_of(ps - timedelta(days=1), accounts, entries)
        beg_cash.append(sum(beg_bals.get(cid, 0.0) for cid in cash_ids))
        end_bals = compute_cumulative_balances_as_of(pe, accounts, entries)
        end_cash.append(sum(end_bals.get(cid, 0.0) for cid in cash_ids))

    rows.append(make_row("Beginning Cash Balance", beg_cash))
    rows.append(make_row("ENDING CASH BALANCE", end_cash, bold=True))
    return pd.DataFrame(rows)

# ── Entry Form Helpers ────────────────────────────────────────────────────────
def auto_ref():
    return f"JE-{get_next_id():04d}"

def open_entry_form(entry=None):
    st.session_state.show_entry_form = True
    st.session_state.view_entry_id = None
    st.session_state.editing_entry_id = entry["id"] if entry else None
    if entry:
        st.session_state.form_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
        st.session_state.form_ref  = entry["reference"]
        st.session_state.form_memo = entry["memo"]
        st.session_state.form_lines = [
            {
                "account":     account_label(account_by_id(l["account_id"])),
                "description": l.get("description", ""),
                "debit":       l.get("debit", 0.0),
                "credit":      l.get("credit", 0.0),
            }
            for l in entry["lines"]
        ]
    else:
        st.session_state.form_date  = date.today()
        st.session_state.form_ref   = auto_ref()
        st.session_state.form_memo  = ""
        st.session_state.form_lines = [
            {"account": "", "description": "", "debit": 0.0, "credit": 0.0},
            {"account": "", "description": "", "debit": 0.0, "credit": 0.0},
        ]

def close_entry_form():
    st.session_state.show_entry_form  = False
    st.session_state.editing_entry_id = None
    st.session_state.form_lines       = []

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Entity Management
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("Entities")

    all_entities = sorted(st.session_state.entities.values(), key=lambda e: e["name"])
    entity_names = [e["name"] for e in all_entities]
    entity_ids   = [e["id"]   for e in all_entities]
    cur_idx = entity_ids.index(active_eid()) if active_eid() in entity_ids else 0

    chosen_name = st.selectbox(
        "Active Entity",
        options=entity_names,
        index=cur_idx,
    )
    chosen_id = entity_ids[entity_names.index(chosen_name)]
    if chosen_id != active_eid():
        set_active_entity(chosen_id)
        st.rerun()

    ae = get_active_entity()
    meta_parts = [ae["type"]]
    if ae.get("description"):
        meta_parts.append(ae["description"])
    st.caption(" · ".join(meta_parts))
    n_je = len(get_entries())
    st.caption(f"{n_je} journal {'entry' if n_je == 1 else 'entries'}")

    st.divider()

    btn_new, btn_edit = st.columns(2)
    with btn_new:
        if st.button("+ New", use_container_width=True, key="sb_new_entity"):
            st.session_state.show_entity_form  = True
            st.session_state.editing_entity_id = None
            st.rerun()
    with btn_edit:
        if st.button("✏ Edit", use_container_width=True, key="sb_edit_entity"):
            st.session_state.show_entity_form  = True
            st.session_state.editing_entity_id = active_eid()
            st.rerun()

    if len(st.session_state.entities) > 1:
        if st.button(
            f"Delete \"{ae['name']}\"",
            use_container_width=True,
            type="secondary",
            key="sb_del_entity",
        ):
            delete_entity(active_eid())
            st.rerun()

    # ── Inline Entity Form ──
    if st.session_state.show_entity_form:
        st.divider()
        eid_editing  = st.session_state.editing_entity_id
        existing_ent = st.session_state.entities.get(eid_editing) if eid_editing else None

        st.subheader("Edit Entity" if existing_ent else "New Entity")

        ef_name = st.text_input(
            "Client / Entity Name",
            value=existing_ent["name"] if existing_ent else "",
            key="ef_name",
        )
        type_idx = ENTITY_TYPES.index(existing_ent["type"]) if existing_ent and existing_ent["type"] in ENTITY_TYPES else 0
        ef_type = st.selectbox("Entity Type", ENTITY_TYPES, index=type_idx, key="ef_type")
        ef_desc = st.text_input(
            "Description / Account #",
            value=existing_ent.get("description", "") if existing_ent else "",
            placeholder="e.g. Schwab #1234-5678",
            key="ef_desc",
        )

        ef_c, ef_s = st.columns(2)
        with ef_c:
            if st.button("Cancel", use_container_width=True, key="ef_cancel"):
                st.session_state.show_entity_form  = False
                st.session_state.editing_entity_id = None
                st.rerun()
        with ef_s:
            if st.button("Save", use_container_width=True, type="primary", key="ef_save"):
                if not ef_name.strip():
                    st.error("Name is required.")
                else:
                    if existing_ent:
                        update_entity(eid_editing, ef_name.strip(), ef_type, ef_desc.strip())
                    else:
                        new_eid = create_entity(ef_name.strip(), ef_type, ef_desc.strip())
                        set_active_entity(new_eid)
                    st.session_state.show_entity_form  = False
                    st.session_state.editing_entity_id = None
                    st.rerun()

    # ── Entity Directory ──
    if len(st.session_state.entities) > 1:
        st.divider()
        st.caption("**All Entities**")
        for ent in all_entities:
            marker = "▶" if ent["id"] == active_eid() else " "
            n = len(ent["entries"])
            st.caption(f"{marker} **{ent['name']}** · {ent['type']} · {n} JEs")

# ══════════════════════════════════════════════════════════════════════════════
# APP HEADER
# ══════════════════════════════════════════════════════════════════════════════
ae = get_active_entity()
st.title("Account Ledger")
entity_badge = f"**{ae['name']}** · {ae['type']}"
if ae.get("description"):
    entity_badge += f" · {ae['description']}"
st.caption(f"Active Entity: {entity_badge}")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_journal, tab_ledger, tab_accounts, tab_reports = st.tabs(
    ["Journal Entries", "General Ledger", "Chart of Accounts", "Reports"]
)

# ══════════════════════════════════════════════════════════════════════════════
# JOURNAL ENTRIES TAB
# ══════════════════════════════════════════════════════════════════════════════
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
        editing    = st.session_state.editing_entry_id is not None
        form_title = f"Edit Entry — {st.session_state.form_ref}" if editing else "New Journal Entry"

        with st.container(border=True):
            st.subheader(form_title)

            col_date, col_ref, col_memo = st.columns([1, 1, 2])
            with col_date:
                form_date = st.date_input("Date", value=st.session_state.form_date)
            with col_ref:
                form_ref = st.text_input("Reference #", value=st.session_state.form_ref)
            with col_memo:
                form_memo = st.text_input("Memo / Description", value=st.session_state.form_memo)

            st.markdown("**Line Items** — add rows with ＋ at the bottom; delete rows with the trash icon.")

            acct_options = get_account_options()
            lines_df = pd.DataFrame(
                st.session_state.form_lines,
                columns=["account", "description", "debit", "credit"],
            )
            edited_df = st.data_editor(
                lines_df,
                column_config={
                    "account":     st.column_config.SelectboxColumn("GL Account", options=acct_options, width="large"),
                    "description": st.column_config.TextColumn("Description", width="medium"),
                    "debit":       st.column_config.NumberColumn("Debit",  min_value=0.0, format="%.2f", width="small"),
                    "credit":      st.column_config.NumberColumn("Credit", min_value=0.0, format="%.2f", width="small"),
                },
                num_rows="dynamic",
                hide_index=True,
                use_container_width=True,
            )

            total_debit  = float(edited_df["debit"].fillna(0).sum())
            total_credit = float(edited_df["credit"].fillna(0).sum())
            diff = abs(total_debit - total_credit)

            tot_col, bal_col = st.columns(2)
            with tot_col:
                st.markdown(f"**Total Debits:** {fmt(total_debit)} &nbsp;|&nbsp; **Total Credits:** {fmt(total_credit)}")
            with bal_col:
                if diff < 0.005:
                    st.success("Entry is balanced ✓")
                else:
                    st.error(f"Out of balance by {fmt(diff)}")

            cancel_col, _, save_col = st.columns([1, 4, 1])
            with cancel_col:
                if st.button("Cancel", use_container_width=True, key="je_cancel"):
                    close_entry_form()
                    st.rerun()
            with save_col:
                if st.button("Post Entry", type="primary", use_container_width=True, key="je_post"):
                    errors = []
                    if not form_ref.strip():
                        errors.append("Please enter a reference number.")
                    valid_lines = edited_df[edited_df["account"].notna() & (edited_df["account"] != "")]
                    if len(valid_lines) < 2:
                        errors.append("A journal entry must have at least 2 lines with accounts selected.")
                    if diff >= 0.005:
                        errors.append(f"Entry is out of balance by {fmt(diff)}. Debits must equal credits.")
                    if total_debit == 0:
                        errors.append("Entry has no amounts.")

                    if errors:
                        for err in errors:
                            st.error(err)
                    else:
                        lines_internal = []
                        for _, row in valid_lines.iterrows():
                            acct = label_to_account(row["account"])
                            if acct:
                                lines_internal.append({
                                    "account_id":  acct["id"],
                                    "description": str(row.get("description") or ""),
                                    "debit":       float(row.get("debit")  or 0),
                                    "credit":      float(row.get("credit") or 0),
                                })

                        if st.session_state.editing_entry_id is not None:
                            idx = next(
                                (i for i, e in enumerate(get_entries())
                                 if e["id"] == st.session_state.editing_entry_id),
                                None,
                            )
                            if idx is not None:
                                get_entries()[idx] = {
                                    **get_entries()[idx],
                                    "date":      form_date.strftime("%Y-%m-%d"),
                                    "reference": form_ref.strip(),
                                    "memo":      form_memo.strip(),
                                    "lines":     lines_internal,
                                }
                        else:
                            get_entries().append({
                                "id":        get_next_id(),
                                "date":      form_date.strftime("%Y-%m-%d"),
                                "reference": form_ref.strip(),
                                "memo":      form_memo.strip(),
                                "lines":     lines_internal,
                            })
                            increment_next_id()

                        close_entry_form()
                        st.rerun()

    # ── Entry Detail View ─────────────────────────────────────────────
    if st.session_state.view_entry_id is not None:
        entry = next((e for e in get_entries() if e["id"] == st.session_state.view_entry_id), None)
        if entry:
            with st.container(border=True):
                tc, cc = st.columns([5, 1])
                with tc:
                    st.subheader(f"Journal Entry — {entry['reference']}")
                with cc:
                    if st.button("Close", use_container_width=True, key="je_close_modal"):
                        st.session_state.view_entry_id = None
                        st.rerun()

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Date",      entry["date"])
                m2.metric("Reference", entry["reference"])
                m3.metric("Memo",      entry["memo"] or "—")
                m4.metric("Total",     fmt(sum(l.get("debit", 0) for l in entry["lines"])))

                detail_rows = []
                for i, line in enumerate(entry["lines"]):
                    acct = account_by_id(line["account_id"])
                    detail_rows.append({
                        "#":           i + 1,
                        "Account":     account_label(acct) if acct else "Unknown",
                        "Description": line.get("description", ""),
                        "Debit":       fmt(line["debit"])  if line.get("debit",  0) > 0 else "",
                        "Credit":      fmt(line["credit"]) if line.get("credit", 0) > 0 else "",
                    })
                total_d = sum(l.get("debit",  0) for l in entry["lines"])
                total_c = sum(l.get("credit", 0) for l in entry["lines"])
                detail_rows.append({"#": "", "Account": "**Totals**", "Description": "",
                                     "Debit": fmt(total_d), "Credit": fmt(total_c)})
                st.dataframe(pd.DataFrame(detail_rows), hide_index=True, use_container_width=True)

    # ── Entries List ──────────────────────────────────────────────────
    if not get_entries():
        st.info("No journal entries yet. Click **+ New Entry** to get started.")
    else:
        sorted_entries = sorted(get_entries(), key=lambda e: (e["date"], e["id"]))

        h1, h2, h3, h4, h5, h6 = st.columns([1.2, 1.2, 3, 1.2, 1.2, 2])
        h1.markdown("**Date**"); h2.markdown("**Reference**"); h3.markdown("**Memo**")
        h4.markdown("**Debits**"); h5.markdown("**Credits**"); h6.markdown("**Actions**")
        st.divider()

        for entry in sorted_entries:
            total_d = sum(l.get("debit",  0) for l in entry["lines"])
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
                        st.session_state.view_entry_id  = entry["id"]
                        st.session_state.show_entry_form = False
                        st.rerun()
                with a2:
                    if st.button("Edit", key=f"edit_{entry['id']}"):
                        e = next((x for x in get_entries() if x["id"] == entry["id"]), None)
                        if e:
                            open_entry_form(e)
                            st.rerun()
                with a3:
                    if st.button("Del", key=f"del_{entry['id']}"):
                        st.session_state.entities[active_eid()]["entries"] = [
                            x for x in get_entries() if x["id"] != entry["id"]
                        ]
                        if st.session_state.view_entry_id == entry["id"]:
                            st.session_state.view_entry_id = None
                        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# GENERAL LEDGER TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_ledger:
    st.subheader("General Ledger")

    acct_options_all = ["— All Accounts —"] + get_account_options()
    filter_label = st.selectbox("Filter by Account", options=acct_options_all)
    filter_acct  = label_to_account(filter_label) if filter_label != "— All Accounts —" else None

    if not get_entries():
        st.info("Post journal entries to see ledger activity.")
    else:
        sorted_entries = sorted(get_entries(), key=lambda e: (e["date"], e["id"]))
        all_lines = []
        for entry in sorted_entries:
            for line in entry["lines"]:
                if filter_acct and line["account_id"] != filter_acct["id"]:
                    continue
                all_lines.append({**line, "date": entry["date"],
                                   "reference": entry["reference"],
                                   "entry_memo": entry["memo"]})

        if not all_lines:
            st.info("No transactions for the selected account.")
        else:
            rows = []
            running_balance  = 0.0
            current_acct_id  = None

            for line in all_lines:
                acct      = account_by_id(line["account_id"])
                acct_lbl  = account_label(acct) if acct else "Unknown"

                if not filter_acct and line["account_id"] != current_acct_id:
                    current_acct_id  = line["account_id"]
                    running_balance  = 0.0
                    rows.append({"Date": "", "Reference": "",
                                 "Account": f"── {acct_lbl} ──",
                                 "Memo": "", "Debit": "", "Credit": "", "Balance": ""})

                if acct:
                    if acct["normal"] == "Debit":
                        running_balance += line.get("debit", 0) - line.get("credit", 0)
                    else:
                        running_balance += line.get("credit", 0) - line.get("debit", 0)

                bal_str = fmt(abs(running_balance))
                if running_balance < 0:
                    bal_str += " Cr"

                rows.append({
                    "Date":      line["date"],
                    "Reference": line["reference"],
                    "Account":   acct_lbl if filter_acct else "",
                    "Memo":      line.get("description") or line.get("entry_memo", ""),
                    "Debit":     fmt(line["debit"])  if line.get("debit",  0) > 0 else "",
                    "Credit":    fmt(line["credit"]) if line.get("credit", 0) > 0 else "",
                    "Balance":   bal_str,
                })

            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# CHART OF ACCOUNTS TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_accounts:
    hdr_col, btn_col = st.columns([5, 1])
    with hdr_col:
        st.subheader("Chart of Accounts")
    with btn_col:
        if st.button("+ Add Account", type="primary", use_container_width=True):
            st.session_state.show_account_form = not st.session_state.show_account_form
            st.rerun()

    if st.session_state.show_account_form:
        with st.container(border=True):
            st.subheader("New GL Account")
            fc1, fc2, fc3, fc4 = st.columns([1, 2, 1, 1])
            with fc1:
                new_number = st.text_input("Account #", placeholder="e.g. 1050")
            with fc2:
                new_name = st.text_input("Account Name", placeholder="e.g. Petty Cash")
            with fc3:
                new_type = st.selectbox("Type", ["Asset", "Liability", "Equity", "Revenue", "Expense"])
            with fc4:
                default_normal = "Debit" if new_type in ("Asset", "Expense") else "Credit"
                new_normal = st.selectbox("Normal Balance", ["Debit", "Credit"],
                                          index=0 if default_normal == "Debit" else 1)
            fa_c, _, fa_s = st.columns([1, 4, 1])
            with fa_c:
                if st.button("Cancel", key="cancel_acct", use_container_width=True):
                    st.session_state.show_account_form = False
                    st.rerun()
            with fa_s:
                if st.button("Save Account", type="primary", key="save_acct", use_container_width=True):
                    errors = []
                    if not new_number.strip(): errors.append("Please enter an account number.")
                    if not new_name.strip():   errors.append("Please enter an account name.")
                    if any(a["number"] == new_number.strip() for a in get_accounts()):
                        errors.append(f"Account number {new_number.strip()} already exists.")
                    if errors:
                        for err in errors: st.error(err)
                    else:
                        get_accounts().append({
                            "id":     f"custom_{int(datetime.now().timestamp() * 1000)}",
                            "number": new_number.strip(),
                            "name":   new_name.strip(),
                            "type":   new_type,
                            "normal": new_normal,
                        })
                        get_accounts().sort(key=lambda a: a["number"])
                        st.session_state.show_account_form = False
                        st.rerun()

    balances   = compute_balances()
    type_order = ["Asset", "Liability", "Equity", "Revenue", "Expense"]
    grouped    = {}
    for acct in sorted(get_accounts(), key=lambda a: a["number"]):
        grouped.setdefault(acct["type"], []).append(acct)

    rows = []
    for acct_type in type_order:
        if acct_type not in grouped or not grouped[acct_type]:
            continue
        rows.append({"Account #": f"── {acct_type}s ──", "Account Name": "",
                     "Type": "", "Normal Balance": "", "Balance": ""})
        for acct in grouped[acct_type]:
            bal = balances.get(acct["id"], 0.0)
            rows.append({
                "Account #":      acct["number"],
                "Account Name":   acct["name"],
                "Type":           acct["type"],
                "Normal Balance": acct["normal"],
                "Balance":        fmt(abs(bal)),
            })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# REPORTS TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_reports:
    st.subheader("Financial Reports")

    # ── Entity Selection ──────────────────────────────────────────────
    all_ent_list  = sorted(st.session_state.entities.values(), key=lambda e: e["name"])
    all_ent_names = [e["name"] for e in all_ent_list]
    all_ent_ids   = [e["id"]   for e in all_ent_list]

    # Default to the active entity
    active_name = get_active_entity()["name"]
    default_sel = [active_name] if active_name in all_ent_names else [all_ent_names[0]]

    selected_names = st.multiselect(
        "Entities to include in this report",
        options=all_ent_names,
        default=default_sel,
        help=(
            "Select one entity for a standard report. "
            "Select multiple to generate a consolidated report where accounts "
            "with the same number are combined across entities."
        ),
    )
    selected_ids = [all_ent_ids[all_ent_names.index(n)] for n in selected_names]

    is_consolidated = len(selected_ids) > 1
    if is_consolidated:
        st.info(
            f"**Consolidated** across {len(selected_ids)} entities: "
            + ", ".join(f"*{n}*" for n in selected_names)
        )

    # ── Report Controls ───────────────────────────────────────────────
    ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([2, 1.5, 1.5, 1.5])
    with ctrl1:
        report_type = st.selectbox(
            "Report",
            ["Income Statement", "Balance Sheet", "Trial Balance", "Statement of Cash Flows"],
        )
    with ctrl2:
        if selected_ids:
            all_dates = [
                e["date"]
                for eid in selected_ids
                for e in st.session_state.entities[eid]["entries"]
            ]
            if all_dates:
                default_start = datetime.strptime(min(all_dates), "%Y-%m-%d").date().replace(month=1, day=1)
                default_end   = datetime.strptime(max(all_dates), "%Y-%m-%d").date().replace(month=12, day=31)
            else:
                default_start = date.today().replace(month=1, day=1)
                default_end   = date.today().replace(month=12, day=31)
        else:
            default_start = date.today().replace(month=1, day=1)
            default_end   = date.today().replace(month=12, day=31)
        report_start = st.date_input("From", value=default_start, key="rpt_start")
    with ctrl3:
        report_end = st.date_input("To", value=default_end, key="rpt_end")
    with ctrl4:
        grouping = st.selectbox("Group By", ["None", "Monthly", "Quarterly", "Yearly"])

    # ── Generate ──────────────────────────────────────────────────────
    if not selected_ids:
        st.warning("Select at least one entity above.")
    elif report_start > report_end:
        st.error("Start date must be on or before end date.")
    elif not any(st.session_state.entities[eid]["entries"] for eid in selected_ids):
        st.info("No journal entries found for the selected entities.")
    else:
        # Build data context (single-entity or consolidated)
        if is_consolidated:
            rpt_accounts, rpt_entries = build_report_context(selected_ids)
        else:
            rpt_accounts = get_accounts(selected_ids[0])
            rpt_entries  = get_entries(selected_ids[0])

        with st.spinner("Generating report…"):
            if report_type == "Income Statement":
                report_df = generate_income_statement(report_start, report_end, grouping, rpt_accounts, rpt_entries)
            elif report_type == "Balance Sheet":
                report_df = generate_balance_sheet(report_start, report_end, grouping, rpt_accounts, rpt_entries)
            elif report_type == "Trial Balance":
                report_df = generate_trial_balance(report_start, report_end, grouping, rpt_accounts, rpt_entries)
            elif report_type == "Statement of Cash Flows":
                report_df = generate_cash_flow_statement(report_start, report_end, grouping, rpt_accounts, rpt_entries)
            else:
                report_df = pd.DataFrame()

        if report_df.empty:
            st.info("No data for the selected parameters.")
        else:
            # Report header
            entity_label = (
                f"CONSOLIDATED — {', '.join(selected_names)}"
                if is_consolidated
                else selected_names[0]
            )
            if report_type in ("Income Statement", "Trial Balance", "Statement of Cash Flows"):
                period_desc = (
                    f"{entity_label} — "
                    f"For the Period {report_start.strftime('%B %d, %Y')} "
                    f"through {report_end.strftime('%B %d, %Y')}"
                )
            else:
                period_desc = f"{entity_label} — As of {report_end.strftime('%B %d, %Y')}"
            st.caption(period_desc)

            st.dataframe(
                report_df,
                hide_index=True,
                use_container_width=True,
                height=min(len(report_df) * 38 + 40, 800),
            )

            # CSV export (strip markdown bold markers)
            csv_df = report_df.copy()
            for col in csv_df.columns:
                csv_df[col] = csv_df[col].astype(str).str.replace(r"\*\*", "", regex=True)

            st.download_button(
                label="Export to CSV",
                data=csv_df.to_csv(index=False),
                file_name=(
                    report_type.lower().replace(" ", "_")
                    + f"_{report_start.strftime('%Y%m%d')}_{report_end.strftime('%Y%m%d')}.csv"
                ),
                mime="text/csv",
                type="secondary",
            )
