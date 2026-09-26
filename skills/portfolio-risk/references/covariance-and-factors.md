# Covariance estimation and factor models

## Why the sample matrix fails

With N assets and T observations the sample covariance has N(N+1)/2 free parameters estimated from NT
numbers. When N is not small relative to T, the largest eigenvalues are biased up, the smallest are
biased down toward zero, and the inverse, which is what an optimiser uses, amplifies the smallest ones.
The optimiser then loads on combinations of assets that look riskless in sample and are not.

The ratio q = N / T summarises the problem. At q = 0.5, for example, sample eigenvalues of a matrix whose
true eigenvalues are all one spread across a band from (1 - sqrt(q))^2 to (1 + sqrt(q))^2, about 0.09 to
2.9. That band is the Marchenko-Pastur distribution for independent data.

## Shrinkage

Shrink the sample matrix toward a structured target, with an intensity estimated from the data:

- Scaled identity: Ledoit and Wolf (2004, "A well-conditioned estimator for large-dimensional covariance matrices", Journal of Multivariate Analysis). Implemented in `scripts/risk_lab.py`.
- Constant correlation: Ledoit and Wolf (2004, "Honey, I Shrunk the Sample Covariance Matrix", Journal of Portfolio Management), better for equities where average correlation is positive.
- Single factor (market) model: Ledoit and Wolf (2003, Journal of Empirical Finance).
- Nonlinear shrinkage of each eigenvalue separately: Ledoit and Wolf (2012, "Nonlinear shrinkage estimation of large-dimensional covariance matrices", Annals of Statistics) and their later refinements, stronger for large N.

Report the intensity. An intensity near one means the data carries little information beyond the target
at this sample size.

## Denoising with random matrix theory

Compute eigenvalues of the correlation matrix, compare with the Marchenko-Pastur upper edge
(1 + sqrt(N/T))^2, keep eigenvalues above it, and replace those below with their average so the trace is
preserved (the constant residual eigenvalue method; Laloux, Cizeau, Bouchaud and Potters, 1999, "Noise
Dressing of Financial Correlation Matrices", Physical Review Letters). The first eigenvalue in equity data
is usually the market and sits far above the edge.

Caveats: returns are not independent or normal, so the band is approximate; and removing noise from the
correlation matrix does not fix errors in the volatilities.

## Factor models

Returns = exposures x factor returns + specific returns. Covariance = B F B' + D, with B the N by K
exposure matrix, F the K by K factor covariance and D diagonal specific variances. K much smaller than N
makes the estimate stable.

Three kinds:

- Fundamental: exposures are observed characteristics (industry, size, value, momentum, volatility), factor returns are estimated by cross-sectional regression each period. Commercial equity risk models work this way.
- Macroeconomic: factor returns are observed series (rates, credit spreads, oil, currencies), exposures are estimated by time series regression.
- Statistical: factors are principal components. No labels, and components rotate over time.

Check the model: the share of variance explained, stability of exposures, and whether specific returns
are really uncorrelated (residual correlation within an industry means a missing factor).

## Weighting and horizon

An exponentially weighted estimate with half-life h reacts to regime change. Use a shorter half-life
for volatility than for correlation, since correlations need more data. RiskMetrics (J.P. Morgan, 1996)
popularised a decay factor of 0.94 for daily volatility; treat any fixed value as an `ASSUMPTION:` and
choose by backtesting the risk forecast.

Match the horizon. Scaling daily risk by the square root of time assumes independent returns; with
autocorrelation or volatility clustering it is wrong. Estimate at the horizon of the decision where data
allows, or scale with the variance ratio of the actual series.

Asynchronous closing times across markets bias daily correlations toward zero. Use weekly returns or
adjust for the lead-lag.

## Stress correlations

Correlations estimated in calm periods understate correlations in stress. Keep a stressed covariance
estimated on crisis windows alongside the normal one and report risk under both. Longin and Solnik (2001,
"Extreme Correlation of International Equity Markets", Journal of Finance) document that correlation rises
in bear markets.
