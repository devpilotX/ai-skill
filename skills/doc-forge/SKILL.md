---
name: doc-forge
description: Produce documents that survive contact with a reader, in Markdown and as print ready HTML or PDF. Use when the user asks to write or generate a document, a README, a specification, a report, a proposal, a runbook, a one pager, release notes, an architecture decision record, or documentation, or asks to convert Markdown to PDF or HTML, or asks to clean up and structure an existing document. Chooses the document type from what the reader needs to do after reading, front loads the decision or answer, keeps structure flat, and converts with scripts/md2doc.py which needs no third party packages and embeds print styling so any browser can produce the PDF. Applies the human-prose rules so the output does not read as machine generated. Triggers on write a README, write a spec, make a PDF, convert markdown to pdf, write documentation, write a report, one pager, runbook, release notes, format this document.
license: MIT
metadata:
  version: 1.0.0
  suite: ai-skill
---

# Doc forge

A document exists so a reader can do something. Decide what that something is, then write the shortest
thing that lets them do it.

## Pick the type from the reader's next action

The type follows from what happens after reading, and getting this wrong is the main reason documents go
unread.

The reader needs to install and use software. Write a README. Opening line says what the thing is and who
it is for, then installation, then the smallest working example, then configuration, then where to go for
more. Nothing else above the example.

The reader needs to build something. Write a specification. State the problem, the constraints, the
interfaces, the acceptance criteria, and what is explicitly out of scope. The out of scope section
prevents more argument than any other part.

The reader needs to decide. Write a one pager or a decision record. Recommendation first, options
considered, the reasoning, the cost, the risk, and what would reverse the decision.

The reader needs to fix a live problem at three in the morning. Write a runbook. Numbered steps, exact
commands, expected output after each step, and what to do when it differs. No prose, no background. A
runbook with explanation in it is a runbook nobody can follow under pressure.

The reader needs to know what changed. Write release notes. Grouped by what it means to the user, not by
commit. Breaking changes first, with the migration step.

The reader needs to understand a subject. Write an explainer. One idea per section, concrete example per
idea, and the common misunderstanding named directly.

If the reader's next action cannot be named, the document does not have a purpose yet. Ask.

## Non-negotiables

1. Answer or recommendation first. A document that makes the reader work for the conclusion loses most readers before it arrives.
2. No filler sections. No introduction that restates the title, no conclusion that restates the body, no "overview" that says the document has sections.
3. Every command is runnable as written, and every code sample is complete enough to execute. Placeholders are marked clearly with what to substitute.
4. No invented facts, figures, versions, or citations. Anything unverified gets marked as needing confirmation.
5. Apply the `human-prose` rules. Sentence case headings, no em dashes, straight quotes, plain copulas, no significance padding. Run the detector before delivering.
6. Length is decided by content. Padding a document to look substantial makes it less likely to be read.

## Structure rules

Flat beats deep. Three heading levels at most. A fourth level means the document should be split.

One idea per section, and the heading says what the idea is. A heading that only contains other headings
gets merged.

Front load every section too, not just the document. The first sentence of a section carries its point.

Prose for reasoning, lists for enumeration, tables for comparison across a shared set of attributes. A
table with one column of real content should be prose. A list of sentences that relate to each other
should be a paragraph.

Code blocks get a language tag so they highlight correctly.

Link rather than repeat. Duplicated content goes stale in one place and then contradicts itself.

A table of contents earns its place above roughly eight sections, and not below that.

## Converting

`scripts/md2doc.py` converts Markdown to self contained HTML with embedded print styling, A4 page rules,
and page break handling that avoids splitting headings from their content.

```
python3 scripts/md2doc.py report.md                      # writes report.html
python3 scripts/md2doc.py report.md -o out.html --toc    # with a contents block
python3 scripts/md2doc.py report.md --pdf                # also tries to make a PDF
python3 scripts/md2doc.py a.md b.md -o manual.html --toc # concatenate in order
```

It needs no third party packages, which is the point: it works in a clean environment. YAML frontmatter
is read for the title and removed from the body.

For PDF it tries weasyprint, then wkhtmltopdf, then a headless Chromium, then pandoc, and reports which
one it used. When none is installed it says so and exits with status 3, and the HTML is still print ready,
so opening it and printing to PDF from a browser gives the same result. Do not claim a PDF was produced
when the exit status was 3.

Supported Markdown covers headings, paragraphs, fenced and indented code, ordered and unordered lists
with one nesting level, blockquotes, pipe tables, horizontal rules, inline code, bold, italic,
strikethrough, links, bare URLs, and images. Anything outside that list needs checking in the output, or
use pandoc directly.

## Reusable shapes

`references/templates.md` has skeletons for a README, a specification, a decision record, a runbook, and
release notes, each annotated with what goes in every section and what commonly gets put there wrongly.

## Self-audit

- The reader's next action is named, and the type matches it.
- The conclusion or recommendation is in the first few lines.
- No introduction or conclusion that only restates.
- Every command was run, or is marked as unverified.
- Three heading levels at most, sentence case throughout.
- The human-prose detector runs clean at `--strict`.
- Links resolve.
- Removing any section would lose information. If not, remove it.
