# Overfitting controls

A backtest is the maximum of a search. These controls estimate how much of the result the search
explains, and each needs the trial registry kept since step 3 of the skill.

## The trial registry

One row per configuration evaluated: date, code version, data version, universe, parameters, model,
in-sample and validation statistics, and whether it was abandoned. Abandoned trials count. A search that
tried 200 variants and reports the best one has 200 trials, not one.

When trials are highly correlated (parameter sweeps around one idea), the effective number of
independent trials is smaller than the raw count. Estimate it by clustering the trial return series and
counting clusters (the approach suggested by Lopez de Prado in later work on the deflated Sharpe ratio),
and report both numbers.

## Probabilistic and deflated Sharpe ratio

The probabilistic Sharpe ratio (Bailey and Lopez de Prado, 2012) is the probability that the true Sharpe
ratio exceeds a benchmark, given the sample length, skewness and kurtosis. Negative skew and fat tails
lower it, which is why a strategy selling insurance with a high Sharpe ratio can still score poorly.

The deflated Sharpe ratio (Bailey and Lopez de Prado, 2014) sets the benchmark to the expected maximum
Sharpe ratio of the trials under the null of no skill. Inputs: the number of trials and the variance of
their Sharpe ratios. The published worked example (annual Sharpe 2.5 over 1250 daily observations,
skewness -3, kurtosis 10, 100 trials with annualised Sharpe variance 0.5) gives a DSR of about 0.90, and
`tests/test_quant_tools.py` in the repository checks the script against it.

Minimum track record length gives the number of observations needed for the PSR to reach a confidence
level. Use it to set the paper trading period before any live capital.

All three are computed by `scripts/strategy_stats.py`.

## Multiple testing thresholds

Harvey, Liu and Zhu (2016) propose raising the t statistic hurdle for new factors to about 3.0 given the
number already tested in the literature. More generally, adjust p values for the number of trials:

- Bonferroni or Holm for control of the family-wise error rate. Conservative when trials are correlated.
- Benjamini-Hochberg or Benjamini-Yekutieli for control of the false discovery rate. The BY variant is valid under arbitrary dependence. `numbers-check` ships a Benjamini-Hochberg calculator.

Haircut the Sharpe ratio by converting the adjusted p value back to a Sharpe ratio, as Harvey and Liu
(2015, "Backtesting", Journal of Portfolio Management) describe.

## Data snooping tests across strategies

White's reality check (White, 2000, "A Reality Check for Data Snooping", Econometrica) tests whether the
best of a set of strategies beats a benchmark after accounting for the search, using a stationary
bootstrap of the performance differences. Hansen's superior predictive ability test (Hansen, 2005,
Journal of Business and Economic Statistics) is less sensitive to poor strategies in the set. Romano and
Wolf (2005, Econometrica) give a stepwise version that identifies which strategies survive.

## Probability of backtest overfitting

Combinatorially symmetric cross-validation (Bailey, Borwein, Lopez de Prado and Zhu, 2017):

1. Arrange the performance of all N configurations over T periods in a matrix and split the periods into S equal blocks (S even).
2. For every combination of S/2 blocks as in-sample and the rest as out-of-sample, find the best configuration in sample and its rank out of sample.
3. The probability of backtest overfitting is the share of combinations where the in-sample best ranks below the out-of-sample median.

A PBO near or above one half says the selection process has no out-of-sample value.

## Validation design

Walk-forward: fit on a window, test on the next, roll forward. Simple and honest, but uses each period
for testing only once, so the estimate is noisy.

Purged k-fold: remove from training any observation whose label window overlaps the test fold, and embargo
a period after the test fold so that serially correlated features do not leak across the boundary
(Lopez de Prado, 2018, chapter 7).

Combinatorial purged cross-validation: many train and test paths from the same data, giving a
distribution of out-of-sample performance rather than a single number (same book, chapter 12).

Never tune on the final holdout. Decide in advance which period or universe it is, lock it, and run on it
once with every choice already fixed. Report the holdout result even when it disappoints.

## Warning signs

- The Sharpe ratio rises as the search continues. The search is fitting noise.
- Performance depends on a narrow parameter value, and neighbouring values perform much worse.
- The equity curve is smooth in sample and ragged out of sample.
- Most of the return comes from a handful of days or names.
- The strategy works on the market it was designed on and nowhere else.
- Skewness is strongly negative and the Sharpe ratio is high; check the PSR and the stress windows.
