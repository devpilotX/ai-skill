# Markdown subset supported by md2doc

`scripts/md2doc.py` implements a fixed subset of Markdown with no third party packages. Anything outside
this list is either escaped and shown as text or passed through as a plain paragraph, so check the output
or use pandoc directly. `tests/test_md2doc.py` in the repository checks these constructs.

## Supported

ATX headings, one to six hash marks followed by a space. Headings get stable identifiers for links and the
optional table of contents.

Paragraphs, with consecutive lines joined.

Emphasis: bold with double asterisks, italic with single asterisks, strikethrough with double tildes.
Only asterisk emphasis is recognised.

Inline code in backticks. Its contents are escaped and not processed further.

Fenced code blocks with backtick or tilde fences, with an optional language tag.

Indented code blocks, four spaces or more, outside a list and not directly after a line of paragraph
text.

Links and images with these targets only: `http`, `https`, `mailto`, relative paths, and in-page anchors
starting with `#`. Any other scheme, such as `javascript:` or `data:`, is not turned into a link and is
shown as its source text. Link text, image alt text, titles and URLs are escaped once. A title in quotes
after the URL becomes a `title` attribute.

Autolinks: bare `http` and `https` URLs, and angle bracket autolinks for `http`, `https`, `mailto` and
plain email addresses. Trailing punctuation, and a closing parenthesis with no opener, stay outside the
link, so URLs with balanced parentheses are kept whole.

Unordered lists (`-`, `*`, `+`) and ordered lists (`1.` or `1)`), with nesting by indentation, lazy
continuation lines, and the first number used as the start of an ordered list.

Blockquotes, with consecutive quoted lines joined.

Pipe tables with a header row and a delimiter row. Colons in the delimiter row set left, centre, or right
alignment. A pipe inside a code span, or written as `\|`, does not split a cell.

Horizontal rules, which the house style avoids but the converter supports.

YAML frontmatter at the top of each input file, removed from the body. The title comes from the first
file that has one, unless `-t` is given.

A table of contents with `--toc`, built from h2 and h3 headings when there are at least three of them;
otherwise the converter prints a note and leaves it out.

## Not supported

Raw HTML passthrough. Tags are escaped and shown as text, which is deliberate: a document cannot inject
script into the output.

Footnotes.

Setext headings, the underlined form. Use ATX headings.

Definition lists.

Math, inline or display.

## Output formats

HTML is always produced. PDF depends on an external engine, described in `../SKILL.md`. DOCX is not
supported by the script; if pandoc is installed, run pandoc on the Markdown source directly, knowing the
print CSS does not apply there.

## Command line rules

The output path given with `-o` must end in `.html`, and the converter refuses to write over any input
file. With `--pdf` it tries weasyprint, wkhtmltopdf, a headless Chromium, Chrome or Edge, then pandoc,
each under a time limit, and names the engine it used. Exit status 3 means no engine produced a PDF,
whether none was installed or every one failed; the HTML is still written.
