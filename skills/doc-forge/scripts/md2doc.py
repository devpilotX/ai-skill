#!/usr/bin/env python3
"""Convert Markdown to print ready HTML, and to PDF when an engine is available.

The HTML output needs only the standard library. It is self contained, with
embedded CSS and A4 page rules, so any browser can print it to PDF. With --pdf the
script tries, in this order: weasyprint, wkhtmltopdf, a headless Chromium, Chrome
or Edge, then pandoc. Each runs under a timeout, and the script prints which
engine produced the PDF. pandoc converts the Markdown sources itself and ignores
the print CSS.

Supported Markdown, listed in full in ../references/markdown-subset.md:
  ATX headings (closing hashes are stripped), paragraphs, fenced code with
  backtick or tilde fences, indented code (four spaces, outside lists), ordered
  and unordered lists with nesting, lazy continuation lines and a start number,
  blockquotes, pipe tables with alignment, horizontal rules, inline code, bold,
  italic, strikethrough, links, images, and autolinks (bare and in angle
  brackets). Link and image targets are limited to http, https, mailto, relative
  paths and #anchors; anything else is shown as text. Raw HTML is escaped. YAML
  frontmatter is read for the title and removed from the body.

Usage:
  python3 md2doc.py input.md                    # writes input.html
  python3 md2doc.py input.md -o out.html --toc  # adds a table of contents
  python3 md2doc.py input.md --pdf              # also tries to produce a PDF
  python3 md2doc.py a.md b.md -o combined.html  # concatenates in order

Exit status: 0 success, 2 usage or input error, 3 --pdf given and no engine
produced a PDF (the HTML is still written).
"""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CSS = """
:root { --ink: #1a1a1a; --muted: #565656; --rule: #d6d6d6; --bg: #ffffff; }
* { box-sizing: border-box; }
body {
  font-family: Georgia, "Times New Roman", serif;
  font-size: 11.5pt; line-height: 1.55; color: var(--ink); background: var(--bg);
  margin: 0 auto; padding: 2.2rem 1.4rem; max-width: 46rem;
  text-rendering: optimizeLegibility;
}
h1, h2, h3, h4 {
  font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
  line-height: 1.25; margin: 1.8em 0 0.6em; page-break-after: avoid;
}
h1 { font-size: 1.9em; margin-top: 0; }
h2 { font-size: 1.38em; border-bottom: 1px solid var(--rule); padding-bottom: 0.22em; }
h3 { font-size: 1.12em; }
h4 { font-size: 1em; color: var(--muted); }
p, ul, ol, blockquote, table, pre { margin: 0 0 0.9em; }
ul, ol { padding-left: 1.5em; }
li { margin: 0.2em 0; }
li > ul, li > ol { margin: 0.25em 0 0.35em; }
a { color: #0b4fa8; text-decoration: underline; }
code {
  font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  font-size: 0.88em; background: #f2f2f2; padding: 0.1em 0.32em; border-radius: 3px;
}
pre {
  background: #f7f7f7; border: 1px solid #e3e3e3; border-radius: 4px;
  padding: 0.8em 0.95em; overflow-x: auto; page-break-inside: avoid;
}
pre code { background: none; padding: 0; font-size: 0.84em; }
blockquote {
  margin-left: 0; padding: 0.15em 0 0.15em 1em;
  border-left: 3px solid var(--rule); color: var(--muted);
}
table { border-collapse: collapse; width: 100%; font-size: 0.95em; page-break-inside: avoid; }
th, td { border: 1px solid var(--rule); padding: 0.45em 0.6em; text-align: left; vertical-align: top; }
th { background: #f4f4f4; font-weight: 600; }
hr { border: 0; border-top: 1px solid var(--rule); margin: 1.6em 0; }
img { max-width: 100%; }
.toc { background: #fafafa; border: 1px solid var(--rule); border-radius: 4px; padding: 0.9em 1.2em; }
.toc-title {
  font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
  font-weight: 600; margin-bottom: 0.4em;
}
.toc ul { list-style: none; padding-left: 0; margin: 0; }
.toc ul ul { padding-left: 1.1em; }
@page { size: A4; margin: 19mm 17mm; }
@media print {
  body { padding: 0; max-width: none; font-size: 10.5pt; }
  a { color: var(--ink); }
  a[href^="http"]::after { content: " (" attr(href) ")"; font-size: 0.78em; color: var(--muted); }
  h1, h2 { page-break-after: avoid; }
  .no-print { display: none; }
}
"""

