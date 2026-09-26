---
name: finance-books
description: Bookkeeping, reconciliation, month-end close, and financial statements, prepared for an accountant. Use when the user asks for help with books in QuickBooks, Xero or a spreadsheet, a chart of accounts, categorising transactions, a journal entry, reconciling a bank account, a trial balance that does not balance, accruals or prepayments, accounts payable or receivable, VAT or sales tax postings, payroll liabilities, foreign currency revaluation, supplier bank detail changes, or reading a profit and loss, balance sheet or cash flow statement. Finds the errors behind imbalances, checks payment controls, and writes exact questions for a licensed accountant. No tax, audit, or regulatory advice. For cash forecasting use business-model instead. For checking general maths use numbers-check. Triggers on bookkeeping help, reconcile my bank, trial balance, journal entry, month-end close, VAT return, accounts payable, read my P and L, balance sheet, cash flow statement, prepare for my accountant, double entry.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Finance books

The failure this corrects is books that look finished and are wrong: a difference plugged instead of
found, a period left open, VAT posted gross, a supplier paid to a fraudster's new bank account, or a
false alarm raised because a check was applied without its conditions. The work here is the mechanics
and the error hunting underneath professional advice, with the professional questions handed over
precisely.

## When to use and when to stay off

Run when the user is keeping books, reconciling, closing a period, building or reading statements, or
assembling records for an accountant.

Stay off when:

- The user wants a cash forecast, pricing, unit economics or a funding model. `business-model` takes that.
- The user wants a calculation or a figure in a document checked, with no ledger involved. `numbers-check` takes that.
- The question is tax, audit, or regulatory judgement: what is deductible, which structure, whether a worker is an employee, how to answer a tax notice. Hand over the exact question for an accountant, as set out in "What this cannot do".

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of
the session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Never invent a figure. Every number comes from a document the user supplied, or it is marked as needing the source.
2. Decimal arithmetic for money, never binary floating point. `scripts/reconcile.py` uses `decimal.Decimal`; any other script does the same.
3. Debits equal credits, always. An imbalance is an error to find, not a rounding issue to absorb.
4. Every categorisation follows a written policy, so the same transaction gets the same treatment next month.
5. Never state a tax rate, threshold, filing deadline or allowance from memory. Retrieve it from the revenue authority with a link and a date, or say it needs checking.
6. Never approve or process a change to a supplier's bank details on the strength of an email or invoice alone. Verify by phone to a number already on file.
7. Say when a number cannot be produced from the available records. Do not estimate into a gap and present it as a figure.

## Double entry and how the statements connect

Every transaction touches at least two accounts and total debits equal total credits. Assets and
expenses increase with a debit. Liabilities, equity and income decrease with a debit. Assets equal
liabilities plus equity.

The profit and loss covers a period. Its result flows into retained earnings on the balance sheet,
which is a snapshot at a moment:

```
closing retained earnings = opening retained earnings + profit for the period
                            - distributions (dividends, owner drawings)
                            +/- prior-period adjustments
```

Profit alone will not equal the movement whenever there were dividends, drawings or prior-period
adjustments, so check the full identity.

The cash flow statement has three sections. Operating cash flow, under the indirect method, starts from
profit and reconciles it to cash from operations through non-cash items (depreciation) and working
capital movements (receivables, inventory, payables). Investing covers capital expenditure and asset
sales. Financing covers loans drawn and repaid, equity raised, dividends, and owner drawings. Together
they explain the movement in the bank.

A profitable period with less cash is common and has several causes: receivables or inventory grew,
capital purchases, loan principal repayments (which are not expenses), and owner drawings or dividends.

## Procedure

### Step 1, establish the framework, basis and period

Find out which reporting framework the accounts follow: IFRS, US GAAP, FRS 102 or another national
standard, or cash basis for a small unincorporated business. The framework decides revenue
recognition, lease treatment and several adjustments below. If the user does not know, that is a
question for their accountant: "Which reporting framework and basis should my accounts use, given my
entity type and size?"

Then cash basis or accrual basis, and which period. Mixing the two produces statements that cannot be
reconciled.

Establish the functional currency, any foreign currency accounts, whether the business is registered
for VAT or sales tax, whether it runs payroll, and whether there is an existing chart of accounts.
Never renumber an existing chart without saying what it will break.

### Step 2, set up or review the chart of accounts

Keep it small. Add an account when a real decision depends on seeing that line separately.

Group as assets, liabilities, equity, income, cost of sales, and operating expenses, with cost of sales
kept separate so gross margin is readable.

Give owner transactions their own accounts: drawings, contributions, and director loan movements.

Include the control accounts the business needs: VAT or sales tax, payroll liabilities (tax withheld,
employer and employee contributions, pension, net pay due), accounts receivable, accounts payable, and
accruals and prepayments.

### Step 3, categorise against a written policy

Write the policy first, then apply it. For each category: what belongs there, what looks similar and
belongs elsewhere, and the treatment for the awkward cases.

Keep a suspense account for anything unclear, and list its contents as open questions.

Separate a cost of sale, an operating expense, and a capital purchase. The third is not an expense in
the period it is bought.

