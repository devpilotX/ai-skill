# Statements, ratios, and handover

## Reading a profit and loss

Work down the statement and ask what each level tells you.

Revenue, recognised in the right period. For anything invoiced in advance, the amount not yet earned is a
liability rather than revenue, and getting this wrong overstates both revenue and profit.

Cost of sales, meaning only costs that vary with what was sold. Gross profit and gross margin percentage
come from this line and show whether each sale covers its direct costs. Margin moving without a price
change means the cost base moved or the mix changed.

Operating expenses, which should be stable as a proportion of revenue. A line that jumps needs an
explanation, and a line that never moves at all sometimes means it is being missed rather than that it is
stable.

Operating profit, which is the honest measure of whether the trading activity works.

Below that sit interest, tax, and one off items. Keep genuinely exceptional items visible rather than
buried, because hiding them makes trends unreadable next period.

## Reading a balance sheet

Current assets against current liabilities tells you whether short term obligations can be met. A working
capital deficit in a growing business is a warning sign to investigate.

Receivables ageing matters more than the total. A single large invoice over ninety days old is a different
problem from many small recent ones.

Inventory: is it real, is it saleable, and how long has it been there. Inventory that cannot be sold at
carrying value is an overstated asset and therefore an overstated profit.

Check for assets that should have been expensed and expenses that should have been capitalised, since both
distort the period.

Owner and director accounts. In a small company these are frequently the least accurate figures on the
statement and the ones a professional will question first.

## Reading a cash flow statement

Three sections: operating, investing, financing. Operating shows whether the trading generates cash; a
business that does not generate cash from operations is funded by something else, and that something else
ends.

Under the indirect method, the operating section starts from profit and reconciles it to operating cash:
add back non-cash items such as depreciation, then adjust for movements in receivables, inventory and
payables. Large working capital adjustments are where the cash went.

Investing covers capital expenditure and proceeds from selling assets. Financing covers loans drawn and
principal repaid, equity raised, dividends, and owner drawings. A profitable business can still lose cash
through any of these.

Free cash flow after the capital spending the business actually needs, rather than the discretionary part,
is the number that tells you whether it can fund itself.

## Ratios, and what each one hides

Gross margin percentage. Hides mix. A stable overall margin can conceal one product collapsing while
another improves.

Current ratio. Hides receivable quality. Uncollectable invoices count as current assets until someone
writes them off.

Debtor days, meaning trade receivables divided by credit sales for the period, times the number of days
in the period. Use credit sales, not total revenue, since cash sales never create a receivable. Receivables
include VAT or sales tax and revenue excludes it, so for a registered business either strip the tax out of
receivables or gross up credit sales by the tax rate, retrieved for the period; otherwise the result is
overstated by roughly the tax rate. Hides concentration, since one slow large customer can set the whole
figure.

Inventory turnover. Hides obsolescence. Slow moving stock drags the average without appearing as a
problem.

Interest cover. Hides refinancing risk, which arrives on the maturity date rather than gradually.

Net margin. Hides whether the profit came from trading or from one off items.

Compute each one the same way every period and write down the formula used, since there are several
conventions for most of these and comparing across conventions is meaningless.

## Reconciliation difference diagnostics

A difference divisible by nine points at transposed digits, such as 54 entered as 45, or at a slide,
meaning a decimal shift, such as 120.00 entered as 12.00. Both produce a difference divisible by nine.

A difference that is exactly twice a transaction amount points at a posting on the wrong side, so the entry
went the wrong way.

`scripts/reconcile.py` flags both patterns, plus duplicates, from CSV exports of the bank and the ledger.
Usage is in `references/period-close.md`.

A round difference often means a fee, a standing order, or an interest posting that was never entered.

A difference equal to a whole transaction means it is missing or duplicated. Search for the amount.

A difference that appears only in one period and then disappears usually means a timing cut off, so a
transaction landed on the wrong side of the period end.

A small persistent difference often means a currency conversion done at a different rate than the one used
for the ledger entry.

Work the difference until it is explained. A plugged difference hides a real error and grows.

## Handover pack for a professional

Bank statements for every account, for the full period, in the format the bank issues rather than
retyped.

The general ledger or transaction export, with categories.

Sales invoices raised, and purchase invoices and receipts received. Card receipts for anything without an
invoice.

Loan agreements and finance or lease agreements, with schedules.

Payroll records, including any filings already made.

Sales tax or value added tax returns already submitted for the period.

Asset purchases with their invoices, separated from expenses.

Opening balances agreed to last period's closing figures. Without them the accountant has to rebuild the
prior period before starting.

A list of related party transactions, meaning anything involving the owner, family, or another business
they control.

The suspense account contents with a note on each item.

The question list, one question per item, each with the situation, the amount, what was already checked,
and the decision needed.

## Records retention

Retention periods are set by law and they differ by country and by document type, so retrieve the current
requirement from the relevant revenue authority rather than assuming a number. Keep the underlying
documents, not only the ledger entries, because a ledger entry without the invoice behind it is not
evidence.

Keep the audit trail. An accounting system that allows a past entry to be edited without a record of the
change creates a problem that only becomes visible under scrutiny.
