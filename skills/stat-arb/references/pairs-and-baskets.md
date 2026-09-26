# Pairs and baskets

## Cointegration in brief

Two non-stationary series are cointegrated when a linear combination of them is stationary. For log
prices y and x, the spread s = y - beta x - alpha then reverts to a mean. Correlation of returns is a
different property: two series can be highly correlated in returns and drift apart forever, or weakly
correlated and cointegrated.

## Engle-Granger

Two steps (Engle and Granger, 1987, Econometrica): regress y on x to estimate beta, then test the
residual for a unit root with an augmented Dickey-Fuller regression. Because beta was chosen to make the
residual look stationary, the critical values are more negative than for a plain ADF test. MacKinnon
(2010) gives response surface critical values; with a constant and two variables the asymptotic values
are about -3.90, -3.34 and -3.04 at 1, 5 and 10 percent, which `scripts/pairs_lab.py` uses.

Caveats: the result depends on which series is the dependent variable (test both directions); lag choice
changes the statistic (report the lags); and the test has low power against slow mean reversion, so a
non-rejection is weak evidence of no cointegration.

## Johansen

For three or more series, the Johansen (1991) procedure estimates a vector error correction model and tests
the rank of the cointegration matrix with trace and maximum eigenvalue statistics. It finds every
cointegrating vector at once and treats all series symmetrically. Critical values depend on the
deterministic terms (constant, trend) included; state which. Not implemented in the script; use a
statistics package and record its version.

## Ornstein-Uhlenbeck fit

ds = theta (mu - s) dt + sigma dW. Sampled at interval dt, it is an AR(1): s_t = a + b s_{t-1} + e with
b = exp(-theta dt). Half-life = ln 2 / theta. Equilibrium standard deviation = sigma / sqrt(2 theta),
estimated as sd(e) / sqrt(1 - b^2). AR(1) estimates of b are biased toward zero in short samples, so
half-lives are biased short; bootstrap the half-life to see its uncertainty.

## Hedge ratio choices

- OLS of y on x: minimises variance of the spread in y units; asymmetric.
- Total least squares or orthogonal regression: symmetric in the two series.
- Rolling OLS: tracks change, lags it, and has a window to choose.
- Kalman filter with the hedge ratio as a random walk state: observation y_t = alpha_t + beta_t x_t + v_t, state (alpha, beta) with process noise. The ratio of process noise to observation noise sets how fast beta adapts; choose it on formation data and fix it. A fast-adapting filter absorbs the divergence and the spread looks stationary by construction.

Whatever the method, hedge in currency terms for execution (shares of x per share of y implied by beta
and the prices), and recompute after corporate actions.

## Residual reversion in a factor model

Avellaneda and Lee (2010, "Statistical arbitrage in the US equities market", Quantitative Finance): regress
each stock's returns on sector ETF returns or on principal components, model the cumulated residual as an
OU process, and trade on its standardised level (the s-score) when the fitted mean reversion is fast
enough. This spreads the bet across many residuals and makes the book factor neutral by construction.

Points to handle: the number of factors (eigenvalues above the Marchenko-Pastur edge, per
`portfolio-risk`), the estimation window, earnings dates (exclude or treat as events), and volume
conditions (they report using volume information improved results).

## Search and selection bias

- Screening thousands of pairs and keeping the best is a multiple testing problem; record the count.
- Use a formation period to select and fit, and a later trading period to evaluate. Gatev, Goetzmann and Rouwenhorst (2006) use a 12 month formation and 6 month trading window; any choice works if it is fixed in advance.
- Reselection frequency is a parameter and counts as a trial.
- Survivorship: include pairs whose members were later delisted, with delisting returns.

## Costs and constraints specific to spreads

- Both legs pay spread and impact, on entry and exit.
- Legging risk: if one leg fills and the other does not, the position is directional until it does.
- Borrow cost and availability for the short leg, recalls, and short sale restrictions during stress.
- Dividends: the short pays them. Special dividends and rights issues move the spread.
- Different currencies or trading hours between legs add FX exposure and asynchronous prices.

## Signs a spread has broken

- Rolling ADF statistic rising above critical values and staying there.
- Rolling half-life lengthening steadily.
- Hedge ratio drifting in one direction.
- A fundamental event on one leg: acquisition, divestiture, index inclusion, regulatory change, guidance change.
- The z-score beyond any level seen in formation, with volume.

Close on a break. Adding to a position because the z-score is more extreme treats a regime change as an
opportunity.
