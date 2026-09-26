## What changed and why

One paragraph. Name the failure the change corrects, not the files it touches.

## Checks run

Paste the last lines of each.

```
python3 tools/run_tests.py
python3 tools/validate_skills.py
python3 tools/build_agents.py --check
```

## Checklist

- [ ] Every new or changed SKILL.md keeps the required sections and a working off switch.
- [ ] Every new reference or script is mentioned from SKILL.md, so it can load.
- [ ] Changed skills have their metadata version bumped.
- [ ] Every external claim has a source that resolves, or is labelled as an assumption.
- [ ] New script behaviour has a test under `tests/`.
- [ ] Agent changes were made in `agents/src/` and regenerated with `tools/build_agents.py`.
- [ ] `CHANGELOG.md` has an entry under the next version.
