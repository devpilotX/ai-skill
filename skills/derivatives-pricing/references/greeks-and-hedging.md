# Greeks, hedging and P&L attribution

## Units

State them every time. Delta in underlying units per option, or as a share-equivalent position. Gamma per
unit of underlying move, or dollar gamma (0.5 x gamma x S^2 x 1 percent squared is the P&L from a 1 percent
move). Vega per 1.00 of volatility or per vol point. Theta per year or per calendar or trading day. Rho per
1.00 or per basis point. `scripts/options_lab.py` reports vega per 1.00, theta per year and rho per 1.00.

## P&L attribution

Over one period, for an option position with value V(S, sigma, t):

dV = delta dS + 0.5 gamma dS^2 + vega d sigma + theta dt + vanna dS d sigma + 0.5 volga d sigma^2 + residual

Compute each term with Greeks from the start of the period and the observed changes. A residual that is
large or trends means a missing Greek (for example a dividend or rate change), a smile-dynamics effect not
captured by using a single implied vol, a bad Greek, or a data error. Set a tolerance and investigate
breaches.

For a delta-hedged position, the delta term cancels, and gamma plus theta combine to approximately
0.5 x gamma x S^2 x (realised variance - implied variance) x dt. Summed over the life:

P&L of a delta-hedged option is approximately the integral of 0.5 x gamma x S^2 x (sigma_realised^2 -
sigma_implied^2) dt.

The weighting by dollar gamma means the path matters: realised volatility near the strike close to expiry
counts much more than the same volatility far from the strike.

## Hedging frequency

Discrete hedging leaves a hedging error whose standard deviation falls roughly with the square root of the
number of rebalances, while transaction costs grow with it. Kamal and Derman (1999, "When You
Cannot Hedge Continuously: The Corrections of Black-Scholes", Risk) and later work on discrete
hedging quantify the error; Leland (1985, "Option Pricing and Replication with Transactions Costs",
Journal of Finance) adjusts the volatility for costs. Practical rules: hedge on a delta band rather than a
clock, widen the band as gamma rises near expiry if costs dominate, and measure hedging error explicitly.

## Which delta

Black-Scholes delta at the implied volatility assumes sticky strike behaviour. When the smile moves with
spot, the hedge that minimises variance differs. Estimate the minimum variance delta by regressing option
price changes on underlying changes in history, or use the model's dynamics (local volatility, SABR,
Heston) consistently for price and hedge. Report which delta is used.

## Vega risk

Aggregate vega by expiry bucket and by strike region (put wing, at the money, call wing). A book flat on
total vega can be long short-dated and short long-dated volatility, which is a term structure bet. Weight
vega across expiries if hedging with a different expiry, since short-dated implied volatility moves more
than long-dated.

## Near expiry

Gamma grows without bound at the strike as expiry approaches. Pin risk: at expiry with the underlying near
the strike, whether the option is exercised is uncertain, and the resulting position in the underlying is
unknown until after the close. Cut positions near large strikes before expiry or hedge the pin explicitly.

## Dividends and borrow

Discrete dividends lower the forward and create early exercise incentives for American calls just before
the ex-date. Borrow cost acts like a dividend yield for the forward. Hard-to-borrow stocks show put-call
parity violations that are the borrow cost, not arbitrage.

## American exercise

Early exercise of a call on a non-dividend paying stock is never optimal; with dividends it can be,
before the ex-date. Early exercise of a put can be optimal when deep in the money and rates are positive.
Price American options with a lattice, finite differences with a free boundary, or least squares Monte
Carlo, and compare the early exercise premium against the European price.

## Exotics

Barriers: delta and gamma are discontinuous near the barrier, and hedging near it is expensive. Price with
a model that has realistic smile dynamics, since barrier values depend on the forward smile. Apply a
barrier shift for discrete monitoring (Broadie, Glasserman and Kou, 1997).

Multi-asset: correlation is an input with no liquid market for most pairs. Report sensitivity to it, and
use a correlation stress in risk.
