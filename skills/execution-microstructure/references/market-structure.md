# Market structure

Venue rules, fees, tick sizes and auction times change. Retrieve the current rulebook and fee schedule
from each venue and regulator, note the date, and trust the retrieved text over this file.

## The limit order book

A continuous market keeps resting limit orders by price level. Most equity and futures venues match by
price then time priority: the best price trades first, and at the same price the earliest order trades
first. Some futures contracts use pro rata allocation at a price level, which rewards size over speed and
changes quoting behaviour entirely. Check the matching algorithm for each product.

Queue position is the value of a resting order. An order at the front of a long queue fills in normal
trading; one at the back fills mostly when the level is about to be exhausted, which is when the price is
about to move against it. Cancelling and rejoining loses position.

Tick size relative to price sets the queue dynamics. A large tick relative to the spread (a stock whose
spread is almost always one tick) produces long queues and makes queue position valuable. A small tick
produces a spread of many ticks and more price competition.

## Order types

Market, limit, stop, stop limit, immediate or cancel, fill or kill, good till cancelled, post only (rejected
or repriced if it would take liquidity), midpoint peg, primary peg, iceberg or reserve (displayed part of a
larger order), and auction-only orders (market on open, limit on close). Venue specific types differ in
priority and behaviour; read the venue's order type documentation before relying on one.

## Fragmentation

US equities trade on many lit exchanges plus alternative trading systems (including dark pools) and
off-exchange wholesalers. Regulation NMS (SEC, 2005) includes an order protection rule requiring trading
centres to prevent trade-throughs of protected quotations, and an access fee cap. Retrieve the current
rule text and fee caps from the SEC, since both have been amended.

In the EU and UK, MiFID II and its UK equivalent set best execution duties, trading obligations, and
transparency rules including waivers for dark trading. Retrieve current thresholds and caps from ESMA and
the FCA.

Smart order routers choose venues by price, fees, fill probability and markouts. Measure routing quality by
venue level markouts and fill rates, not by quoted price alone.

## Fees

Maker-taker venues pay a rebate to passive orders and charge takers; inverted venues do the opposite.
Fees change the effective spread and the incentive to rest orders. A passive strategy's profit can be
mostly rebate, which disappears with a fee change. Retrieve schedules and tier requirements from each
venue.

## Auctions

Opening and closing auctions concentrate a large share of daily volume on many equity markets. They
publish indicative prices and imbalances before the match, with cut-off times for entering and cancelling
orders that differ by venue. Index rebalances and fund flows cluster at the close. Retrieve the auction
schedule and imbalance rules per venue.

## Circuit breakers and halts

Market-wide circuit breakers halt trading after index declines of set sizes. Single stock mechanisms (in
the US, the Limit Up-Limit Down plan) pause trading when prices move outside bands. Volatility auctions on
European venues serve a similar role. An execution algorithm must handle halts, resumptions, and orders
rejected for being outside price bands. Retrieve the current thresholds.

## Latency

Latency matters when the strategy competes for queue position or reacts to quote changes. It matters
little for orders worked over hours. Measure end to end: market data receipt, decision, order out, venue
acknowledgement. Use hardware timestamps where sub-millisecond precision matters, and synchronised clocks
(see `trading-systems`).

## Asset class differences

Futures: central limit order book per contract, often a single venue, exchange fees, and calendar spreads
traded as separate instruments. Currencies: mostly over the counter across dealer and multi-dealer
platforms, with last look on some venues, which gives the liquidity provider an option to reject after
seeing the order. Corporate bonds: request for quote and dealer markets, sparse prints, and wide spreads
that depend on size. Options: many strikes and expiries with thin books, quoted by market makers who hedge
in the underlying.
