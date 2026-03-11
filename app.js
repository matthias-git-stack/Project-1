/* ══════════════════════════════════════════════════════════
   Account Ledger — app.js
   ══════════════════════════════════════════════════════════ */

'use strict';

/* ── State ─────────────────────────────────────────────────── */
const state = {
  accounts: [],          // Chart of Accounts
  entries: [],           // Posted journal entries
  nextEntryId: 1,
  editingEntryId: null,  // null = new entry
};

/* ── Default Chart of Accounts ─────────────────────────────── */
const DEFAULT_ACCOUNTS = [
  // Assets
  { id: 'a1000', number: '1000', name: 'Cash',                         type: 'Asset',     normal: 'Debit'  },
  { id: 'a1010', number: '1010', name: 'Petty Cash',                   type: 'Asset',     normal: 'Debit'  },
  { id: 'a1200', number: '1200', name: 'Accounts Receivable',          type: 'Asset',     normal: 'Debit'  },
  { id: 'a1300', number: '1300', name: 'Inventory',                    type: 'Asset',     normal: 'Debit'  },
  { id: 'a1400', number: '1400', name: 'Prepaid Expenses',             type: 'Asset',     normal: 'Debit'  },
  { id: 'a1500', number: '1500', name: 'Property, Plant & Equipment',  type: 'Asset',     normal: 'Debit'  },
  { id: 'a1600', number: '1600', name: 'Accumulated Depreciation',     type: 'Asset',     normal: 'Credit' },
  // Liabilities
  { id: 'l2000', number: '2000', name: 'Accounts Payable',             type: 'Liability', normal: 'Credit' },
  { id: 'l2100', number: '2100', name: 'Accrued Liabilities',          type: 'Liability', normal: 'Credit' },
  { id: 'l2200', number: '2200', name: 'Notes Payable',                type: 'Liability', normal: 'Credit' },
  { id: 'l2300', number: '2300', name: 'Deferred Revenue',             type: 'Liability', normal: 'Credit' },
  { id: 'l2400', number: '2400', name: 'Income Tax Payable',           type: 'Liability', normal: 'Credit' },
  // Equity
  { id: 'e3000', number: '3000', name: 'Common Stock',                 type: 'Equity',    normal: 'Credit' },
  { id: 'e3100', number: '3100', name: 'Additional Paid-In Capital',   type: 'Equity',    normal: 'Credit' },
  { id: 'e3200', number: '3200', name: 'Retained Earnings',            type: 'Equity',    normal: 'Credit' },
  { id: 'e3300', number: '3300', name: 'Dividends Paid',               type: 'Equity',    normal: 'Debit'  },
  // Revenue
  { id: 'r4000', number: '4000', name: 'Sales Revenue',                type: 'Revenue',   normal: 'Credit' },
  { id: 'r4100', number: '4100', name: 'Service Revenue',              type: 'Revenue',   normal: 'Credit' },
  { id: 'r4200', number: '4200', name: 'Interest Income',              type: 'Revenue',   normal: 'Credit' },
  { id: 'r4300', number: '4300', name: 'Other Income',                 type: 'Revenue',   normal: 'Credit' },
  // Expenses
  { id: 'x5000', number: '5000', name: 'Cost of Goods Sold',           type: 'Expense',   normal: 'Debit'  },
  { id: 'x5100', number: '5100', name: 'Salaries & Wages Expense',     type: 'Expense',   normal: 'Debit'  },
  { id: 'x5200', number: '5200', name: 'Rent Expense',                 type: 'Expense',   normal: 'Debit'  },
  { id: 'x5300', number: '5300', name: 'Utilities Expense',            type: 'Expense',   normal: 'Debit'  },
  { id: 'x5400', number: '5400', name: 'Depreciation Expense',         type: 'Expense',   normal: 'Debit'  },
  { id: 'x5500', number: '5500', name: 'Insurance Expense',            type: 'Expense',   normal: 'Debit'  },
  { id: 'x5600', number: '5600', name: 'Office Supplies Expense',      type: 'Expense',   normal: 'Debit'  },
  { id: 'x5700', number: '5700', name: 'Advertising Expense',          type: 'Expense',   normal: 'Debit'  },
  { id: 'x5800', number: '5800', name: 'Interest Expense',             type: 'Expense',   normal: 'Debit'  },
  { id: 'x5900', number: '5900', name: 'Income Tax Expense',           type: 'Expense',   normal: 'Debit'  },
];

