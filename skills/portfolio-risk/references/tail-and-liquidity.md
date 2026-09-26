# Tail risk, stress testing and liquidity

## Value at risk and expected shortfall

VaR at confidence alpha and horizon h is the loss exceeded with probability 1 - alpha. Expected shortfall
is the average loss given that VaR is exceeded. ES is subadditive (a coherent risk measure in the sense of
Artzner, Delbaen, Eber and Heath, 1999, "Coherent Measures of Risk", Mathematical Finance) and VaR is not,
so VaR can penalise diversification.

Methods:

- Historical simulation: apply past returns to today's positions. No distribution assumption; limited by the window, which may contain no stress at all.
- Parametric (variance-covariance): assumes normal returns, understates tails for most assets.
- Filtered historical simulation: rescale past returns by the ratio of current to past volatility from a GARCH type model. Keeps the empirical shape and reacts to current conditions.
- Extreme value theory: fit a generalised Pareto distribution to losses beyond a high threshold (peaks over threshold) for quantiles beyond the data.

With 250 observations, a 99 percent VaR rests on two or three losses. Report how many observations lie in
the tail, and do not quote 99.9 percent figures from a year of data.

Options and other non-linear positions need full revaluation, not delta approximation, for large moves.

## Backtesting the model

Coverage: the Kupiec (1995) proportion of failures test, computed by `scripts/risk_lab.py kupiec`.
Independence: exceptions should not cluster; Christoffersen (1998) gives a test, and a conditional
coverage test combining both. The Basel traffic light approach classifies 250-day backtests of 99 percent
VaR by exception count; retrieve the current zone boundaries from the Basel Committee text before
quoting them.

Low power is the usual problem: a year of data barely distinguishes a model with 1 percent exceptions
from one with 2 percent. Say so when reporting a pass.

## Stress scenarios

Historical, applied to today's positions with the moves observed in the episode:

- October 1987 equity crash.
- August to September 1998, the Russian default and the LTCM unwind: credit spreads widened, liquidity vanished, and relative value trades that were hedged lost together.
- August 2007 quant equity unwind: market neutral equity strategies lost sharply over a few days while the market index barely moved, consistent with forced deleveraging of similar portfolios (Khandani and Lo, 2007).
- September to November 2008.
- May 2010 flash crash (intraday).
- March 2020 liquidity shock, including dislocation in markets normally treated as the most liquid.

Hypothetical:

- All correlations moved toward one, with volatilities doubled.
- The largest factor exposure moving by a multiple of its worst historical move.
- A crowded trade unwinding: the positions most shared with similar strategies moving against the book at the same time.
- Funding: margin requirements raised and a financing counterparty withdrawing.
- Idiosyncratic: the largest single position gapping by its worst historical move.

Report for each: loss, the margin call it triggers, the liquidity available to meet it, and whether
positions must be sold into the stress.

## Liquidity risk

Market liquidity: the cost and time to exit. Measure days to liquidate each position at a stated share of
average daily volume, and the cost from the impact model in `execution-microstructure`. In a stress,
volume can fall and spreads widen at the same time; scale both, labelled `ASSUMPTION:`.

Liquidity-adjusted VaR adds the exit cost to the loss, and uses a horizon matched to the time needed to
exit rather than one day. Basel FRTB assigns liquidity horizons by risk factor for the same reason.

Funding liquidity: margin, haircuts and financing lines. Brunnermeier and Pedersen (2009, "Market
Liquidity and Funding Liquidity", Review of Financial Studies) describe how the two reinforce each other:
losses raise margins, which force sales, which worsen prices.

## Leverage

Size leverage to the stress loss: the book must survive the worst stress scenario with margin still
available and without forced sales at the bottom. Volatility-based leverage rules fail exactly when
volatility jumps, which is when they matter.

Track gross exposure, net exposure, and exposure per unit of equity separately. A market neutral book
with low volatility and high gross exposure carries the most hidden leverage.

## Crowding

Signs: rising correlation with published factors or peer strategies, high short interest and low borrow
availability in the short book, high ownership concentration by similar funds in the long book. Crowded
books share exits. Reduce concentration in the most shared names, and stress the book for a peer unwind.
