# Probability toolkit

The tools that come up again and again in trading decisions, estimation questions and interview style
problems, with the traps attached to each.

## Expected value and its limits

EV = sum of outcome x probability. Compute it, then ask three questions. Is the variance survivable at
the size proposed? Is the outcome distribution skewed, so that the mean comes from a rare event the sample
has not shown? And is the bet repeated, so that growth (the expected log) matters more than the mean?

The St Petersburg game has infinite expected value and a fair price of a few units to anyone with finite
wealth. Expected log wealth, not expected wealth, is the quantity a repeated bettor maximises.

## Conditioning and Bayes

Posterior odds = prior odds x likelihood ratio. Work in odds for sequential updates: each independent
piece of evidence multiplies by its ratio. Base rates dominate when the prior is small: a test with 99
percent sensitivity and 98 percent specificity for a condition with prevalence 0.1 percent gives a
positive predictive value under 5 percent. `scripts/edge_calc.py bayes` computes it.

Traps: conditioning on the wrong event (the host's behaviour in the Monty Hall problem is information),
treating evidence as independent when it shares a source, and updating on the fact that someone chose to
tell you something without modelling why they chose to.

## Adverse selection and the winner's curse

The trade you get filled on is more likely to be the one you mispriced. In an auction, the winner is the
bidder with the highest estimate, which on average is too high; bid below your estimate by an amount that
grows with the number of bidders and the dispersion of estimates. When someone offers to trade with you,
update your value toward theirs before deciding: their willingness is evidence.

In a market making game: when asked for a two-sided quote on an uncertain quantity, set the mid at your
expected value and the width by your uncertainty and by how much the other side might know. After each
trade against you, move your quote in the direction of their trade. A quote that does not move after being
hit is being picked off.

## Sizing

Kelly for a binary bet paying b per unit with win probability p: f* = p - (1 - p) / b. Growth is highest
at f*, about zero at 2 f*, and negative beyond. With an uncertain p, the expected growth of betting f* on
the estimate is lower than it looks, and overestimating p is costlier than underestimating it, which is the
reason for fractional Kelly. Multiple simultaneous bets: size them jointly, since correlated bets are one
bet.

Risk of ruin grows quickly with overbetting. Simulate it with `scripts/edge_calc.py ruin` rather than
guessing.

## Order statistics and extremes

The maximum of n independent draws grows slowly: for standard normals, roughly sqrt(2 ln n). The best of
many backtests, fund managers or A/B variants is therefore expected to look good by chance; this is the
logic behind the deflated Sharpe ratio in `quant-research`. Regression to the mean follows: the next result
of the top performer is expected to be closer to the average.

## Martingales and stopping

A fair game stays fair under any stopping rule that does not see the future (the optional stopping
theorem, under mild conditions). Doubling strategies appear to win because they assume unlimited capital
and no table limit; with limits they convert many small wins into rare ruinous losses. Any betting system
claiming to turn a negative expected value game positive is wrong; find the assumption that breaks.

## Estimation under uncertainty

Fermi decomposition: split the quantity into factors you can bound, give each a range, combine in log
space, and report a range. Name the factor whose range contributes most, since that is the one to pin
down. `numbers-check` ships a Monte Carlo estimator for products of ranged inputs.

Calibration: when you say 70 percent, events should happen about 70 percent of the time. Score forecasts
with the Brier score or log loss and a calibration table (`scripts/edge_calc.py score`). Log loss punishes
confident wrong answers harshly, which is the property a trader wants from a scoring rule.

## Common traps

- Probability of a union added as if disjoint; probability of an intersection multiplied as if independent.
- Linear thinking about compounding: a 50 percent loss needs a 100 percent gain to recover.
- The gambler's fallacy (independent events do not correct) and its mirror, the hot hand, which does exist in some settings and not others: test it.
- Survivorship: conditioning on the funds, strategies or companies still around.
- Anchoring on the first number offered, including one's own first estimate.
- Ignoring the option value of waiting for information when a decision is reversible.