# Seconds any external PDF engine may run before it is stopped.
PDF_TIMEOUT = 120

SAFE_SCHEMES = ("http", "https", "mailto")
TOC_MIN_ENTRIES = 3

# Inline patterns. Code spans use a run of backticks closed by a run of the same length.
CODE_SPAN = re.compile(r"(`+)(.+?)(?<!`)\1(?!`)")
BOLD = re.compile(r"\*\*([^*]+)\*\*")
ITALIC = re.compile(r"(?<![*\w])\*([^*\n]+)\*(?!\*)")
STRIKE = re.compile(r"~~([^~]+)~~")
ANGLE_URL = re.compile(r"<((?:https?|mailto):[^\s<>\x00]+)>", re.I)
ANGLE_EMAIL = re.compile(r"<([^\s<>@\x00:/]+@[^\s<>@\x00]+\.[A-Za-z]{2,})>")
BARE_URL = re.compile(r"(?<![\w/])https?://[^\s<>\"\x00]+", re.I)
SLOT = re.compile(r"\x00(\d+)\x00")
URL_SCHEME = re.compile(r"([a-z][a-z0-9+.\-]*):")
URL_IGNORED = re.compile(r"[\x00-\x20\x7f-\x9f]")

# Block patterns.
FENCE_OPEN = re.compile(r"^( {0,3})(`{3,}|~{3,})(.*)$")
LIST_ITEM = re.compile(r"^( *)([-*+]|(\d{1,9})[.)])[ \t]+(\S.*)$")
ATX = re.compile(r"^(#{1,6})[ \t]+(.*?)[ \t]*$")
HRULE = re.compile(r"(-{3,}|\*{3,}|_{3,})")
DELIM_CELL = re.compile(r":?-+:?")


# ---------------------------------------------------------------- small helpers

def normalise_newlines(text: str) -> str:
    """Drop a byte order mark and turn CRLF or lone CR line endings into LF."""
    if text.startswith("\ufeff"):
        text = text[1:]
    return text.replace("\r\n", "\n").replace("\r", "\n")


def expand_indent(line: str) -> str:
    """Expand tabs in the leading whitespace only, at a tab width of four."""
    lead = len(line) - len(line.lstrip(" \t"))
    return line[:lead].expandtabs(4) + line[lead:]


def indent_width(line: str) -> int:
    expanded = expand_indent(line)
    return len(expanded) - len(expanded.lstrip(" "))


def warn(message: str) -> None:
    print("md2doc: warning: %s" % message, file=sys.stderr)


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-{2,}", "-", s) or "section"


def safe_url(url: str) -> bool:
    """True when the URL is http, https, mailto, relative, or an in-page anchor.

    The check runs on the entity decoded URL with every control character and
    space removed and the case folded, because browsers ignore those when they
    read the scheme, so " JaVa\\tScRiPt:" and "&#106;avascript:" are both caught.
    """
    probe = URL_IGNORED.sub("", url).lower()
    m = URL_SCHEME.match(probe)
    if m:
        return m.group(1) in SAFE_SCHEMES
    return True


# ---------------------------------------------------------------- inline markup

def _match_bracket(text: str, open_at: int) -> int | None:
    """Index of the ] that closes the [ at open_at, allowing nested brackets."""
    depth = 0
    k = open_at
    while k < len(text):
        ch = text[k]
        if ch == "\\" and k + 1 < len(text):
            k += 2
            continue
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return k
        k += 1
    return None


def _parse_target(text: str, k: int) -> tuple[str, str | None, int] | None:
    """Parse "url" or "url "title"" after the ( at k-1. Returns url, title, end."""
    n = len(text)
    while k < n and text[k] in " \t":
        k += 1
    if k < n and text[k] == "<":
        end = text.find(">", k + 1)
        if end == -1 or "<" in text[k + 1:end]:
            return None
        url = text[k + 1:end]
        k = end + 1
    else:
        start, depth = k, 0
        while k < n:
            ch = text[k]
            if ch == "\\" and k + 1 < n:
                k += 2
                continue
            if ch.isspace():
                break
            if ch == "(":
                depth += 1
            elif ch == ")":
                if depth == 0:
                    break
                depth -= 1
            k += 1
        if depth:
            return None
        url = text[start:k]
    if "\x00" in url:
        return None
    while k < n and text[k] in " \t":
        k += 1
    title = None
    if k < n and text[k] in "\"'":
        end = text.find(text[k], k + 1)
        if end == -1:
            return None
        title = text[k + 1:end]
        k = end + 1
        while k < n and text[k] in " \t":
            k += 1
    if k < n and text[k] == ")":
        return url, title, k + 1
    return None


