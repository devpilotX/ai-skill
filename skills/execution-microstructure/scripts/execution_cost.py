#!/usr/bin/env python3
"""Execution cost arithmetic: optimal liquidation schedules, impact estimates,
implementation shortfall, and market making quotes.

Standard library only. Python 3.9 or later. Every model here is a simplification
with named assumptions; the output states them. Calibrate impact parameters on your
own fills before trusting any number.

Usage:
  python3 execution_cost.py almgren-chriss --shares 1000000 --horizon 1 --steps 10 \
      --sigma 0.95 --eta 2.5e-6 --gamma 2.5e-7 --epsilon 0.0625 --risk-aversion 1e-6
  python3 execution_cost.py sqrt-impact --shares 250000 --adv 5000000 --daily-vol 0.02 \
      --price 40 --coefficient 1.0 --spread-bps 4
  python3 execution_cost.py shortfall --side buy --decision 50.00 --arrival 50.10 \
      --fills 3000@50.15 5000@50.22 --target 10000 --close 50.40 --fees 12.50
  python3 execution_cost.py avellaneda-stoikov --mid 100 --inventory 5 --gamma 0.1 \
      --sigma 2 --time-left 0.5 --k 1.5

Models:
  almgren-chriss   Almgren and Chriss (2000), "Optimal execution of portfolio
                   transactions", Journal of Risk. Linear permanent impact gamma,
                   linear temporary impact eta, fixed cost epsilon per share, price
                   volatility sigma per unit time (price units), risk aversion lambda.
                   With tau = T/N and eta_t = eta - gamma tau / 2, kappa solves
                   cosh(kappa tau) = 1 + lambda sigma^2 tau^2 / (2 eta_t), and holdings
                   are x_j = X sinh(kappa (T - t_j)) / sinh(kappa T). Lambda 0 gives
                   the straight line (TWAP) schedule.
  sqrt-impact      the square root law: impact = Y * daily vol * sqrt(Q / ADV). Y is
                   an empirical coefficient of order one that must be calibrated; see
                   Toth et al. (2011), "Anomalous price impact and the critical nature
                   of liquidity in financial markets", Physical Review X.
  shortfall        Perold (1988) implementation shortfall against the decision price,
                   split into delay (decision to arrival), execution (arrival to
                   fills), opportunity (unfilled shares marked at --close) and fees.
                   Positive numbers are costs.
  avellaneda-stoikov   Avellaneda and Stoikov (2008), "High-frequency trading in a
                   limit order book", Quantitative Finance. Reservation price
                   r = s - q gamma sigma^2 (T - t) and total spread
                   gamma sigma^2 (T - t) + (2 / gamma) ln(1 + gamma / k).

Exit codes: 0 success, 2 invalid input.
"""

from __future__ import annotations

import argparse
import math
import sys
from typing import Dict, List, Optional, Sequence, Tuple


class InputError(ValueError):
    """Raised for input that cannot produce a meaningful result."""


def almgren_chriss(shares: float, horizon: float, steps: int, sigma: float, eta: float,
                   gamma: float, epsilon: float, risk_aversion: float) -> Dict[str, object]:
    if shares <= 0 or horizon <= 0 or steps < 1:
        raise InputError("shares and horizon must be positive and steps at least 1")
    if sigma < 0 or eta <= 0 or gamma < 0 or epsilon < 0 or risk_aversion < 0:
        raise InputError("sigma, gamma, epsilon and risk aversion must be non-negative, eta positive")
    tau = horizon / steps
    eta_t = eta - gamma * tau / 2
    if eta_t <= 0:
        raise InputError("eta - gamma * tau / 2 must be positive; use more steps or check units")
    times = [j * tau for j in range(steps + 1)]
    increment = risk_aversion * sigma * sigma * tau * tau / (2 * eta_t)
    # acosh(1 + y) = log1p(y + sqrt(y (y + 2))), accurate when y is tiny.
    kappa = math.log1p(increment + math.sqrt(increment * (increment + 2))) / tau if increment > 0 else 0.0
    if kappa * horizon < 1e-9:
        # No effective risk aversion: the straight line (TWAP) schedule.
        kappa = 0.0
        holdings = [shares * (1 - j / steps) for j in range(steps + 1)]
    else:
        # sinh(k (T - t)) / sinh(k T), written with exponentials so large k T cannot overflow.
        kt = kappa * horizon
        holdings = [shares * math.exp(-kappa * t) * -math.expm1(-2 * kappa * (horizon - t))
                    / -math.expm1(-2 * kt) for t in times]
        holdings[0], holdings[-1] = shares, 0.0
    trades = [holdings[j - 1] - holdings[j] for j in range(1, steps + 1)]
    expected = (0.5 * gamma * shares * shares + epsilon * math.fsum(abs(n) for n in trades)
                + eta_t / tau * math.fsum(n * n for n in trades))
    variance = sigma * sigma * tau * math.fsum(x * x for x in holdings[1:])
    return {"kappa": kappa, "tau": tau, "times": times, "holdings": holdings,
            "trades": trades, "expected_cost": expected, "variance": variance,
            "std_cost": math.sqrt(variance),
            "half_life": (1 / kappa) if kappa > 0 else math.inf}


