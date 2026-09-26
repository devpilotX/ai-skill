#!/usr/bin/env python3
"""Validate every skill in this repository.

Checks the skill specification, reference integrity, script health, and house
style. Exits non-zero on any error so that CI blocks a bad commit.

What it checks:
  spec        SKILL.md exists, frontmatter parses, name matches the folder and the
              character rules, description present and within the length limit,
              metadata carries a semantic version and the suite name
  shape       every SKILL.md has the sections CONTRIBUTING.md requires: when to
              use and when to stay off (the off switch), non-negotiables, a
              self-audit, and what the skill cannot do
  references  every path mentioned in prose exists, and every file in references/
              or scripts/ is reachable from SKILL.md through a chain of mentions,
              so nothing is orphaned or loaded only by accident
  crossrefs   a skill named in backticks refers to a skill that exists, and a
              near miss of a real skill name is an error rather than a warning
  agents      every agent source parses, names only skills that exist, and the
              generated Kiro and Claude Code files are in sync with the source
  scripts     every Python script compiles, has a docstring, and is referenced
  style       runs the human-prose detector over all Markdown outside fixtures
  hygiene     final newline, no trailing whitespace, no tab indentation
  readme      the README lists every skill, and lists no skill that is absent

Usage:
  python3 tools/validate_skills.py
  python3 tools/validate_skills.py --style-level pedantic
"""

from __future__ import annotations

import argparse
import difflib
import importlib.util
import py_compile
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
DETECTOR = SKILLS_DIR / "human-prose" / "scripts" / "ai_tells.py"
STYLE_EXCLUDE_DIRS = {"tests/fixtures"}
SKIP_PARTS = {".git", "dist", "__pycache__", ".venv", "venv", "node_modules"}
AGENT_BUILDER = ROOT / "tools" / "build_agents.py"

# Sections CONTRIBUTING.md requires in every SKILL.md, as heading patterns.
REQUIRED_SECTIONS = [
    (re.compile(r"^## when to (use|run)\b.*\bstay off\b", re.I | re.M),
     "## When to use and when to stay off (activation and the off switch)"),
    (re.compile(r"^## non-negotiables\b", re.I | re.M), "## Non-negotiables"),
    (re.compile(r"^## self-audit\b", re.I | re.M), "## Self-audit"),
    (re.compile(r"^## what this (skill )?(cannot do|will not claim)\b", re.I | re.M),
     "## What this cannot do"),
]
OFF_SWITCH_RE = re.compile(r"\bstop\b", re.I)
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
NAME_MAX = 64
DESCRIPTION_MAX = 1024
# Matches a reference or script path whether it is wrapped in backticks or sits
# inside a fenced usage example.
PATH_MENTION_RE = re.compile(r"(?:references|scripts)/[A-Za-z0-9_./-]+\.(?:md|py|sh)")
SKILL_MENTION_RE = re.compile(r"`([a-z][a-z0-9]*(?:-[a-z0-9]+)+)`")

errors: list[str] = []
warnings: list[str] = []
checks_run = 0


def fail(where: str, message: str) -> None:
    errors.append("%s: %s" % (where, message))


def warn(where: str, message: str) -> None:
    warnings.append("%s: %s" % (where, message))


def ok(_where: str) -> None:
    global checks_run
    checks_run += 1


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        fail(rel(path), "is not valid UTF-8")
        return ""


def check_agents(all_names: set[str]) -> None:
    if not AGENT_BUILDER.is_file():
        return
    spec = importlib.util.spec_from_file_location("build_agents", AGENT_BUILDER)
    if not (spec and spec.loader):
        fail(rel(AGENT_BUILDER), "cannot load the agent builder")
        return
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_agents"] = module
    spec.loader.exec_module(module)
    problems = module.check(all_names)
    for problem in problems:
        fail("agents", problem)
    if not problems:
        ok("agents")


def load_detector():
    spec = importlib.util.spec_from_file_location("ai_tells", DETECTOR)
    if not DETECTOR.is_file() or not (spec and spec.loader):
        fail(rel(DETECTOR), "cannot load the style detector")
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules["ai_tells"] = module
    spec.loader.exec_module(module)
    return module


def parse_frontmatter(text: str, where: str) -> dict:
    """Minimal frontmatter reader. Avoids a yaml dependency on purpose."""
    if not text.startswith("---\n"):
        fail(where, "missing YAML frontmatter as the first line")
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        fail(where, "frontmatter is not terminated")
        return {}
    meta: dict = {}
    current_key = None
    for raw in text[4:end].split("\n"):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[0] in " \t":
            if current_key:
                meta.setdefault(current_key + "._nested", []).append(raw.strip())
            continue
        if ":" not in raw:
            fail(where, "frontmatter line is not a key value pair: %r" % raw[:40])
            continue
        key, _, value = raw.partition(":")
        current_key = key.strip()
        meta[current_key] = value.strip()
    return meta


