---
name: business-model
description: Build and stress test the economics of a business, product, or pricing decision. Use when the user asks how to price something, whether a business can make money, what their margins, gross margin, break-even, CAC, LTV, churn, payback or runway look like, how to structure a subscription, usage based plan or pricing page, or asks for a financial model, cash flow forecast, or unit economics breakdown. Also use after reality-check returns BUILD or PIVOT. Computes contribution net of VAT, the cash conversion cycle, break-even, payback on contribution, LTV from a retention curve and peak funding with a script, and names the single assumption the outcome depends on. Triggers on how should I price this, unit economics, business model, financial model, can this make money, what are my margins, break even, runway, CAC payback, LTV to CAC, churn, cash flow forecast, pricing strategy, subscription pricing. For whether to do it at all use reality-check. For bookkeeping and statements use finance-books.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Business model

The failure this corrects: business arithmetic done in prose, where a unit error or a double count goes
unnoticed and the model says a plan works when it runs out of cash. The usual culprits are multiplying
cycle days by a monthly cost, computing payback on revenue instead of contribution, counting the founder's
pay twice, and treating a VAT inclusive price as revenue. This skill computes with a script and names the
number that decides the outcome before real money gets committed to finding it out.

## When to use and when to stay off

Run when the decision to pursue something is made, or nearly made, and the question is whether the numbers
work, at what price, at what volume, and with how much cash. Run when a user shares a model, a pricing
page, or a forecast and asks whether it holds up.

Stay off when the user wants a quick definition of a term, or has said the figures are a rough classroom
exercise and asked for no modelling.

Routing. Whether to do this at all goes to `reality-check` first, which hands over here after a BUILD or
PIVOT verdict. Checking arithmetic, statistics or a spreadsheet someone else built goes to
`numbers-check`, whose conventions apply here in full: compute with a script, carry units, cross-check,
label every assumption. Bookkeeping, statements, and tax filings go to `finance-books`.

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of the
session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Every input is given by the user, retrieved with a citation, or labelled `ASSUMPTION:` with a range. No invented market sizes, conversion rates, churn, or acquisition costs.
2. Compute with `scripts/unit_economics.py`, never in prose, and paste its output next to the conclusion.
3. Model cash, not only profit. The cash conversion cycle and peak funding appear in every model that holds stock, extends credit, or grows.
4. Count founder labour exactly once: as a salary in fixed cost, or as hours per unit at a market rate in variable cost.
5. Name the one assumption that decides it, and say how to verify it this week.
6. If the model does not work, say so in the first line.

## Procedure

Every formula and a worked example with real script output are in `references/formulas.md`. Run from the
skill folder as shown, or from the repository root as
`python3 skills/business-model/scripts/unit_economics.py`.

```
python3 scripts/unit_economics.py contribution --price 36 --vat-rate 0.20 --variable-cost 11 --variable-cost 5.40
python3 scripts/unit_economics.py breakeven --fixed 6000 --contribution 12.70
python3 scripts/unit_economics.py ccc --inventory-days 40 --receivable-days 2 --payable-days 30 --monthly-cogs 5500 --monthly-revenue 15000
python3 scripts/unit_economics.py payback --cac 45 --monthly-contribution 12.70
python3 scripts/unit_economics.py ltv --monthly-contribution 12.70 --churn 0.08 --months 24 --cac 45
python3 scripts/unit_economics.py ltv --monthly-contribution 12.70 --retention 1 0.78 0.66 0.60 --cac 45
python3 scripts/unit_economics.py peak-funding --flows -9000 -4500 -3200 -1800 -600 700 1900
```

Exit status 0 means computed, 2 means invalid input, and 3 means no finite answer, such as a negative
contribution that never breaks even. Report a status 3 as the finding, not as an error to work around.

### Step 1, define the unit

What is one of the thing being sold? One subscription month, one delivered order, one billable hour, one
seat, one transaction. State it and hold it constant, because mixing units between revenue and cost breaks
every later step.

### Step 2, net price and contribution per unit

Start from what the business keeps. Consumer prices in the UK and EU are normally displayed VAT inclusive,
so net price = displayed price / (1 + VAT rate). Retrieve the current rate for the product and country from
the tax authority. US sales tax is usually added at checkout and varies by location; retrieve it per
jurisdiction.

Subtract everything that varies with the unit: goods, direct labour at a market rate, payment processing,
shipping and packaging, platform fees, hosting or model API cost, refunds, chargebacks and spoilage as a
rate, and support per unit.

