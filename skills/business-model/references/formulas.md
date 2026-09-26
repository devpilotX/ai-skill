# Formulas and a worked example

Every formula here is implemented in `scripts/unit_economics.py`, which uses exact decimal arithmetic.
Run the script rather than doing the arithmetic in prose. Paths are relative to the skill folder; from the
repository root use `python3 skills/business-model/scripts/unit_economics.py`.

## Contribution per unit

Contribution = net price - variable cost per unit.

Net price is what the business keeps. Where consumer prices are shown VAT inclusive, as they are for
consumers in the UK and the EU, net price = displayed price / (1 + VAT rate). A 36.00 price at a 20 percent
rate nets 30.00, not 28.80. Retrieve the current rate for the product category and country from the tax
authority (HMRC in the UK; the national tax authority, or the European Commission Taxes in Europe database, in the
EU). In the US, sales tax is usually added on top of the displayed price and varies by state and locality,
so retrieve it for each ship-to location.

Variable costs are the ones that scale with the unit: goods, packaging, shipping, payment fees, platform
fees, refunds and spoilage as a rate, per-unit support, hosting or model API cost.

Founder labour appears once. Either pay the founder a salary in fixed costs, or charge their hours per
unit in variable costs at a market rate. Never both, and never neither.

## Break-even

Break-even units per period = fixed cost per period / contribution per unit, rounded up.

No finite answer exists when contribution is zero or negative. The script exits with status 3 in that case.

## Cash conversion cycle

CCC in days = DIO + DSO - DPO.

DIO, days inventory outstanding, is valued at cost of goods. DSO, days sales outstanding, is valued at
revenue, because the customer owes the selling price. DPO, days payables outstanding, is valued at cost of
goods, approximating purchases by cost of goods sold.

Cash tied up = DIO x daily COGS + DSO x daily revenue - DPO x daily COGS, where daily = monthly x 12 / 365.

The common error is multiplying days by a monthly figure, which overstates the cash by roughly thirty
times. Another is valuing receivables at cost, which understates it whenever margins are healthy.

Levers that shorten the cycle: deposits or payment upfront (DSO falls to zero, and a deposit taken before
goods are bought funds the purchase with the customer's money), shorter payment terms with early payment discounts, longer
supplier terms, and holding less stock. An early payment discount has a cost, so compare its annualised
rate with the cost of the capital it replaces.

## Payback

Payback months = CAC / monthly contribution per customer.

Use contribution, not revenue. Payback computed on revenue equals the true payback multiplied by the
contribution margin, so a 40 percent margin makes it look 2.5 times faster than it is.
The script exits with status 3 when monthly contribution is not positive.

## Retention and lifetime value

Retention in month t is the fraction of a starting cohort still paying in that month. Month 1 is 1.

With a constant monthly churn c, retention in month t is (1 - c) to the power t - 1, and lifetime value over
an unlimited horizon is monthly contribution / c. Real cohorts churn fastest early and then flatten, so a
single churn rate misstates both ends.

With a measured retention curve, LTV = monthly contribution x the sum of the retention values over the
horizon. Cohort payback is the first month in which that running sum reaches CAC. It is the payback that
counts churn, and it is always later than CAC / monthly contribution.

A new business has no retention curve. Label any curve used as `ASSUMPTION:`, state where the shape came
from, and treat LTV as the least reliable number in the model.

## Peak funding

From a list of monthly net cash flows, peak funding is the deepest point of the running total. It includes
the working capital that growth consumes, so feed the script flows that already account for stock bought
and receivables not yet collected.

## Pricing comparison

Expected value per prospect = conversion rate x contribution per customer - acquisition cost per prospect.

Two prices converting at 20 and 80 percent with the same cost per prospect favour the higher price only
when its contribution is more than four times the lower one's, since 0.8 / 0.2 = 4.

## Worked example

A consumer subscription box sold in the UK. Every input is `ASSUMPTION:` chosen to demonstrate the
arithmetic. None is a market figure.

Inputs: price 36.00 per month including VAT at 20 percent; goods 11.00, packaging and postage 5.40,
payment fee 0.90 per box; fixed costs 6,000 per month including the founder's salary (so no founder line
in variable cost); CAC 45; 500 subscribers giving monthly COGS of 5,500 and monthly net revenue of 15,000;
40 inventory days, 2 receivable days for card settlement, 30 supplier days.

```
python3 scripts/unit_economics.py contribution --price 36 --vat-rate 0.20 --variable-cost 11 --variable-cost 5.40 --variable-cost 0.90
price incl. VAT: 36.00
VAT: 6.00
net price: 30.00
variable cost: 17.30
contribution per unit: 12.70
contribution margin: 42.3%

python3 scripts/unit_economics.py breakeven --fixed 6000 --contribution 12.70
break-even units per period: 473

python3 scripts/unit_economics.py ccc --inventory-days 40 --receivable-days 2 --payable-days 30 --monthly-cogs 5500 --monthly-revenue 15000
cash conversion cycle days: 12.0
inventory at cost: 7232.88
receivables at revenue: 986.30
payables at cost: 5424.66
cash tied up: 2794.52
cash tied up at 3x revenue: 8383.56

python3 scripts/unit_economics.py payback --cac 45 --monthly-contribution 12.70
payback months: 3.5

python3 scripts/unit_economics.py ltv --monthly-contribution 12.70 --churn 0.08 --months 24 --cac 45
LTV over 24 months: 137.29
LTV with no horizon (contribution / churn): 158.75
LTV to CAC: 3.1
cohort payback month: 4

python3 scripts/unit_economics.py ltv --monthly-contribution 12.70 --retention 1 0.78 0.66 0.60 0.56 0.53 0.51 0.50 --cac 45
LTV over 8 months: 65.28
LTV to CAC: 1.5
cohort payback month: 5

python3 scripts/unit_economics.py peak-funding --flows -9000 -4500 -3200 -1800 -600 700 1900 2600 3400 4100
peak funding needed: 19100.00
lowest cumulative cash: -19100.00 in month 5
closing cash: -6400.00
recovered to opening balance: not within the flows given
```

Reading it. The business needs 473 subscribers to cover fixed cost, so 500 is barely past break-even. The
cash cycle is short because card payments settle in days; the same model with 60 day trade terms would tie
up far more. Multiplying 40 days by the monthly COGS of 5,500 would have claimed 220,000 of inventory cash
instead of 7,232.88. Payback on revenue (45 / 30 = 1.5 months) would have looked twice as good as the 3.5
months on contribution, and the retention curve pushes real cohort payback to month 5. The deciding
assumption is the retention curve: at 8 percent flat churn LTV to CAC is 3.1, on the front-loaded curve it
is 1.5 over the eight months measured. The plan needs 19,100 of funding and has not recovered it by month
10.