def check_spec(skill_dir: Path) -> dict:
    where = rel(skill_dir / "SKILL.md")
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        fail(rel(skill_dir), "no SKILL.md")
        return {}
    text = skill_md.read_text(encoding="utf-8")
    meta = parse_frontmatter(text, where)
    if not meta:
        return {}

    name = meta.get("name", "")
    if not name:
        fail(where, "frontmatter has no name")
    else:
        ok(where)
        if name != skill_dir.name:
            fail(where, "name %r does not match folder %r" % (name, skill_dir.name))
        else:
            ok(where)
        if len(name) > NAME_MAX:
            fail(where, "name is %d characters, limit is %d" % (len(name), NAME_MAX))
        else:
            ok(where)
        if not NAME_RE.match(name):
            fail(where, "name %r must be lowercase letters, digits and single hyphens" % name)
        else:
            ok(where)

    desc = meta.get("description", "")
    if not desc:
        fail(where, "frontmatter has no description, so the skill cannot auto activate")
    else:
        ok(where)
        if len(desc) > DESCRIPTION_MAX:
            fail(where, "description is %d characters, limit is %d" % (len(desc), DESCRIPTION_MAX))
        else:
            ok(where)
        if len(desc) < 80:
            warn(where, "description is short at %d characters, activation may be unreliable" % len(desc))
        if meta.get("description._nested"):
            fail(where, "description spans multiple lines, keep it on one line")

    for key in meta:
        if key.endswith("._nested"):
            continue
        if key not in {"name", "description", "license", "compatibility", "metadata",
                       "allowed-tools"}:
            warn(where, "unrecognised frontmatter key %r" % key)

    nested = dict(item.partition(":")[::2] for item in meta.get("metadata._nested", []))
    nested = {k.strip(): v.strip() for k, v in nested.items()}
    version = nested.get("version", "")
    if not SEMVER_RE.match(version):
        fail(where, "metadata.version %r is not a semantic version" % version)
    else:
        ok(where)
    if nested.get("suite") != "ai-skill":
        fail(where, "metadata.suite must be ai-skill")
    else:
        ok(where)

    body = text[text.find("\n---", 4) + 4:]
    if len(body.strip()) < 400:
        warn(where, "body is very short, %d characters" % len(body.strip()))
    check_shape(where, body)
    return meta


def check_shape(where: str, body: str) -> None:
    for pattern, label in REQUIRED_SECTIONS:
        if not pattern.search(body):
            fail(where, "missing required section %s" % label)
        else:
            ok(where)
    match = REQUIRED_SECTIONS[0][0].search(body)
    if match:
        section = body[match.end():]
        nxt = re.search(r"^## ", section, re.M)
        section = section[:nxt.start()] if nxt else section
        if not OFF_SWITCH_RE.search(section):
            fail(where, "the activation section does not say how to stop the skill")
        else:
            ok(where)


def check_references(skill_dir: Path) -> None:
    md_files = sorted(skill_dir.rglob("*.md"))
    for md in md_files:
        text = read(md)
        for match in PATH_MENTION_RE.findall(text):
            target = skill_dir / match
            if not target.is_file():
                fail(rel(md), "mentions %s which does not exist" % match)
            else:
                ok(rel(md))

    # Reachability: walk mentions outward from SKILL.md. A reference file that is
    # only mentioned by itself, or by another unreachable file, never loads.
    mentioned: set[str] = set()
    queue = [skill_dir / "SKILL.md"]
    seen: set[Path] = set()
    while queue:
        current = queue.pop()
        if current in seen or not current.is_file():
            continue
        seen.add(current)
        if current.suffix != ".md":
            continue
        for match in PATH_MENTION_RE.findall(read(current)):
            mentioned.add(match)
            queue.append(skill_dir / match)

    present: set[str] = set()
    for sub in ("references", "scripts"):
        folder = skill_dir / sub
        if not folder.is_dir():
            continue
        for item in sorted(folder.rglob("*")):
            if not item.is_file() or item.name.startswith("."):
                continue
            if "__pycache__" in item.parts or item.suffix == ".pyc":
                continue
            present.add("%s/%s" % (sub, item.relative_to(folder).as_posix()))

    for path in sorted(present - mentioned):
        fail(rel(skill_dir), "%s is not reachable from SKILL.md, so it will never load" % path)
    for _ in sorted(present & mentioned):
        ok(rel(skill_dir))