/* ── Helpers ───────────────────────────────────────────────── */
const $ = id => document.getElementById(id);
const fmt = n => n.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');

function today() {
  const d = new Date();
  return d.toISOString().slice(0, 10);
}

function accountById(id) {
  return state.accounts.find(a => a.id === id);
}

function typeBadge(type) {
  const cls = { Asset: 'asset', Liability: 'liability', Equity: 'equity', Revenue: 'revenue', Expense: 'expense' };
  return `<span class="badge badge-${cls[type] || ''}">${type}</span>`;
}

/** Compute running account balances from all posted entries */
function computeBalances() {
  const balances = {};
  state.accounts.forEach(a => { balances[a.id] = 0; });
  state.entries.forEach(entry => {
    entry.lines.forEach(line => {
      if (!balances.hasOwnProperty(line.accountId)) balances[line.accountId] = 0;
      const acct = accountById(line.accountId);
      if (!acct) return;
      if (acct.normal === 'Debit') {
        balances[line.accountId] += line.debit - line.credit;
      } else {
        balances[line.accountId] += line.credit - line.debit;
      }
    });
  });
  return balances;
}

/* ── Persistence ───────────────────────────────────────────── */
function saveState() {
  localStorage.setItem('ledger_state', JSON.stringify({
    accounts: state.accounts,
    entries: state.entries,
    nextEntryId: state.nextEntryId,
  }));
}

function loadState() {
  const raw = localStorage.getItem('ledger_state');
  if (raw) {
    const saved = JSON.parse(raw);
    state.accounts    = saved.accounts    || DEFAULT_ACCOUNTS;
    state.entries     = saved.entries     || [];
    state.nextEntryId = saved.nextEntryId || 1;
  } else {
    state.accounts = DEFAULT_ACCOUNTS.map(a => ({ ...a }));
  }
}

/* ── Tab Switching ─────────────────────────────────────────── */
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    $(`tab-${btn.dataset.tab}`).classList.add('active');

    if (btn.dataset.tab === 'ledger')   renderLedger();
    if (btn.dataset.tab === 'accounts') renderCoA();
  });
});

/* ══════════════════════════════════════════════════════════
   JOURNAL ENTRIES
   ══════════════════════════════════════════════════════════ */

/* ── Entry Form State ──────────────────────────────────────── */
let lineItems = [];  // { id, accountId, description, debit, credit }
let lineCounter = 0;

function newLineItem() {
  return { id: ++lineCounter, accountId: '', description: '', debit: 0, credit: 0 };
}

/* ── Open / Close Form ─────────────────────────────────────── */
function openEntryForm(existingEntry) {
  state.editingEntryId = existingEntry ? existingEntry.id : null;
  $('form-title').textContent = existingEntry ? `Edit Entry — ${existingEntry.reference}` : 'New Journal Entry';

  // Populate header fields
  $('entry-date').value = existingEntry ? existingEntry.date : today();
  $('entry-ref').value  = existingEntry ? existingEntry.reference : autoRef();
  $('entry-memo').value = existingEntry ? existingEntry.memo : '';

  // Populate lines
  if (existingEntry) {
    lineItems = existingEntry.lines.map(l => ({ ...l }));
    lineCounter = lineItems.reduce((m, l) => Math.max(m, l.id), 0);
  } else {
    lineItems = [newLineItem(), newLineItem()];
  }

  renderLineItems();
  $('entry-form-container').classList.remove('hidden');
  $('entry-date').focus();
}

function closeEntryForm() {
  $('entry-form-container').classList.add('hidden');
  lineItems = [];
}

function autoRef() {
  return `JE-${String(state.nextEntryId).padStart(4, '0')}`;
}

