---
name: finance-books
description: Organise bookkeeping, reconcile accounts, read financial statements, and prepare records for an accountant. Use when the user asks for help with bookkeeping, a chart of accounts, categorising transactions, reconciling a bank account, reading or building a profit and loss or balance sheet or cash flow statement, understanding a financial ratio, preparing documents for tax filing or an audit, or working out what records they need to keep. Explains the mechanics, sets up the structure, finds the errors that make statements fail to balance, and prepares a question list for a licensed professional. Does not give tax, audit, or regulatory advice and states plainly which decisions require a qualified accountant in the user's own jurisdiction. Triggers on bookkeeping help, chart of accounts, reconcile my accounts, categorise transactions, read my P and L, balance sheet, cash flow statement, prepare for my accountant, what records do I need, double entry.
license: MIT
metadata:
  version: 1.0.0
  suite: ai-skill
---

# Finance books

Mechanics, structure, and error hunting. Not professional advice, and the boundary is not decoration.

## Boundary, read first

This skill does the bookkeeping work that sits underneath professional advice. It does not replace the
professional.

What it does. Sets up a chart of accounts. Explains double entry and how the three statements connect.
Categorises transactions against a stated policy. Reconciles a bank account against the ledger and finds
the difference. Builds and checks statements arithmetically. Explains what a ratio means. Assembles the
documents an accountant will ask for. Writes the list of questions to put to them.

What it does not do, in any jurisdiction. Tell the user what to claim as deductible. Choose a business
structure for tax reasons. Interpret tax law or a tax notice. Decide whether a worker is an employee or a
contractor. Advise on transfer pricing, residency, or cross border treatment. Sign off on anything.
Estimate a tax liability as though it were reliable. Advise on audit response.

Tax and company law are jurisdiction specific, they change every year, and the consequence of getting them
wrong falls on the user and not on a model. Where a question crosses the line, say so, say why, and hand
back the exact question to ask a licensed accountant in their country. A precise question saves them
billable time, and that is the useful contribution.

Never state a tax rate, threshold, filing deadline, or allowance from memory. Retrieve it from the
relevant revenue authority with a link and a date, or say it needs checking. A confidently wrong deadline
causes a penalty.

## Non-negotiables

1. Never invent a figure. Every number comes from a document the user supplied, or it is marked as needing the source.
2. Decimal arithmetic for money, never binary floating point. Use a decimal type in any script.
3. Debits equal credits, always. If a set of entries does not balance, that is an error to find, not a rounding issue to absorb.
4. Every categorisation follows a written policy, so the same transaction gets treated the same way next month. Consistency matters more than which reasonable choice was made.
5. Flag anything unusual rather than smoothing it. A round number payment to a new supplier, a duplicate invoice, a personal expense in a business account, a transaction dated outside the period.
6. Say when a number cannot be produced from the available records. Do not estimate into a gap and present it as a figure.

## Double entry, the part people skip

Every transaction touches at least two accounts and the total of debits equals the total of credits. Five
account types, with the direction a debit moves them:

Assets increase with a debit. Liabilities decrease with a debit. Equity decreases with a debit. Income
decreases with a debit. Expenses increase with a debit.

The identity that has to hold: assets equal liabilities plus equity. When a balance sheet does not
balance, the error is in the entries, and it is findable.

How the statements connect. The profit and loss covers a period and its result flows into retained
earnings on the balance sheet, which is a snapshot at a moment. The cash flow statement reconciles
profit to the movement in the bank, and the gap between them is where most misunderstanding lives. A
profitable month with less cash is normal and usually means receivables or inventory grew.

## Procedure

### Step 1, establish the basis and the period

Cash basis or accrual basis, and which period. This decides every categorisation that follows, and
mixing the two produces statements that cannot be reconciled.

Also establish the currency, whether the business is registered for a sales tax or value added tax, and
whether there is an existing chart of accounts to match. Never renumber an existing chart without saying
what it will break.

### Step 2, set up or review the chart of accounts

Keep it small. A chart with two hundred accounts nobody uses is harder to work with than one with forty.
Add an account when a real decision depends on seeing that line separately.

Group as assets, liabilities, equity, income, cost of sales, and operating expenses, and keep cost of
sales separate from operating expenses, because gross margin is unreadable otherwise.

Separate owner transactions into their own accounts. Owner draws, owner contributions, and director loan
movements are the most commonly mis-posted items in a small business ledger.

### Step 3, categorise against a written policy

Write the policy first, then apply it. For each category: what belongs there, what looks similar and
belongs elsewhere, and the treatment for the awkward cases.

Keep a suspense or holding account for anything genuinely unclear, and list its contents as open
questions. An unclear item sitting in a wrong category is worse than one sitting visibly in suspense.

Separate the three things people conflate: a cost of sale, an operating expense, and a capital purchase.
The third is not an expense at all in the period it is bought.

### Step 4, reconcile

Reconciliation is the control that catches almost everything. Compare the bank statement to the ledger for
the period.

Opening balance plus receipts minus payments should equal the closing balance on the statement. When it
does not, the difference is a number, and the number points at the cause.

Find the difference, do not plug it. Common causes: a transaction entered twice, a transaction missing, a
transposed digit, which shows up as a difference divisible by nine, a sign error, which shows up as a
difference of exactly twice an entry, a payment dated in the wrong period, bank fees never entered, and a
foreign currency amount entered at the wrong rate.

Reconcile the other accounts too, not just the bank. Receivables against unpaid invoices, payables against
unpaid bills, sales tax control against the return, and any payment processor against its settlement
report, since the gross and net difference there is a frequent source of missing fee entries.

### Step 5, produce and check the statements

Build the profit and loss, the balance sheet, and the cash flow. Then check them against each other, which
is how errors surface.

Does the balance sheet balance? Does the profit for the period match the movement in retained earnings?
Does the closing cash on the cash flow match the bank figure on the balance sheet? Does gross margin look
like last period, and if not, why? Are there negative balances that cannot be negative, such as a negative
inventory or a negative bank balance on an account with no overdraft?

Ratios worth computing, in `references/statements.md`, along with what each one hides.

### Step 6, prepare the handover

Assemble what a professional will ask for so they spend their time on judgement rather than on collecting
documents. The list is in `references/statements.md`.

Then write the question list. Each question states the situation, the amounts, what was already checked,
and the specific decision needed. That is the output that saves the user money.

## Self-audit

- Debits equal credits, and the balance sheet balances.
- Every reconciliation difference was explained, not plugged.
- Money arithmetic used a decimal type.
- Every figure traces to a supplied document.
- Categorisation policy is written down and applied consistently.
- Unclear items sit in suspense and appear on the question list.
- No tax rate, threshold, or deadline stated from memory.
- Anything crossing into professional advice was handed off with a specific question.
