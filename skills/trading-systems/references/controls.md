# Trading controls

Rules differ by jurisdiction and venue and are amended. Retrieve the current rule text, the venue's
rulebook and the broker's requirements, and have compliance confirm what applies. The lists below are the
engineering content those rules expect.

## Regulatory anchors

United States. SEC Rule 15c3-5, the market access rule (Release No. 34-63241, 2010), requires broker-dealers
with market access, including those providing sponsored access, to have risk management controls and
supervisory procedures: pre-trade controls that prevent orders exceeding credit or capital thresholds or
appearing erroneous, prevention of orders that violate regulatory requirements, and restriction of access
to authorised persons. Controls must be under the broker's direct and exclusive control and reviewed
regularly, with an annual CEO certification. Regulation SCI applies to certain market infrastructure.

European Union. MiFID II Article 17 and Commission Delegated Regulation (EU) 2017/589 (RTS 6) require
investment firms engaged in algorithmic trading to have testing of algorithms before deployment,
conformance testing with venues, pre-trade controls (price collars, maximum order value and volume,
maximum message counts), real-time monitoring, a kill functionality to cancel unexecuted orders, and an
annual self-assessment. Commission Delegated Regulation (EU) 2017/574 (RTS 25) sets business clock
synchronisation requirements, with tighter granularity for high frequency trading. The UK retained
equivalent rules; check the FCA versions.

Venues set their own requirements: certification tests before connection, message rate limits, fat
finger checks at the exchange, self-trade prevention options, and market maker obligations.

## Pre-trade checks

Run in the order path, before the message leaves, with no bypass:

- Maximum order quantity and notional, per instrument and per strategy.
- Price collar: reject orders priced more than a stated percentage or number of ticks away from a reference (last trade, mid, or a theoretical price), with a defined behaviour when the reference is stale or missing (reject, never pass).
- Position limits per instrument, net and gross, counting working orders as if filled.
- Credit or capital limits per account and aggregate.
- Message rate throttles per session and per strategy, below the venue's limits.
- Duplicate client order ID and duplicate order detection (same side, size and price within a short window).
- Restricted and hard-to-borrow lists, and short sale rules where applicable.
- Self-trade prevention, using the venue's mechanism where offered.
- Instrument status: halted, in auction, or outside trading hours.

`scripts/pretrade_check.py` is a reference model of most of these for testing a gateway's decisions.

## Kill switches

Levels: a strategy-level stop, an account-level stop, and a firm-level stop that cancels every resting
order on every venue and blocks new ones. The firm-level switch runs outside strategy processes, reachable
by an operator from a separate interface, and can use venue-side cancel-on-disconnect and mass cancel
functions.

Automatic triggers: realised or unrealised loss beyond a threshold, position beyond a limit, reject rate
spike, order rate spike, a run of fills in one direction, market data staleness, loss of connectivity to
the risk service, and reconciliation breaks.

Test in production hours on a schedule with a small known position, and record the time from trigger to
all orders confirmed cancelled.

## Lessons from incidents

Knight Capital, 1 August 2012 (SEC Release No. 34-70694): new code was deployed to only seven of eight
servers; a repurposed flag activated retired functionality on the eighth; the system sent millions of
orders into the market in about 45 minutes, and the firm lacked adequate controls to stop it. The SEC found
violations of the market access rule. Engineering lessons: atomic deployment with verification on every
server, never repurposing flags, removing dead code, alerts that reach someone with authority to stop
trading, and a kill switch that works without diagnosis.

The flash crash of 6 May 2010 (joint SEC and CFTC staff report, September 2010): a large sell program
executed by volume participation without regard to price or time, in a stressed market, contributed to a
rapid decline and liquidity withdrawal. Lessons: participation algorithms need price limits, and liquidity
providers need stale data and volatility pull rules.

## Reconciliation

Compare, intraday and at end of day: internal fills against exchange drop copy or broker execution
reports, positions against the clearing firm, cash and fees against statements. Any break stops the
affected strategy until explained. Keep the break log.

## Change management

Four-eyes review for any change to risk limits or order logic. Limits changed through a controlled
interface with an audit trail, never by editing a config file on a server. Releases tagged, deployed
atomically, verified per server, with rollback prepared. Algorithms tested in a simulator and in venue
conformance environments before production, with the test evidence kept.
