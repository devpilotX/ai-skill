#!/usr/bin/env python3
"""European option pricing, Greeks, implied volatility and static arbitrage checks.

Standard library only. Python 3.9 or later. Use it to check numbers, validate a
pricer, and screen a quote chain for arbitrage before fitting anything to it.

Usage:
  python3 options_lab.py price --spot 100 --strike 100 --rate 0.05 --vol 0.2 --expiry 1
  python3 options_lab.py price --spot 100 --strike 95 --rate 0.03 --div 0.01 --vol 0.25 --expiry 0.5 --put
  python3 options_lab.py price --forward 101 --strike 100 --rate 0.05 --vol 0.2 --expiry 1   # Black-76
  python3 options_lab.py iv --price 10.45 --spot 100 --strike 100 --rate 0.05 --expiry 1
  python3 options_lab.py parity --call 10.45 --put 5.57 --spot 100 --strike 100 --rate 0.05 --expiry 1
  python3 options_lab.py chain calls.csv --rate 0.05 --expiry 0.25 --spot 100
  python3 options_lab.py calendar 0.25:0.22 0.5:0.21 1.0:0.18
  python3 options_lab.py mc --spot 100 --strike 100 --rate 0.05 --vol 0.2 --expiry 1 --paths 200000 --seed 7

Conventions:
  Rates and dividend yields are continuously compounded, per year. Expiry is in
  years. Vol is annualised. Vega is per 1.00 of vol (divide by 100 for per point),
  theta is per year (divide by 365 or 252 for per day), rho is per 1.00 of rate.
  With --forward the Black-76 model is used, discounting at --rate.

Checks:
  chain      one expiry, CSV with columns strike and call (or strike and put). Tests
             the no-arbitrage conditions that hold for any model: price within its
             bounds, calls non-increasing in strike, slope between -exp(-rT) and 0,
             and convexity (butterflies non-negative) with unequal strike spacing.
  calendar   pairs expiry:implied vol at the same forward moneyness. Total implied
             variance vol^2 T must not decrease with T.
  mc         Monte Carlo under geometric Brownian motion with antithetic variates,
             against the closed form. A pricer that disagrees by more than about
             three standard errors has a bug.

Exit codes: 0 success, 1 a check found an arbitrage or a mismatch, 2 invalid input.
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import sys
from statistics import NormalDist
from typing import Dict, List, Optional, Sequence, Tuple

N = NormalDist()


class InputError(ValueError):
    """Raised for input that cannot produce a meaningful result."""


def _check(strike: float, expiry: float, vol: float) -> None:
    if strike <= 0 or expiry <= 0:
        raise InputError("strike and expiry must be positive")
    if vol <= 0:
        raise InputError("vol must be positive")


def black(forward: float, strike: float, rate: float, vol: float, expiry: float,
          call: bool = True) -> Dict[str, float]:
    """Black-76 price and Greeks with respect to the forward."""
    _check(strike, expiry, vol)
    if forward <= 0:
        raise InputError("forward must be positive")
    df = math.exp(-rate * expiry)
    sq = vol * math.sqrt(expiry)
    d1 = (math.log(forward / strike) + 0.5 * sq * sq) / sq
    d2 = d1 - sq
    if call:
        price = df * (forward * N.cdf(d1) - strike * N.cdf(d2))
        delta = df * N.cdf(d1)
    else:
        price = df * (strike * N.cdf(-d2) - forward * N.cdf(-d1))
        delta = -df * N.cdf(-d1)
    gamma = df * N.pdf(d1) / (forward * sq)
    vega = df * forward * N.pdf(d1) * math.sqrt(expiry)
    return {"price": price, "delta": delta, "gamma": gamma, "vega": vega, "d1": d1, "d2": d2}


def bsm(spot: float, strike: float, rate: float, vol: float, expiry: float,
        div: float = 0.0, call: bool = True) -> Dict[str, float]:
    """Black-Scholes-Merton price and Greeks with a continuous dividend yield."""
    _check(strike, expiry, vol)
    if spot <= 0:
        raise InputError("spot must be positive")
    sq = vol * math.sqrt(expiry)
    d1 = (math.log(spot / strike) + (rate - div + 0.5 * vol * vol) * expiry) / sq
    d2 = d1 - sq
    dq, dr = math.exp(-div * expiry), math.exp(-rate * expiry)
    if call:
        price = spot * dq * N.cdf(d1) - strike * dr * N.cdf(d2)
        delta = dq * N.cdf(d1)
        theta = (-spot * dq * N.pdf(d1) * vol / (2 * math.sqrt(expiry))
                 - rate * strike * dr * N.cdf(d2) + div * spot * dq * N.cdf(d1))
        rho = strike * expiry * dr * N.cdf(d2)
    else:
        price = strike * dr * N.cdf(-d2) - spot * dq * N.cdf(-d1)
        delta = -dq * N.cdf(-d1)
        theta = (-spot * dq * N.pdf(d1) * vol / (2 * math.sqrt(expiry))
                 + rate * strike * dr * N.cdf(-d2) - div * spot * dq * N.cdf(-d1))
        rho = -strike * expiry * dr * N.cdf(-d2)
    gamma = dq * N.pdf(d1) / (spot * sq)
    vega = spot * dq * N.pdf(d1) * math.sqrt(expiry)
    return {"price": price, "delta": delta, "gamma": gamma, "vega": vega, "theta": theta,
            "rho": rho, "d1": d1, "d2": d2}


def price_bounds(spot: float, strike: float, rate: float, expiry: float, div: float,
                 call: bool) -> Tuple[float, float]:
    fwd_s = spot * math.exp(-div * expiry)
    pv_k = strike * math.exp(-rate * expiry)
    if call:
        return max(0.0, fwd_s - pv_k), fwd_s
    return max(0.0, pv_k - fwd_s), pv_k


def implied_vol(price: float, spot: float, strike: float, rate: float, expiry: float,
                div: float = 0.0, call: bool = True, tol: float = 1e-12) -> float:
    """Implied vol by Newton steps safeguarded with bisection on [1e-6, 10].

    Converged when the price error is below tol relative to the price, or the bracket
    is narrower than 1e-12 in vol. Raises if neither happens, or if the answer sits on
    the edge of the search bracket.
    """
    low_b, high_b = price_bounds(spot, strike, rate, expiry, div, call)
    if not low_b < price < high_b:
        raise InputError("price %.6g is outside the no-arbitrage bounds (%.6g, %.6g)"
                         % (price, low_b, high_b))
    lo, hi = 1e-6, 10.0
    vol = 0.2
    for _ in range(500):
        r = bsm(spot, strike, rate, vol, expiry, div, call)
        diff = r["price"] - price
        if abs(diff) <= tol * price or hi - lo < 1e-12:
            if vol <= 1e-6 * 1.01 or vol >= 10.0 * 0.99:
                raise InputError("implied vol is at the edge of the search range [1e-6, 10]")
            return vol
        if diff > 0:
            hi = vol
        else:
            lo = vol
        step = vol - diff / r["vega"] if r["vega"] > 1e-12 else None
        vol = step if step is not None and lo < step < hi else 0.5 * (lo + hi)
    raise InputError("implied vol did not converge")


def parity_gap(call: float, put: float, spot: float, strike: float, rate: float,
               expiry: float, div: float = 0.0) -> float:
    """C - P - (S e^-qT - K e^-rT). Zero for European options without frictions."""
    return call - put - (spot * math.exp(-div * expiry) - strike * math.exp(-rate * expiry))


def check_chain(rows: Sequence[Tuple[float, float]], rate: float, expiry: float,
                spot: Optional[float] = None, div: float = 0.0, call: bool = True,
                tol: float = 1e-9) -> List[str]:
    """Static arbitrage violations in a single-expiry strike chain, as messages."""
    pts = sorted(rows)
    problems: List[str] = []
    if len({k for k, _ in pts}) != len(pts):
        problems.append("duplicate strikes")
        return problems
    df = math.exp(-rate * expiry)
    for k, c in pts:
        if c < -tol:
            problems.append("negative price %.6g at strike %.6g" % (c, k))
        if spot is not None:
            lo, hi = price_bounds(spot, k, rate, expiry, div, call)
            if c < lo - tol or c > hi + tol:
                problems.append("price %.6g at strike %.6g outside bounds [%.6g, %.6g]" % (c, k, lo, hi))
    slopes = []
    for (k1, c1), (k2, c2) in zip(pts, pts[1:]):
        slope = (c2 - c1) / (k2 - k1)
        slopes.append((k1, k2, slope))
        if call and not (-df - tol <= slope <= tol):
            problems.append("call slope %.6g between strikes %.6g and %.6g outside [-%.6g, 0]"
                            % (slope, k1, k2, df))
        if not call and not (-tol <= slope <= df + tol):
            problems.append("put slope %.6g between strikes %.6g and %.6g outside [0, %.6g]"
                            % (slope, k1, k2, df))
    for (ka, kb, s1), (_, kc, s2) in zip(slopes, slopes[1:]):
        if s2 < s1 - tol:
            problems.append("convexity violated around strike %.6g: a butterfly %.6g/%.6g/%.6g "
                            "has negative value" % (kb, ka, kb, kc))
    return problems


def check_calendar(points: Sequence[Tuple[float, float]], tol: float = 1e-12) -> List[str]:
    pts = sorted(points)
    problems = []
    for (t1, v1), (t2, v2) in zip(pts, pts[1:]):
        w1, w2 = v1 * v1 * t1, v2 * v2 * t2
        if w2 < w1 - tol:
            problems.append("total variance falls from %.6g at T=%.4g to %.6g at T=%.4g"
                            % (w1, t1, w2, t2))
    return problems


def monte_carlo(spot: float, strike: float, rate: float, vol: float, expiry: float,
                div: float = 0.0, call: bool = True, paths: int = 100000,
                seed: Optional[int] = None) -> Tuple[float, float]:
    """GBM terminal price Monte Carlo with antithetic pairs. Returns price and std error."""
    _check(strike, expiry, vol)
    if paths < 1000:
        raise InputError("use at least 1000 paths")
    rng = random.Random(seed)
    drift = (rate - div - 0.5 * vol * vol) * expiry
    diffusion = vol * math.sqrt(expiry)
    df = math.exp(-rate * expiry)
    pairs = paths // 2
    total = 0.0
    total_sq = 0.0
    for _ in range(pairs):
        z = rng.gauss(0.0, 1.0)
        s1 = spot * math.exp(drift + diffusion * z)
        s2 = spot * math.exp(drift - diffusion * z)
        if call:
            payoff = 0.5 * (max(s1 - strike, 0.0) + max(s2 - strike, 0.0))
        else:
            payoff = 0.5 * (max(strike - s1, 0.0) + max(strike - s2, 0.0))
        total += payoff
        total_sq += payoff * payoff
    mean = total / pairs
    var = max(total_sq / pairs - mean * mean, 0.0)
    return df * mean, df * math.sqrt(var / pairs)


def read_chain(path: str) -> Tuple[List[Tuple[float, float]], bool]:
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = [f.strip().lower() for f in (reader.fieldnames or [])]
        if "strike" not in fields or not ({"call", "put"} & set(fields)):
            raise InputError("chain CSV needs a strike column and a call or put column")
        kind = "call" if "call" in fields else "put"
        rows = []
        for number, row in enumerate(reader, start=2):
            row = {(k or "").strip().lower(): v for k, v in row.items()}
            try:
                rows.append((float(row["strike"]), float(row[kind])))
            except (TypeError, ValueError):
                raise InputError("row %d is not numeric" % number)
    if len(rows) < 2:
        raise InputError("need at least two strikes")
    return rows, kind == "call"


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="options_lab.py", description="European option checks.")
    sub = ap.add_subparsers(dest="command", required=True)

    def market(p: argparse.ArgumentParser, need_vol: bool = True) -> None:
        p.add_argument("--spot", type=float)
        p.add_argument("--forward", type=float, help="use Black-76 on this forward instead of spot")
        p.add_argument("--strike", type=float, required=True)
        p.add_argument("--rate", type=float, default=0.0)
        p.add_argument("--div", type=float, default=0.0, help="continuous dividend or borrow yield")
        p.add_argument("--expiry", type=float, required=True, help="years")
        if need_vol:
            p.add_argument("--vol", type=float, required=True)
        p.add_argument("--put", action="store_true")

    market(sub.add_parser("price"))
    iv = sub.add_parser("iv")
    market(iv, need_vol=False)
    iv.add_argument("--price", type=float, required=True)
    par = sub.add_parser("parity")
    for name in ("call", "put", "spot", "strike", "expiry"):
        par.add_argument("--" + name, type=float, required=True)
    par.add_argument("--rate", type=float, default=0.0)
    par.add_argument("--div", type=float, default=0.0)
    par.add_argument("--tolerance", type=float, default=0.01, help="acceptable gap, e.g. half the spreads")
    ch = sub.add_parser("chain")
    ch.add_argument("path")
    ch.add_argument("--rate", type=float, default=0.0)
    ch.add_argument("--expiry", type=float, required=True)
    ch.add_argument("--spot", type=float)
    ch.add_argument("--div", type=float, default=0.0)
    cal = sub.add_parser("calendar")
    cal.add_argument("points", nargs="+", help="EXPIRY:VOL at the same forward moneyness")
    mc = sub.add_parser("mc")
    market(mc)
    mc.add_argument("--paths", type=int, default=100000)
    mc.add_argument("--seed", type=int)
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    try:
        if args.command == "price":
            call = not args.put
            if args.forward is not None:
                r = black(args.forward, args.strike, args.rate, args.vol, args.expiry, call)
                model = "Black-76"
            else:
                if args.spot is None:
                    raise InputError("give --spot or --forward")
                r = bsm(args.spot, args.strike, args.rate, args.vol, args.expiry, args.div, call)
                model = "Black-Scholes-Merton"
            print("%s %s price %.6f" % (model, "call" if call else "put", r["price"]))
            for key in ("delta", "gamma", "vega", "theta", "rho"):
                if key in r:
                    print("  %-6s %.6f" % (key, r[key]))
            print("  vega per 1.00 vol, theta per year, rho per 1.00 rate")
        elif args.command == "iv":
            if args.spot is None:
                raise InputError("iv needs --spot")
            vol = implied_vol(args.price, args.spot, args.strike, args.rate, args.expiry,
                              args.div, not args.put)
            print("implied vol %.6f" % vol)
        elif args.command == "parity":
            gap = parity_gap(args.call, args.put, args.spot, args.strike, args.rate,
                             args.expiry, args.div)
            print("put-call parity gap %.6f (C - P - (S e^-qT - K e^-rT))" % gap)
            if abs(gap) > args.tolerance:
                print("gap exceeds tolerance %.4g: check dividends, borrow cost, early "
                      "exercise, stale quotes, or an arbitrage" % args.tolerance)
                return 1
        elif args.command == "chain":
            rows, call = read_chain(args.path)
            problems = check_chain(rows, args.rate, args.expiry, args.spot, args.div, call)
            print("%d strikes checked (%s)" % (len(rows), "calls" if call else "puts"))
            for p in problems:
                print("  ARBITRAGE " + p)
            if problems:
                return 1
            print("  no static arbitrage found in the quotes as given (mids; widen by spreads before trading)")
        elif args.command == "calendar":
            pts = []
            for spec in args.points:
                t, sep, v = spec.partition(":")
                if not sep:
                    raise InputError("point %r must look like EXPIRY:VOL" % spec)
                pts.append((float(t), float(v)))
            problems = check_calendar(pts)
            for p in problems:
                print("  ARBITRAGE " + p)
            if problems:
                return 1
            print("total variance is non-decreasing across %d expiries" % len(pts))
        else:
            if args.spot is None:
                raise InputError("mc needs --spot")
            call = not args.put
            est, se = monte_carlo(args.spot, args.strike, args.rate, args.vol, args.expiry,
                                  args.div, call, args.paths, args.seed)
            exact = bsm(args.spot, args.strike, args.rate, args.vol, args.expiry, args.div, call)["price"]
            z = (est - exact) / se if se > 0 else 0.0
            print("Monte Carlo %.6f, standard error %.6f, closed form %.6f, z %.2f"
                  % (est, se, exact, z))
            if abs(z) > 3:
                print("disagreement beyond three standard errors")
                return 1
    except (InputError, OSError, ValueError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
