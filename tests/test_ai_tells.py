#!/usr/bin/env python3
"""Tests for the ai_tells detector.

Two guarantees are checked. The detector finds the patterns it claims to find in a
deliberately machine flavoured fixture, and it stays quiet on plain human prose.
The second half matters more than the first, because a linter with false positives
gets switched off.

Run with: python3 tests/test_ai_tells.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DETECTOR = ROOT / "skills" / "human-prose" / "scripts" / "ai_tells.py"
FIXTURES = ROOT / "tests" / "fixtures"

spec = importlib.util.spec_from_file_location("ai_tells", DETECTOR)
assert spec and spec.loader, "cannot load detector at %s" % DETECTOR
ai_tells = importlib.util.module_from_spec(spec)
# Register before executing, otherwise dataclass resolution fails on Python 3.9.
sys.modules["ai_tells"] = ai_tells
spec.loader.exec_module(ai_tells)

# Rules the machine flavoured fixture must trigger.
MUST_FIND = {
    "artifact",
    "placeholder",
    "chatter",
    "cutoff-disclaimer",
    "em-dash",
    "curly-quote",
    "emoji",
    "thematic-break",
    "title-case-heading",
    "x-and-y-heading",
    "bold-label-list",
    "vocab",
    "vocab-density",
    "vague-attribution",
    "section-summary",
    "negative-parallelism",
    "participle-tail",
    "rule-of-three",
    "copula-avoidance",
}

failures: list[str] = []


def check(condition: bool, message: str) -> None:
    if condition:
        print("  pass  %s" % message)
    else:
        print("  FAIL  %s" % message)
        failures.append(message)


def rules_for(path: Path) -> set[str]:
    findings = ai_tells.scan(str(path), path.read_text(encoding="utf-8"))
    return {f.rule for f in findings}


print("detecting tells in machine_sample.md")
found = rules_for(FIXTURES / "machine_sample.md")
for rule in sorted(MUST_FIND):
    check(rule in found, "detects %s" % rule)

print("\nstaying quiet on clean_sample.md")
clean = rules_for(FIXTURES / "clean_sample.md")
check(clean == set(), "no findings on human prose, got %s" % (sorted(clean) or "none"))

print("\nexemption parsing")
ex = ai_tells.parse_exemptions(["<!-- lint-exempt: vocab,chatter -->", "# Title"])
check(ex == {"vocab", "chatter"}, "parses a two rule exemption, got %s" % sorted(ex))
ex2 = ai_tells.parse_exemptions(["<!-- lint-vocab-exempt -->"])
check(ex2 == {"vocab", "vocab-density"}, "legacy vocab marker still works")
ex3 = ai_tells.parse_exemptions(["# Title", "no marker here"])
check(ex3 == set(), "no marker means no exemption")
ex4 = ai_tells.parse_exemptions(["<!-- lint-exempt: not-a-real-rule -->"])
check(ex4 == set(), "unknown rule names are ignored rather than trusted")

print("\nexemptions actually suppress findings")
suppressed = ai_tells.scan("x.md", "<!-- lint-exempt: em-dash -->\n\nA sentence \u2014 with a dash.\n")
check(not any(f.rule == "em-dash" for f in suppressed), "declared exemption suppresses its rule")
not_suppressed = ai_tells.scan("x.md", "A sentence \u2014 with a dash.\n")
check(any(f.rule == "em-dash" for f in not_suppressed), "undeclared em dash is still reported")

print("\ncode fences are not linted for style")
fenced = ai_tells.scan("x.md", "Text.\n\n```\nnot just a, but b \u2014 really\n```\n")
check(not any(f.rule == "em-dash" for f in fenced), "em dash inside a code fence is ignored")

print("\nfrontmatter is not linted for style")
fm = ai_tells.scan("x.md", "---\ntitle: A Thing \u2014 With Dash\n---\n\nBody text.\n")
check(not any(f.rule == "em-dash" for f in fm), "em dash inside frontmatter is ignored")

print("\nrules not covered by the fixture")


def rules_in(text: str) -> set[str]:
    return {f.rule for f in ai_tells.scan("x.md", text)}


check("significance-padding" in rules_in("The launch reflects a broader shift.\n"),
      "detects significance-padding")
check("en-dash" in rules_in("It worked \u2013 mostly.\n"), "detects en-dash")
check("trailing-space" in rules_in("A line with a space. \n"), "detects trailing-space")
check("final-newline" in rules_in("No newline at the end."), "detects final-newline")
check("chatter" in rules_in("Certainly! Here is the plan.\n"), "detects Certainly! at a sentence start")
check("section-summary" in rules_in("Overall, the plan works.\n"), "detects Overall, as an opener")
check("bold-label-list" in rules_in("- **Speed:** fast\n"), "detects a bold label with the colon inside")
check("em-dash" in rules_in("---\nnot closed\n\nA dash \u2014 here.\n"),
      "an unclosed frontmatter block does not hide the rest of the file")
check("artifact" in rules_in("---\ndescription: x oaicite y\n---\n\nBody.\n"),
      "leaked markup inside frontmatter is still reported")

print("\nno false positives on ordinary text")
for sample, label in [
    ("Build a todo list app.\n", "lowercase todo is not a leftover TODO"),
    ("See [your settings](https://example.com/settings).\n", "a link whose text starts with your"),
    ("The API is not widely available yet.\n", "not widely available is a plain statement"),
    ("It preserves as a rule the original order.\n", "preserves as a is not serves as a"),
    ("Title\n-----\n\nBody text.\n", "a setext heading underline is not a thematic break"),
    ("The Acme\u2122 widget ships in May.\n", "the trade mark sign is not an emoji"),
    ("~~~\nnot just a, but b \u2014 really\n~~~\n", "tilde fences are treated as code"),
    ("The seamless option.\n", None),
]:
    got = rules_in(sample)
    if label is None:
        check("vocab-density" not in got, "density is not applied to a very short file")
    else:
        high_or_medium = {f.rule for f in ai_tells.scan("x.md", sample) if f.severity != "low"}
        check(not high_or_medium, "%s, got %s" % (label, sorted(high_or_medium) or "none"))
soft = [f for f in ai_tells.scan("x.md", "Let me know if Tuesday works.\n") if f.rule == "chatter"]
check(bool(soft) and all(f.severity == "low" for f in soft), "email sign-offs are low severity, not high")

print("\nthe all token cannot exempt near-proof rules")
ex_all = ai_tells.parse_exemptions(["<!-- lint-exempt: all -->"])
check("artifact" not in ex_all and "placeholder" not in ex_all, "all excludes artifact and placeholder")

print("\ncommand line exit codes")
import subprocess
import tempfile


def run(args: list[str], stdin: str = "") -> int:
    return subprocess.run([sys.executable, str(DETECTOR)] + args, input=stdin,
                          capture_output=True, text=True).returncode


with tempfile.TemporaryDirectory() as tmp:
    clean = Path(tmp) / "clean.md"
    clean.write_text("A plain sentence.\n", encoding="utf-8")
    medium = Path(tmp) / "medium.md"
    medium.write_text("A dash \u2014 here.\n", encoding="utf-8")
    check(run([str(clean)]) == 0, "clean file exits 0")
    check(run([str(medium)]) == 0, "medium finding passes the default threshold")
    check(run(["--strict", str(medium)]) == 1, "medium finding fails --strict")
    check(run(["--pedantic", str(clean)]) == 0, "clean file passes --pedantic")
    check(run([str(clean), str(Path(tmp) / "missing.md")]) == 2, "a missing path exits 2")
    check(run([], stdin="oaicite\n") == 1, "stdin is scanned and high findings exit 1")

print("\n%d check(s) failed" % len(failures))
sys.exit(1 if failures else 0)