def check_crossrefs(all_names: set[str]) -> None:
    known_words = {
        "lint-exempt", "lint-vocab-exempt", "vocab-density", "title-case-heading",
        "x-and-y-heading", "bold-label-list", "copula-avoidance", "significance-padding",
        "vague-attribution", "cutoff-disclaimer", "section-summary", "negative-parallelism",
        "participle-tail", "rule-of-three", "trailing-space", "final-newline",
        "em-dash", "en-dash", "curly-quote", "thematic-break", "no-sandbox",
        "print-to-pdf", "disable-gpu", "enable-local-file-access", "omit-dev",
        "ppl-ai-file-upload", "utm-source", "pip-audit", "oai-citation",
        "read-only", "read-write",
    }
    for md in sorted(ROOT.rglob("*.md")):
        if any(part in SKIP_PARTS for part in md.parts):
            continue
        text = read(md)
        for token in set(SKILL_MENTION_RE.findall(text)):
            if token in known_words or token in all_names:
                continue
            if (SKILLS_DIR / token).is_dir():
                continue
            near = difflib.get_close_matches(token, sorted(all_names), n=1, cutoff=0.85)
            if near:
                fail(rel(md), "backtick token %r looks like a typo for the skill %r"
                     % (token, near[0]))
                continue
            looks_like_skill = token.count("-") == 1 and len(token) > 6
            if looks_like_skill and token not in all_names:
                warn(rel(md), "backtick token %r looks like a skill name but no such skill exists" % token)


def check_scripts() -> None:
    for script in sorted(SKILLS_DIR.rglob("scripts/*.py")):
        where = rel(script)
        with tempfile.TemporaryDirectory() as tmp:
            try:
                py_compile.compile(str(script), cfile=str(Path(tmp) / "out.pyc"),
                                   doraise=True)
                ok(where)
            except py_compile.PyCompileError as exc:
                fail(where, "does not compile: %s" % exc)
                continue
        text = read(script)
        if not re.match(r'^(#![^\n]*\n)?"""', text):
            fail(where, "has no module docstring")
        else:
            ok(where)
        if "def main(" not in text:
            warn(where, "has no main function, so it may not be runnable directly")


def check_hygiene() -> None:
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.suffix not in {".md", ".py", ".yml", ".yaml", ".sh", ".txt", ".json"}:
            continue
        where = rel(path)
        text = read(path)
        if "\r" in text:
            fail(where, "carriage return found, use LF line endings")
        if text and not text.endswith("\n"):
            fail(where, "no newline at end of file")
        else:
            ok(where)
        for n, line in enumerate(text.split("\n"), start=1):
            if line != line.rstrip():
                fail(where, "trailing whitespace on line %d" % n)
            if path.suffix in {".md", ".py"} and line.startswith("\t"):
                fail(where, "tab indentation on line %d" % n)


def check_style(detector, level: str) -> None:
    targets: list[Path] = []
    for md in sorted(ROOT.rglob("*.md")):
        rel_posix = md.relative_to(ROOT).as_posix()
        if any(part in SKIP_PARTS for part in md.parts):
            continue
        if any(rel_posix.startswith(prefix) for prefix in STYLE_EXCLUDE_DIRS):
            continue
        targets.append(md)

    counts = {"high": 0, "medium": 0, "low": 0}
    for md in targets:
        findings = detector.scan(rel(md), read(md))
        for finding in findings:
            counts[finding.severity] += 1
            message = "[%s] line %d: %s" % (finding.rule, finding.line, finding.detail)
            if finding.severity == "low" and level != "pedantic":
                warn(rel(md), message)
            else:
                fail(rel(md), message)
        if not findings:
            ok(rel(md))

    print("style scan: %d markdown files, %d high, %d medium, %d low"
          % (len(targets), counts["high"], counts["medium"], counts["low"]))


def check_readme(all_names: set[str]) -> None:
    readme = ROOT / "README.md"
    if not readme.is_file():
        fail("README.md", "missing")
        return
    text = read(readme)
    for name in sorted(all_names):
        if "](skills/%s/)" % name not in text:
            fail("README.md", "has no table link to skills/%s/" % name)
        else:
            ok("README.md")
    for token in set(re.findall(r"skills/([a-z0-9-]+)/", text)):
        if token not in all_names:
            fail("README.md", "references skills/%s/ which does not exist" % token)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="validate_skills.py")
    ap.add_argument("--style-level", choices=["strict", "pedantic"], default="pedantic",
                    help="pedantic treats low severity style findings as errors")
    args = ap.parse_args(argv)

    if not SKILLS_DIR.is_dir():
        print("no skills directory at %s" % SKILLS_DIR, file=sys.stderr)
        return 2

    skill_dirs = sorted(d for d in SKILLS_DIR.iterdir() if d.is_dir())
    if not skill_dirs:
        print("no skills found", file=sys.stderr)
        return 2

    names: set[str] = set()
    for skill_dir in skill_dirs:
        meta = check_spec(skill_dir)
        name = meta.get("name")
        if name:
            if name in names:
                fail(rel(skill_dir), "duplicate skill name %r" % name)
            names.add(name)
        check_references(skill_dir)

    check_crossrefs(names)
    check_agents(names)
    check_scripts()
    check_hygiene()
    check_readme(names)

    detector = load_detector()
    if detector:
        check_style(detector, args.style_level)

    print("validated %d skills, %d checks passed" % (len(skill_dirs), checks_run))

    if warnings:
        print("\n%d warning(s):" % len(warnings))
        for w in warnings:
            print("  warn  %s" % w)

    if errors:
        print("\n%d error(s):" % len(errors))
        for e in errors:
            print("  ERROR %s" % e)
        return 1

    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
