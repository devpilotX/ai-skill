#!/usr/bin/env python3
"""Run every test script in tests/ and report a combined result.

Each tests/test_*.py is a standalone script that exits non-zero on failure, so this
runner needs no test framework. CI and CONTRIBUTING.md both call it, which means a
new test file is picked up without editing either.

Usage:
  python3 tools/run_tests.py
  python3 tools/run_tests.py --verbose     # print each script's full output

Exit codes: 0 every script passed, 1 at least one failed, 2 no test scripts found.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Sequence

ROOT = Path(__file__).resolve().parents[1]


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="run_tests.py", description="Run every tests/test_*.py script.")
    ap.add_argument("--verbose", action="store_true", help="print the output of passing scripts too")
    ap.add_argument("--timeout", type=int, default=300, help="seconds allowed per script (default 300)")
    args = ap.parse_args(argv)
    scripts = sorted((ROOT / "tests").glob("test_*.py"))
    if not scripts:
        print("no test scripts found in tests/", file=sys.stderr)
        return 2
    failed = []
    for script in scripts:
        start = time.monotonic()
        try:
            proc = subprocess.run([sys.executable, "-B", str(script)], cwd=str(ROOT),
                                  capture_output=True, text=True, timeout=args.timeout)
        except subprocess.TimeoutExpired:
            print("FAIL %-28s timed out after %d s" % (script.name, args.timeout))
            failed.append(script.name)
            continue
        elapsed = time.monotonic() - start
        checks = proc.stdout.count("  pass  ")
        status = "ok  " if proc.returncode == 0 else "FAIL"
        print("%s %-28s %4d checks  %5.1fs" % (status, script.name, checks, elapsed))
        if proc.returncode != 0:
            failed.append(script.name)
        if proc.returncode != 0 or args.verbose:
            print(proc.stdout.rstrip())
            if proc.stderr.strip():
                print(proc.stderr.rstrip())
    print("\n%d script(s), %d failed" % (len(scripts), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
