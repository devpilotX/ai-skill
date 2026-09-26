# Market making

A market maker earns the spread and pays in three currencies: adverse selection (trading with better
informed flow), inventory risk (holding a position while the price moves), and fees. A quoting model is
a way to balance them; the measurements after trading decide whether it did.

## Adverse selection

Glosten and Milgrom (1985, "Bid, Ask and Transaction Prices in a Specialist Market with Heterogeneously
Informed Traders", Journal of Financial Economics): a dealer facing some informed traders sets the ask at
the expected value given that someone buys, and the bid at the expected value given that someone sells.
The spread exists even with zero costs, and it widens with the share of informed flow.

In practice: spreads widen around news, at the open, and when flow becomes one-sided. A maker who does not
widen then is paying the informed traders.

## Inventory and the reservation price

Avellaneda and Stoikov (2008) solve for quotes that maximise expected exponential utility of terminal
wealth, with fills arriving at a rate that decays exponentially with distance from the mid. The result:

- Reservation price r = s - q x gamma x sigma^2 x (T - t): shifted against inventory q, more so with higher risk aversion gamma, volatility sigma and time remaining.
- Total spread = gamma x sigma^2 x (T - t) + (2 / gamma) x ln(1 + gamma / k), where k measures how fast fill intensity falls with distance.

`scripts/execution_cost.py avellaneda-stoikov` computes both. The model has no adverse selection, constant
volatility, and a finite horizon; Gueant, Lehalle and Fernandez-Tapia (2013, "Dealing with the inventory
risk", Mathematics and Financial Economics) give closed-form approximations with inventory limits.

Use it for structure (skew against inventory, widen with volatility) and calibrate the parameters from
fills. Its numbers are not a production quote.

## Measuring a quoting strategy

- Spread capture: the realised spread per fill, gross and net of fees.
- Markouts by horizon and by counterparty type or venue, per `references/impact-and-tca.md`.
- Inventory: distribution, holding time, and the P&L from inventory moves separated from spread capture.
- Fill rate by distance from the mid, which calibrates k.
- P&L attribution per day: spread capture, inventory P&L, hedging cost, fees and rebates.

A strategy that makes money from rebates and loses on markouts is exposed to a fee change.

## Toxicity signals

Order flow imbalance over short windows, trade size relative to typical size, quote changes on correlated
instruments, and the markout history of the flow. Measures such as VPIN (Easley, Lopez de Prado and O'Hara,
2012, "Flow Toxicity and Liquidity in a High-frequency World", Review of Financial Studies) are debated as
predictors; test any toxicity measure against markouts in your own data before quoting off it.

## Hedging

A maker in options or ETFs hedges in the underlying or constituents. Hedging costs come off the spread
captured. Decide hedging bands (hedge when delta exceeds a threshold) by trading off hedge cost against
inventory risk, and include the hedge in the P&L attribution.

## Controls specific to market making

- Position and inventory limits that widen or pull quotes as they approach, not only at the hard limit.
- Maximum quote size and minimum spread, enforced in the gateway.
- Pull quotes on stale market data, on a halt, on a connectivity loss to the hedge venue, and on a burst of fills in one direction.
- A kill switch that cancels every resting order, tested regularly. See `trading-systems`.
- Obligations: a registered market maker may have quoting obligations (presence, maximum spread) set by the venue. Retrieve them before designing the pull rules.