/* ── Render Line Items ─────────────────────────────────────── */
function renderLineItems() {
  const tbody = $('line-items-body');
  tbody.innerHTML = '';

  lineItems.forEach((line, idx) => {
    const tr = document.createElement('tr');
    tr.dataset.lineId = line.id;
    tr.innerHTML = `
      <td class="row-num">${idx + 1}</td>
      <td>
        <select class="acct-select" data-field="accountId">
          <option value="">— Select account —</option>
          ${accountOptionsHtml(line.accountId)}
        </select>
      </td>
      <td><input type="text" class="desc-input" data-field="description" value="${escHtml(line.description)}" placeholder="Line description" /></td>
      <td class="amount-col"><input type="number" class="amount-input" data-field="debit"  min="0" step="0.01" value="${line.debit  || ''}" placeholder="0.00" /></td>
      <td class="amount-col"><input type="number" class="amount-input" data-field="credit" min="0" step="0.01" value="${line.credit || ''}" placeholder="0.00" /></td>
      <td class="action-col"><button class="btn-icon remove-line-btn" title="Remove line">&times;</button></td>
    `;

    // Wire up events
    tr.querySelector('[data-field="accountId"]').addEventListener('change', e => {
      updateLine(line.id, 'accountId', e.target.value);
    });
    tr.querySelector('[data-field="description"]').addEventListener('input', e => {
      updateLine(line.id, 'description', e.target.value);
    });
    tr.querySelector('[data-field="debit"]').addEventListener('input', e => {
      const v = parseFloat(e.target.value) || 0;
      updateLine(line.id, 'debit', v);
      if (v > 0) {
        const creditInput = tr.querySelector('[data-field="credit"]');
        creditInput.value = '';
        updateLine(line.id, 'credit', 0);
      }
    });
    tr.querySelector('[data-field="credit"]').addEventListener('input', e => {
      const v = parseFloat(e.target.value) || 0;
      updateLine(line.id, 'credit', v);
      if (v > 0) {
        const debitInput = tr.querySelector('[data-field="debit"]');
        debitInput.value = '';
        updateLine(line.id, 'debit', 0);
      }
    });
    tr.querySelector('.remove-line-btn').addEventListener('click', () => {
      removeLine(line.id);
    });

    tbody.appendChild(tr);
  });

  updateTotals();
}

function accountOptionsHtml(selectedId) {
  const grouped = groupAccountsByType();
  const order = ['Asset', 'Liability', 'Equity', 'Revenue', 'Expense'];
  let html = '';
  order.forEach(type => {
    if (!grouped[type] || grouped[type].length === 0) return;
    html += `<optgroup label="${type}">`;
    grouped[type].forEach(a => {
      html += `<option value="${a.id}" ${a.id === selectedId ? 'selected' : ''}>${a.number} — ${escHtml(a.name)}</option>`;
    });
    html += '</optgroup>';
  });
  return html;
}

function groupAccountsByType() {
  const groups = {};
  const sorted = [...state.accounts].sort((a, b) => a.number.localeCompare(b.number));
  sorted.forEach(a => {
    if (!groups[a.type]) groups[a.type] = [];
    groups[a.type].push(a);
  });
  return groups;
}

function updateLine(id, field, value) {
  const line = lineItems.find(l => l.id === id);
  if (line) line[field] = value;
  updateTotals();
}

function removeLine(id) {
  if (lineItems.length <= 2) { alert('A journal entry must have at least 2 lines.'); return; }
  lineItems = lineItems.filter(l => l.id !== id);
  renderLineItems();
}

function updateTotals() {
  const totalD = lineItems.reduce((s, l) => s + (l.debit  || 0), 0);
  const totalC = lineItems.reduce((s, l) => s + (l.credit || 0), 0);

  $('total-debit').textContent  = fmt(totalD);
  $('total-credit').textContent = fmt(totalC);

  const msg = $('balance-msg');
  const diff = Math.abs(totalD - totalC);
  if (diff < 0.005) {
    msg.textContent = 'Entry is balanced \u2713';
    msg.className = 'balance-ok';
  } else {
    msg.textContent = `Out of balance by ${fmt(diff)}`;
    msg.className = 'balance-err';
  }
}

/* ── Add / Save / Cancel ───────────────────────────────────── */
$('btn-new-entry').addEventListener('click', () => openEntryForm(null));

$('btn-add-line').addEventListener('click', () => {
  lineItems.push(newLineItem());
  renderLineItems();
});

$('btn-cancel-entry').addEventListener('click', closeEntryForm);

