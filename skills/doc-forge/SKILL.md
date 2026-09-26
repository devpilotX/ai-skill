---
name: doc-forge
description: Produce documents a reader can act on, in Markdown and as print ready HTML or PDF. Use when the user asks to write or generate a README, a specification, a report, a proposal, a runbook, a one pager, release notes, a decision record, or documentation, asks to restructure an existing document, or asks to convert Markdown to HTML or PDF. Chooses the document type from what the reader needs to do after reading, puts the decision or answer first, keeps structure flat, and converts with scripts/md2doc.py, which needs no third party packages for HTML and uses an installed engine for PDF. Does not produce DOCX. Applies the human-prose rules to the output. Triggers on write a README, write a spec, write a runbook, write documentation, write a report, one pager, make a PDF, convert markdown to pdf, markdown to html, restructure this document. For choosing an architecture use arch-decide. For the release process itself use release-manage. For editing wording only use human-prose.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Doc forge

The failure this corrects: documents written from the topic outward instead of from the reader's next
action, so the answer sits on page three under an introduction nobody needed, and a converter that is
trusted to produce the same PDF everywhere when it does not. This skill picks the document type from what
the reader must do, writes the shortest thing that lets them do it, and says exactly what the conversion
produced.

## When to use and when to stay off

Run when the user asks for a document of any of the types below, asks to restructure one, or asks to turn
Markdown into HTML or PDF.

Stay off when the user wants only the wording of existing text improved; that goes to `human-prose`. Stay
off for code comments and docstrings, which belong to the code review or the change itself.

Routing. The content of an architecture decision (the options, trade-offs, and reversibility) comes from
`arch-decide`; this skill only lays out the record. How to version, tag, and roll out a release goes to
`release-manage`; this skill writes the notes once the content is known. A CV or cover letter goes to
`job-hunt`.

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of the
session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Answer or recommendation first.
2. No filler sections: no introduction that restates the title, no conclusion that restates the body.
3. Every command is runnable as written, or marked as unverified. Placeholders say what to substitute.
4. No invented facts, figures, versions, or citations. Anything unverified is marked as needing confirmation.
5. Never claim a PDF was produced unless the converter exited 0 and named the engine. Never promise DOCX.
6. Run the `human-prose` detector before delivering, or say it was not available.

## Procedure

### Step 1, name the reader's next action and pick the type

The type follows from what happens after reading. If the next action cannot be named, the document has no
purpose yet. Ask.

The reader needs to install and use software. Write a README. Opening line says what the thing is and who
it is for, then installation, then the smallest working example, then configuration, then where to go for
more. Nothing else above the example.

The reader needs to build something. Write a specification. State the problem, the constraints, the
interfaces, the acceptance criteria, and what is explicitly out of scope.

The reader needs to decide. Write a one pager, or a decision record if the decision is technical and has
already been worked through with `arch-decide`. Recommendation first, options considered, the reasoning,
the cost, the risk, and what would reverse the decision.

The reader needs to fix a live problem at three in the morning. Write a runbook. Numbered steps, exact
commands, expected output after each step, and what to do when it differs. Give it an owner and a last
verified date, put a warning line directly above every destructive command, and give the rollback for each
step that changes state. No background prose.

The reader needs to know what changed. Write release notes. Grouped by what it means to the user, not by
commit. Breaking changes first, with the migration step.

The reader needs to understand a subject. Write an explainer. One idea per section, a concrete example per
idea, and the common misunderstanding named directly.

### Step 2, draft from the skeleton

`references/templates.md` has skeletons for a README, a specification, a decision record, a runbook,
release notes, and a report, each annotated with what goes in every section and the mistake made there.

### Step 3, apply the structure rules

Three heading levels at most. A fourth level means the document should be split.

One idea per section, and the heading says what the idea is. A heading that only contains other headings
gets merged.

Front load every section. The first sentence of a section carries its point.

Prose for reasoning, lists for enumeration, tables for comparison across a shared set of attributes. A
table with one column of real content should be prose.

Code blocks get a language tag.

Link rather than repeat. Duplicated content goes stale in one place and then contradicts itself.

A table of contents earns its place above roughly eight sections, and not below that.

### Step 4, run the prose check

The detector is `ai_tells.py`, part of the `human-prose` skill, not this one. It ships in that skill's
folder, so it runs only when `human-prose` is installed alongside this skill; a standalone install of this
skill does not include it. In this repository, run `python3 ai_tells.py --strict <file>` from inside
`skills/human-prose/scripts/`, giving the file as an absolute path. If `human-prose` is not installed,
apply the rules from that skill by hand and tell the user the detector was not run.

### Step 5, convert

Paths are relative to this skill's folder. From the repository root, use
`python3 skills/doc-forge/scripts/md2doc.py`.

```
python3 scripts/md2doc.py report.md                      # writes report.html
python3 scripts/md2doc.py report.md -o out.html --toc    # with a contents block
python3 scripts/md2doc.py report.md --pdf                # also tries to make a PDF
python3 scripts/md2doc.py a.md b.md -o manual.html --toc # concatenate in order
```

HTML needs no third party packages and is self contained, with embedded print CSS, A4 page rules, and
page break handling that keeps headings with their content. YAML frontmatter is read for the title and
removed from the body. The supported syntax, and what is escaped or ignored, is listed in
`references/markdown-subset.md`.

PDF needs an external engine. The script tries weasyprint, then wkhtmltopdf, then a headless Chromium or
Chrome, then pandoc, with a timeout on each, and reports which one it used. The output differs by engine:

- weasyprint applies the embedded CSS, including the page rules.
- wkhtmltopdf is archived and unmaintained, and its old WebKit ignores CSS custom properties, so borders and colours defined through them drop out, table borders included. Prefer another engine.
- Chromium is run with `--no-pdf-header-footer` so the browser's date, title, and URL lines are not printed. Older builds that do not know the flag may still print them.
- pandoc converts the Markdown source through its own pipeline and ignores this CSS entirely; by default it also needs a TeX engine. The script says so when it falls back to pandoc.

When no engine is available it exits with status 3 and the HTML is still print ready: open it in a
browser and print to PDF, turning off the browser's headers and footers in the print dialog. Do not claim
a PDF was produced when the exit status was 3.

DOCX is not supported. If the user needs Word output and pandoc is installed, run pandoc on the Markdown
directly and say that the print styling does not carry over.

### Step 6, check the output

Open the HTML or PDF and look at it. Check the constructs that are outside the supported subset, the
tables, and the first page.

## Self-audit

- The reader's next action is named, and the type matches it.
- The conclusion or recommendation is in the first few lines.
- No introduction or conclusion that only restates.
- Every command was run, or is marked as unverified.
- A runbook has an owner, a last verified date, warnings above destructive commands, and rollback steps.
- Three heading levels at most, sentence case throughout.
- The `human-prose` detector ran clean at `--strict`, or the reply says it was not available.
- Links resolve.
- The reply names the PDF engine used, or says no PDF was produced.
- Removing any section would lose information. If not, remove it.

## What this cannot do

It cannot guarantee identical PDF output across machines. The result depends on which engine is
installed, and only weasyprint and Chromium apply the embedded CSS closely.

It does not produce DOCX, and it does not convert Markdown outside the subset in
`references/markdown-subset.md`. Raw HTML is escaped, not rendered.

It cannot verify facts, versions, or commands in a document it did not run. Unverified items stay marked.

It does not make legal or regulatory documents compliant. For a privacy notice, terms of service, or a
regulated disclosure, ask a solicitor or attorney: "Does this document meet the disclosure requirements
for a business doing X in jurisdiction Y, and what is missing?"
