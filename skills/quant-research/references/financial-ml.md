# Machine learning on financial data

Financial returns have a low signal to noise ratio, change behaviour over time, and are serially
dependent. Methods built for independent, identically distributed samples overfit here unless each of
the points below is handled. The general model discipline in `ml-build` still applies; this file covers
what is specific to returns.

## Labels

Fixed horizon labels (the sign of the return over the next h periods) ignore the path, so a trade that
would have hit its stop loss is labelled a winner if the price recovered by the horizon. The triple
barrier method labels each observation by whichever is touched first: a profit barrier, a loss barrier,
or a time limit, with barriers scaled to recent volatility (Lopez de Prado, 2018, Advances in Financial
Machine Learning, chapter 3).

Meta-labelling separates direction from sizing: a primary model or rule proposes the side, and a second
model predicts whether to act on it and with what confidence. It is useful when a discretionary or simple
rule already exists and the question is when to trust it.

## Overlapping labels and sample weights

When labels span several periods, neighbouring observations share most of their outcome, so the sample
contains far fewer independent observations than rows. Consequences:

- Standard cross-validation leaks. Use purged and embargoed splits, per `references/overfitting-controls.md`.
- Bagging with ordinary bootstraps draws near duplicates. Weight observations by their uniqueness (the average inverse number of concurrent labels over the label window), or use sequential bootstrap (same book, chapter 4).
- Reported accuracy overstates the evidence. Count effective observations, not rows.

## Stationarity against memory

Prices are non-stationary and returns throw away most of the memory in prices. Fractional differentiation
with a small order keeps more memory while passing a stationarity test (same book, chapter 5). Whatever
transformation is used, fit its parameters on training data only.

Standardise features with statistics from the training window, rolled forward, never from the full
sample.

## Feature importance

Mean decrease impurity from tree ensembles favours high cardinality features and is computed in sample.
Prefer mean decrease accuracy on purged out-of-sample folds, or single feature importance, and cluster
correlated features before judging importance, since substitutes split the credit between them
(same book, chapter 8).

Importance says what the model used, not what drives returns. It is a diagnostic, not evidence.

## Model choice and complexity

Start with a linear or regularised linear model on a handful of features, and a gradient boosted tree
model with strong regularisation. Report both. A deep model that beats them in sample and ties them out
of sample adds operational risk and nothing else.

Tune hyperparameters inside the training folds only. Every hyperparameter setting evaluated is a trial
for the deflated Sharpe ratio.

## Regime and decay

Refit on a rolling window and track out-of-sample IC over time. A model whose live IC decays toward zero
is being arbitraged or has hit a regime it never saw. Decide the retraining schedule and the decay
threshold that retires the model before going live.

## Leakage specific to finance

- Features computed with data from after the label start (for example a volatility estimate centred on the date).
- Target encoding or scaling fitted on the whole sample.
- Survivorship in the training universe, per `references/data-integrity.md`.
- Cross-sectional features computed over the full universe including securities that were not yet listed.
- Using the close to build a feature and to fill the trade.

## Large language model features

Text features built with a language model trained on data after the backtest date leak the future: the
model already knows how the story ended. Use models with a training cutoff before the test period, or
restrict text signals to the period after the model's cutoff, and say which was done.
