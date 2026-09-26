# Portfolio construction

Each method below is a different answer to the question of how much to trust the inputs. Pick by that,
not by habit.

## Mean-variance

Maximise w'mu - (lambda / 2) w'Sigma w subject to constraints. The solution without constraints is
w = (1 / lambda) Sigma^-1 mu. Sensitivity to mu is extreme: a small change in an expected return moves
weights by a large amount, and the optimiser picks the assets whose estimation errors are most
flattering. Chopra and Ziemba (1993, "The Effect of Errors in Means, Variances, and Covariances on
Optimal Portfolio Choice", Journal of Portfolio Management) found errors in means matter roughly an order
of magnitude more than errors in covariances.

Mitigations: shrink mu toward a prior, add realistic constraints (they act as shrinkage, as Jagannathan
and Ma, 2003, "Risk Reduction in Large Portfolios: Why Imposing the Wrong Constraints Helps", Journal of
Finance, showed for no-short constraints), and resample (Michaud's resampled efficiency averages
optimised weights across bootstrapped inputs).

## Minimum variance

w = Sigma^-1 1 / (1' Sigma^-1 1). Uses no return forecast. In equities it tilts toward low volatility,
low beta stocks, which is a factor bet; report it as one. Still needs a stable Sigma.

## Risk parity and risk budgeting

Equal risk contribution: each position contributes the same share of portfolio volatility. For
uncorrelated assets the weights are inverse volatility. Needs no return forecast and is less sensitive
to estimation error than mean-variance. With low volatility assets such as bonds it needs leverage to hit
a return target, and the leverage carries funding and liquidity risk that the volatility number hides.

Risk budgeting generalises it: assign target risk shares by conviction. `scripts/risk_lab.py riskparity`
computes the equal case with the cyclical coordinate method.

## Hierarchical risk parity

Lopez de Prado (2016, "Building Diversified Portfolios that Outperform Out of Sample", Journal of
Portfolio Management): cluster assets by correlation distance, order the matrix by the tree
(quasi-diagonalisation), then split weight recursively between clusters in inverse proportion to their
variance. Avoids inverting the covariance matrix. It is still a heuristic; compare its out-of-sample
risk against minimum variance and risk parity on the same data.

## Kelly and fractional Kelly

Growth optimal weights for a continuous-time model are Sigma^-1 mu, the same direction as mean-variance
with lambda = 1. With estimated mu the full Kelly bet overbets, and overbetting reduces growth and sharply
increases drawdowns. Half Kelly gives about three quarters of the growth rate with half the volatility
(MacLean, Thorp and Ziemba, 2011, The Kelly Capital Growth Investment Criterion). Use a fraction, and
justify it by the uncertainty in the edge.

## Volatility targeting

Scale exposure so predicted volatility stays near a target. Reduces tail risk when volatility clusters,
at the cost of turnover and of selling after losses. Moreira and Muir (2017, "Volatility-Managed
Portfolios", Journal of Finance) report improved Sharpe ratios for several factors; check the result
after costs for the specific strategy.

## Combining strategies

Treat strategies as assets. Estimate their return correlation from live or out-of-sample returns, not
from overlapping backtests that share data and design choices. Allocate by risk budget, and cap any one
strategy's share of risk so that a model failure in one cannot dominate.

## Constraints and costs

Include in the optimisation:

- Transaction costs, with impact growing with trade size relative to volume, from `execution-microstructure`.
- A turnover penalty or cap.
- Position and liquidity limits (a share of average daily volume, and days to exit).
- Factor and sector exposure limits.
- Gross and net exposure, and borrow availability for shorts.

Rebalancing: trade only when the benefit of moving toward the target exceeds the cost. A no-trade band
around the target weights is a simple rule that captures most of the gain.

## Drawdown control

A drawdown rule (cut risk by half after a stated drawdown, restore after recovery) limits the damage from
a model that stopped working. It also sells after losses and buys back after gains, which costs money
when drawdowns are noise. Decide the rule in advance, from the strategy's expected drawdown distribution
(for a Sharpe ratio S and horizon, simulate it), and write down who executes it.

## Stability test

Bootstrap the returns, re-estimate, re-optimise, and report the spread of each weight. Choose among
methods by out-of-sample risk and turnover on held-out data, not by the in-sample efficient frontier.
