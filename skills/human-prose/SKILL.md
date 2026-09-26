---
name: human-prose
description: Edit or write text so it reads as written by a person, with the residue of machine generation removed. Use when the user asks to edit my draft, proofread, tighten this, make it sound natural, remove AI tells, AI slop, robotic tone or ChatGPT style, asks why their text sounds like AI, or wants an article, README, essay, email, blog post, documentation or report cleaned up before publishing. Runs a working detector at scripts/ai_tells.py that reports em dashes, curly quotes, title case headings, overrepresented vocabulary, vague attribution, significance padding, leaked chatbot markup and unfilled placeholders, then rewrites the text. Never fabricates specifics and never claims text is undetectable. Triggers on edit my draft, proofread this, tighten this, make this sound human, remove AI tells, does this sound like AI, humanize this, sounds robotic, reads like ChatGPT wrote it. For choosing a document type, structure or PDF conversion use doc-forge. For CVs and cover letters use job-hunt.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

<!-- lint-exempt: artifact,chatter,vocab,significance-padding,copula-avoidance,participle-tail -->

# Human prose

This file quotes the patterns it bans, and cites a paper whose title contains a flagged word, so it
declares those rules as linter exemptions. The lint report prints them.

The failure this corrects: text that says nothing specific in a recognisable machine accent, and an
editor that fixes it by vibe, so the accent survives and hollow sentences get polished instead of cut.
This skill removes the residue, adds facts only the author can supply, and checks the result with a
script.

## When to use and when to stay off

Run when the user asks to edit, proofread, tighten, or clean up prose, asks why text reads as machine
written, or hands over a draft to publish: an article, README, essay, email, post, documentation, or
report.

Stay off when the text is code, data, a legal or contractual document whose exact wording carries
obligations, or a quotation that has to stay verbatim. Stay off when the user asks only for a factual
check or a translation.

Stay off, and say why, when the goal is to pass off generated text as the user's own work where
authorship must be disclosed, such as coursework, exams, journal submission, or Wikipedia. See
non-negotiable 3.

Routing. Choosing the document type, its structure, and converting it to HTML or PDF goes to
`doc-forge`, which applies these rules to its output. CVs, cover letters, and applications go to
`job-hunt`. Rewriting a prompt for a model goes to `prompt-forge`.

The user says "stop", "leave my wording alone", or "just execute": comply at once and stay off for the
rest of the session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Never fabricate specifics. The number, date, name, or incident added in step 2 comes from the user or a cited source. If it is missing, ask or mark the gap; never invent a plausible one.
2. Never claim the text is undetectable, human authored, or safe from a detector. The skill changes how text reads, not where it came from.
3. Refuse academic integrity evasion, and say so plainly. Where authorship or tool use has to be disclosed, the answer is to disclose it.
4. Every external claim keeps a link that resolves, or loses the claim. Open each link.
5. Deliver only text that passes the detector at high severity. A draft handed back for the author to fill is labelled as a draft.

## Procedure

### Step 1, read the target and decide the voice

Ask who writes this and who reads it. A README for developers, a landing page, a personal essay, and
a maintenance log have four different registers, and the generic register is the tell that matters
most.

If the user has existing writing, read it first and match it. Sentence length, contraction habits,
whether they use lists, how formal they are. Matching a real sample beats any rule in this file.

### Step 2, rewrite for substance before style

Most of what reads as machine text is not word choice. It is the absence of specifics.

Replace evaluation with fact. "A leading provider of innovative solutions" carries nothing. "Sells
brake pads to 40 independent garages in Ohio" carries everything.

Cut any sentence that would be true of a different subject. This is the same swap test used in
`reality-check`, applied to prose.

Add the detail only the writer would know: the number, the date, the name, the thing that went wrong,
the exception. Get it from the user. Where they have not supplied it yet, mark the gap with a short
square-bracketed note starting with the word insert, as below. The detector reports that shape as a
high severity placeholder, so a marked draft cannot pass as finished by accident.

```
Cut the monthly hosting bill from [insert old figure] to [insert new figure].
```

Keep each marker under forty characters so the detector sees it, and hand back the list of markers as
questions the author can answer in a sentence each.

Delete significance padding. If no source says this marks a turning point, do not say it does.

### Step 3, fix the sentence mechanics

Full catalogue in `references/tells-catalogue.md`. The short version:

