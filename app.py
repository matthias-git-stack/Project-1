import streamlit as st
import pandas as pd
from datetime import date, datetime

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

# ── App Header ──────────────────────────────────────────────────────────────
st.title("Account Ledger")

# ── Tabs ────────────────────────────────────────────────────────────────────
tab_journal, tab_ledger, tab_accounts = st.tabs(["Journal Entries", "General Ledger", "Chart of Accounts"])

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
