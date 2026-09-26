---
name: trading-systems
description: Build and operate automated trading infrastructure where a bug costs money in seconds, with the controls a regulated trading firm is expected to have. Use when the user asks to build an order management system, execution engine, trading bot, market data handler, FIX or exchange gateway, backtester that must match live trading, pre-trade risk checks, kill switch, position or P&L service, or asks about latency, clock sync, order state, reconciliation or deploying trading code. Puts risk checks in front of every order, makes the order lifecycle a tested state machine, keeps backtest and live on one code path, reconciles against independent sources, and deploys with the kill switch tested. Research goes to quant-research, cost models to execution-microstructure. Triggers on trading system, OMS, EMS, trading bot, FIX protocol, exchange gateway, pre-trade risk, kill switch, market data feed, low latency, backtest live parity, drop copy, reconciliation.
license: MIT
metadata:
  version: 1.0.0
  suite: ai-skill
---

# Trading systems

The failure this corrects is trading code built like ordinary application code: a deploy that reuses an
old flag, a retry that sends an order twice, a risk check that runs after the order left, a kill switch
nobody has pressed, and a backtest engine that shares no code with production. The SEC's order against
Knight Capital (Release No. 34-70694, 2013) describes how a deployment that missed one server, and
repurposed a flag that activated old code, produced millions of unintended orders in about 45 minutes.
This skill treats every order path as money leaving the building and builds the controls first.

## When to use and when to stay off

Run when the user is building or changing software that sends orders, handles market data, tracks
positions and P&L, applies risk limits, or runs strategies against a live or simulated market.

Stay off, and route instead, when:

- The question is whether the strategy has an edge. Use `quant-research`.
- The question is which algorithm or order type to use and what it costs. Use `execution-microstructure`; this skill implements what it decides.
- The question is portfolio limits and their levels. Use `portfolio-risk`; this skill enforces them.
- The service has no order path and is ordinary backend work. Use `backend-build`, and `observability-setup` for monitoring.
- The user asks for a bot that manipulates a market, wash trades, or evades a venue's controls. Refuse.

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of
the session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Every order passes pre-trade risk checks in the same process path before it reaches the venue, and there is no code path that bypasses them.
2. A kill switch exists that stops new orders and cancels resting ones across every strategy and venue, independent of the strategy process, and it is tested on a schedule.
3. Client order identifiers are unique and never reused, and every retry is idempotent. A timeout never triggers a blind resend.
4. The order lifecycle is an explicit state machine, with every venue message type handled, including rejects, partial fills, busted trades and unsolicited cancels.
5. Positions and P&L are reconciled against an independent source (exchange drop copy, broker statement, clearing records) intraday and at end of day, and breaks stop trading until explained.
6. The backtest, the simulator and production share the strategy and risk code, differing only in the market adapter.
7. Deployment is atomic across every server that trades, with old code and unused flags removed, and nothing goes live without a rollback and a tested kill switch.

## Procedure

### Step 1, write the control requirements before the architecture

List the pre-trade checks, their limits and who owns them, from `references/controls.md`: order size and
notional, price collars against a reference, position and credit limits, message rate throttles,
duplicate detection, restricted lists, self-trade prevention, and the kill switch triggers. In the US,
brokers with market access must have risk controls under SEC Rule 15c3-5; in the EU, MiFID II Delegated
Regulation 2017/589 (RTS 6) sets organisational requirements for algorithmic trading firms. Retrieve the
current texts and have compliance confirm which apply.

### Step 2, design the event flow

An event-driven core: market data and order events in, a single-threaded or sequenced decision per
instrument, orders out through the risk gateway. Persist every inbound and outbound message with a
sequence number and timestamp, so any session can be replayed deterministically. Architecture patterns
are in `references/architecture.md`.

### Step 3, implement the order state machine

States such as pending new, new, partially filled, filled, pending cancel, cancelled, pending replace,
replaced, rejected, expired, with transitions driven only by venue messages. Handle out-of-order messages,
fills after a cancel request, cancel rejects, and trade busts. Treat an unknown order state after a
disconnect as open until the venue confirms otherwise, and reconcile by querying order status on
reconnect.

### Step 4, build market data handling

Sequence numbers with gap detection and recovery (snapshot plus replay), book building per venue, crossed
or locked book detection, stale data detection with a timeout that pulls quotes, and trading halt
handling. Strategies must see when data is stale; a strategy acting on a frozen price is a common cause of
large losses.

### Step 5, keep backtest and live on one path

The strategy receives the same events through the same interfaces in simulation and production. The
simulator models queue position, latency, fees, partial fills and rejects well enough that the gap to live
is measured, not assumed. Compare live fills to what the simulator predicted for the same decisions and
track the difference as a metric.

### Step 6, test the controls as code

Replay order sequences through the risk checks and compare decisions with a reference model:

```
python3 scripts/pretrade_check.py orders.csv limits.json
```

From the repository root the path is `skills/trading-systems/scripts/pretrade_check.py`. It applies size,
notional, collar, position, gross, rate, duplicate, restricted and kill switch rules and exits 1 on any
rejection. Add property-based tests for the state machine (random message orders never produce an
impossible state), fault injection (disconnect mid-order, duplicate fills, clock jumps), and a load test
at several times the peak message rate.

### Step 7, deploy and operate

Deploy to every trading server atomically, verify the version on each before enabling trading, and never
repurpose a flag. Start in a reduced mode (small size, one venue) with limits tightened. Monitor latency
percentiles, reject rates, order to fill ratios, position against limits, P&L against expectation, and
reconciliation breaks, with alerts that page a person who can press the kill switch. Run the kill switch
on schedule in production hours with a known small position, and record how long it took.

## Self-audit

- Every order path goes through the pre-trade checks, confirmed by code search and a test that tries to bypass them.
- The kill switch is independent of strategy processes, covers every venue, and was tested with its time recorded.
- Client order IDs are unique across restarts, and retries are idempotent.
- The order state machine handles rejects, partial fills, busts, unsolicited cancels and reconnects.
- Market data gaps, stale data and halts are detected and pull quotes.
- Every inbound and outbound message is persisted with sequence and timestamp, and a session replay reproduces decisions.
- Backtest and production share strategy and risk code, and the live-versus-simulated fill gap is measured.
- Reconciliation against an independent source runs intraday and end of day, and breaks halt trading.
- Deployment is atomic, verified on every server, with no repurposed flags.
- Regulatory controls were confirmed with compliance, not assumed.

## What this cannot do

It cannot certify that a system meets regulatory requirements; that is a judgement for compliance and
legal functions and, for exchange members, the venue.

It cannot see the user's venue certification requirements, which differ by exchange and must be
retrieved and passed before connecting.

It cannot promise latency figures without measurement on the user's hardware and network.

Before connecting to a market, ask the compliance officer or regulatory counsel: "Given that we will send
orders to these venues through this broker or as a direct member, in these jurisdictions, which market
access, algorithmic trading and record keeping rules apply to us, and what testing, documentation and
annual certification do they require?"
