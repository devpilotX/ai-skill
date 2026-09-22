---
name: human-prose
description: Write or rewrite text so it reads as human written, with the stylistic residue of machine generation removed. Use when the user asks for writing that sounds human, natural, or not AI generated, asks to remove AI tells, AI slop, AI fingerprints, robotic tone, or ChatGPT style, asks why their text sounds like AI, or wants an article, README, essay, email, blog post, documentation or report cleaned up before publishing. Also use before delivering any long form prose in a project that cares about voice. Runs a working detector at scripts/ai_tells.py that reports em dashes, curly quotes, emoji, title case headings, overrepresented vocabulary, vague attribution, significance padding, negative parallelism, leaked chatbot markup and unfilled placeholders, then rewrites the text rather than only flagging it. Triggers on make this sound human, remove AI tells, does this sound like AI, humanize this, no AI fingerprint, sounds robotic, reads like ChatGPT wrote it.
license: MIT
metadata:
  version: 1.0.0
  suite: ai-skill
---

<!-- lint-exempt: artifact,significance-padding,copula-avoidance,participle-tail -->

# Human prose

This file quotes the patterns it bans, so it declares those four rules as linter exemptions. The
lint report prints them.

Machine written text has a recognisable accent. This skill removes it, then checks the result with a
script instead of trusting a vibe.

## What this skill will not claim

Read this before promising anything to anyone.

Removing the tells does not make text human authored. It changes how the text reads, not where it
came from.

Detection is unreliable in both directions. Wikipedia tells its own editors not to lean on
classifier tools, which have error rates that matter at scale
([WP:AIDETECTION](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)). Untrained human
judgement performs near chance, while people who use these models heavily reach roughly ninety
percent, which still means one wrong call in ten
([Russell, Karpinska and Iyyer, ACL 2025](https://arxiv.org/abs/2501.15654)).

Human and machine writing are converging, partly because people now read a lot of machine text and
absorb its habits. So a clean style check is not proof of anything, and neither is a failed one.

Where authorship has to be disclosed, disclose it. Academic submission, journalism, and Wikipedia
all treat undisclosed generated content as a problem regardless of how the prose reads. Passing this
skill's checks is not permission to skip that, and this skill is not for defeating an academic
integrity process.

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
the exception. Specificity is the hardest thing for a model to fake and the easiest thing for a human
to supply.

Delete significance padding. If no source says this marks a turning point, do not say it does.

### Step 3, fix the sentence mechanics

Full catalogue in `references/tells-catalogue.md`. The short version:

Use plain copulas. Write is, has, and used. Not serves as, features, or utilised.

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

```
python3 scripts/ai_tells.py <files>        # fails on high severity only
python3 scripts/ai_tells.py --strict <f>   # fails on medium too
python3 scripts/ai_tells.py --pedantic <f> # fails on anything
```

High severity findings are near proof of origin: leaked citation markup such as `oaicite` or
`turn0search`, tracking parameters such as `utm_source=chatgpt.com`, unfilled placeholders, text
addressed to the operator, and knowledge cutoff disclaimers. Fix every one, with no exceptions.

Medium severity findings are strong style markers. Fix them unless a specific reason applies, and
state the reason.

Low severity findings are soft patterns that are fine in small numbers. Judge them.

A file whose job is to document these patterns declares per-rule exemptions with an HTML comment
such as `<!-- lint-exempt: vocab,chatter -->` in its first twenty lines. The report prints every
exemption, so an exemption is a visible decision rather than a silent one.

### Step 5, read it aloud

The detector cannot hear rhythm. Read the result out loud. Where you run out of breath, split the
sentence. Where it sounds like a brochure, cut the adjective. Where every sentence has the same
shape, break one.

## Method for rewriting someone else's text

`references/rewrite-method.md` covers working on text you did not write, including how to preserve
an author's voice while removing the residue, and what to do when the underlying content is the
problem rather than the wording.

## Self-audit before delivering

- The detector runs clean at `--strict`, or every remaining finding has a stated reason.
- No sentence survives that would be equally true of a different subject.
- At least one concrete detail appears that only the author could supply.
- Heading case is sentence case throughout.
- No summary section restating what the document already said.
- Every external claim has a link that resolves. Check them, because fabricated citations are the most damaging failure in this category.
- Voice matches the user's existing writing if a sample was available.