def sqrt_impact(shares: float, adv: float, daily_vol: float, price: float,
                coefficient: float = 1.0, spread_bps: float = 0.0) -> Dict[str, float]:
    if shares <= 0 or adv <= 0 or daily_vol < 0 or price <= 0 or coefficient < 0:
        raise InputError("shares, adv and price must be positive; vol and coefficient non-negative")
    participation = shares / adv
    impact = coefficient * daily_vol * math.sqrt(participation)
    impact_bps = impact * 1e4
    total_bps = impact_bps + spread_bps / 2
    notional = shares * price
    return {"participation_of_adv": participation, "impact_bps": impact_bps,
            "half_spread_bps": spread_bps / 2, "total_bps": total_bps,
            "notional": notional, "cost": notional * total_bps / 1e4}


def parse_fills(specs: Sequence[str]) -> List[Tuple[float, float]]:
    fills = []
    for spec in specs:
        qty, sep, px = spec.partition("@")
        if not sep:
            raise InputError("fill %r must look like QTY@PRICE" % spec)
        try:
            q, p = float(qty), float(px)
        except ValueError:
            raise InputError("fill %r is not numeric" % spec)
        if q <= 0 or p <= 0:
            raise InputError("fill %r needs positive quantity and price" % spec)
        fills.append((q, p))
    return fills


def shortfall(side: str, decision: float, arrival: float, fills: Sequence[Tuple[float, float]],
              target: float, close: float, fees: float = 0.0) -> Dict[str, float]:
    if side not in ("buy", "sell"):
        raise InputError("side is buy or sell")
    if min(decision, arrival, close) <= 0 or target <= 0 or fees < 0:
        raise InputError("prices and target must be positive, fees non-negative")
    filled = math.fsum(q for q, _ in fills)
    if filled > target + 1e-9:
        raise InputError("filled quantity %.0f exceeds the target %.0f" % (filled, target))
    sign = 1 if side == "buy" else -1
    avg = math.fsum(q * p for q, p in fills) / filled if filled else arrival
    delay = sign * filled * (arrival - decision)
    execution = sign * math.fsum(q * (p - arrival) for q, p in fills)
    unfilled = target - filled
    opportunity = sign * unfilled * (close - decision)
    total = delay + execution + opportunity + fees
    paper = target * decision
    return {"filled": filled, "unfilled": unfilled, "average_price": avg,
            "delay": delay, "execution": execution, "opportunity": opportunity,
            "fees": fees, "total": total, "total_bps": 1e4 * total / paper}


