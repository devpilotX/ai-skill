# Data integrity for backtests

Most backtest errors are data errors that make the past look more predictable than it was. Work
through each section and record, for every input, the source, the version or download date, and a
file hash.

## The rule

A value may enter a signal at time t only if a trader could have known it at time t, in the form it
had at time t. Every section below is a way that rule gets broken.

## Universe and survivorship

Build the universe as of each rebalance date: index membership on that date, or listing status on that
date. A universe of today's constituents drops every company that failed, was delisted or was acquired,
and those are disproportionately the losers.

Keep delisted securities in the history, with their final returns. In US equity data, CRSP provides
delisting returns; a stock that stops trading without a delisting return usually lost most of its value
in the missing step. Dropping the last return biases short-side strategies in particular.

Apply liquidity and price filters with data available at the time (trailing volume, prior close), not
with the full-period average.

## Identifiers

Map on a permanent security identifier (a vendor permanent ID, or a time-stamped mapping from CUSIP,
ISIN or SEDOL). Tickers are reused and change on mergers and renames, so a ticker join silently splices
two companies together.

Record share class explicitly. Dual listed and multiple class companies duplicate exposure if both lines
enter the universe.

## Prices and corporate actions

Use prices adjusted for splits and dividends for return calculations, and unadjusted prices for anything
that depends on the traded price level (tick size, price filters, lot size, borrow fees quoted per
share).

Total return needs dividends reinvested on the ex-date, not the pay date.

Spin-offs, rights issues and special dividends produce price jumps that are not returns. Check the
largest daily moves in the data by hand; a fair share of them are data errors.

## Timing

Stamp fundamentals with the time they became public (filing or press release time), not the fiscal
period end. Use the original reported values, not later restatements. Point-in-time fundamental
databases exist for this reason; if the data is not point in time, lag it conservatively and say by how
much, labelled `ASSUMPTION:`.

Decide the execution price explicitly. A signal computed from the close cannot be traded at that same
close unless it uses information from before the closing auction and the order reaches the auction in
time. The honest default is the next open or a volume weighted price over the next interval.

Align time zones and calendars. Markets that close at different times produce spurious lead-lag
relations when daily closes are compared directly. Daylight saving changes move the offset between
markets twice a year.

Intraday data: check for stale quotes, crossed markets, out-of-sequence prints, and trades flagged as
corrections or cancellations. Use exchange timestamps where available and state which clock the data
used.

## Revisions and backfill

Vendors add history for newly covered companies, fill gaps retroactively, and revise estimates. A
series that looks complete in today's download may not have existed at the time. Ask the vendor for the
first-available date of each record, or use snapshots taken at the time.

Economic data is revised; use first-release (vintage) data for any macro signal. The Federal Reserve
Bank of St. Louis ALFRED database keeps vintages for many US series.

Analyst estimates and alternative data carry the same risk, plus the risk that the vendor's coverage
universe itself changed over time.

## Short side and costs data

Borrow availability and fees vary by stock and over time, and hard-to-borrow names are where many short
anomalies concentrate. Without historical borrow data, exclude the names a prime broker would not have
lent, or label the short side `ASSUMPTION:` and report the long leg separately.

Historical spreads and volumes are needed for the cost model in `execution-microstructure`. Using
today's spreads for twenty-year-old trades understates past costs.

## Checks to run before any signal work

- Count securities per date and plot it. Jumps usually mean a coverage change, not a market event.
- Compare the equal and cap weighted universe returns against a published index for the same universe.
- List the twenty largest absolute daily returns and confirm each against a second source.
- Shift every signal forward by one period and confirm performance drops; if it does not, the signal is not being used as intended, or there is a leak.
- Shift every signal backward by one period (deliberate look-ahead) and confirm performance jumps; a result that barely changes suggests the timing is already leaking.
- Rerun the backtest from raw files on a clean machine and compare the output hash.