Post VAT or sales tax net. When registered, the sale is income net of tax and the tax goes to the
control account; purchase tax that can be reclaimed goes to the same control account. Posting gross
overstates both income and costs. Whether a given purchase is reclaimable is a question for the
accountant.

Post payroll through liabilities: gross pay and employer costs as expenses, deductions and employer
contributions as liabilities until paid, net pay as a liability until the transfer clears.

### Step 4, reconcile

Compare the bank statement to the ledger for the period. Opening balance plus receipts minus payments
should equal the closing statement balance, after listing timing items: unpresented cheques and
payments, and deposits not yet cleared. A negative bank balance in the books can be legitimate when
cheques have been written but not presented, even without an overdraft.

Run `scripts/reconcile.py` on CSV exports of the bank and the ledger:

```
python3 scripts/reconcile.py bank.csv ledger.csv
python3 scripts/reconcile.py bank.csv ledger.csv --window 5 --flip-ledger
```

Each file needs date, amount and reference columns. It matches on amount within a date window, lists
unmatched lines, and flags candidate transpositions and slides, doubled-sign errors, and duplicates.
Exit code 1 means items remain unreconciled.

Find the difference, do not plug it. A difference divisible by 9 points at a transposition (54 entered
as 45) or a slide, meaning a decimal shift (120.00 entered as 12.00). A difference equal to twice an
amount points at a posting on the wrong side. Other causes: a missing or duplicated entry, a payment
dated in the wrong period, bank fees never entered, a foreign currency amount at the wrong rate.

Reconcile the other control accounts too: receivables against unpaid invoices, payables against unpaid
bills and supplier statements, VAT control against the return, payroll liabilities against the payroll
reports, and any payment processor against its settlement report.

### Step 5, post period-end adjustments and run the trial balance

Post accruals, prepayments, depreciation, deferred revenue, and foreign currency revaluation, using the
checklist in `references/period-close.md`. Record realised FX gains and losses on settled items, and
revalue open foreign currency balances at the closing rate as unrealised.

Then run the trial balance. Total debits must equal total credits. Review each balance for its normal
side, since a credit balance on an asset or a debit balance on a liability needs an explanation.

Lock the period in the accounting system once the trial balance is agreed, so later entries go into
the next period with a visible adjustment.

### Step 6, produce and check the statements

Build the profit and loss, the balance sheet, and the cash flow from the trial balance, then check them
against each other.

Does the balance sheet balance? Does the retained earnings identity hold? Does the closing cash on the
cash flow match the bank figure on the balance sheet? Does gross margin look like last period, and if
not, why? Are there balances that cannot be negative, such as negative inventory?

Ratios, with their formulas and what each one hides, are in `references/statements.md`.

### Step 7, check payment controls

Before any payment run, confirm:

- Every change to a supplier's bank details was verified by phone to a number already on file, not one in the email or on the invoice. A request to change bank details is the standard business email compromise pattern.
- The person who sets up or changes a supplier is not the person who approves the payment. In a very small business, the owner reviews the payment run and the bank audit log.
- New suppliers, round-number payments, urgent requests from a senior person, and invoices that differ from the purchase order were flagged.

Red flags and the response if a fraudulent payment went out are in `references/period-close.md`.

### Step 8, prepare the handover

Assemble what the accountant will ask for, using the list in `references/statements.md`. Then write the
question list. Each question states the situation, the amounts, what was already checked, and the
decision needed.

## Self-audit

- The reporting framework and basis were established in step 1, or flagged as a question for the accountant.
- Debits equal credits in the trial balance, and the balance sheet balances.
- The retained earnings check included distributions and prior-period adjustments.
- Every reconciliation difference was explained, not plugged, and timing items were listed.
- `scripts/reconcile.py` or another decimal-based method did the matching arithmetic.
- VAT or sales tax was posted net through a control account, and the control account reconciles to the return.
- Payroll liabilities reconcile to the payroll reports.
- Accruals, prepayments, depreciation, deferred revenue and FX revaluation were considered, and the period was locked.
- Supplier bank detail changes were verified by phone to a known number, and set-up and approval were separated.
- Every figure traces to a supplied document; no tax rate, threshold or deadline was stated from memory.
- Anything crossing into professional advice was handed off with a specific question.

## What this cannot do

It cannot give tax, audit, legal or regulatory advice, sign off accounts, or estimate a tax liability as
reliable. It cannot detect fraud that leaves no trace in the records supplied. Tax and company law are
jurisdiction specific and change every year. Name a licensed accountant (chartered, certified or CPA)
in the user's jurisdiction and hand over questions such as:

- "Which reporting framework and basis should these accounts use for an entity of this type and size, and does that change how I recognise this revenue?"
- "Is VAT or sales tax on (purchase, amount) reclaimable, and which box or line of the return does it belong in?"
- "Should (item, amount) be capitalised or expensed, and over what useful life should it be depreciated under our framework?"
- "How should I treat this prior-period error of (amount): as a prior-period adjustment or in the current year?"
- "Is (person) an employee or a contractor for payroll purposes?"
- "We paid (amount) to a changed bank account that turned out to be fraudulent. What do we report, to whom, and how is the loss treated?"