def _resolve(text: str, slots: list[str]) -> str:
    while "\x00" in text:
        text = SLOT.sub(lambda m: slots[int(m.group(1))], text)
    return text


def _plain(text: str, slots: list[str]) -> str:
    """Plain text of already converted inline markup, for alt text and slugs."""
    return html.unescape(re.sub(r"<[^>]*>", "", _resolve(text, slots)))


def _trim_url(url: str) -> str:
    """Drop trailing punctuation, and closing brackets that have no opener."""
    while url:
        last = url[-1]
        if last in ".,;:!?*_~'\"":
            url = url[:-1]
        elif last == ")" and url.count(")") > url.count("("):
            url = url[:-1]
        elif last == "]" and url.count("]") > url.count("["):
            url = url[:-1]
        else:
            break
    return url


def _inline(text: str, slots: list[str], links: bool) -> str:
    """Convert inline markup, parking finished HTML in slots behind placeholders."""
    def put(fragment: str) -> str:
        slots.append(fragment)
        return "\x00%d\x00" % (len(slots) - 1)

    def code(m: re.Match) -> str:
        body = m.group(2)
        if len(body) >= 2 and body[0] == body[-1] == " " and body.strip():
            body = body[1:-1]
        return put("<code>%s</code>" % html.escape(body, quote=False))

    text = CODE_SPAN.sub(code, text)

    # Links and images, parsed from the raw text so every part is escaped once.
    parts: list[str] = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        is_image = ch == "!" and text.startswith("[", i + 1)
        if ch == "[" or is_image:
            open_at = i + 1 if is_image else i
            close = _match_bracket(text, open_at)
            if (close is not None and (links or is_image)
                    and text.startswith("(", close + 1)):
                target = _parse_target(text, close + 2)
                if target:
                    url, title, end = target
                    url = html.unescape(url).strip()
                    label = text[open_at + 1:close]
                    source = text[i:end]
                    if not safe_url(url):
                        # Shown as the literal source text, never as a link or image.
                        parts.append(put(html.escape(source, quote=False)))
                    else:
                        attr_title = (' title="%s"' % html.escape(html.unescape(title), quote=True)
                                      if title else "")
                        if is_image:
                            alt = _plain(_inline(label, slots, links=False), slots)
                            parts.append(put('<img src="%s" alt="%s"%s>' % (
                                html.escape(url, quote=True), html.escape(alt, quote=True),
                                attr_title)))
                        else:
                            parts.append(put('<a href="%s"%s>%s</a>' % (
                                html.escape(url, quote=True), attr_title,
                                _inline(label, slots, links=False))))
                    i = end
                    continue
            parts.append(ch)
            i += 1
            continue
        parts.append(ch)
        i += 1
    text = "".join(parts)

    if links:
        def anchor(href: str, shown: str) -> str:
            return put('<a href="%s">%s</a>' % (html.escape(href, quote=True),
                                                html.escape(shown, quote=False)))

        text = ANGLE_URL.sub(lambda m: anchor(m.group(1), m.group(1)), text)
        text = ANGLE_EMAIL.sub(lambda m: anchor("mailto:" + m.group(1), m.group(1)), text)

        def bare(m: re.Match) -> str:
            url = _trim_url(m.group(0))
            if not re.match(r"https?://[^/]", url, re.I):
                return m.group(0)
            return anchor(url, url) + m.group(0)[len(url):]

        text = BARE_URL.sub(bare, text)

    text = html.escape(text, quote=False)
    text = BOLD.sub(r"<strong>\1</strong>", text)
    text = ITALIC.sub(r"<em>\1</em>", text)
    text = STRIKE.sub(r"<del>\1</del>", text)
    return text


def inline(text: str) -> str:
    """Convert inline markup to HTML. Code spans are escaped and not processed further."""
    slots: list[str] = []
    return _resolve(_inline(text.replace("\x00", ""), slots, links=True), slots)


