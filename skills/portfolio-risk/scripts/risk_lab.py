#!/usr/bin/env python3
"""Portfolio risk arithmetic that should be computed, not estimated in prose.

Standard library only. Python 3.9 or later. Matrix routines are written out in plain
Python, so they suit tens of assets, not thousands.

Input is a CSV of periodic asset returns with a header row naming the assets, one row
per period, no date column (or name it with --skip). Weights are given as
NAME=VALUE pairs.

Usage:
  python3 risk_lab.py cov returns.csv                     # sample and Ledoit-Wolf covariance
  python3 risk_lab.py spectrum returns.csv                # eigenvalues against the Marchenko-Pastur edge
  python3 risk_lab.py minvar returns.csv --shrink         # global minimum variance weights
  python3 risk_lab.py contrib returns.csv --weights A=0.5 B=0.3 C=0.2
  python3 risk_lab.py riskparity returns.csv --shrink     # equal risk contribution weights
  python3 risk_lab.py var returns.csv --weights A=0.6 B=0.4 --alpha 0.99
  python3 risk_lab.py kupiec --exceptions 9 --observations 250 --alpha 0.99
  python3 risk_lab.py kelly returns.csv --fraction 0.5 --shrink

Methods:
  Ledoit-Wolf    shrinkage toward a scaled identity, Ledoit and Wolf (2004), "A
                 well-conditioned estimator for large-dimensional covariance
                 matrices", Journal of Multivariate Analysis. The shrinkage
                 intensity is estimated from the data and printed.
  spectrum       eigenvalues of the correlation matrix by the Jacobi method, compared
                 with the Marchenko-Pastur upper edge (1 + sqrt(N/T))^2. Eigenvalues
                 below the edge are indistinguishable from noise for i.i.d. data.
  minvar         w = S^-1 1 / (1' S^-1 1). Fully invested, shorts allowed.
  contrib        Euler risk contributions w_i (S w)_i / sigma_p, which sum to sigma_p.
  riskparity     long-only weights with equal risk contributions, by the cyclical
                 coordinate method of Griveau-Billion, Richard and Roncalli (2013).
  var            historical value at risk and expected shortfall of the weighted
                 portfolio, as positive loss fractions.
  kupiec         proportion of failures likelihood ratio test for a VaR model,
                 Kupiec (1995). Small p values reject the stated coverage.
  kelly          continuous-time growth optimal weights S^-1 (mu - rf), scaled by
                 --fraction, with --rf the risk-free return per period.
                 Estimation error in mu makes full Kelly far too aggressive; the
                 output says so.

Exit codes: 0 success, 2 invalid input.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from typing import Dict, List, Optional, Sequence, Tuple

Matrix = List[List[float]]


class InputError(ValueError):
    """Raised for input that cannot produce a meaningful result."""


def read_returns(path: str, skip: Sequence[str] = ()) -> Tuple[List[str], Matrix]:
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        try:
            header = [h.strip() for h in next(reader)]
        except StopIteration:
            raise InputError("%s is empty" % path)
        keep = [i for i, h in enumerate(header) if h not in skip]
        names = [header[i] for i in keep]
        if len(set(names)) != len(names):
            raise InputError("asset names in the header must be unique")
        rows: Matrix = []
        for number, row in enumerate(reader, start=2):
            if not any(cell.strip() for cell in row):
                continue
            try:
                rows.append([float(row[i]) for i in keep])
            except (ValueError, IndexError):
                raise InputError("row %d has a missing or non-numeric value" % number)
    if len(names) < 1:
        raise InputError("no asset columns found")
    if len(rows) < len(names) + 2:
        raise InputError("need more periods (%d) than assets (%d) plus two"
                         % (len(rows), len(names)))
    return names, rows


def column_means(x: Matrix) -> List[float]:
    n = len(x)
    return [math.fsum(row[j] for row in x) / n for j in range(len(x[0]))]


def sample_cov(x: Matrix, ddof: int = 1) -> Matrix:
    n, p = len(x), len(x[0])
    mu = column_means(x)
    d = [[row[j] - mu[j] for j in range(p)] for row in x]
    return [[math.fsum(d[t][i] * d[t][j] for t in range(n)) / (n - ddof) for j in range(p)]
            for i in range(p)]


def ledoit_wolf(x: Matrix) -> Tuple[Matrix, float]:
    """Ledoit-Wolf (2004) shrinkage toward mu * I. Returns the matrix and the intensity."""
    n, p = len(x), len(x[0])
    means = column_means(x)
    d = [[row[j] - means[j] for j in range(p)] for row in x]
    s = sample_cov(x, ddof=0)
    mu = sum(s[i][i] for i in range(p)) / p
    delta2 = math.fsum((s[i][j] - (mu if i == j else 0.0)) ** 2
                       for i in range(p) for j in range(p)) / p
    beta_bar = 0.0
    for t in range(n):
        beta_bar += math.fsum((d[t][i] * d[t][j] - s[i][j]) ** 2
                              for i in range(p) for j in range(p))
    beta_bar = beta_bar / (n * n) / p
    beta2 = min(beta_bar, delta2)
    shrink = 0.0 if delta2 == 0 else beta2 / delta2
    out = [[shrink * (mu if i == j else 0.0) + (1 - shrink) * s[i][j] for j in range(p)]
           for i in range(p)]
    return out, shrink


def solve(a: Matrix, b: Sequence[float]) -> List[float]:
    """Solve a x = b by Gaussian elimination with partial pivoting."""
    p = len(a)
    m = [list(a[i]) + [b[i]] for i in range(p)]
    scale = max(abs(v) for row in a for v in row) or 1.0
    for col in range(p):
        pivot = max(range(col, p), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-14 * scale:
            raise InputError("covariance matrix is singular or nearly so; try --shrink")
        m[col], m[pivot] = m[pivot], m[col]
        for r in range(col + 1, p):
            f = m[r][col] / m[col][col]
            for c in range(col, p + 1):
                m[r][c] -= f * m[col][c]
    out = [0.0] * p
    for r in range(p - 1, -1, -1):
        out[r] = (m[r][p] - math.fsum(m[r][c] * out[c] for c in range(r + 1, p))) / m[r][r]
    return out


def matvec(a: Matrix, v: Sequence[float]) -> List[float]:
    return [math.fsum(a[i][j] * v[j] for j in range(len(v))) for i in range(len(a))]


def jacobi_eigenvalues(a: Matrix, tol: float = 1e-12, max_sweeps: int = 100) -> List[float]:
    """Eigenvalues of a symmetric matrix by cyclic Jacobi rotations, largest first."""
    p = len(a)
    m = [list(row) for row in a]
    for _ in range(max_sweeps):
        off = math.fsum(m[i][j] ** 2 for i in range(p) for j in range(p) if i != j)
        if off < tol:
            break
        for i in range(p - 1):
            for j in range(i + 1, p):
                if abs(m[i][j]) < 1e-300:
                    continue
                theta = (m[j][j] - m[i][i]) / (2 * m[i][j])
                t = (1 if theta >= 0 else -1) / (abs(theta) + math.sqrt(theta * theta + 1))
                c = 1 / math.sqrt(t * t + 1)
                s = t * c
                for k in range(p):
                    mik, mjk = m[i][k], m[j][k]
                    m[i][k] = c * mik - s * mjk
                    m[j][k] = s * mik + c * mjk
                for k in range(p):
                    mki, mkj = m[k][i], m[k][j]
                    m[k][i] = c * mki - s * mkj
                    m[k][j] = s * mki + c * mkj
    return sorted((m[i][i] for i in range(p)), reverse=True)


def correlation(cov: Matrix) -> Matrix:
    p = len(cov)
    sd = [math.sqrt(cov[i][i]) for i in range(p)]
    if any(v == 0 for v in sd):
        raise InputError("an asset has zero variance")
    return [[cov[i][j] / (sd[i] * sd[j]) for j in range(p)] for i in range(p)]


def marchenko_pastur_edge(n_assets: int, n_obs: int) -> float:
    q = n_assets / n_obs
    return (1 + math.sqrt(q)) ** 2


def min_variance(cov: Matrix) -> List[float]:
    raw = solve(cov, [1.0] * len(cov))
    total = math.fsum(raw)
    if total == 0:
        raise InputError("minimum variance weights are undefined")
    return [w / total for w in raw]


def risk_contributions(cov: Matrix, w: Sequence[float]) -> Tuple[float, List[float]]:
    sw = matvec(cov, w)
    var = math.fsum(w[i] * sw[i] for i in range(len(w)))
    if var <= 0:
        raise InputError("portfolio variance is not positive")
    sigma = math.sqrt(var)
    return sigma, [w[i] * sw[i] / sigma for i in range(len(w))]


def risk_parity(cov: Matrix, tol: float = 1e-10, max_iter: int = 10000) -> List[float]:
    """Long-only equal risk contribution weights, cyclical coordinate descent."""
    p = len(cov)
    if any(cov[i][i] <= 0 for i in range(p)):
        raise InputError("every asset needs positive variance")
    w = [1 / math.sqrt(cov[i][i]) for i in range(p)]
    b = 1.0 / p
    for _ in range(max_iter):
        previous = list(w)
        sigma = math.sqrt(math.fsum(w[i] * matvec(cov, w)[i] for i in range(p)))
        for i in range(p):
            c = math.fsum(cov[i][j] * w[j] for j in range(p) if j != i)
            a = cov[i][i]
            w[i] = (-c + math.sqrt(c * c + 4 * a * b * sigma)) / (2 * a)
            sigma = math.sqrt(math.fsum(w[k] * matvec(cov, w)[k] for k in range(p)))
        if max(abs(w[i] - previous[i]) for i in range(p)) < tol:
            break
    total = math.fsum(w)
    return [v / total for v in w]


def portfolio_series(x: Matrix, w: Sequence[float]) -> List[float]:
    return [math.fsum(row[j] * w[j] for j in range(len(w))) for row in x]


def historical_var_es(series: Sequence[float], alpha: float) -> Tuple[float, float]:
    """Loss quantile and mean loss beyond it, as positive fractions."""
    if not 0.5 < alpha < 1:
        raise InputError("alpha is a confidence level such as 0.99")
    losses = sorted(-r for r in series)
    n = len(losses)
    k = min(n - 1, int(math.ceil(alpha * n)) - 1)
    var = losses[k]
    tail = losses[k:]
    return var, math.fsum(tail) / len(tail)


def kupiec(exceptions: int, observations: int, alpha: float) -> Tuple[float, float]:
    """Kupiec proportion of failures test. Returns the LR statistic and its chi-square (1 df) p value."""
    if observations <= 0 or not 0 <= exceptions <= observations:
        raise InputError("need 0 <= exceptions <= observations and observations > 0")
    if not 0 < alpha < 1:
        raise InputError("alpha must be between 0 and 1")
    p = 1 - alpha
    x, t = exceptions, observations

    def loglik(prob: float) -> float:
        total = 0.0
        if t - x:
            total += (t - x) * math.log(1 - prob) if prob < 1 else -math.inf
        if x:
            total += x * math.log(prob) if prob > 0 else -math.inf
        return total

    lr = -2 * (loglik(p) - loglik(x / t))
    lr = max(lr, 0.0)
    return lr, math.erfc(math.sqrt(lr / 2))


def parse_weights(pairs: Sequence[str], names: Sequence[str]) -> List[float]:
    given: Dict[str, float] = {}
    for pair in pairs:
        name, sep, value = pair.partition("=")
        if not sep:
            raise InputError("weight %r must look like NAME=VALUE" % pair)
        try:
            given[name.strip()] = float(value)
        except ValueError:
            raise InputError("weight %r is not a number" % pair)
    unknown = set(given) - set(names)
    if unknown:
        raise InputError("unknown asset(s): %s" % ", ".join(sorted(unknown)))
    return [given.get(n, 0.0) for n in names]


def fmt_matrix(names: Sequence[str], m: Matrix) -> str:
    width = max(10, max(len(n) for n in names) + 1)
    lines = [" " * width + "".join(n.rjust(width) for n in names)]
    for name, row in zip(names, m):
        lines.append(name.ljust(width) + "".join(("%.4g" % v).rjust(width) for v in row))
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="risk_lab.py", description="Portfolio risk arithmetic.")
    sub = ap.add_subparsers(dest="command", required=True)
    for name in ("cov", "spectrum", "minvar", "contrib", "riskparity", "var", "kelly"):
        p = sub.add_parser(name)
        p.add_argument("path", help="CSV of asset returns with a header row")
        p.add_argument("--skip", nargs="*", default=[], help="columns to ignore, such as date")
        p.add_argument("--shrink", action="store_true", help="use the Ledoit-Wolf covariance")
        if name in ("contrib", "var"):
            p.add_argument("--weights", nargs="+", required=True, help="NAME=VALUE pairs")
        if name == "var":
            p.add_argument("--alpha", type=float, default=0.99)
        if name == "kelly":
            p.add_argument("--fraction", type=float, default=0.5,
                           help="fraction of full Kelly to report (default 0.5)")
            p.add_argument("--rf", type=float, default=0.0,
                           help="risk-free return per period, subtracted from each asset's mean")
    k = sub.add_parser("kupiec")
    k.add_argument("--exceptions", type=int, required=True)
    k.add_argument("--observations", type=int, required=True)
    k.add_argument("--alpha", type=float, default=0.99)
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    try:
        if args.command == "kupiec":
            lr, pval = kupiec(args.exceptions, args.observations, args.alpha)
            expected = (1 - args.alpha) * args.observations
            print("exceptions %d of %d, expected %.1f at %.1f%% VaR"
                  % (args.exceptions, args.observations, expected, 100 * args.alpha))
            print("Kupiec LR %.3f, p value %.4f" % (lr, pval))
            print("coverage rejected at 5 percent" if pval < 0.05 else
                  "coverage not rejected at 5 percent (the test has low power on short samples)")
            return 0
        names, x = read_returns(args.path, args.skip)
        if args.shrink:
            cov, intensity = ledoit_wolf(x)
        else:
            cov, intensity = sample_cov(x), None
        label = "Ledoit-Wolf" if args.shrink else "sample"
        if args.command == "cov":
            print("sample covariance (%d periods, %d assets)" % (len(x), len(names)))
            print(fmt_matrix(names, sample_cov(x)))
            lw, shrink = ledoit_wolf(x)
            print("\nLedoit-Wolf covariance, shrinkage intensity %.4f" % shrink)
            print(fmt_matrix(names, lw))
        elif args.command == "spectrum":
            eig = jacobi_eigenvalues(correlation(cov))
            edge = marchenko_pastur_edge(len(names), len(x))
            print("correlation eigenvalues (%s), Marchenko-Pastur upper edge %.4f for N=%d, T=%d"
                  % (label, edge, len(names), len(x)))
            for i, v in enumerate(eig, start=1):
                print("  %2d  %.4f  %s" % (i, v, "signal" if v > edge else "noise band"))
            print("%d of %d eigenvalues above the edge" % (sum(v > edge for v in eig), len(eig)))
            if args.shrink:
                print("note: the edge is derived for the sample matrix; shrinkage compresses the "
                      "spectrum, so run without --shrink to count signal eigenvalues")
        elif args.command == "minvar":
            w = min_variance(cov)
            sigma, _ = risk_contributions(cov, w)
            print("global minimum variance weights (%s covariance, shorts allowed)" % label)
            for n_, v in zip(names, w):
                print("  %s %.4f" % (n_, v))
            print("portfolio sd per period %.6g" % sigma)
        elif args.command == "contrib":
            w = parse_weights(args.weights, names)
            sigma, rc = risk_contributions(cov, w)
            print("portfolio sd per period %.6g (%s covariance)" % (sigma, label))
            for n_, wi, c in zip(names, w, rc):
                print("  %s weight %.4f  risk contribution %.6g  share %.2f%%"
                      % (n_, wi, c, 100 * c / sigma))
        elif args.command == "riskparity":
            w = risk_parity(cov)
            sigma, rc = risk_contributions(cov, w)
            print("equal risk contribution weights (%s covariance, long only)" % label)
            for n_, wi, c in zip(names, w, rc):
                print("  %s %.4f  share of risk %.2f%%" % (n_, wi, 100 * c / sigma))
        elif args.command == "var":
            w = parse_weights(args.weights, names)
            var, es = historical_var_es(portfolio_series(x, w), args.alpha)
            print("historical %.1f%% VaR %.4f%%, expected shortfall %.4f%% per period (%d periods)"
                  % (100 * args.alpha, 100 * var, 100 * es, len(x)))
            if (1 - args.alpha) * len(x) < 10:
                print("warning: fewer than 10 tail observations, the tail estimate is unstable")
        elif args.command == "kelly":
            if not 0 < args.fraction <= 1:
                raise InputError("fraction must be in (0, 1]")
            mu = [m - args.rf for m in column_means(x)]
            full = solve(cov, mu)
            print("growth optimal weights, %.2f of full Kelly (%s covariance)" % (args.fraction, label))
            for n_, v in zip(names, full):
                print("  %s %.4f" % (n_, args.fraction * v))
            print("gross leverage %.2f" % (args.fraction * math.fsum(abs(v) for v in full)))
            print("warning: mean returns estimated from history carry large error; these weights "
                  "are an upper bound, not a sizing decision")
    except (InputError, OSError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
