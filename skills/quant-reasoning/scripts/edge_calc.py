#!/usr/bin/env python3
"""Expected value, Kelly sizing, Bayesian updating, ruin probability and forecast
scoring, computed rather than reasoned about in prose.

Standard library only. Python 3.9 or later.

Usage:
  python3 edge_calc.py ev 100:0.2 -20:0.8                  # outcome:probability pairs
  python3 edge_calc.py kelly --p 0.55 --odds 1              # net odds b, pays b per 1 staked
  python3 edge_calc.py kelly --p 0.55 --odds 1 --fraction 0.5
  python3 edge_calc.py bayes --prior 0.001 --sensitivity 0.99 --specificity 0.98
  python3 edge_calc.py bayes --prior 0.2 --likelihood-ratio 3 --likelihood-ratio 0.5
  python3 edge_calc.py ruin --p 0.55 --odds 1 --stake-fraction 0.2 --rounds 500 --floor 0.5 --seed 1
  python3 edge_calc.py score forecasts.csv                  # columns prob,outcome

Formulas:
  ev      E = sum x_i p_i and sd from the second moment. Probabilities must sum to 1.
  kelly   for a binary bet paying b per unit staked with win probability p,
          f* = p - (1 - p) / b, and the expected log growth per bet is
          g(f) = p ln(1 + b f) + (1 - p) ln(1 - f). Kelly (1956), "A new
          interpretation of information rate", Bell System Technical Journal.
          Betting twice Kelly gives roughly zero growth; betting more loses.
  bayes   posterior odds = prior odds x product of likelihood ratios. From a test:
          LR+ = sensitivity / (1 - specificity).
  ruin    Monte Carlo of fixed fraction betting: the share of paths whose bankroll
          ever falls below --floor times the start.
  score   Brier score (mean squared error of probabilities), log loss, and a
          calibration table in ten bins.

Exit codes: 0 success, 2 invalid input.
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import sys
from typing import Dict, List, Optional, Sequence, Tuple


class InputError(ValueError):
    """Raised for input that cannot produce a meaningful result."""


def expected_value(outcomes: Sequence[Tuple[float, float]], tol: float = 1e-9) -> Dict[str, float]:
    if not outcomes:
        raise InputError("give at least one outcome")
    if not all(math.isfinite(x) and math.isfinite(p) for x, p in outcomes):
        raise InputError("values and probabilities must be finite numbers")
    if any(p < 0 for _, p in outcomes):
        raise InputError("probabilities cannot be negative")
    total = math.fsum(p for _, p in outcomes)
    if abs(total - 1) > tol:
        raise InputError("probabilities sum to %.6g, not 1" % total)
    ev = math.fsum(x * p for x, p in outcomes)
    var = math.fsum(p * (x - ev) ** 2 for x, p in outcomes)
    return {"ev": ev, "sd": math.sqrt(var)}


def kelly_fraction(p: float, odds: float) -> float:
    if not 0 < p < 1:
        raise InputError("p must be strictly between 0 and 1")
    if not math.isfinite(odds) or odds <= 0:
        raise InputError("net odds must be positive")
    return p - (1 - p) / odds


def log_growth(p: float, odds: float, f: float) -> float:
    if f >= 1:
        return -math.inf
    if f <= -1 / odds:
        return -math.inf
    return p * math.log(1 + odds * f) + (1 - p) * math.log(1 - f)


def bayes(prior: float, ratios: Sequence[float]) -> float:
    if not 0 < prior < 1:
        raise InputError("prior must be strictly between 0 and 1")
    if any(r <= 0 or not math.isfinite(r) for r in ratios):
        raise InputError("likelihood ratios must be positive and finite")
    odds = prior / (1 - prior)
    for r in ratios:
        odds *= r
    return odds / (1 + odds)


def ruin_probability(p: float, odds: float, stake_fraction: float, rounds: int, floor: float,
                     paths: int = 10000, seed: Optional[int] = None) -> Dict[str, float]:
    if not 0 < stake_fraction < 1:
        raise InputError("stake fraction must be between 0 and 1")
    if not 0 < floor < 1:
        raise InputError("floor is a fraction of the starting bankroll, between 0 and 1")
    if rounds < 1 or paths < 100:
        raise InputError("need at least 1 round and 100 paths")
    kelly_fraction(p, odds)
    rng = random.Random(seed)
    ruined = 0
    finals: List[float] = []
    win, lose = math.log(1 + odds * stake_fraction), math.log(1 - stake_fraction)
    level = math.log(floor)
    for _ in range(paths):
        wealth = 0.0
        hit = False
        for _ in range(rounds):
            wealth += win if rng.random() < p else lose
            if wealth < level:
                hit = True
        ruined += hit
        finals.append(wealth)
    finals.sort()
    return {"probability": ruined / paths, "median_multiple": math.exp(finals[len(finals) // 2]),
            "paths": paths}


def score(pairs: Sequence[Tuple[float, int]]) -> Dict[str, object]:
    if not pairs:
        raise InputError("no forecasts")
    for prob, outcome in pairs:
        if not 0 <= prob <= 1 or outcome not in (0, 1):
            raise InputError("each row needs a probability in [0, 1] and an outcome of 0 or 1")
    n = len(pairs)
    brier = math.fsum((p - o) ** 2 for p, o in pairs) / n
    eps = 1e-15
    logloss = -math.fsum(o * math.log(max(p, eps)) + (1 - o) * math.log(max(1 - p, eps))
                         for p, o in pairs) / n
    base = math.fsum(o for _, o in pairs) / n
    bins: List[Tuple[float, float, int]] = []
    for b in range(10):
        lo, hi = b / 10, (b + 1) / 10
        inside = [(p, o) for p, o in pairs if lo <= p < hi or (b == 9 and p == 1.0)]
        if inside:
            bins.append((math.fsum(p for p, _ in inside) / len(inside),
                         math.fsum(o for _, o in inside) / len(inside), len(inside)))
    return {"n": n, "brier": brier, "log_loss": logloss, "base_rate": base,
            "brier_of_base_rate": base * (1 - base), "bins": bins}


def read_forecasts(path: str) -> List[Tuple[float, int]]:
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = [f.strip().lower() for f in (reader.fieldnames or [])]
        if "prob" not in fields or "outcome" not in fields:
            raise InputError("forecast CSV needs prob and outcome columns")
        out = []
        for number, raw in enumerate(reader, start=2):
            if None in raw:
                raise InputError("row %d has more fields than the header" % number)
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
            if not any(row.values()):
                continue
            try:
                out.append((float(row["prob"]), int(row["outcome"])))
            except ValueError:
                raise InputError("row %d is not numeric" % number)
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="edge_calc.py", description="Edge, sizing and forecast arithmetic.")
    sub = ap.add_subparsers(dest="command", required=True)
    e = sub.add_parser("ev")
    e.add_argument("outcomes", nargs="+", help="VALUE:PROBABILITY pairs")
    k = sub.add_parser("kelly")
    k.add_argument("--p", type=float, required=True)
    k.add_argument("--odds", type=float, required=True, help="net odds b")
    k.add_argument("--fraction", type=float, default=1.0, help="fraction of Kelly to evaluate")
    b = sub.add_parser("bayes")
    b.add_argument("--prior", type=float, required=True)
    b.add_argument("--sensitivity", type=float)
    b.add_argument("--specificity", type=float)
    b.add_argument("--likelihood-ratio", type=float, action="append", default=[])
    r = sub.add_parser("ruin")
    r.add_argument("--p", type=float, required=True)
    r.add_argument("--odds", type=float, required=True)
    r.add_argument("--stake-fraction", type=float, required=True)
    r.add_argument("--rounds", type=int, required=True)
    r.add_argument("--floor", type=float, default=0.5)
    r.add_argument("--paths", type=int, default=10000)
    r.add_argument("--seed", type=int)
    s = sub.add_parser("score")
    s.add_argument("path")
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    try:
        if args.command == "ev":
            pairs = []
            for spec in args.outcomes:
                x, sep, p = spec.rpartition(":")
                if not sep:
                    raise InputError("outcome %r must look like VALUE:PROBABILITY" % spec)
                pairs.append((float(x), float(p)))
            res = expected_value(pairs)
            print("expected value %.6g, standard deviation %.6g" % (res["ev"], res["sd"]))
        elif args.command == "kelly":
            f = kelly_fraction(args.p, args.odds)
            edge = args.p * args.odds - (1 - args.p)
            print("edge per unit staked %.6g" % edge)
            if f <= 0:
                print("no positive edge: Kelly says do not bet (f* = %.4f)" % f)
            else:
                used = args.fraction * f
                print("full Kelly fraction %.4f of bankroll" % f)
                print("at %.2f Kelly: stake %.4f, expected log growth per bet %.6g (full Kelly %.6g)"
                      % (args.fraction, used, log_growth(args.p, args.odds, used),
                         log_growth(args.p, args.odds, f)))
                print("growth at 2x Kelly %.6g; the edge estimate is uncertain, so fractional Kelly "
                      "is the usual choice" % log_growth(args.p, args.odds, min(2 * f, 0.999999)))
        elif args.command == "bayes":
            ratios = list(args.likelihood_ratio)
            if args.sensitivity is not None or args.specificity is not None:
                if args.sensitivity is None or args.specificity is None:
                    raise InputError("give both --sensitivity and --specificity")
                if not (0 < args.sensitivity <= 1 and 0 <= args.specificity < 1):
                    raise InputError("sensitivity in (0, 1], specificity in [0, 1)")
                ratios.append(args.sensitivity / (1 - args.specificity))
            if not ratios:
                raise InputError("give a test (sensitivity and specificity) or likelihood ratios")
            post = bayes(args.prior, ratios)
            print("prior %.6g, likelihood ratio product %.6g, posterior %.6g"
                  % (args.prior, math.prod(ratios), post))
        elif args.command == "ruin":
            res = ruin_probability(args.p, args.odds, args.stake_fraction, args.rounds, args.floor,
                                   args.paths, args.seed)
            print("probability of falling below %.0f%% of the start within %d bets: %.4f (%d paths)"
                  % (100 * args.floor, args.rounds, res["probability"], res["paths"]))
            print("median final bankroll multiple %.4g; Kelly fraction here is %.4f"
                  % (res["median_multiple"], kelly_fraction(args.p, args.odds)))
        else:
            res = score(read_forecasts(args.path))
            print("%d forecasts, base rate %.4f" % (res["n"], res["base_rate"]))
            print("Brier %.4f (always forecasting the base rate scores %.4f), log loss %.4f"
                  % (res["brier"], res["brier_of_base_rate"], res["log_loss"]))
            print("calibration: mean forecast, observed frequency, count")
            for mean_p, freq, count in res["bins"]:  # type: ignore[union-attr]
                print("  %.3f  %.3f  %d" % (mean_p, freq, count))
    except (InputError, OSError, ValueError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