def plain_text(text: str) -> str:
    """The visible text of inline markup: link text without its URL, no tags."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", "", inline(text)))).strip()


# ---------------------------------------------------------------- frontmatter

def split_frontmatter(text: str) -> tuple[dict, str]:
    """Split YAML frontmatter from the body.

    The block opens with a line that is exactly --- and closes at the next line
    that is exactly --- (trailing spaces allowed). Without a closing line the
    text is returned unchanged.
    """
    text = normalise_newlines(text)
    meta: dict = {}
    lines = text.split("\n")
    if lines[0].rstrip(" \t") != "---":
        return meta, text
    for j in range(1, len(lines)):
        if lines[j].rstrip(" \t") == "---":
            break
    else:
        return meta, text
    for line in lines[1:j]:
        if ":" in line and not line.startswith((" ", "\t", "#")):
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip("'\"")
    rest = "\n".join(lines[j + 1:])
    return meta, rest.lstrip("\n")


# ---------------------------------------------------------------- tables

def split_row(row: str) -> list[str]:
    """Split a table row on pipes, ignoring pipes in code spans and escaped \\|."""
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|") and not row.endswith("\\|"):
        row = row[:-1]
    cells: list[str] = []
    cur: list[str] = []
    i, n = 0, len(row)
    while i < n:
        ch = row[i]
        if ch == "\\" and i + 1 < n and row[i + 1] == "|":
            cur.append("|")
            i += 2
        elif ch == "`":
            run = len(row[i:]) - len(row[i:].lstrip("`"))
            closing = re.compile(r"(?<!`)`{%d}(?!`)" % run).search(row, i + run)
            if closing:
                cur.append(row[i:closing.end()].replace("\\|", "|"))
                i = closing.end()
            else:
                cur.append("`" * run)
                i += run
        elif ch == "|":
            cells.append("".join(cur).strip())
            cur = []
            i += 1
        else:
            cur.append(ch)
            i += 1
    cells.append("".join(cur).strip())
    return cells


def delimiter_alignments(line: str) -> list[str | None] | None:
    """Alignments from a delimiter row, or None if the line is not one."""
    stripped = line.strip()
    if not stripped or not set(stripped) <= set("|:- \t"):
        return None
    cells = split_row(stripped)
    aligns: list[str | None] = []
    for cell in cells:
        if not DELIM_CELL.fullmatch(cell):
            return None
        if cell.startswith(":") and cell.endswith(":") and len(cell) > 1:
            aligns.append("center")
        elif cell.endswith(":"):
            aligns.append("right")
        elif cell.startswith(":"):
            aligns.append("left")
        else:
            aligns.append(None)
    return aligns


def table_rows(lines: list[str], start: int) -> tuple[str, int]:
    """Render a pipe table starting at start. Returns html and the next index."""
    header = split_row(lines[start])
    aligns = delimiter_alignments(lines[start + 1]) or [None] * len(header)
    width = len(header)
    i = start + 2
    body: list[list[str]] = []
    while i < len(lines) and "|" in lines[i] and lines[i].strip():
        row = split_row(lines[i])
        body.append((row + [""] * width)[:width])
        i += 1

    def cell(tag: str, text: str, col: int) -> str:
        style = ' style="text-align: %s"' % aligns[col] if aligns[col] else ""
        return "<%s%s>%s</%s>" % (tag, style, inline(text), tag)

    out = ["<table>", "<thead><tr>"]
    out += [cell("th", c, k) for k, c in enumerate(header)]
    out.append("</tr></thead>")
    if body:
        out.append("<tbody>")
        for row in body:
            out.append("<tr>" + "".join(cell("td", c, k) for k, c in enumerate(row)) + "</tr>")
        out.append("</tbody>")
    out.append("</table>")
    return "\n".join(out), i


def is_table_start(lines: list[str], i: int) -> bool:
    if i + 1 >= len(lines) or "|" not in lines[i]:
        return False
    header = split_row(lines[i])
    if len(header) < 2 and not lines[i].strip().startswith("|"):
        return False
    aligns = delimiter_alignments(lines[i + 1])
    return aligns is not None and len(aligns) == len(header)


# ---------------------------------------------------------------- blocks

def convert(md: str, headings: list[tuple[int, str, str]],
            source: str = "<input>", line_offset: int = 0) -> str:
    """Convert a Markdown body to HTML. Headings found are appended to headings as
    (level, plain text, slug); slugs stay unique across calls sharing the list."""
    lines = normalise_newlines(md).split("\n")
    n = len(lines)
    out: list[str] = []
    para: list[str] = []
    # One entry per open list: kind, marker indent, pending item text, and
    # whether the item's opening <li> has already been written.
    stack: list[dict] = []
    i = 0

    def flush_para() -> None:
        if para:
            out.append("<p>%s</p>" % inline(" ".join(para).strip()))
            para.clear()

    def emit_item(level: dict) -> None:
        if not level["emitted"]:
            out.append("<li>%s" % inline(" ".join(level["text"]).strip()))
            level["emitted"] = True

    def close_item(level: dict) -> None:
        if level["emitted"]:
            out.append("</li>")
        else:
            out.append("<li>%s</li>" % inline(" ".join(level["text"]).strip()))
        level["text"], level["emitted"] = [], False

    def open_list(kind: str, indent: int, start: int, text: str) -> None:
        if kind == "ol" and start != 1:
            out.append('<ol start="%d">' % start)
        else:
            out.append("<%s>" % kind)
        stack.append({"kind": kind, "indent": indent, "text": [text], "emitted": False})

    def close_level() -> None:
        level = stack.pop()
        close_item(level)
        out.append("</%s>" % level["kind"])

    def close_blocks() -> None:
        flush_para()
        while stack:
            close_level()

    while i < n:
        line = lines[i]
        stripped = line.strip()
        expanded = expand_indent(line)
        indent = len(expanded) - len(expanded.lstrip(" "))

        fence = FENCE_OPEN.match(expanded)
        if fence and not (fence.group(2)[0] == "`" and "`" in fence.group(3)):
            close_blocks()
            pad, marker = len(fence.group(1)), fence.group(2)
            info = fence.group(3).strip()
            lang = info.split()[0] if info else ""
            closing = re.compile(r"^ {0,3}%s{%d,}[ \t]*$" % (re.escape(marker[0]), len(marker)))
            opened_at = i
            i += 1
            buf: list[str] = []
            closed = False
            while i < n:
                if closing.match(expand_indent(lines[i])):
                    closed = True
                    i += 1
                    break
                body = lines[i]
                drop = 0
                while drop < pad and drop < len(body) and body[drop] == " ":
                    drop += 1
                buf.append(body[drop:])
                i += 1
            if not closed:
                while buf and not buf[-1].strip():
                    buf.pop()
                warn("%s:%d: code fence %s is never closed; it runs to the end of the document"
                     % (source, opened_at + 1 + line_offset, marker))
            cls = ' class="language-%s"' % html.escape(lang, quote=True) if lang else ""
            out.append("<pre><code%s>%s</code></pre>"
                       % (cls, html.escape("\n".join(buf), quote=False)))
            continue

        if not stripped:
            flush_para()
            if stack:
                k = i + 1
                while k < n and not lines[k].strip():
                    k += 1
                if k >= n or not LIST_ITEM.match(expand_indent(lines[k])):
                    close_blocks()
            i += 1
            continue

        if indent >= 4 and not para and not stack:
            buf = []
            while i < n:
                if not lines[i].strip():
                    buf.append("")
                elif indent_width(lines[i]) >= 4:
                    buf.append(expand_indent(lines[i])[4:])
                else:
                    break
                i += 1
            while buf and not buf[-1]:
                buf.pop()
            out.append("<pre><code>%s</code></pre>" % html.escape("\n".join(buf), quote=False))
            continue

        heading = ATX.match(stripped) if indent < 4 else None
        if heading:
            close_blocks()
            level = len(heading.group(1))
            body = re.sub(r"(?:^|[ \t]+)#+$", "", heading.group(2)).strip()
            text = plain_text(body)
            slug = base = slugify(text)
            existing = {h[2] for h in headings}
            count = 2
            while slug in existing:
                slug = "%s-%d" % (base, count)
                count += 1
            headings.append((level, text, slug))
            out.append('<h%d id="%s">%s</h%d>' % (level, slug, inline(body), level))
            i += 1
            continue

        if indent < 4 and HRULE.fullmatch(stripped):
            close_blocks()
            out.append("<hr>")
            i += 1
            continue

        if indent < 4 and stripped.startswith(">"):
            close_blocks()
            quote: list[str] = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append("<blockquote><p>%s</p></blockquote>" % inline(" ".join(quote)))
            continue

        if indent < 4 and is_table_start(lines, i):
            close_blocks()
            block, i = table_rows(lines, i)
            out.append(block)
            continue

        item = LIST_ITEM.match(expanded)
        if item and (stack or indent < 4):
            flush_para()
            ind = len(item.group(1))
            kind = "ol" if item.group(3) else "ul"
            start = int(item.group(3)) if item.group(3) else 1
            text = item.group(4).strip()
            while stack and ind < stack[-1]["indent"]:
                close_level()
            if stack and ind >= stack[-1]["indent"] + 2:
                emit_item(stack[-1])
                open_list(kind, ind, start, text)
            elif stack and stack[-1]["kind"] != kind:
                close_level()
                open_list(kind, ind, start, text)
            elif stack:
                close_item(stack[-1])
                stack[-1]["text"] = [text]
            else:
                open_list(kind, ind, start, text)
            i += 1
            continue

        if stack:
            # A lazy continuation line joins the item it follows.
            stack[-1]["text"].append(stripped)
        else:
            para.append(stripped)
        i += 1

    close_blocks()
    return "\n".join(out)


def build_toc(headings: list[tuple[int, str, str]]) -> str:
    entries = [h for h in headings if 2 <= h[0] <= 3]
    if len(entries) < TOC_MIN_ENTRIES:
        return ""
    out = ['<nav class="toc"><div class="toc-title">Contents</div><ul>']
    depth = 2
    for level, text, slug in entries:
        while level > depth:
            out.append("<ul>")
            depth += 1
        while level < depth:
            out.append("</ul>")
            depth -= 1
        out.append('<li><a href="#%s">%s</a></li>'
                   % (html.escape(slug, quote=True), html.escape(text, quote=False)))
    while depth > 2:
        out.append("</ul>")
        depth -= 1
    out.append("</ul></nav>")
    return "\n".join(out)


# ---------------------------------------------------------------- PDF

CHROMIUM_NAMES = ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable",
                  "chrome", "microsoft-edge", "microsoft-edge-stable", "msedge")
CHROMIUM_APP_PATHS = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
)


def chromium_candidates() -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    paths = [shutil.which(name) for name in CHROMIUM_NAMES]
    paths += [p for p in CHROMIUM_APP_PATHS if os.path.isfile(p) and os.access(p, os.X_OK)]
    for path in paths:
        if path and os.path.realpath(path) not in seen:
            seen.add(os.path.realpath(path))
            found.append(path)
    return found


def _remove_stale(pdf_path: Path) -> bool:
    try:
        if pdf_path.exists():
            pdf_path.unlink()
        return True
    except OSError as exc:
        print("md2doc: cannot remove the old %s: %s" % (pdf_path, exc), file=sys.stderr)
        return False


def _run_engine(name: str, cmd: list[str], pdf_path: Path) -> bool:
    """Run one engine after removing any old PDF. True only if it made a new PDF."""
    if not _remove_stale(pdf_path):
        return False
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=PDF_TIMEOUT)
    except subprocess.TimeoutExpired:
        print("md2doc: %s did not finish within %d s and was stopped" % (name, PDF_TIMEOUT),
              file=sys.stderr)
        _remove_stale(pdf_path)
        return False
    except OSError as exc:
        print("md2doc: could not run %s: %s" % (name, exc), file=sys.stderr)
        return False
    if r.returncode == 0 and pdf_path.is_file() and pdf_path.stat().st_size > 0:
        return True
    detail = (r.stderr or r.stdout or "").strip().splitlines()
    if detail:
        reason = ": %s" % detail[-1]
    elif r.returncode == 0:
        reason = " and wrote no PDF"
    else:
        reason = ""
    print("md2doc: %s failed (exit %d)%s" % (name, r.returncode, reason), file=sys.stderr)
    _remove_stale(pdf_path)
    return False


def to_pdf(html_path: Path, pdf_path: Path, sources: list[Path],
           title: str | None = None) -> str | None:
    """Try the available engines in order. Returns a description of the engine used, or None."""
    weasy = shutil.which("weasyprint")
    if weasy and _run_engine("weasyprint", [weasy, str(html_path), str(pdf_path)], pdf_path):
        return "weasyprint"
    wk = shutil.which("wkhtmltopdf")
    if wk and _run_engine("wkhtmltopdf", [wk, "--quiet", "--enable-local-file-access",
                                          str(html_path), str(pdf_path)], pdf_path):
        return "wkhtmltopdf (archived; CSS custom properties are ignored)"
    as_root = (sys.platform.startswith("linux") and hasattr(os, "geteuid")
               and os.geteuid() == 0)
    for browser in chromium_candidates():
        with tempfile.TemporaryDirectory(prefix="md2doc-profile-") as profile:
            cmd = [browser, "--headless", "--disable-gpu", "--no-first-run",
                   "--no-default-browser-check", "--user-data-dir=%s" % profile,
                   "--no-pdf-header-footer", "--print-to-pdf-no-header"]
            if as_root:
                cmd.append("--no-sandbox")
            cmd += ["--print-to-pdf=%s" % pdf_path, html_path.resolve().as_uri()]
            if _run_engine(os.path.basename(browser), cmd, pdf_path):
                return "headless browser %s" % browser
    pandoc = shutil.which("pandoc")
    if pandoc and sources:
        print("md2doc: falling back to pandoc, which converts the Markdown itself; "
              "the print CSS is ignored and a TeX engine is needed by default",
              file=sys.stderr)
        cmd = [pandoc] + [str(s) for s in sources] + ["-o", str(pdf_path)]
        if title:
            cmd += ["--metadata", "title=%s" % title]
        if _run_engine("pandoc", cmd, pdf_path):
            return "pandoc (print CSS not applied)"
    return None


# ---------------------------------------------------------------- command line

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="md2doc.py",
                                 description="Markdown to print ready HTML and PDF.")
    ap.add_argument("inputs", nargs="+", help="markdown files, concatenated in order")
    ap.add_argument("-o", "--output", help="output html path, must end in .html")
    ap.add_argument("-t", "--title", help="document title, defaults to frontmatter or first heading")
    ap.add_argument("--toc", action="store_true", help="insert a table of contents")
    ap.add_argument("--pdf", action="store_true", help="also try to produce a PDF")
    try:
        args = ap.parse_args(sys.argv[1:] if argv is None else argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2

    def fail(message: str) -> int:
        print("md2doc: %s" % message, file=sys.stderr)
        return 2

    inputs = [Path(p) for p in args.inputs]
    for path in inputs:
        if not path.is_file():
            return fail("no such file: %s" % path)

    if args.output:
        out_path = Path(args.output)
        if out_path.suffix.lower() != ".html":
            return fail("output path must end in .html, got %s "
                        "(with --pdf the PDF is written next to it)" % out_path)
    else:
        out_path = inputs[0].with_suffix(".html")
    pdf_path = out_path.with_suffix(".pdf")
    resolved = {p.resolve() for p in inputs}
    if out_path.resolve() in resolved:
        return fail("output %s would overwrite an input file; pass -o" % out_path)
    if args.pdf and pdf_path.resolve() in resolved:
        return fail("PDF %s would overwrite an input file; pass -o" % pdf_path)

    bodies: list[str] = []
    headings: list[tuple[int, str, str]] = []
    title = args.title
    for path in inputs:
        try:
            raw = normalise_newlines(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as exc:
            return fail("cannot read %s: %s" % (path, exc))
        meta, text = split_frontmatter(raw)
        offset = raw[:len(raw) - len(text)].count("\n")
        if not title:
            title = meta.get("title") or meta.get("name")
        bodies.append(convert(text, headings, source=str(path), line_offset=offset))

    if not title and headings:
        title = headings[0][1]
    title = title or "Document"

    toc = ""
    if args.toc:
        toc = build_toc(headings)
        if not toc:
            found = len([h for h in headings if 2 <= h[0] <= 3])
            print("md2doc: note: --toc needs at least %d level 2 or 3 headings and found %d, "
                  "so no contents block was added" % (TOC_MIN_ENTRIES, found), file=sys.stderr)

    document = (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n%s%s\n</body>\n</html>\n"
        % (html.escape(title, quote=False), CSS, (toc + "\n") if toc else "",
           "\n".join(bodies))
    )

    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(document, encoding="utf-8")
    except OSError as exc:
        return fail("cannot write %s: %s" % (out_path, exc))
    print("wrote %s (%d bytes, %d headings)" % (out_path, len(document), len(headings)))

    if args.pdf:
        engine = to_pdf(out_path, pdf_path, inputs, args.title)
        if engine:
            print("wrote %s using %s" % (pdf_path, engine))
        else:
            print(
                "md2doc: no PDF engine produced a PDF. The HTML is print ready, so either "
                "open it and print to PDF from the browser with headers and footers off, "
                "or install one of: weasyprint (pip install weasyprint), chromium or "
                "chrome, wkhtmltopdf, pandoc.",
                file=sys.stderr)
            return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
