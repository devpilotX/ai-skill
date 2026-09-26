# Volatility surfaces

## Static arbitrage conditions

For call prices C(K, T) on one underlying with forward F(T) and discount factor D(T):

- Bounds: max(0, D(T)(F - K)) <= C <= D(T) F.
- Monotonic in strike: C non-increasing in K, with slope between -D(T) and 0. A steeper slope makes a vertical spread worth more than its maximum payoff.
- Convex in strike: butterflies cost at least zero. With unequal spacing, the slope between successive strike pairs must be non-decreasing.
- Calendar: for the same forward moneyness k = ln(K / F(T)), total implied variance w(k, T) = sigma^2 T must not decrease with T. With proportional dividends this is the right test; with discrete cash dividends, compare at the same moneyness and check with care.

`scripts/options_lab.py chain` and `calendar` check these. Violations on mid prices that close inside the
bid-ask are not arbitrage. Violations beyond the spread are usually stale quotes, a wrong forward, or
American exercise.

In density terms: the second derivative of the call price in strike, divided by the discount factor, is
the risk neutral density (Breeden and Litzenberger, 1978). Convexity violations mean a negative density.

## Parameterisations

SVI (stochastic volatility inspired, Gatheral, 2004): total variance per expiry
w(k) = a + b (rho (k - m) + sqrt((k - m)^2 + sigma^2)). Five parameters, linear wings consistent with
Lee's (2004) moment formula bounds. Individual slices can still admit butterfly arbitrage, and slices can
cross. Gatheral and Jacquier (2014, "Arbitrage-free SVI volatility surfaces", Quantitative Finance) give
conditions and the surface SVI form that prevents calendar arbitrage.

SABR (Hagan, Kumar, Lesniewski and Woodward, 2002, "Managing Smile Risk", Wilmott Magazine): forward
dynamics dF = alpha F^beta dW, d alpha = nu alpha dZ, correlation rho. The widely used implied volatility
expansion is accurate near the money and for short expiries; at low strikes and long expiries it can
imply a negative density. Fixes include arbitrage-free SABR via a finite difference density, and shifted
SABR for negative rates.

Heston (1993): variance follows a square root process with mean reversion kappa, long-run level theta,
vol of vol xi, correlation rho. Semi-closed form prices via characteristic functions. The Feller condition
2 kappa theta >= xi^2 keeps variance away from zero; calibrations to equity smiles often violate it, which
matters for the simulation scheme (use the Andersen quadratic exponential scheme or full truncation, not a
naive Euler step). Heston fits long expiries better than the short-expiry skew.

Local volatility (Dupire, 1994): sigma_loc(K, T)^2 = (dC/dT + (r - q) K dC/dK + q C) / (0.5 K^2 d2C/dK2),
reproducing every vanilla. It needs a smooth, arbitrage-free input surface, because it divides by the
density. Its forward smile flattens, so it misprices products that depend on future smile (cliquets,
forward starts), and its implied spot-vol dynamics give a delta that differs from market behaviour.

## Fitting practice

- Fit in implied volatility or total variance, weighted by vega or by inverse bid-ask spread, so illiquid wings do not dominate.
- Enforce no-arbitrage in the fit (constraints or a penalty), and check after fitting with the chain and calendar tests.
- Handle the forward explicitly per expiry; do not fit through it.
- Short expiries around events (earnings, central bank meetings) carry jumps; separate the event variance from the diffusive part.
- Extrapolate wings with forms that respect Lee's moment bounds.
- Track parameters over time. Jumps in fitted parameters without market moves mean the fit is unstable.

## Smile dynamics

How the smile moves when spot moves decides delta:

- Sticky strike: implied vol at each strike stays fixed as spot moves.
- Sticky moneyness (sticky delta): the smile moves with spot.
- Local volatility implies the at-the-money vol moves by about twice the skew slope times the spot move, in the direction of the skew.

Equity index markets show at-the-money volatility rising as spot falls. The hedge ratio that accounts for
this (the smile-adjusted delta) differs from Black-Scholes delta, and for skewed markets the difference is
material. Measure it from history for the underlying.

## Data hygiene

Use synchronous quotes for the option and the underlying. Record bid, ask and size. Exclude quotes with
zero bid, crossed markets, and quotes older than a stated threshold. For American options, back out
European-equivalent volatility with a model that includes early exercise, or restrict the fit to strikes
where early exercise premium is negligible.
