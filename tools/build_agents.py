#!/usr/bin/env python3
"""Generate Kiro and Claude Code agent files from the agent sources.

Each agent is written once, in agents/src/<name>.md, with this frontmatter:

  ---
  name: quant-researcher
  description: One line saying when to delegate to this agent.
  skills: quant-research, stat-arb, numbers-check
  access: read-write
  ---
  System prompt in Markdown.

access is read-only (the agent may read files and the web and run commands that
change nothing) or read-write (it may also edit files and run any command).

The script writes:

  agents/kiro/<name>.md     Kiro custom agent: frontmatter with tools and one
                            skill:// resource per skill, body as the prompt.
  agents/claude/<name>.md   Claude Code subagent: frontmatter with tools and the
                            skills to preload, body as the system prompt.

Usage:
  python3 tools/build_agents.py           # regenerate both folders
  python3 tools/build_agents.py --check   # exit 1 if a generated file is stale

tools/validate_skills.py imports check() from this module, so CI fails when an
agent names a skill that does not exist or a generated file is out of date.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "agents" / "src"
KIRO = ROOT / "agents" / "kiro"
CLAUDE = ROOT / "agents" / "claude"
SKILLS = ROOT / "skills"

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ACCESS = {
    "read-only": {
        "kiro": ["read", "web"],
        "claude": "Read, Grep, Glob, WebFetch, WebSearch",
    },
    "read-write": {
        "kiro": ["read", "write", "shell", "web"],
        "claude": "Read, Grep, Glob, Edit, Write, Bash, WebFetch, WebSearch",
    },
}
BANNER = "<!-- Generated from agents/src/%s.md by tools/build_agents.py. Edit the source, not this file. -->"


def parse(path: Path) -> Tuple[Dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("%s: missing frontmatter" % path.name)
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("%s: frontmatter is not closed" % path.name)
    meta: Dict[str, str] = {}
    for line in text[4:end].split("\n"):
        if not line.strip():
            continue
        key, sep, value = line.partition(":")
        if not sep:
            raise ValueError("%s: bad frontmatter line %r" % (path.name, line))
        meta[key.strip()] = value.strip()
    body = text[end + 5:].strip("\n") + "\n"
    return meta, body


def skills_of(meta: Dict[str, str]) -> List[str]:
    return [s.strip() for s in meta.get("skills", "").split(",") if s.strip()]


def yaml_string(value: str) -> str:
    return '"%s"' % value.replace("\\", "\\\\").replace('"', '\\"')


def render(meta: Dict[str, str], body: str) -> Tuple[str, str]:
    name = meta["name"]
    access = ACCESS[meta["access"]]
    skills = skills_of(meta)
    banner = BANNER % name
    kiro = ["---", "name: %s" % name, "description: %s" % yaml_string(meta["description"]),
            "tools: [%s]" % ", ".join('"%s"' % t for t in access["kiro"]), "resources:"]
    kiro += ["  - skill://%s" % s for s in skills]
    kiro += ["---", "", banner, "", body]
    claude = ["---", "name: %s" % name, "description: %s" % yaml_string(meta["description"]),
              "tools: %s" % access["claude"], "skills: %s" % ", ".join(skills), "---", "",
              banner, "", body]
    return "\n".join(kiro), "\n".join(claude)


def sources() -> List[Path]:
    return sorted(SRC.glob("*.md")) if SRC.is_dir() else []


def check(all_skills: Optional[Set[str]] = None) -> List[str]:
    """Return a list of problems. Empty means every agent is valid and up to date."""
    if all_skills is None:
        all_skills = {d.name for d in SKILLS.iterdir() if (d / "SKILL.md").is_file()}
    problems: List[str] = []
    names: Set[str] = set()
    for path in sources():
        try:
            meta, body = parse(path)
        except ValueError as exc:
            problems.append(str(exc))
            continue
        name = meta.get("name", "")
        where = "agents/src/%s" % path.name
        if name != path.stem:
            problems.append("%s: name %r does not match the file name" % (where, name))
            continue
        if not NAME_RE.match(name):
            problems.append("%s: name must be lowercase letters, digits and hyphens" % where)
        if name in names:
            problems.append("%s: duplicate agent name" % where)
        names.add(name)
        if not meta.get("description") or len(meta["description"]) < 80:
            problems.append("%s: description missing or too short to route on" % where)
            continue
        if meta.get("access") not in ACCESS:
            problems.append("%s: access must be one of %s" % (where, ", ".join(sorted(ACCESS))))
            continue
        listed = skills_of(meta)
        if not listed:
            problems.append("%s: lists no skills" % where)
        for skill in listed:
            if skill not in all_skills:
                problems.append("%s: skill %r does not exist" % (where, skill))
            elif "`%s`" % skill not in body:
                problems.append("%s: skill %r is listed but the prompt never says when to use it"
                                % (where, skill))
        if len(body.strip()) < 600:
            problems.append("%s: prompt is too short to be useful" % where)
        kiro, claude = render(meta, body)
        for folder, expected in ((KIRO, kiro), (CLAUDE, claude)):
            target = folder / path.name
            if not target.is_file() or target.read_text(encoding="utf-8") != expected:
                problems.append("%s is stale; run python3 tools/build_agents.py"
                                % target.relative_to(ROOT))
    for folder in (KIRO, CLAUDE):
        if folder.is_dir():
            for generated in folder.glob("*.md"):
                if generated.stem not in names:
                    problems.append("%s has no source in agents/src" % generated.relative_to(ROOT))
    return problems


def build() -> int:
    KIRO.mkdir(parents=True, exist_ok=True)
    CLAUDE.mkdir(parents=True, exist_ok=True)
    count = 0
    for path in sources():
        meta, body = parse(path)
        for key in ("name", "description", "access"):
            if not meta.get(key):
                raise ValueError("%s: frontmatter needs %s" % (path.name, key))
        if meta["access"] not in ACCESS:
            raise ValueError("%s: access must be one of %s" % (path.name, ", ".join(sorted(ACCESS))))
        kiro, claude = render(meta, body)
        (KIRO / path.name).write_text(kiro, encoding="utf-8")
        (CLAUDE / path.name).write_text(claude, encoding="utf-8")
        count += 1
    known = {p.stem for p in sources()}
    for folder in (KIRO, CLAUDE):
        for generated in folder.glob("*.md"):
            if generated.stem not in known:
                generated.unlink()
    return count


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="build_agents.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="report problems instead of writing")
    args = ap.parse_args(argv)
    if args.check:
        problems = check()
        for p in problems:
            print("  ERROR %s" % p)
        print("%d agent problem(s)" % len(problems))
        return 1 if problems else 0
    try:
        count = build()
    except ValueError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    problems = check()
    for p in problems:
        print("  ERROR %s" % p)
    print("generated %d agent(s) for Kiro and Claude Code" % count)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