Use plain copulas. Write is, has, and used. Not serves as, features, or the latinate stand-in for used.

Kill em dashes. Use a comma, a colon, parentheses, or two sentences.

Straight quotes and apostrophes only.

Vary sentence length on purpose, and let some sentences be short.

Repeat a word when it is the right word, rather than rotating synonyms.

Cut the participle tails. A sentence ending in ", highlighting the importance of quality" is adding
commentary, not information.

Use negative parallelism once per document at most.

Break the three item rhythm when only two things are true.

Sentence case headings.

### Step 4, run the detector

The script path is relative to this skill's folder. From inside `skills/human-prose/`:

```
python3 scripts/ai_tells.py <files>             # fails on high severity only
python3 scripts/ai_tells.py --strict <files>    # fails on medium too
python3 scripts/ai_tells.py --pedantic <files>  # fails on anything
```

From the repository root, use `python3 skills/human-prose/scripts/ai_tells.py --strict <files>`. With no
file arguments it reads stdin. Exit status 0 means nothing at or above the threshold, 1 means findings,
2 means a usage error or a path that could not be read.

The detector has 23 rules. Each rule's severity, what it matches, its known false positives, and how to
exempt it are in `references/detector-rules.md`.

High severity findings almost never belong in a finished document: leaked citation markup such as
`oaicite` or `turn0search`, tracking parameters such as `utm_source=chatgpt.com`, unfilled placeholders
outside code blocks (the leftover-task marker only when written in capitals), text addressed to the
operator such as "I hope this helps", and knowledge cutoff disclaimers. Fix every one.

Medium severity findings are strong style markers. Fix them unless a specific reason applies, and
state the reason.

Low severity findings are soft patterns that are fine in small numbers. Judge them. Sign-off phrases
such as "let me know if" and "feel free to" are low, because they are normal in an email and a tell only
when they close a document addressed to a reader.

A file whose job is to document these patterns declares per-rule exemptions with an HTML comment
such as `<!-- lint-exempt: vocab,chatter -->` in its first twenty lines. The report prints every
exemption, so an exemption is a visible decision rather than a silent one.

### Step 5, read it aloud

The detector cannot hear rhythm. Read the result out loud. Where you run out of breath, split the
sentence. Where it sounds like a brochure, cut the adjective. Where every sentence has the same
shape, break one.

### Rewriting someone else's text

`references/rewrite-method.md` covers working on text you did not write, including how to preserve
an author's voice while removing the residue, and what to do when the underlying content is the
problem rather than the wording.

## Self-audit

- The detector runs clean at `--strict`, or every remaining finding has a stated reason.
- No specific detail was invented. Each one traces to the user or a cited source.
- Any unfilled gap is still marked, and the output is labelled as a draft with the questions attached.
- No sentence survives that would be equally true of a different subject.
- At least one concrete detail appears that only the author could supply.
- Heading case is sentence case throughout.
- No summary section restating what the document already said.
- Every external claim has a link that resolves, and each was opened.
- Voice matches the user's existing writing if a sample was available.
- Nothing in the reply claims the text is undetectable or human authored.

## What this cannot do

Removing the tells does not make text human authored. It changes how the text reads, not where it
came from.

Detection is unreliable in both directions, and this skill cannot tell you whether a given reader or
tool will flag the text. Wikipedia tells its own editors not to lean on classifier tools
([WP:AIDETECTION](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)). Readers who rarely use
these models perform close to chance, while people who frequently use ChatGPT for writing are far
better: in Russell, Karpinska and Iyyer, "People who frequently use ChatGPT for writing tasks are
accurate and robust detectors of AI-generated text" ([arXiv 2501.15654](https://arxiv.org/abs/2501.15654)),
the majority vote of five such expert annotators misclassified only 1 of 300 articles. A panel of
experienced readers is a much stronger check than this detector.

Human and machine writing are converging, partly because people now read a lot of machine text and
absorb its habits. So a clean style check is not proof of anything, and neither is a failed one.

The detector matches patterns line by line. It cannot judge rhythm, voice, or whether a claim is true,
and every rule has false positives listed in `references/detector-rules.md`.

It does not decide disclosure obligations. Where a course, publisher, or employer has a policy on AI
assistance, ask the person who sets it: "Does using an AI tool to edit wording, without generating the
content, need to be disclosed under this policy, and if so, where and how?"
