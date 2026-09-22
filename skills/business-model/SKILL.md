---
name: business-model
description: Build and stress test the economics of a business, product, or pricing decision with real numbers. Use when the user asks how to price something, whether a business can make money, how to model revenue and costs, what their margins or break-even or runway look like, how to structure a subscription or usage based plan, or asks for a financial model, a unit economics breakdown, or help with a business plan. Also use after reality-check returns BUILD or PIVOT, since this is the constructive follow-on. Computes contribution margin per unit, the working capital cycle, break-even volume, payback period and runway with a script rather than in prose, names which single assumption the outcome depends on, and states the price the market will actually bear rather than a cost-plus figure. Triggers on how should I price this, unit economics, business model, financial model, can this make money, what are my margins, break even, runway, pricing strategy, subscription pricing.
license: MIT
metadata:
  version: 1.0.0
  suite: ai-skill
---

# Business model

Arithmetic about a business, done honestly. The purpose is to find the number that decides the outcome
before real money gets committed to finding it out.

## Relationship to the other skills

Use `reality-check` first when the question is whether to do this at all. Use this skill when the
decision is made and the question is whether the numbers work, and at what price and volume.

Use `numbers-check` conventions throughout: compute with a script, carry units, cross-check, and label
every assumption. Those rules apply here in full and are not repeated.

## Non-negotiables

1. Every input is given by the user, retrieved with a citation, or labelled `ASSUMPTION:` with a range. No invented market sizes, conversion rates, or acquisition costs. A made up number in a model is worse than no model, because it gets acted on.
2. Model cash, not only profit. A profitable business with a ninety day receivable cycle and thirty day payables runs out of money while growing. This kills more small businesses than weak demand.
3. Pay the founder's labour in the model. A plan that only works when the owner works unpaid is a job with extra risk, and that should be a conscious choice.
4. Price from value and willingness to pay, not from cost plus a margin. Then check that cost plus is covered. Those are two different tests and both have to pass.
5. Name the one assumption that decides it, and say how to verify it this week.
6. If the model does not work, say so in the first line. Do not bury a negative result in a spreadsheet.

## Procedure

### Step 1, define the unit

Everything follows from this and it is where most models go wrong. What is one of the thing being sold?
One subscription month, one delivered order, one billable hour, one seat, one transaction.

State the unit explicitly, then hold it constant. Mixing units between revenue and cost is the most
common structural error in a homemade model.

### Step 2, contribution margin per unit

Revenue per unit, then subtract everything that varies with the unit.

Direct materials or wholesale cost. Direct labour at a market rate, including the founder's. Payment
processing. Shipping and packaging. Platform or marketplace fees. Hosting or model API cost per unit for
software. Refunds, chargebacks, spoilage, and wastage as a rate. Support cost per unit, which is real and
usually omitted.

If contribution margin is negative, stop. Volume makes a negative unit worse, and no amount of scale
fixes it. Report that and stop.

### Step 3, fixed costs and break-even

Fixed monthly costs, including the ones people forget: insurance, accounting, software subscriptions,
premises, compliance, and the founder's minimum draw.

Break-even volume is fixed cost divided by contribution margin per unit. Compute it, then ask whether
that volume is reachable through a named channel. A break-even number with no distribution answer is
arithmetic without meaning.

### Step 4, the working capital cycle

Days from paying for input to receiving cash from the customer. Inventory days plus receivable days minus
payable days.

Multiply the cycle by the monthly cost of goods to get the cash locked up at a given revenue level. Then
compute it at three times that revenue, since growth increases the requirement.

This is the step most models skip and the one most likely to reveal that a plan needs twice the capital
assumed.

### Step 5, acquisition and payback

Cost to acquire one customer through each named channel, retrieved or assumed with a range.

Payback period in months, which matters more than lifetime value because it decides whether growth can
be funded from revenue or needs outside money.

Retention or repeat rate, cohorted. Lifetime value only after that, and treated with suspicion, since it
depends on a retention curve that does not exist yet for a new business.

The test that matters: is acquisition cost recovered inside the cash cycle, not merely inside the
customer's lifetime?

### Step 6, pricing

Willingness to pay comes from what the buyer currently spends on the problem, including the cost of
doing nothing and of the manual workaround. Find that number before proposing a price.

Check the price against three references: the incumbent's price, the do-nothing cost, and the buyer's
budget authority. A price above the level requiring approval from someone else lengthens the sales cycle
regardless of value.

Model structure and tier design, value metric selection, and the traps in usage based pricing are in
`references/pricing.md`.

### Step 7, sensitivity and the deciding assumption

Vary each assumption across its range. Report which single input moves the outcome most, and whether the
conclusion flips inside the plausible range. If it does, the model does not yet answer the question, and
the honest output says which measurement would settle it.

### Step 8, report

```
VERDICT
[Works at the stated assumptions / does not work / undetermined, in one line.]

THE UNIT
[What one unit is.]

CONTRIBUTION MARGIN
[Per unit, itemised, with provenance on each line.]

BREAK-EVEN
[Volume, and whether a named channel can deliver it.]

CASH
[Working capital cycle in days, cash locked at current and 3x revenue, peak funding need.]

ACQUISITION
[Cost per customer by channel, payback in months.]

PRICE
[Proposed price, the three reference points, and the reasoning.]

THE DECIDING ASSUMPTION
[The one input that determines the answer, and how to verify it within a week.]

MODEL
[The script, so the arithmetic can be checked and re-run.]
```

## Self-audit

- The unit is stated and held constant.
- Founder labour is priced.
- Cash cycle is modelled, not just profit.
- Every input has provenance, assumptions have ranges.
- Break-even volume is tied to a named channel.
- Price is justified from willingness to pay, and cost coverage is checked separately.
- The deciding assumption is named with a verification step.
- The script is included and its output matches the numbers in the text.