$('btn-save-entry').addEventListener('click', () => {
  // Validate header
  const date = $('entry-date').value;
  const ref  = $('entry-ref').value.trim();
  const memo = $('entry-memo').value.trim();

  if (!date) { alert('Please enter a date.'); return; }
  if (!ref)  { alert('Please enter a reference number.'); return; }

  // Validate lines
  const hasAccount = lineItems.every(l => l.accountId);
  if (!hasAccount) { alert('Please select a GL account for every line.'); return; }

  const totalD = lineItems.reduce((s, l) => s + (l.debit  || 0), 0);
  const totalC = lineItems.reduce((s, l) => s + (l.credit || 0), 0);
  if (Math.abs(totalD - totalC) >= 0.005) {
    alert(`Entry is out of balance by ${fmt(Math.abs(totalD - totalC))}. Debits must equal credits.`);
    return;
  }
  if (totalD === 0) { alert('Entry has no amounts. Please enter debit or credit values.'); return; }

  if (state.editingEntryId !== null) {
    // Update existing
    const idx = state.entries.findIndex(e => e.id === state.editingEntryId);
    if (idx !== -1) {
      state.entries[idx] = { ...state.entries[idx], date, reference: ref, memo, lines: lineItems.map(l => ({ ...l })) };
    }
  } else {
    // New entry
    state.entries.push({
      id: state.nextEntryId++,
      date,
      reference: ref,
      memo,
      lines: lineItems.map(l => ({ ...l })),
    });
  }

  saveState();
  closeEntryForm();
  renderEntriesList();
});

/* ── Entries List ──────────────────────────────────────────── */
function renderEntriesList() {
  const tbody = $('entries-tbody');
  tbody.innerHTML = '';

  if (state.entries.length === 0) {
    $('no-entries-msg').classList.remove('hidden');
    $('entries-table-container').classList.add('hidden');
    return;
  }

  $('no-entries-msg').classList.add('hidden');
  $('entries-table-container').classList.remove('hidden');

  const sorted = [...state.entries].sort((a, b) => a.date.localeCompare(b.date) || a.id - b.id);

  sorted.forEach(entry => {
    const totalD = entry.lines.reduce((s, l) => s + (l.debit  || 0), 0);
    const totalC = entry.lines.reduce((s, l) => s + (l.credit || 0), 0);
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${formatDate(entry.date)}</td>
      <td><code>${escHtml(entry.reference)}</code></td>
      <td>${escHtml(entry.memo)}</td>
      <td class="amount-col debit-amt">${fmt(totalD)}</td>
      <td class="amount-col credit-amt">${fmt(totalC)}</td>
      <td class="action-col">
        <button class="btn btn-secondary btn-sm view-entry-btn" data-id="${entry.id}" style="font-size:.8rem;padding:.3rem .7rem;">View</button>
        <button class="btn btn-ghost btn-sm edit-entry-btn" data-id="${entry.id}" style="font-size:.8rem;padding:.3rem .7rem;">Edit</button>
        <button class="btn btn-ghost btn-sm delete-entry-btn" data-id="${entry.id}" style="font-size:.8rem;padding:.3rem .7rem;color:var(--clr-danger);">Delete</button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  // Bind row buttons
  tbody.querySelectorAll('.view-entry-btn').forEach(btn => {
    btn.addEventListener('click', () => openEntryModal(parseInt(btn.dataset.id)));
  });
  tbody.querySelectorAll('.edit-entry-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const entry = state.entries.find(e => e.id === parseInt(btn.dataset.id));
      if (entry) openEntryForm(entry);
    });
  });
  tbody.querySelectorAll('.delete-entry-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const entry = state.entries.find(e => e.id === parseInt(btn.dataset.id));
      if (entry && confirm(`Delete entry "${entry.reference}"? This cannot be undone.`)) {
        state.entries = state.entries.filter(e => e.id !== entry.id);
        saveState();
        renderEntriesList();
      }
    });
  });
}

