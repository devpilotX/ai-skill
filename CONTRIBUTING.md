# Contributing

## Before you open a pull request

```
python3 tools/run_tests.py
python3 tools/validate_skills.py
python3 tools/build_agents.py --check
```

All three have to pass. CI runs the same commands on Python 3.9, 3.12 and 3.14, so a local failure is a
guaranteed CI failure. `tools/run_tests.py` runs every `tests/test_*.py`, so a new test file needs no
other wiring.

## Layout of a skill

```
skills/<name>/
  SKILL.md          required
  references/*.md   optional, for anything long
  scripts/*.py      optional, for work that should be deterministic
```

The folder name and the `name` field in the frontmatter have to match. Lowercase letters, digits, and
single hyphens.

## Frontmatter

```
---
name: my-skill
description: One line. This is what decides whether the skill activates, so it must be specific and carry the words a user would actually type. Maximum 1024 characters.
license: MIT
metadata:
  version: 1.0.0
  suite: ai-skill
---
```

`metadata.version` is a semantic version, bumped whenever the skill's instructions change: patch for a
correction, minor for new content, major when the skill's scope or output shape changes. The validator
rejects anything that is not X.Y.Z.

The description is the only thing loaded at startup, so it does the whole job of matching a request.
Write it with the phrases a user would really use, including the awkward ones. A vague description means
the skill never fires, which is the most common reason a skill appears not to work.

## What a good SKILL.md contains

A short statement of the failure it corrects, as the opening paragraph. Not a description of the topic.

`## When to use and when to stay off`: when it runs, when it stays off, which sibling skill takes
overlapping requests, and an off switch sentence containing the word stop. A skill that cannot be told
to stop becomes nagging.

`## Non-negotiables`, numbered, opening with "These override everything else in this file." Keep the
list short, because a rule that gets ignored teaches that every rule is optional.

A procedure in ordered steps, where a later step depends on an earlier one.

`## Self-audit`, written as checks that can fail.

`## What this cannot do`, an honest statement of limits, naming the licensed professional and the exact
question to ask them where one is needed.

The validator fails a SKILL.md that is missing any of the four headings, or whose activation section has
no off switch.

Push anything long into `references/`. The main file stays actionable.

## Rules that apply to every skill in this suite

No fabrication. Numbers are retrieved and cited, or labelled as assumptions with their reasoning.

No manufactured criticism. A clean result gets a short report saying it is clean.

No invented scores. A count of specific defects is honest. A rating out of ten is not.

Consequence over effort when ranking anything.

State what was not covered rather than implying completeness.

Say when a question needs a licensed professional, and give the exact question to ask them.

## House style

[STYLE.md](STYLE.md) is enforced, not advisory. The short version: no em dashes, straight quotes only,
no emoji, sentence case headings, plain copulas, no significance padding, no closing summary, and no
overrepresented vocabulary.

A file that has to enumerate banned patterns declares per rule exemptions on one of its first twenty
lines:

```
<!-- lint-exempt: vocab,chatter -->
```

Exemptions appear in every lint report. Use the fewest rules you can, and only in files whose purpose is
documenting the patterns.

## References have to be reachable

The validator fails if a file in `references/` or `scripts/` is never mentioned, because an unmentioned
file never gets loaded. It also fails if prose mentions a path that does not exist. Mention each file by
its relative path in prose or in a usage example.

## Scripts

No third party packages. These have to run in a clean environment, which is most of their value.

Target Python 3.9, since that is the oldest version CI covers.

Module docstring explaining the usage, a `main` function, and meaningful exit codes.

If a script makes a claim, add a test for it under `tests/`.

## Agents

Agents live in `agents/src/<name>.md`, with frontmatter `name`, `description`, `skills` (comma separated)
and `access` (`read-only` or `read-write`), and the system prompt as the body. Every listed skill must
exist and be named in backticks in the prompt, with when to use it. Run `python3 tools/build_agents.py` to
regenerate `agents/kiro/` and `agents/claude/`; never edit those by hand, because the check fails when
they drift from the source.

## Releases

Add an entry under a new version in `CHANGELOG.md`, then tag `vX.Y.Z` on the default branch and push the
tag. The release workflow runs the checks, builds reproducible zips from the tag, creates the release with
the changelog section as notes, and attaches the zips and `SHA256SUMS.txt`. It fails if the changelog
has no section for the tag.

## Adding a skill to the list

Add a row to the table in the README, linking to `skills/<name>/`. The validator checks that every skill appears there and that the
README does not reference a skill that was removed.

## Commit messages

Imperative mood, lowercase, no trailing full stop. Say what changed and why when the why is not obvious.

```
add working capital cycle to business-model
fix autolink consuming trailing punctuation
tighten participle-tail rule to cut false positives on noun lists
```

No generated attribution trailers.
