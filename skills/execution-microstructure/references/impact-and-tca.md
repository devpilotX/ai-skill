# Market impact and transaction cost analysis

## Components of cost

For an order decided at price P_d, reaching the market at P_a, filled at an average P_f on part of the
target, with the rest marked at P_c:

- Delay cost: filled quantity x (P_a - P_d), signed by side.
- Execution cost: sum over fills of quantity x (fill price - P_a). It contains the spread paid and the impact.
- Opportunity cost: unfilled quantity x (P_c - P_d). Missing a trade that would have made money is a cost.
- Fees, commissions, taxes, and rebates as a negative cost.

This is Perold's (1988, "The Implementation Shortfall: Paper versus Reality", Journal of Portfolio
Management) implementation shortfall, and `scripts/execution_cost.py shortfall` computes it.

## Impact models

Temporary impact affects the price of the current trade and decays; permanent impact shifts the price for
everyone after. Separating them matters because permanent impact is paid on every later slice.

Square root law: the price move from a metaorder of size Q, in units of daily volatility, grows with the
square root of Q over daily volume, I = Y x sigma_daily x sqrt(Q / V). The coefficient Y is of order one
in many studies across equities, futures and other markets (Toth et al., 2011; Bouchaud, Bonart, Donier
and Gould, 2018, Trades, Quotes and Prices, Cambridge University Press). Treat Y as a parameter to
calibrate, not a constant; it varies by market, period and execution style.

Almgren and Chriss (2000): linear temporary and permanent impact, arithmetic Brownian motion prices, and a
mean-variance objective. The optimal schedule is a hyperbolic sine decay with rate kappa; the parameter
1 / kappa is the half-life scale of the trade. With zero risk aversion it becomes a straight line. It is a
planning tool: linear impact is a poor fit for large orders, and there is no alpha term. Later work adds
non-linear impact, decay (Obizhaeva and Wang, 2013, "Optimal trading strategy and supply/demand dynamics",
Journal of Financial Markets), and alpha.

Kyle (1985, "Continuous Auctions and Insider Trading", Econometrica): price moves by lambda times signed
order flow, where lambda measures how much market makers learn from flow. Estimate it by regressing price
changes on signed volume.

## Spread measures

- Quoted spread: ask minus bid at the time of the trade.
- Effective spread: twice the signed difference between the trade price and the prevailing mid.
- Realised spread: twice the signed difference between the trade price and the mid some interval later. The gap between effective and realised spread is the price impact, the part a liquidity provider loses to informed flow.
- Roll (1984, "A Simple Implicit Measure of the Effective Bid-Ask Spread", Journal of Finance): 2 x sqrt(-cov(dp_t, dp_t-1)) from trade prices alone, when quotes are unavailable. Undefined when the autocovariance is positive.

## Calibrating on your own fills

1. Collect parent orders with decision time and price, child fills with timestamps, and market data (mid, spread, volume, volatility) for the period.
2. For each parent order compute participation (Q / V over the execution window), duration, volatility, and the shortfall in units of volatility.
3. Fit shortfall = a + Y x sigma x (Q / V)^beta by outlier-resistant regression (Huber loss or median based), with beta free and then fixed at 0.5 to compare.
4. Check residuals by time of day, venue, algorithm and market regime. Systematic residuals mean a missing variable.
5. Keep a holdout of recent orders to test the fitted model.

Selection bias: orders that were cancelled after the price ran away are missing from the fill data, and
they are the expensive ones. Include cancelled and partially filled parents with their opportunity cost.

## Markouts

For each fill, compute the signed mid change at horizons after the fill: +1 s, +10 s, +1 min, +5 min, and
for slower strategies +30 min and the close. Average by strategy, venue, order type and time of day.

- Negative markouts on passive fills: adverse selection, the fills came from better-informed flow.
- Negative markouts on aggressive fills that deepen with horizon: the trades are moving the price and the permanent impact is large, or the signal is being chased.
- Markouts that reverse at longer horizons: temporary impact that decays.

## Benchmarks

Arrival price: the fairest measure for alpha-driven orders. VWAP: easy to beat by trading passively and
missing the volume, and inflated by the order's own volume when it is a large share of the day. Close:
appropriate for index funds and orders that must match the close. Choose before the order and keep it.

## Information leakage

Signs: the price moves before the order is visible in the prints, larger moves on venues where the order
rested, or unusual quote activity when a pattern starts. Responses: randomise, split across venues, use
conditional orders, reduce displayed size, and measure pre-trade drift conditional on the order.
