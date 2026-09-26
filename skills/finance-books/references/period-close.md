# Period close

The month-end or year-end sequence after the bank is reconciled: adjustments, the trial balance, VAT or
sales tax control, foreign currency, and payment fraud checks. Treatments depend on the reporting
framework (IFRS, US GAAP, FRS 102, cash basis), so confirm anything marked as a judgement with the
accountant.

## Reconciling the bank with the script

`scripts/reconcile.py` matches bank lines to ledger lines and exits 1 if anything is left over.

```
python3 scripts/reconcile.py bank.csv ledger.csv
python3 scripts/reconcile.py bank.csv ledger.csv --window 5
python3 scripts/reconcile.py bank.csv ledger.csv --flip-ledger
python3 scripts/reconcile.py bank.csv ledger.csv --date-format %d/%m/%Y
```

Input: two CSV files with a header row and the columns date, amount and reference. Extra columns are
ignored. Both files use the bank account's view, receipts positive and payments negative; use
`--flip-ledger` when the ledger export has the opposite sign. Amounts must be plain decimals, or
accounting negatives in parentheses. Thousands separators are rejected, so clean them first.

Matching: same amount, dates no more than `--window` days apart (default 3; set it to the bank's clearing
time), closest date first, then matching reference.

Report: matched count, totals and the difference, unmatched lines on each side, candidate transpositions
and slides (difference divisible by 9), doubled-sign candidates (same amount, opposite sign), and
duplicates within one file. Exit 0 reconciled, 1 not reconciled, 2 input error.

A candidate is a lead, not a conclusion. Open the source document for each one before correcting the
ledger. Unpresented cheques and uncleared deposits show up as unmatched until they clear; list them as
timing items instead of correcting them.

## Trial balance

1. Export the trial balance after the bank and control account reconciliations.
2. Confirm total debits equal total credits.
3. Check each account sits on its normal side: assets and expenses debit, liabilities, equity and income credit. Explain every exception, such as an overdrawn bank or a supplier overpayment.
4. Agree opening balances to last period's signed-off closing balances.
5. Compare each balance with the prior period and investigate movements the user cannot explain.
6. Clear the suspense account, or list each remaining item as a question.

## Adjustments checklist

Work through each line and record the calculation and source document next to the journal.

- Accruals: costs incurred in the period with no invoice yet (utilities, contractor time, professional fees). Debit the expense, credit accruals. Reverse next period when the invoice arrives.
- Prepayments: costs paid in advance that cover later periods (insurance, annual software, rent in advance). Move the unexpired part to a prepayment asset and release it over the periods covered.
- Deferred revenue: amounts invoiced or received for work not yet delivered. Hold them as a liability and recognise revenue as it is earned, following the framework's revenue rules.
- Accrued income: work delivered and not yet invoiced, where the framework allows it.
- Depreciation and amortisation: charge each fixed asset over its useful life using the written policy. The policy itself is a judgement for the accountant.
- Bad debt: review aged receivables and provide for or write off amounts that will not be collected, following the framework.
- Inventory: count or confirm quantities, and adjust for stock that cannot be sold at its carrying value.
- Payroll: agree the payroll liabilities (tax withheld, employee and employer contributions, pension, net pay due) to the payroll reports, and accrue any unpaid bonus or holiday pay the framework requires.
- Loans: split repayments between interest (expense) and principal (reduces the liability), using the lender's statement.
- Foreign currency: see below.
- Lock the period in the accounting system once the adjusted trial balance is agreed. QuickBooks, Xero and most other systems have a lock or closing date setting; retrieve the current steps from the vendor documentation.

## VAT or sales tax control

For a registered business, every sale and reclaimable purchase is posted net, with the tax to a single
control account (or one per tax type).

- The control account balance at the return date should equal the net amount on the return, payable or reclaimable.
- After payment or refund, the control account for that period returns to zero.
- A residual balance means a posting went gross, a rate was applied wrongly, a non-reclaimable item was reclaimed, or a payment was posted to the wrong account.
- Rates, thresholds, deadlines and which purchases are reclaimable change and differ by country. Retrieve them from the revenue authority with a date, and put doubtful items to the accountant.
- Keep the filed return and the report that produced it with the period's records.

## Foreign currency

- Record each foreign currency transaction at the rate on the transaction date, using a stated rate source applied consistently.
- Realised gain or loss: on settlement, the difference between the booked amount and the amount actually received or paid in the functional currency. It usually shows as a small residual on the bank reconciliation.
- Unrealised gain or loss: at period end, revalue open monetary balances in foreign currency (bank accounts, receivables, payables, loans) at the closing rate and post the difference. Many systems reverse it at the start of the next period.
- Which items get revalued and where the difference is presented depend on the framework; confirm with the accountant.

## Payment fraud red flags

Business email compromise is a fraud in which someone impersonates a supplier or a senior person by
email to redirect a payment. The US FBI publishes guidance and takes reports through
[IC3](https://www.ic3.gov); in the UK, reports go to Action Fraud.

Red flags:

- A supplier emails new bank details, or an invoice arrives with different bank details from the last one.
- The sender's domain is slightly different from the usual one, or replies go to a different address.
- Urgency or secrecy, especially from someone senior who is travelling or unreachable.
- A first payment to a new supplier for a round amount, or an invoice with no purchase order.
- Changes to payroll bank details requested by email.

Controls:

- Verify every bank detail change by phone to a number already on file, never one in the request. Record who called, when, and who confirmed.
- Separate duties: the person who sets up or edits suppliers does not approve payments. Where only one or two people exist, the owner reviews every payment run and the supplier change log.
- Use the bank's payee name check where it is offered, and treat a mismatch as a stop.
- Hold the first payment to changed details until the verification is recorded.

If a fraudulent payment went out: call the bank at once to request a recall, report it to the national
fraud body, preserve the emails with headers, and ask the accountant how to record and report the loss.
