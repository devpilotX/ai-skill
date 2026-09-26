# Signal evaluation

Evaluate the signal before building the strategy. A strategy adds sizing, costs and constraints that can
hide whether the signal predicts anything.

## Information coefficient

The information coefficient (IC) on a date is the cross-sectional correlation between the signal and the
subsequent return over the chosen horizon. Use the Spearman rank correlation by default, since it is
insensitive to outliers in either variable.

Report the mean IC across dates, its standard deviation, the ratio of the two (the IC information ratio),
and a t statistic. When the return horizon is longer than the sampling interval, consecutive ICs overlap
and are autocorrelated; use a Newey-West standard error with lags at least equal to the overlap, or
sample non-overlapping dates.

Typical cross-sectional equity ICs are small. Treat an IC that looks large for the asset class as a
prompt to look for leakage before celebrating it.

## Decay and horizon

Measure IC at several forward horizons (for a daily signal, one day, five days, twenty days and more).
The decay profile says how fast the signal must be traded and therefore what it costs. A signal whose IC
peaks at one day must be traded daily and pays daily costs.

Measure the autocorrelation of the signal itself. Low autocorrelation means high turnover.

## Quantile portfolios

Sort into quantiles by signal on each date and track forward returns of each quantile. Look for a
monotonic pattern across quantiles, not only a spread between the extremes. Report long and short legs
separately; many anomalies live mostly in the short leg, where borrow is expensive or unavailable.

## Factor exposure and neutralisation

Regress the signal on known characteristics (market beta, size, value, momentum, sector or industry,
volatility) and keep the residual. Recompute the IC on the residual. The part of the IC that survives
is what the signal adds. Fama and MacBeth (1973) cross-sectional regressions of returns on the signal plus
controls, with Newey-West standard errors on the time series of coefficients, give the same answer in
regression form.

After building the strategy, regress its returns on published factor returns (for equities, for example
the factor data maintained by Kenneth French) and report the intercept with its t statistic.

## Breadth and the fundamental law

Grinold (1989) relates the information ratio to skill and breadth: IR is approximately IC times the square
root of breadth. Clarke, de Silva and Thorley (2002, "Portfolio Constraints and the Fundamental Law of
Active Management", Financial Analysts Journal) add a transfer coefficient for the loss from constraints.

Two cautions. Breadth counts independent bets, and a thousand stocks driven by three factors are not a
thousand bets. And the law gives an upper bound before costs; it is a planning tool, not a forecast.

## Stability

Split results by calendar year, by market capitalisation bucket, by sector, and by market regime (for
example high and low volatility periods, defined in advance). An effect concentrated in one slice is a
finding about that slice. Say which slice.

Check the signal in a second universe or market that was not used to design it. Out-of-universe
replication is one of the strongest pieces of evidence available.

## Combining signals

Combining many weak signals is how breadth is built, and also how overfitting hides. Rules:

- Fix the combination method in advance: equal weights on standardised signals, or weights shrunk toward equal.
- Estimate weights on training data only, with the same purged splits as the signals themselves.
- Orthogonalise or at least report correlations between signals; two versions of the same effect are one signal.
- Count each candidate signal and each combination rule as trials.

## Capacity and crowding

Capacity falls with turnover and with the liquidity of the names where the signal is strongest. Estimate
it by raising traded capital in the cost model until net performance halves.

Crowding shows up as rising correlation between the strategy and published factor returns, falling
returns after publication (McLean and Pontiff, 2016, "Does Academic Research Destroy Stock Return
Predictability?", Journal of Finance, report an average decline after publication), and sharp joint
drawdowns across similar strategies when one large holder unwinds.

## What to put in the report

For the signal: mean rank IC with t statistic and lag count, IC by horizon, signal autocorrelation,
quantile returns with long and short legs separated, IC after neutralisation, and results by year.
For the strategy: the output of `scripts/strategy_stats.py` on net returns, turnover, capacity, factor
regression intercept and loadings, and stress window returns.