/* ── Entry Detail Modal ────────────────────────────────────── */
function openEntryModal(id) {
  const entry = state.entries.find(e => e.id === id);
  if (!entry) return;

  const totalD = entry.lines.reduce((s, l) => s + (l.debit  || 0), 0);

  $('modal-title').textContent = `Journal Entry — ${entry.reference}`;

  const linesHtml = entry.lines.map((line, idx) => {
    const acct = accountById(line.accountId);
    const acctLabel = acct ? `${acct.number} — ${escHtml(acct.name)}` : 'Unknown Account';
    const hasDebit  = (line.debit  || 0) > 0;
    const hasCredit = (line.credit || 0) > 0;
    return `
      <tr>
        <td>${idx + 1}</td>
        <td>${acctLabel}</td>
        <td>${escHtml(line.description)}</td>
        <td class="amount-col debit-amt">${hasDebit  ? fmt(line.debit)  : ''}</td>
        <td class="amount-col credit-amt">${hasCredit ? fmt(line.credit) : ''}</td>
      </tr>`;
  }).join('');

  $('modal-body').innerHTML = `
    <div class="modal-meta">
      <div class="modal-meta-item"><strong>Date</strong>${formatDate(entry.date)}</div>
      <div class="modal-meta-item"><strong>Reference</strong>${escHtml(entry.reference)}</div>
      <div class="modal-meta-item"><strong>Memo</strong>${escHtml(entry.memo) || '—'}</div>
      <div class="modal-meta-item"><strong>Total Amount</strong>${fmt(totalD)}</div>
    </div>
    <div class="table-scroll">
      <table class="data-table">
        <thead>
          <tr><th>#</th><th>Account</th><th>Description</th><th class="amount-col">Debit</th><th class="amount-col">Credit</th></tr>
        </thead>
        <tbody>${linesHtml}</tbody>
        <tfoot>
          <tr>
            <td colspan="3" style="font-weight:700;padding:.6rem 1rem;border-top:2px solid var(--clr-border)">Totals</td>
            <td class="amount-col debit-amt" style="font-weight:700;border-top:2px solid var(--clr-border)">${fmt(entry.lines.reduce((s,l)=>s+(l.debit||0),0))}</td>
            <td class="amount-col credit-amt" style="font-weight:700;border-top:2px solid var(--clr-border)">${fmt(entry.lines.reduce((s,l)=>s+(l.credit||0),0))}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  `;

  $('entry-modal').classList.remove('hidden');
}

$('modal-close').addEventListener('click', () => $('entry-modal').classList.add('hidden'));
$('entry-modal').addEventListener('click', e => {
  if (e.target === $('entry-modal')) $('entry-modal').classList.add('hidden');
});

/* ══════════════════════════════════════════════════════════
   GENERAL LEDGER
   ══════════════════════════════════════════════════════════ */

function renderLedger() {
  // Populate account filter
  const filter = $('ledger-account-filter');
  const currentVal = filter.value;
  filter.innerHTML = '<option value="">— All Accounts —</option>';

  const grouped = groupAccountsByType();
  const order = ['Asset', 'Liability', 'Equity', 'Revenue', 'Expense'];
  order.forEach(type => {
    if (!grouped[type]) return;
    const og = document.createElement('optgroup');
    og.label = type;
    grouped[type].forEach(a => {
      const opt = document.createElement('option');
      opt.value = a.id;
      opt.textContent = `${a.number} — ${a.name}`;
      og.appendChild(opt);
    });
    filter.appendChild(og);
  });
  filter.value = currentVal;

  renderLedgerTable();
}

$('ledger-account-filter').addEventListener('change', renderLedgerTable);

function renderLedgerTable() {
  const filterAcctId = $('ledger-account-filter').value;
  const tbody = $('ledger-tbody');
  tbody.innerHTML = '';

  // Collect all lines from all entries, sorted by date then entry id
  const allLines = [];
  const sorted = [...state.entries].sort((a, b) => a.date.localeCompare(b.date) || a.id - b.id);
  sorted.forEach(entry => {
    entry.lines.forEach(line => {
      if (filterAcctId && line.accountId !== filterAcctId) return;
      allLines.push({ ...line, date: entry.date, reference: entry.reference, entryMemo: entry.memo });
    });
  });

  if (allLines.length === 0) {
    $('no-ledger-msg').classList.remove('hidden');
    $('ledger-table-container').classList.add('hidden');
    return;
  }

  $('no-ledger-msg').classList.add('hidden');
  $('ledger-table-container').classList.remove('hidden');

  // Group by account if showing all
  let runningBalance = 0;
  let currentAccountId = null;

  allLines.forEach(line => {
    const acct = accountById(line.accountId);
    const acctLabel = acct ? `${acct.number} — ${acct.name}` : 'Unknown';

    // Insert account header when account changes (all-accounts view)
    if (!filterAcctId && line.accountId !== currentAccountId) {
      currentAccountId = line.accountId;
      runningBalance = 0;
      const hdr = document.createElement('tr');
      hdr.className = 'coa-category-row';
      hdr.innerHTML = `<td colspan="7">${acctLabel}</td>`;
      tbody.appendChild(hdr);
    }

    // Running balance
    if (acct) {
      if (acct.normal === 'Debit') {
        runningBalance += (line.debit || 0) - (line.credit || 0);
      } else {
        runningBalance += (line.credit || 0) - (line.debit || 0);
      }
    }

    const tr = document.createElement('tr');
    const balClass = runningBalance >= 0 ? 'balance-pos' : 'balance-neg';
    tr.innerHTML = `
      <td>${formatDate(line.date)}</td>
      <td><code>${escHtml(line.reference)}</code></td>
      <td>${filterAcctId ? acctLabel : ''}</td>
      <td>${escHtml(line.description || line.entryMemo)}</td>
      <td class="amount-col debit-amt">${(line.debit  || 0) > 0 ? fmt(line.debit)  : ''}</td>
      <td class="amount-col credit-amt">${(line.credit || 0) > 0 ? fmt(line.credit) : ''}</td>
      <td class="amount-col ${balClass}">${fmt(Math.abs(runningBalance))} ${runningBalance < 0 ? 'Cr' : ''}</td>
    `;
    tbody.appendChild(tr);
  });
}

