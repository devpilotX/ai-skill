<!-- lint-exempt: rule-of-three,vocab,vocab-density,chatter,copula-avoidance,significance-padding,vague-attribution,cutoff-disclaimer,section-summary,negative-parallelism,participle-tail -->
# Detector rules

The detector at `scripts/ai_tells.py` (from the repository root,
`python3 skills/human-prose/scripts/ai_tells.py`) has 23 rules, the set named `ALL_RULES` in the script.
This file quotes some of the phrases they match, so it declares exemptions for those rules on its first
line. If the rule count in the script changes, update this table in the same commit.

## Scope and exemptions

The scan runs line by line. Lines inside fenced code blocks (backtick or tilde fences) and inside YAML
frontmatter are skipped by every rule except `artifact`, which runs everywhere because leaked markup is
never intended anywhere.

A file opts out of named rules with an HTML comment on one of its first twenty lines, in the form
`<!-- lint-exempt: rule-of-three,vocab,chatter -->`. The token `all` switches off every rule except `artifact` and
`placeholder`; those two can only be exempted by naming them. The older marker `lint-vocab-exempt` in the
first twenty lines exempts `vocab` and `vocab-density`. There is no per-line exemption. Every exemption is
printed in the report.

Severity decides the exit status: the default fails on high, `--strict` on medium and above, `--pedantic`
on anything.

## Rules

| Rule | Severity | What it matches | Known false positives | How to exempt |
|---|---|---|---|---|
| `artifact` | high | Leaked chatbot markup and tracking parameters: ChatGPT citation and search tokens, Gemini cite and span markers, Grok citation cards, DeepSeek bracket citations, Perplexity file and web markers, chatbot `utm_source` values, a Grok referrer, a document wrapper directive, and wikitext inside a Markdown fence | A document that explains these tokens, such as the catalogue | Name `artifact` explicitly; `all` does not cover it |
| `placeholder` | high | A square-bracketed note starting with insert, add, or your that is not a link; a date with xx for month and day; an HTML comment asking to add something if available; template name brackets; the leftover-task marker in capitals only, not followed by an opening parenthesis; the standard Latin filler text used in typesetting | Prose about a task-tracking feature that writes the marker in capitals; a typography sample using filler text | Name `placeholder` explicitly; better, fill or cut the gap |
| `em-dash` | medium | Any em dash character | Quoted source text that uses one | `em-dash` |
| `en-dash` | medium | An en dash between words | None known; it misses a real one when a digit range with an en dash sits on the same line | `en-dash` |
| `curly-quote` | medium | Curly single or double quotation marks | Quoted material copied from a source that uses them | `curly-quote` |
| `emoji` | medium | Characters in emoji blocks, dingbats, and other symbol characters above U+2100 | Some technical and dingbat symbols outside the excluded letterlike, arrow, and box drawing blocks | `emoji` |
| `thematic-break` | medium | A line of three or more hyphens, asterisks, or underscores | A separator line in prose outside a fence that is not a setext underline | `thematic-break` |
| `title-case-heading` | medium | An ATX heading of three or more words where every significant word after the first is capitalised, ignoring known acronyms and all-caps words | Headings made mostly of product or proper names | `title-case-heading` |
| `x-and-y-heading` | low | A heading of exactly two words joined by and, where one is an evaluative noun such as awards, legacy, impact, or challenges | A technical heading such as impact and mitigation | `x-and-y-heading` |
| `bold-label-list` | low | A list item that opens with a bolded label followed by a colon, with the colon inside or outside the bold | A glossary written as a list | `bold-label-list` |
| `vocab` | low for one hit, medium for repeats | Words and phrases overrepresented in model output, such as delve, crucial, robust, serves as a, when it comes to; also a sentence opening with Additionally (medium) | Literal senses (a robust estimator in statistics), quotations, and paper titles | `vocab`, or `lint-vocab-exempt` |
| `vocab-density` | medium | More than 4.0 overrepresented terms per 1000 words, in files of at least 100 words | Short dense glossaries just over the word floor | `vocab-density`, or `lint-vocab-exempt` |
| `copula-avoidance` | low | serves as, stands as, functions as, represents a, marks a, operates as, refers to | Literal uses: a teacher marks a paper, a symbol represents a value, a footnote refers to a source | `copula-avoidance` |
| `significance-padding` | medium | Claims about broader significance or legacy: reflects a broader, setting the stage for, lasting impact, enduring legacy, and similar | History writing that reports a cited source's judgement | `significance-padding` |
| `vague-attribution` | medium | experts argue, observers have noted, industry reports suggest, critics say, scholars note, many believe, some would argue, it is widely believed; studies show unless a URL follows in the same sentence on the same line | A citation on the next wrapped line, or after an abbreviation with a full stop | `vague-attribution` |
| `chatter` | high, or low for sign-offs | High: I hope this helps, would you like me to, is there anything else I can, here is a breakdown of, great question, as an AI model, certainly or of course followed by an exclamation mark, you are absolutely right. Low: let me know if, feel free to | A real email or issue reply, which is why the sign-offs are low | `chatter` |
| `cutoff-disclaimer` | high | Knowledge cutoff and missing source disclaimers, such as as of my last knowledge update, based on available information, not widely documented | A methodology section that genuinely limits its sources | `cutoff-disclaimer` |
| `section-summary` | medium | Headings named conclusion, summary, final thoughts, future outlook; lines opening with in conclusion, in summary, to sum up, or Overall with a comma; despite its challenges | An executive summary a reader asked for; a review that weighs real limitations | `section-summary` |
| `negative-parallelism` | low | not only X but also Y, it is not just X, it is Y, not merely X but Y, rather than simply, no X, no Y, just Z | A single deliberate contrast in a long document | `negative-parallelism` |
| `participle-tail` | low | A comma followed by one of a fixed set of commentary participles, such as highlighting, ensuring, reflecting, showcasing | Technical instructions where the clause states a real effect | `participle-tail` |
| `rule-of-three` | low | Three lowercase words longer than four letters, each with an adjective suffix, in the form a, b, and c | Noun lists that happen to share the suffixes, such as animal, capital, and metal | `rule-of-three` |
| `trailing-space` | low | Whitespace at the end of a line | A Markdown hard line break made with two trailing spaces | `trailing-space` |
| `final-newline` | low | A file that does not end with a newline | None known | `final-newline` |

## Adding or changing a rule

Add the rule ID to `ALL_RULES`, add a row here, and add a finding case and a false positive case to
`tests/test_ai_tells.py` in the repository. A rule that fires on ordinary human text at high severity is
a bug, not a strict rule.
