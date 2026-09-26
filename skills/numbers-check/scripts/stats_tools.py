#!/usr/bin/env python3
"""Small, checkable statistics helpers for the numbers-check skill.

Standard library only. Python 3.9 or later.

Usage:
    python3 stats_tools.py wilson 8 10                    # 95 percent Wilson interval for 8 of 10
    python3 stats_tools.py wilson 8 10 --confidence 0.99
    python3 stats_tools.py ztest 120 1000 150 1000        # two-proportion z test, A then B
    python3 stats_tools.py samplesize 0.10 0.02           # per arm, baseline 10 percent, +2 points absolute
    python3 stats_tools.py samplesize 0.10 0.02 --alpha 0.05 --power 0.8 --one-sided
    python3 stats_tools.py bh 0.01 0.04 0.03 0.20         # Benjamini-Hochberg adjusted p values
    python3 stats_tools.py montecarlo 1e6:5e6 0.01:0.05 20:40
    python3 stats_tools.py montecarlo 100:200:400 0.1:0.2:0.5 --dist triangular --draws 50000 --seed 1

Formulas:
    wilson      Wilson score interval, Wilson (1927).
    ztest       Pooled standard error under the null of equal proportions, two-sided p value
                unless --one-sided.
    samplesize  n = (z_a * sqrt(2 * pbar * (1 - pbar)) + z_b * sqrt(p1 q1 + p2 q2))^2 / (p2 - p1)^2
                with pbar = (p1 + p2) / 2, rounded up. This is the standard pooled normal
                approximation, for example Fleiss, Statistical Methods for Rates and Proportions.
    bh          Benjamini and Hochberg (1995) step-up adjustment, returned in input order.
    montecarlo  Product of independent ranged factors. Log-uniform takes low:high (both > 0).
                Triangular takes low:mode:high. Reports the 5th, 50th and 95th percentiles and
                the product of geometric midpoints for comparison.

These are normal approximations. They are poor for very small counts or proportions near 0 or 1,
and the output says so when the expected counts are small. No function here handles money, so
binary floats are acceptable; use decimal.Decimal for currency elsewhere.

Exit codes: 0 success, 2 invalid input.
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from statistics import NormalDist
from typing import List, Optional, Sequence, Tuple

STD_NORMAL = NormalDist()


class InputError(ValueError):
    """Raised for input that cannot produce a meaningful result."""


def wilson_interval(successes: int, trials: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if trials <= 0:
        raise InputError("trials must be positive")
    if not 0 <= successes <= trials:
        raise InputError("successes must be between 0 and trials")
    if not 0 < confidence < 1:
        raise InputError("confidence must be between 0 and 1")
    z = STD_NORMAL.inv_cdf(1 - (1 - confidence) / 2)
    p = successes / trials
    denom = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denom
    half = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denom
    low = 0.0 if successes == 0 else max(0.0, centre - half)
    high = 1.0 if successes == trials else min(1.0, centre + half)
    return low, high


def two_proportion_z(x1: int, n1: int, x2: int, n2: int,
                     two_sided: bool = True) -> Tuple[float, float, float]:
    """Return (difference p2 - p1, z statistic, p value) using the pooled standard error."""
    for x, n in ((x1, n1), (x2, n2)):
        if n <= 0 or not 0 <= x <= n:
            raise InputError("each group needs 0 <= successes <= trials and trials > 0")
    p1, p2 = x1 / n1, x2 / n2
    pooled = (x1 + x2) / (n1 + n2)
    se = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    if se == 0:
        raise InputError("both groups are all successes or all failures, z is undefined")
    z = (p2 - p1) / se
    if two_sided:
        p_value = 2 * (1 - STD_NORMAL.cdf(abs(z)))
    else:
        p_value = 1 - STD_NORMAL.cdf(z)
    return p2 - p1, z, p_value


def sample_size_two_proportions(baseline: float, mde: float, alpha: float = 0.05,
                                power: float = 0.8, two_sided: bool = True) -> int:
    """Per arm sample size to detect an absolute lift of mde over baseline."""
    p1 = baseline
    p2 = baseline + mde
    if not (0 < p1 < 1 and 0 < p2 < 1):
        raise InputError("baseline and baseline + mde must both lie strictly between 0 and 1")
    if mde == 0:
        raise InputError("mde must be non-zero")
    if not (0 < alpha < 1 and 0 < power < 1):
        raise InputError("alpha and power must be between 0 and 1")
    z_a = STD_NORMAL.inv_cdf(1 - alpha / 2) if two_sided else STD_NORMAL.inv_cdf(1 - alpha)
    z_b = STD_NORMAL.inv_cdf(power)
    pbar = (p1 + p2) / 2
    numerator = (z_a * math.sqrt(2 * pbar * (1 - pbar))
                 + z_b * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    return math.ceil(numerator / (mde * mde))


def benjamini_hochberg(p_values: Sequence[float]) -> List[float]:
    """Benjamini-Hochberg adjusted p values, in the order given."""
    m = len(p_values)
    if m == 0:
        raise InputError("give at least one p value")
    if any(not 0 <= p <= 1 for p in p_values):
        raise InputError("p values must lie between 0 and 1")
    order = sorted(range(m), key=lambda i: p_values[i])
    adjusted = [0.0] * m
    running = 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        running = min(running, p_values[i] * m / rank)
        adjusted[i] = running
    return adjusted


def parse_range(spec: str, dist: str) -> Tuple[float, ...]:
    try:
        parts = tuple(float(x) for x in spec.split(":"))
    except ValueError:
        raise InputError("range %r is not numeric" % spec)
    if dist == "loguniform":
        if len(parts) != 2:
            raise InputError("log-uniform range %r must be low:high" % spec)
        low, high = parts
        if not 0 < low <= high:
            raise InputError("log-uniform range %r needs 0 < low <= high" % spec)
    else:
        if len(parts) != 3:
            raise InputError("triangular range %r must be low:mode:high" % spec)
        low, mode, high = parts
        if not low <= mode <= high or low == high:
            raise InputError("triangular range %r needs low <= mode <= high and low < high" % spec)
    return parts


def monte_carlo_product(ranges: Sequence[Tuple[float, ...]], dist: str = "loguniform",
                        draws: int = 20000, seed: Optional[int] = None) -> dict:
    """Simulate the product of independent ranged factors."""
    if draws < 100:
        raise InputError("use at least 100 draws")
    if not ranges:
        raise InputError("give at least one range")
    rng = random.Random(seed)
    results = []
    for _ in range(draws):
        product = 1.0
        for r in ranges:
            if dist == "loguniform":
                low, high = r
                product *= math.exp(rng.uniform(math.log(low), math.log(high)))
            else:
                low, mode, high = r
                product *= rng.triangular(low, high, mode)
        results.append(product)
    results.sort()

    def pct(q: float) -> float:
        return results[min(len(results) - 1, int(q * len(results)))]

    geo = 1.0
    naive_low = 1.0
    naive_high = 1.0
    for r in ranges:
        low, high = r[0], r[-1]
        naive_low *= low
        naive_high *= high
        geo *= math.sqrt(low * high) if low > 0 else (low + high) / 2
    return {"p05": pct(0.05), "p50": pct(0.50), "p95": pct(0.95),
            "geometric_midpoint_product": geo, "naive_low": naive_low, "naive_high": naive_high}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    w = sub.add_parser("wilson", help="Wilson interval for a proportion")
    w.add_argument("successes", type=int)
    w.add_argument("trials", type=int)
    w.add_argument("--confidence", type=float, default=0.95)

    z = sub.add_parser("ztest", help="two-proportion z test")
    z.add_argument("x1", type=int)
    z.add_argument("n1", type=int)
    z.add_argument("x2", type=int)
    z.add_argument("n2", type=int)
    z.add_argument("--one-sided", action="store_true", help="test B greater than A")

    s = sub.add_parser("samplesize", help="per arm sample size for two proportions")
    s.add_argument("baseline", type=float, help="baseline rate, e.g. 0.10")
    s.add_argument("mde", type=float, help="absolute minimum detectable effect, e.g. 0.02")
    s.add_argument("--alpha", type=float, default=0.05)
    s.add_argument("--power", type=float, default=0.8)
    s.add_argument("--one-sided", action="store_true")

    b = sub.add_parser("bh", help="Benjamini-Hochberg adjustment")
    b.add_argument("p_values", type=float, nargs="+")
    b.add_argument("--fdr", type=float, default=0.05, help="false discovery rate to flag at")

    m = sub.add_parser("montecarlo", help="range of a product of ranged inputs")
    m.add_argument("ranges", nargs="+", help="low:high (log-uniform) or low:mode:high (triangular)")
    m.add_argument("--dist", choices=("loguniform", "triangular"), default="loguniform")
    m.add_argument("--draws", type=int, default=20000)
    m.add_argument("--seed", type=int, default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "wilson":
            low, high = wilson_interval(args.successes, args.trials, args.confidence)
            print("proportion %.4f, %.0f%% Wilson interval %.4f to %.4f"
                  % (args.successes / args.trials, 100 * args.confidence, low, high))
            if min(args.successes, args.trials - args.successes) < 5:
                print("note: fewer than 5 successes or failures, consider an exact interval")
        elif args.command == "ztest":
            diff, zval, p = two_proportion_z(args.x1, args.n1, args.x2, args.n2,
                                             two_sided=not args.one_sided)
            print("p_A %.4f, p_B %.4f, difference %.4f, z %.3f, p value %.4g (%s)"
                  % (args.x1 / args.n1, args.x2 / args.n2, diff, zval, p,
                     "one-sided" if args.one_sided else "two-sided"))
            print("the p value is the probability of a difference at least this extreme if the "
                  "true rates were equal, not the probability that they are equal")
        elif args.command == "samplesize":
            n = sample_size_two_proportions(args.baseline, args.mde, args.alpha, args.power,
                                            two_sided=not args.one_sided)
            print("%d per arm, %d total (baseline %.4f, target %.4f, alpha %g %s, power %g)"
                  % (n, 2 * n, args.baseline, args.baseline + args.mde, args.alpha,
                     "one-sided" if args.one_sided else "two-sided", args.power))
        elif args.command == "bh":
            adjusted = benjamini_hochberg(args.p_values)
            for raw, adj in zip(args.p_values, adjusted):
                flag = "significant" if adj <= args.fdr else ""
                print(("p %.4g  adjusted %.4g  %s" % (raw, adj, flag)).rstrip())
        elif args.command == "montecarlo":
            ranges = [parse_range(r, args.dist) for r in args.ranges]
            res = monte_carlo_product(ranges, args.dist, args.draws, args.seed)
            print("5th %.4g  median %.4g  95th %.4g  (%d draws, %s)"
                  % (res["p05"], res["p50"], res["p95"], args.draws, args.dist))
            print("product of geometric midpoints %.4g" % res["geometric_midpoint_product"])
            print("product of range ends %.4g to %.4g, reached only if every input sits at "
                  "the same end at once"
                  % (res["naive_low"], res["naive_high"]))
            print("assumes the factors are independent")
    except InputError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