def avellaneda_stoikov(mid: float, inventory: float, gamma: float, sigma: float,
                       time_left: float, k: float) -> Dict[str, float]:
    if gamma <= 0 or k <= 0 or sigma < 0 or time_left < 0:
        raise InputError("gamma and k must be positive; sigma and time left non-negative")
    reservation = mid - inventory * gamma * sigma * sigma * time_left
    spread = gamma * sigma * sigma * time_left + (2 / gamma) * math.log(1 + gamma / k)
    return {"reservation": reservation, "spread": spread,
            "bid": reservation - spread / 2, "ask": reservation + spread / 2,
            "skew_from_mid": reservation - mid}


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="execution_cost.py", description="Execution cost models.")
    sub = ap.add_subparsers(dest="command", required=True)
    a = sub.add_parser("almgren-chriss")
    a.add_argument("--shares", type=float, required=True)
    a.add_argument("--horizon", type=float, required=True, help="total time, e.g. days")
    a.add_argument("--steps", type=int, required=True)
    a.add_argument("--sigma", type=float, required=True, help="price vol per sqrt(time unit)")
    a.add_argument("--eta", type=float, required=True, help="temporary impact per (share / time)")
    a.add_argument("--gamma", type=float, default=0.0, help="permanent impact per share")
    a.add_argument("--epsilon", type=float, default=0.0, help="fixed cost per share")
    a.add_argument("--risk-aversion", type=float, default=0.0)
    s = sub.add_parser("sqrt-impact")
    s.add_argument("--shares", type=float, required=True)
    s.add_argument("--adv", type=float, required=True, help="average daily volume in shares")
    s.add_argument("--daily-vol", type=float, required=True, help="daily return vol, 0.02 is 2 percent")
    s.add_argument("--price", type=float, required=True)
    s.add_argument("--coefficient", type=float, default=1.0,
                   help="Y, calibrate on your own fills (default 1.0 is an assumption)")
    s.add_argument("--spread-bps", type=float, default=0.0, help="quoted spread in bps")
    f = sub.add_parser("shortfall")
    f.add_argument("--side", choices=("buy", "sell"), required=True)
    f.add_argument("--decision", type=float, required=True, help="price when the decision was made")
    f.add_argument("--arrival", type=float, required=True, help="price when the order reached the market")
    f.add_argument("--fills", nargs="*", default=[], help="QTY@PRICE for each fill")
    f.add_argument("--target", type=float, required=True, help="shares the decision called for")
    f.add_argument("--close", type=float, required=True, help="price used to mark unfilled shares")
    f.add_argument("--fees", type=float, default=0.0)
    m = sub.add_parser("avellaneda-stoikov")
    m.add_argument("--mid", type=float, required=True)
    m.add_argument("--inventory", type=float, required=True, help="signed position in units")
    m.add_argument("--gamma", type=float, required=True, help="risk aversion")
    m.add_argument("--sigma", type=float, required=True, help="mid price vol per sqrt(time unit)")
    m.add_argument("--time-left", type=float, required=True, help="T - t in the same time unit")
    m.add_argument("--k", type=float, required=True, help="order arrival decay with distance")
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    try:
        if args.command == "almgren-chriss":
            r = almgren_chriss(args.shares, args.horizon, args.steps, args.sigma, args.eta,
                               args.gamma, args.epsilon, args.risk_aversion)
            print("kappa %.6g per time unit, tau %.6g" % (r["kappa"], r["tau"]))
            print("step  time      holding          trade")
            for j, (t, x) in enumerate(zip(r["times"], r["holdings"])):
                trade = r["trades"][j - 1] if j else 0.0
                print("%4d  %-8.4g  %-15.6g  %.6g" % (j, t, x, trade))
            print("expected cost %.6g, cost sd %.6g (price units x shares)"
                  % (r["expected_cost"], r["std_cost"]))
            print("assumes linear impact, arithmetic Brownian prices and no drift or alpha")
        elif args.command == "sqrt-impact":
            r = sqrt_impact(args.shares, args.adv, args.daily_vol, args.price, args.coefficient,
                            args.spread_bps)
            print("participation %.2f%% of ADV" % (100 * r["participation_of_adv"]))
            print("impact %.2f bps + half spread %.2f bps = %.2f bps, cost %.2f on notional %.2f"
                  % (r["impact_bps"], r["half_spread_bps"], r["total_bps"], r["cost"], r["notional"]))
            print("coefficient %.3g is an assumption until fitted to your own fills" % args.coefficient)
            if r["participation_of_adv"] > 0.1:
                print("warning: above 10 percent of ADV the square root law is poorly tested; "
                      "spread the order over more days")
        elif args.command == "shortfall":
            r = shortfall(args.side, args.decision, args.arrival, parse_fills(args.fills),
                          args.target, args.close, args.fees)
            print("filled %.0f of %.0f at average %.6g" % (r["filled"], args.target, r["average_price"]))
            for key in ("delay", "execution", "opportunity", "fees", "total"):
                print("  %-12s %.2f" % (key, r[key]))
            print("total shortfall %.2f bps of paper notional" % r["total_bps"])
        else:
            r = avellaneda_stoikov(args.mid, args.inventory, args.gamma, args.sigma,
                                   args.time_left, args.k)
            print("reservation price %.6g (skew %.6g from mid)" % (r["reservation"], r["skew_from_mid"]))
            print("bid %.6g  ask %.6g  total spread %.6g" % (r["bid"], r["ask"], r["spread"]))
            print("assumes Poisson fills with intensity A exp(-k delta) and no adverse selection")
    except InputError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
