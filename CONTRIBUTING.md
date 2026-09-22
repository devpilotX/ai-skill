# Contributing

## Before you open a pull request

```
python3 tools/validate_skills.py
python3 tests/test_ai_tells.py
python3 tests/test_md2doc.py
```

All three have to pass. CI runs the same commands, so a local failure is a guaranteed CI failure.

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

The description is the only thing loaded at startup, so it does the whole job of matching a request.
Write it with the phrases a user would really use, including the awkward ones. A vague description means
the skill never fires, which is the most common reason a skill appears not to work.

## What a good SKILL.md contains

A short statement of the failure it corrects. Not a description of the topic.

An activation section, and an off switch. A skill that cannot be told to stop becomes nagging.

Non-negotiables, numbered, that override the rest of the file. Keep the list short, because a rule that
gets ignored teaches that every rule is optional.

A procedure in ordered steps, where a later step depends on an earlier one.

A self-audit list at the end, written as checks that can fail.

An honest statement of what the skill cannot do.

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

## Adding a skill to the list

Add a row to the table in the README. The validator checks that every skill appears there and that the
README does not reference a skill that was removed.

## Commit messages

Imperative mood, lowercase, no trailing full stop. Say what changed and why when the why is not obvious.

```
add working capital cycle to business-model
fix autolink consuming trailing punctuation
tighten participle-tail rule to cut false positives on noun lists
```

No generated attribution trailers.
