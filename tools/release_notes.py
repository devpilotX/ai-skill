#!/usr/bin/env python3
"""Print the CHANGELOG.md section for a release tag, for use as release notes.

The changelog follows Keep a Changelog: one "## [X.Y.Z] - YYYY-MM-DD" heading per
release. The tag vX.Y.Z selects the section up to the next "## " heading. The
release workflow fails if the tag has no section, so every release is documented.

Usage:
  python3 tools/release_notes.py v1.2.0

Exit codes: 0 printed, 1 no section for that tag, 2 usage error.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Optional, Sequence

CHANGELOG = Path(__file__).resolve().parents[1] / "CHANGELOG.md"


def section(text: str, version: str) -> Optional[str]:
    pattern = re.compile(r"^## \[%s\][^\n]*\n(.*?)(?=^## |\Z)" % re.escape(version), re.M | re.S)
    match = pattern.search(text)
    return match.group(1).strip() + "\n" if match else None


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1 or not re.fullmatch(r"v\d+\.\d+\.\d+", args[0]):
        print("usage: release_notes.py vX.Y.Z", file=sys.stderr)
        return 2
    body = section(CHANGELOG.read_text(encoding="utf-8"), args[0][1:])
    if body is None:
        print("CHANGELOG.md has no section for %s" % args[0], file=sys.stderr)
        return 1
    sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
