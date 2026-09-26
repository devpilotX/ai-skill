# Pricing

## Choose the value metric first

The value metric is what the price scales with. Getting it wrong causes more damage than setting the
number wrong, because the number can be changed later and the metric usually cannot.

A good value metric grows with the value the customer receives, is easy for the buyer to predict before
buying, and is hard to game.

Seats work when value grows with the number of people using it and fail when a few heavy users carry all
the value, since customers then share logins.

Usage works when consumption tracks value and fails when the customer cannot predict their bill, which
stalls enterprise deals because procurement struggles to approve an unbounded number. A cap or a committed
spend tier fixes most of that.

Outcome based pricing aligns best and is hardest to measure and to collect on.

Flat pricing is easiest to sell and leaves money on the table with large customers, which is acceptable
early and expensive later.

## Setting the number

Start from what the buyer spends on the problem now. That includes the incumbent's licence, the hours
spent on the manual workaround at a loaded labour rate, and the cost of the errors the current approach
causes. Those three numbers give the ceiling.

Cost plus gives the floor. The price has to clear contribution cost with room for acquisition cost and
fixed cost. Check the floor after establishing the ceiling, never the other way around, because starting
from cost anchors the price to the wrong thing.

Then position between floor and ceiling according to how strong the alternative is. Weak alternatives
support a price near the ceiling.

Test the price by asking for the money. A quoted price that a real buyer accepts without hesitation was
probably too low, and one that ends every conversation is too high.

Compare two prices by expected value per prospect: conversion rate x contribution per customer -
acquisition cost per prospect. With the same cost per prospect, two out of ten converting at a high price
beats eight out of ten at a low one only when the high price's contribution is more than four times the
low one's. Use lifetime contribution from `references/formulas.md` where customers repeat.

## Budget authority

Every organisation has thresholds above which a purchase needs another signature. Crossing one adds
weeks and sometimes a procurement process, a security review, and a legal review.

Pricing just under the buyer's threshold can shorten the cycle, and pricing just over it can add an
approval round for a few percent more revenue. Thresholds differ by organisation, so ask each buyer what
they can approve alone rather than assuming a common figure.

## Tiers

Three tiers is a common convention. Whether buyers gravitate to the middle one depends on the product and
the page, so treat that as a hypothesis and measure tier mix on real signups. Design the tier you want sold
first, then build the others around it.

The cheap tier exists to remove the price objection and to qualify buyers, not to make money. Keep it
narrow enough that serious users outgrow it.

The expensive tier exists to capture large customers, and it may also make the middle one look
reasonable by comparison. It
should contain the things large buyers genuinely need, such as access control, audit logs, single sign
on, support response times, and contractual terms.

Differentiate tiers by value received, not by artificial restriction of things that cost nothing to
provide. Buyers notice, and it damages trust.

Keep the number of tiers small enough that a buyer can tell which one fits them. Do not justify this with
choice paralysis: a meta-analysis of choice overload experiments (Scheibehenne, Greifeneder and Todd,
"Can there ever be too many options?", Journal of Consumer Research, 2010) found a mean effect near zero,
with large variation between studies. The practical reason is that each extra tier is another boundary to
explain, support, and defend. Test tier count on real conversion if it matters.

## Changing prices

Raising prices on new customers is straightforward. Raising them on existing customers costs goodwill
and some churn, so it needs notice, a reason, and usually a grandfathering period.

Grandfathering forever is expensive and eventually creates several incompatible generations of customer.
Grandfather for a defined period and say so at the time.

Test a price change on new signups before applying it to the base, and measure conversion rather than
asking people what they would pay. Stated willingness to pay is unreliable in both directions.

## Traps

Discounting to close a deal teaches the buyer that the price is negotiable, and the information spreads.
Concede on terms, scope, or payment schedule instead of on the headline price.

Annual prepayment discounts are a cash decision, not a pricing decision. A 20 percent discount for
twelve months upfront is expensive capital, and sometimes worth it.

Free trials without a credit card produce volume and poor signal. With a card, they produce fewer and
better qualified users. Choose according to whether the constraint is learning or revenue.

Freemium only works when the free tier drives acquisition, meaning free users bring paying ones. Without
that mechanism it is a cost centre with a marketing story attached.

Per seat pricing on a product used by one person in a team caps revenue at one seat regardless of the
value delivered.

Charging for a model API wrapper at a flat rate while the underlying cost is per token puts the heaviest
users at a loss. Compute the unit economics at the usage level of the top decile, and cap or meter.

Pricing in a currency the buyer does not use pushes exchange rate risk onto them, which is a reason to
lose the sale.

Showing a consumer price without tax where the buyer expects it included. UK and EU consumer prices are
normally displayed VAT inclusive, so the business keeps price / (1 + VAT rate), not the displayed number.
Compute contribution on the net figure. B2B prices are usually quoted before VAT.

Payment terms are part of the price. Net 60 on a 1,000 order costs the seller the financing of 1,000 for
two months; a deposit or upfront payment does the reverse. Put terms and deposits into the cash cycle in
`references/formulas.md` before offering them in a negotiation.

Setting a price and never revisiting it. An early price was set when the product did less and the
founder had less evidence, so re-test it against conversion as both change.
