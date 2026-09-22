---
name: prompt-forge
description: Turn a vague request into a specification that produces a usable result on the first attempt. Use when the user asks to improve, rewrite, optimise, or rate a prompt, asks how to prompt something better, says a model keeps giving them the wrong or generic output, asks for a system prompt, a custom instruction set, or a reusable template, or hands over a prompt and asks what is wrong with it. Also use when a request is too underspecified to act on, since the fix is a better specification rather than a guess. Diagnoses which of six specific defects the prompt has, rewrites it with the missing context, success criteria, output contract, and failure instruction, and states what the rewrite cannot fix. Triggers on improve my prompt, rate my prompt, better prompt, prompt engineering, system prompt, why does the AI keep giving me, make this prompt 10/10, write a prompt for.
license: MIT
metadata:
  version: 1.0.0
  suite: ai-skill
---

# Prompt forge

A prompt is a specification. Most bad output comes from a specification that did not say what good
looks like, and no amount of instruction phrasing repairs a missing requirement.

## The honest framing first

Rating a prompt out of ten is theatre. There is no scale, and any number is invented. What can be
done is checking a prompt against the six defects below and reporting which ones it has. That is
falsifiable, and it tells the user what to change.

So this skill reports defects and a rewrite. If a score is demanded anyway, give the count of defects
remaining out of six and say plainly that this is the only honest version of a score.

## The six defects

Diagnose which apply before rewriting. Name them, because the user should learn to spot them without
help.

1. No success criteria. The prompt says what to make and not how anyone would know it worked. This is the most common defect and the most expensive.
2. Missing context that only the user has. Audience, constraints, existing decisions, what was already tried, what the surrounding system looks like. Without it the answer regresses to the generic case, which is the complaint that usually brought them here.
3. No output contract. Format, length, structure, and what to leave out are unspecified, so the reply arrives in a shape that needs manual reworking.
4. Multiple requests fused into one. Three tasks in one sentence produce a shallow pass at each. Splitting is usually the whole fix.
5. No failure instruction. The prompt does not say what to do when the model does not know, cannot comply, or finds the request contradictory. The default is to guess fluently, which is the worst option.
6. Leading or flattering framing. A prompt that signals the desired answer gets it. "Explain why this architecture is the right choice" is a request for advocacy, not analysis.

## Procedure

### Step 1, find the real goal

Ask what the output gets used for. The answer usually changes the prompt more than any phrasing
change. A summary for a decision meeting and a summary for a search index share no requirements.

If the goal is unclear, ask at most three questions. Never rewrite a prompt while guessing what it is
for.

### Step 2, extract what only the user knows

This is the step that produces a non-generic result, and it is the step usually skipped. Pull out the
constraints, the audience, the prior attempts, the things that are fixed and cannot change, and the
things that are explicitly out of scope.

Anything the model could not infer belongs in the prompt. Anything the model can infer is padding and
comes out.

### Step 3, write the success criteria

Write them before the instruction, because they determine it. Good criteria are checkable by someone
who did not write them.

Weak: "write a good landing page". Checkable: "a visitor who sells car parts should be able to tell in
one sentence whether this product handles their VAT case, and the page must not claim any feature not
in the attached list".

### Step 4, rewrite in the six part shape

Role and audience, only if it changes the answer. Skip decorative personas, since claiming expertise
does not create it.

Task, one goal per prompt.

Context, the facts only the user has.

Constraints, including what to leave out, which is more useful than it looks.

Output contract, the exact shape wanted, with an example if the shape is unusual.

Failure instruction, what to do on uncertainty. The sentence that earns its place in almost every
prompt: state uncertainty rather than filling the gap, and name what additional information would
resolve it.

Patterns for specific job types, including extraction, code generation, review, and long research
tasks, are in `references/patterns.md`.

### Step 5, remove what does not work

Politeness, threats, offers of payment, and instructions to think hard do not reliably change quality,
and they consume attention. Cut them.

Instructions that restate the model's defaults are noise. "Be accurate" changes nothing.

Negations are weaker than positive instructions. Rather than saying not to be verbose, give a length.

Long preambles about importance bury the actual request. Put the request first.

### Step 6, state the limits of the rewrite

A better prompt cannot supply facts the model does not have, cannot make a stylistic preference
objective, and cannot prevent confident errors on questions outside the model's knowledge. Say which
of those apply, and say what tooling would fix it, usually retrieval, a test, or a human check.

## Output shape

```
DEFECTS FOUND
[Which of the six, each in one line, quoting the part of the prompt at fault]

REWRITE
[The new prompt, ready to copy]

WHAT I HAD TO ASSUME
[Every assumption made in the rewrite, so the user can correct it]

WHAT THIS STILL WILL NOT FIX
[Limits that a prompt cannot address]
```

## Self-audit

- Each of the six defects was considered, not just the obvious one.
- The rewrite contains at least one fact that only this user could have supplied. If not, the context step was skipped and the result will be generic.
- Success criteria are checkable by a third party.
- Exactly one task per prompt, or the split is explicit.
- A failure instruction is present.
- Every assumption is listed rather than buried in the rewrite.
- No invented score. Defect count only.
