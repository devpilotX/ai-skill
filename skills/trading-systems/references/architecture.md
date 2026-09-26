# Trading system architecture

## Event-driven core

Inputs are events: market data updates, order acknowledgements, fills, rejects, timers and operator
commands. The core processes them in a defined order and emits orders and state changes. Make the order
explicit with a sequencer, so that given the same input log the system makes the same decisions. That
property is what makes replay debugging, simulation and audit possible.

Keep per-instrument decision logic single-threaded (or partitioned by instrument) to avoid locks on the hot
path and to keep ordering deterministic. Put slow work (persistence, analytics, user interfaces) behind
queues off the decision path.

## Message persistence and replay

Persist every inbound and outbound message with a local sequence number, the venue's sequence number, and
timestamps at receipt and send. A replay tool feeds the log back through the same code and compares
outputs. Use it for every incident and as a regression test on code changes.

## Order lifecycle

Model the order as a state machine driven by venue messages. The FIX protocol defines OrdStatus and
ExecType values that map onto states; venue native protocols have equivalents. Rules:

- Assign client order IDs from a persistent, monotonic source that survives restarts. Never reuse one.
- An outbound order is pending until acknowledged. On timeout, query status, do not resend.
- A cancel request can cross with a fill. Handle fills arriving in pending cancel.
- Cancel and replace changes can be rejected; the original order is still live.
- Trade corrections and busts arrive after the fact and must adjust positions and P&L.
- On reconnect, request order status for every open order and reconcile before trading.
- Use venue cancel-on-disconnect where available so a lost session does not leave resting orders.

Property-based tests generate random sequences of venue messages, including duplicates and out-of-order
delivery, and assert that the state machine never reaches an impossible state and that positions equal
the sum of fills.

## Market data

Handle sequence gaps: detect, request a snapshot or replay, rebuild the book, and mark instruments stale
until recovered. Detect crossed and locked books. Expose data age to strategies, and pull quotes when data
is older than a threshold. Handle trading status messages (halts, auctions, reopenings). Normalise symbols
and instrument definitions from a security master with effective dates.

## Time

Use a synchronised clock (PTP where fine granularity is required, NTP otherwise) and record which clock
stamped each event. MiFID II RTS 25 sets maximum divergence from UTC and timestamp granularity by activity
type; retrieve the current table. Measure latency with timestamps at each hop: data receipt, decision,
risk check, send, and venue acknowledgement. Report percentiles, not averages, and track the tail.

## Backtest and live parity

The strategy sees the same interfaces in backtest, simulation and production. Only the adapter changes:
historical replay, a simulated exchange, or the venue gateway. The simulated exchange should model:

- Latency between decision and arrival, and between arrival and acknowledgement.
- Queue position for passive orders, with fills only after the queue ahead is consumed.
- Partial fills, rejects and fees.
- Market impact from the strategy's own orders, at least for aggressive orders.

Measure the gap: for live decisions, compute what the simulator would have filled and compare with actual
fills. Track slippage against simulation as a production metric. A growing gap means the simulator or the
market changed.

## Positions, P&L and risk services

A position service built from fills, not from orders, reconciled against drop copy and clearing. P&L
computed from positions and marks with a stated marking source. Risk limits enforced by the gateway using
positions that include working orders. Separate these services from strategies so a strategy crash does
not lose position state.

## Deployment and operations

- Configuration and limits in version control, promoted through environments, with an audit trail.
- Atomic deployment across all trading hosts, version verified per host before trading is enabled.
- Feature flags with unique names that are never reused, and dead code removed.
- A start-of-day checklist: versions, limits loaded, connectivity, reference data dates, kill switch reachable.
- An end-of-day checklist: reconciliation clean, positions flat or as intended, logs archived.
- Alerts routed to people with authority to stop trading, covering the kill switch triggers in `references/controls.md`.

## Language and performance

Choose for the latency requirement. For strategies trading over seconds or longer, a managed language
with careful garbage collection settings is sufficient and safer to develop. For microsecond competition,
the design choices (kernel bypass networking, lock-free queues, pre-allocated memory, CPU pinning,
possibly FPGAs) dominate over language, and every one needs measurement on the target hardware. Do not pay
the complexity cost of low latency engineering for a strategy that does not need it.
