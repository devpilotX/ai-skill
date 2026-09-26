# Ground reality

Phase 5. Try to break what survived, using real numbers or labelled assumptions.

## Data discipline

Search for the real figures first. Prices, wages, margins, licensing costs, equipment costs, freight
rates, category failure rates. If the tooling can retrieve it, retrieve it and cite the link.

No search tool available? Then every figure in the response is `ASSUMPTION:`, the response says once, near
the top, that nothing was retrieved, and the verdict moves toward NOT ENOUGH INFORMATION unless the
decision survives the whole plausible range of the load-bearing number. Name the source the user should
check for each figure.

Do the arithmetic with a script, never in prose. `numbers-check` sets the method, and the
`business-model` skill ships a calculator for contribution, break-even, cash cycle, payback, LTV and peak
funding.

Label everything else, as in `ASSUMPTION: diesel at 3.90 a gallon`, with the reasoning and how much
the conclusion depends on it.

Flag the leverage. If one assumption decides the verdict, name it as the thing to verify first.

Never round toward the answer you prefer. Optimistic going in and pessimistic coming out is how every
bad plan survives its own spreadsheet.

A hallucinated market size in confident prose is the most harmful thing this skill could produce,
because it turns a vague hope into a false certainty and gets money spent.

## The seven checks

### Unit economics

One transaction, fully loaded. Revenue per unit, minus direct cost, minus allocated overhead, minus
payment fees, minus returns and spoilage and waste, minus the owner's own labour at a market rate.

If the unit loses money, volume makes it worse. Scale is a multiplier and it has a sign.

Ask whether the owner's labour gets paid at all. Divide the profit the plan expects by the hours the
owner will work, and compare the result with the local minimum wage (retrieve the current rate from the
government source) and with what the owner could earn employed. If the effective rate is below either,
the business is a job that pays less than the alternative. That can be a legitimate choice. It has to be a
conscious one.

### Capital and working capital

Cash to first sale, then cash to steady sales, which is a larger number.

The working capital cycle is the item homemade plans most often leave out. Pay suppliers on day zero,
get paid on day ninety, and a growing, genuinely profitable business runs out of money. Growth consumes
cash. Cash conversion cycle = inventory days + receivable days - payable days, valued with daily, not
monthly, figures; the formulas live in `business-model`.

Maximum drawdown before the first dollar arrives.

If any of it is borrowed, does the payment schedule survive a bad quarter?

What breaks if revenue arrives three times slower than planned? Run that case, because first plans
tend to be optimistic about timing.

### Distribution

Often the real bottleneck, and often the part skipped in favour of the product.

Name the first ten buyers. Not a segment. Ten identifiable names or firms.

How does buyer one hundred hear about it, and at what cost to acquire?

Is that cost recoverable inside the cash cycle, not just inside lifetime value?

Does a channel already exist, or does one have to be built? Building one is a second business.

A product with no distribution path fails this phase regardless of quality.

### Competition and the do-nothing option

Who serves this need today, including badly?

The default competitor is inertia. The status quo is free, familiar, and already installed, so the new
option has to beat it by more than the switching cost.

What is the switching cost for the buyer in money, time, risk, retraining, and political cover?

If incumbents are obviously bad at this, find out why. There is usually a structural reason, and it
will apply to the newcomer too.

What happens when the largest incumbent notices? "We're dead" is not automatically fatal, but the
timeline has to be known.

### Regulation, licensing, liability

Licences, permits, inspections, zoning, bonding, insurance. Cost and calendar time, and calendar time
is often the binding constraint.

Is the product in a regulated category such as medical, financial, food, legal, childcare, transport,
alcohol, or energy? Then compliance is a line item, not a footnote.

Personal liability exposure. What is the worst single claim?

Are there rules that make the plan illegal as described? Better to learn that now.

In a regulated category, name the professional and the question. For licensing and liability, a
solicitor or attorney who practises in that sector: "What licences, registrations, and insurance does a
business selling X to Y in Z need before its first sale, how long does each take, and what personal
liability do I carry if a customer is harmed?" For tax and structure, a chartered accountant or CPA:
"Which entity type and tax registrations does this need at an expected first-year revenue of N, and what
does that cost me each year?"

### Base rates

What fraction of entrants to this category still operate after five years? Retrieve it. Do not guess.
Where to find survival data and how to read a cohort table are in `references/base-rates.md`.

What is the median outcome, rather than the outlier in the case study? Survivorship bias is the
default lens on every business story the user has read.

What specifically kills most of them, and is that cause addressed or just unmentioned?

### The load-bearing assumption

Strip it down. What single thing must be true, without which nothing else matters?

Then: is it true? What would prove it? How fast and how cheaply?

A plan with one unexamined load-bearing assumption is betting everything on it without knowing.

## Domain traps

These are where confident generic advice does the most damage.

Commodity and physical goods, including timber, agriculture, metals, fuel, and bulk food. The market
sets the price, so there is no pricing power and no branding your way out. Margin comes from cost
position or logistics and nothing else. Working capital is brutal, inventory degrades, freight can
exceed product value, and one bad counterparty on credit terms can end the business. Cyclical demand
means entering at the top of a cycle looks like genius for a year.

Physical asset businesses such as equipment hire, vehicle fleets, and property. Capital is sunk and
illiquid. Utilisation rate decides the economics, since an asset idle half the time has double the
effective cost per hour used. Budget maintenance and downtime explicitly, from the manufacturer's
schedule or an operator's records, not from hope. Depreciation is a real cost
even when no cash moves. Exit means selling into a thin secondary market.

Marketplaces and two-sided platforms. Chicken and egg on both sides at once. Liquidity per segment
matters, not total users. The take rate ceiling is set by how easily both sides can transact off
platform, and they will try.

Consumer subscription apps. Churn compounds against you. Free incumbents anchor the price at zero.
Compare paid acquisition cost per paying user with contribution-based lifetime value from a retention
curve; if CAC is retrieved from ad platform data and LTV is assumed, say which side is the guess. Store
commission comes off the top, and the rate depends on the programme: Apple and Google both have reduced
rates, including 15 percent tiers for small developers and for subscriptions after the first year, and
court rulings and regional rules such as the EU Digital Markets Act have changed what payment routes are
allowed. Retrieve the current terms from the Apple App Store and Google Play developer documentation for
each target country.

Services and agencies. Revenue is capped by hours unless something gets productised. The founder is
the product, which makes the business hard to sell. Client concentration is a survival risk: compute
what happens to cash if the largest client leaves with thirty days' notice.

Model-wrapper products. Compare cost per call against the subscription price at the usage level of the
heaviest ten percent of users. The underlying provider can ship the feature natively and close the
category overnight. Ask what stays valuable if the model gets ten times cheaper and ten times better.
If nothing does, the answer is already known.

Regulated professional services, including health, legal, finance, and childcare. Licensing gates
entry, which cuts both ways: a moat if you hold the licence, a wall if you do not. Liability insurance
is a major line item, so get a quote early. Institutional procurement can take quarters, so ask
the first buyer how long their last purchase took.

## Output of this phase

For each surviving candidate: the assumptions it needs, which of them are verified against assumed,
the specific number or condition that kills it, and whether it clears the bar. Then go to phase 6.