/* ══════════════════════════════════════════════════════════
   CHART OF ACCOUNTS
   ══════════════════════════════════════════════════════════ */

$('btn-new-account').addEventListener('click', () => {
  $('account-form-container').classList.remove('hidden');
  $('acct-number').focus();
});
$('btn-cancel-account').addEventListener('click', () => {
  $('account-form-container').classList.add('hidden');
  clearAccountForm();
});
$('btn-save-account').addEventListener('click', saveAccount);

// Auto-set normal balance based on type
$('acct-type').addEventListener('change', () => {
  const type = $('acct-type').value;
  $('acct-normal').value = ['Asset', 'Expense'].includes(type) ? 'Debit' : 'Credit';
});

function saveAccount() {
  const number = $('acct-number').value.trim();
  const name   = $('acct-name').value.trim();
  const type   = $('acct-type').value;
  const normal = $('acct-normal').value;

  if (!number) { alert('Please enter an account number.'); return; }
  if (!name)   { alert('Please enter an account name.'); return; }
  if (state.accounts.some(a => a.number === number)) {
    alert(`Account number ${number} already exists.`); return;
  }

  state.accounts.push({ id: `custom_${Date.now()}`, number, name, type, normal });
  state.accounts.sort((a, b) => a.number.localeCompare(b.number));
  saveState();
  clearAccountForm();
  $('account-form-container').classList.add('hidden');
  renderCoA();
}

function clearAccountForm() {
  $('acct-number').value = '';
  $('acct-name').value = '';
  $('acct-type').value = 'Asset';
  $('acct-normal').value = 'Debit';
}

function renderCoA() {
  const tbody = $('coa-tbody');
  tbody.innerHTML = '';
  const balances = computeBalances();
  const order = ['Asset', 'Liability', 'Equity', 'Revenue', 'Expense'];
  const grouped = groupAccountsByType();

  order.forEach(type => {
    if (!grouped[type] || grouped[type].length === 0) return;

    // Category header row
    const hdr = document.createElement('tr');
    hdr.className = 'coa-category-row';
    hdr.innerHTML = `<td colspan="5">${type}s</td>`;
    tbody.appendChild(hdr);

    grouped[type].forEach(acct => {
      const bal = balances[acct.id] || 0;
      const balClass = bal >= 0 ? 'balance-pos' : 'balance-neg';
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><code>${acct.number}</code></td>
        <td>${escHtml(acct.name)}</td>
        <td>${typeBadge(acct.type)}</td>
        <td>${acct.normal}</td>
        <td class="amount-col ${balClass}">${fmt(Math.abs(bal))}</td>
      `;
      tbody.appendChild(tr);
    });
  });
}

/* ── Utility ───────────────────────────────────────────────── */
function formatDate(iso) {
  if (!iso) return '';
  const [y, m, d] = iso.split('-');
  return `${m}/${d}/${y}`;
}

function escHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/* ── Init ──────────────────────────────────────────────────── */
loadState();
renderEntriesList();
renderCoA();