Decide here where founder labour goes. If the founder's hours scale with units, charge them per unit at a
market rate and leave the founder out of fixed cost. Otherwise leave them out of this step and pay a salary
in step 3.

If contribution is negative, stop and report it. Volume makes a negative unit worse.

### Step 3, fixed costs and break-even

Fixed monthly costs, including the forgotten ones: insurance, accounting, software, premises, compliance,
and the founder's salary unless step 2 already charged their time.

Break-even units = fixed cost / contribution per unit, rounded up. Then name the channel that delivers that
volume. A break-even number with no distribution answer means nothing.

### Step 4, the cash conversion cycle

CCC = DIO + DSO - DPO, in days. Inventory and payables are valued at cost of goods, receivables at revenue.
Cash tied up = DIO x daily COGS + DSO x daily revenue - DPO x daily COGS, with daily = monthly x 12 / 365.
Days times a monthly figure overstates the cash by about thirty times.

Compute it at current revenue and at three times current revenue, since growth increases the need. Then
test the levers: deposits, upfront payment, shorter customer terms, early payment discounts priced as
capital, longer supplier terms, less stock.

### Step 5, retention, acquisition and payback

Cost to acquire one customer through each named channel, retrieved or assumed with a range.

Simple payback months = CAC / monthly contribution per customer. Contribution, not revenue.

Retention, cohorted: the fraction of a starting cohort still paying in each month. Feed the curve, or a
constant monthly churn if that is all there is, to the `ltv` subcommand with the CAC. It reports LTV over the
horizon and the cohort payback month, which counts churn and is always later than simple payback. A new
business has no curve, so label it `ASSUMPTION:` and treat LTV as the least reliable output.

The test that matters: is acquisition cost recovered inside the cash the business can fund, not merely
inside the customer's lifetime?

### Step 6, pricing

Willingness to pay comes from what the buyer spends on the problem today, including the cost of doing
nothing and of the manual workaround. Find that number before proposing a price.

Check the price against three references: the incumbent's price, the do-nothing cost, and the buyer's
approval threshold. Compare candidate prices by conversion x contribution - acquisition cost per prospect,
never by conversion alone. Payment terms and deposits change cash, so run them through step 4 before
offering them. Value metric, tiers, and traps are in `references/pricing.md`.

### Step 7, peak funding

Lay out monthly net cash flow, including stock bought ahead and receivables not yet collected, and run
the peak-funding subcommand. The result is the cash the plan needs before it pays back.

### Step 8, sensitivity and the deciding assumption

Rerun the script across each assumption's range. Report which single input moves the outcome most, and
whether the conclusion flips inside the plausible range. If it does, the model does not answer the question
yet, and the output names the measurement that would.

### Step 9, report

```
VERDICT
Works at the stated assumptions / does not work / undetermined, in one line.

THE UNIT
What one unit is.

CONTRIBUTION
Net price after tax, each variable cost with provenance, contribution per unit.

BREAK-EVEN
Volume, and the named channel that can deliver it.

CASH
CCC in days, cash tied up at current and 3x revenue, peak funding need.

ACQUISITION AND RETENTION
CAC by channel, simple payback, retention source, LTV and cohort payback month.

PRICE
Proposed price, the three reference points, and the reasoning.

THE DECIDING ASSUMPTION
The one input that decides the answer, and how to verify it within a week.

MODEL
The exact script commands and their output.
```

## Self-audit

- The unit is stated and held constant.
- Contribution uses the net price after VAT or sales tax.
- Founder labour appears exactly once.
- The cash cycle uses daily figures, receivables at revenue.
- Payback divides by contribution, not revenue.
- LTV names its retention source, and an assumed curve is labelled.
- Every input has provenance, and assumptions have ranges.
- Break-even volume is tied to a named channel.
- The deciding assumption is named with a verification step.
- Every number in the report appears in pasted script output.

## What this cannot do

It cannot tell you demand. Conversion, churn, and CAC for a new business are assumptions until real
customers produce them, and the model is only as good as those inputs.

It does not give tax, legal, or investment advice. VAT registration, the rate for a given product, and
whether a price display is compliant need a professional. Ask a chartered accountant or tax adviser: "At an
expected annual turnover of X selling Y to consumers in Z, when must we register for VAT or sales tax, which
rate applies to this product, and must our displayed price include it?" Payment terms, deposits, and
subscription cancellation rules can carry consumer law obligations; ask a solicitor or attorney: "Are our
deposit, refund, and cancellation terms for consumers in Z enforceable, and what must we disclose before
checkout?"

It does not produce statutory accounts or a cash flow statement for filing. That goes to `finance-books`
and an accountant.
