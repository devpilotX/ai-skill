---
name: deep-research
description: Research a question with graded sources, reported contradictions, and an account of what could not be established. Use when the user asks to research a topic, find out what is true, what the evidence says, whether there is research on something, find sources for or cite a claim, fact check, gather evidence, write a literature or market review, find the latest version of something, or asks the current state of something. Grades sources for independence, currency and primacy, separates established from inferred from contested, reports disagreement, lists open questions, and states no conclusion a cited source does not support. For judging whether a market or idea is worth pursuing use reality-check, for choosing between technologies use arch-decide, for recomputing numbers use numbers-check. Triggers on research this, is it true that, what does the evidence say, sources for, cite, is there research on, latest version of, current state of, fact check this, literature review, market research.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Deep research

Research answers fail by sounding sourced when they are not: a fluent summary built from recall, with
references that do not exist or do not say what is claimed. This skill produces claims that each trace
to a source and a confidence level, plus an honest list of what is still unknown.

## When to use and when to stay off

Run when the answer depends on evidence the user cannot see yet: current facts, published research,
documentation, filings, or a claim that needs checking.

Stay off, and route instead, when:

- The user wants a verdict on whether a market, product, or idea is worth pursuing. Use `reality-check`, which can call this skill for the facts.
- The question is which technology or architecture to choose. Use `arch-decide`. This skill can supply documented facts about each option.
- The figures are found and the question is whether the arithmetic or statistics hold. Use `numbers-check`.
- The question is a vulnerability or security posture of the user's own system. Use `security-hardening`.
- The answer is stable, well known, and nothing rides on it. Just answer, and say it comes from recall.

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of
the session unless asked again.

## Non-negotiables

These override everything else in this file.

1. No claim without a source you opened. A source is cited by a link that resolves, or, where no stable link exists (books, paywalled standards, court filings), by DOI or ISBN plus page or section. A plausible reference that does not exist is the worst failure here, and it comes from confident recall.
2. With no retrieval tool available, say so at the top, label every claim "unverified recall", and cite nothing from memory. A remembered citation is a guess.
3. Never state a conclusion that no cited source supports. Label anything beyond the sources as inference and show the reasoning.
4. Report contradictions. Two credible sources disagreeing is a finding. Averaging them destroys the information.
5. Date every source and weigh its age against how fast the fact changes, using the currency classes in `references/source-grading.md`.
6. AI search summaries and chatbot answers, including this suite's own output, are tertiary. Use them to find sources, never as the citation.
7. State what could not be established. An unanswered question quietly filled with plausible prose is a fabrication.

## Procedure

### Step 1, turn the question into answerable sub-questions

Break the broad question into sub-questions that each have a findable answer, and identify which one
decides the outcome. State the decomposition before searching so the user can correct the framing.

Set the stop condition now: stop when further searches return no new independent sources for the
deciding sub-question, or when the agreed budget (searches, time, or tokens) is spent. Report which
one ended the search.

### Step 2, search deliberately and keep a log

Search for the primary source, not the article about it: documentation, filings, specifications,
standards, the paper itself, the pricing page, the changelog. Where each kind lives, and query
templates, are in `references/search-playbook.md`.

Search for the counter case on purpose. If the first three results agree, look for someone who
disagrees, and for failure reports rather than announcements. Vary the phrasing, because critics and
vendors use different vocabulary.

Keep a log of every query, the tool used, and the retrieval date. The log goes in the report, so a
reader can rerun the search and see what changed.

Note what you searched for and found nothing on. Absence of evidence in a well searched area is
informative.

### Step 3, read laterally before trusting a source

Before reading a source closely, find out who is behind it by leaving the page and searching for the
publisher and author elsewhere. Use the SIFT moves from Mike Caulfield: Stop, Investigate the source,
Find better coverage, Trace claims to the original. Checklist in `references/search-playbook.md`.

### Step 4, grade every source

Full rubric in `references/source-grading.md`: independence from the outcome, currency against the
volatility of the fact, and primacy.

A vendor on its own product is a primary source for what the product claims and a poor source for
whether it works. Both facts can be used, labelled correctly.

### Step 5, build the claim table

Each claim gets the claim, the source, the date, the grade, and one of four confidence values.

Established: multiple independent sources, or one authoritative primary source, with no credible
contradiction found.

Likely: one good source, or several weak ones agreeing, with no contradiction found.

Contested: credible sources disagree. Present both positions with sources and say which way the
evidence leans, if it leans.

Unknown: searched for and not found. Say where you looked.

### Step 6, synthesise without inventing

Answer the original question using only the claim table. Where it is insufficient, say so.

If the question cannot be settled with available public information, that is the answer. Give the best
available reading, the confidence, and what evidence would settle it, using the "cannot establish"
template in `references/search-playbook.md`.

### Step 7, report

```
ANSWER
Direct answer to the question asked, with its confidence level. Two or three sentences.

WHAT IS ESTABLISHED
Claims with sources and dates.

WHAT IS CONTESTED
Each disagreement, both positions, both sources, and which way the evidence leans.

WHAT I COULD NOT ESTABLISH
Named open questions, with where you looked.

SOURCE GRADES
Each source: link or DOI/ISBN with page, date, independence, primacy, and a one line note on its bias.

SEARCH LOG
Queries run, tool used, retrieval date, and what ended the search.

WHAT WOULD CHANGE THE ANSWER
The evidence that would move the conclusion, and how to obtain it.
```

## How to cite

Cite inline with a link, or DOI or ISBN with page or section. Paraphrase rather than reproducing long
passages, and keep any direct quote short and marked as a quote. Where a licence requires attribution,
name the source and the licence. Note when material was condensed, so a reader knows to check the
original.

## Self-audit

- Every cited source was opened in this session, and every link resolves.
- No claim cites memory; without a retrieval tool, claims are labelled "unverified recall".
- Every claim traces to a listed source.
- Every source has a date, and its age was weighed against the currency class of the fact.
- No AI summary or chatbot answer is used as a citation.
- At least one search was made specifically for the opposing view.
- Lateral reading was done on every source the answer depends on.
- Contradictions are reported rather than reconciled.
- Confidence labels are present and used honestly, including Unknown.
- The search log and the reason the search stopped are in the report.
- No number appears without a source.
- Vendor and interested sources are labelled as such.

## What this cannot do

It cannot reach paywalled, private, or unindexed material, and it cannot confirm that a source is
honest, only who published it and whether others corroborate it. Without a retrieval tool it can only
offer labelled recall.

Research into a regulated question is not advice. Name the professional and the exact question:

- Medical: a licensed physician or pharmacist. "Given my history and current medication, does this evidence apply to me, and what are the risks of acting on it?"
- Legal: a lawyer qualified in the relevant jurisdiction. "In this jurisdiction, on these facts, does this rule or decision apply, and has it been superseded or distinguished since?"
- Financial or tax: a regulated financial adviser or qualified accountant. "Given my circumstances, is this conclusion correct and suitable for me, and what rules for my jurisdiction change it?"
