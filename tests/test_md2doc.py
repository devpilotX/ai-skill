#!/usr/bin/env python3
"""Tests for the Markdown converter in the doc-forge skill.

Checks the conversion of every supported construct, and checks escaping and URL
filtering, which are the parts that cause real damage when they are wrong. Also
checks the command line: exit statuses, output path rules, and the PDF engine
handling, using fake engines on a private PATH.

Run with: python3 tests/test_md2doc.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "doc-forge" / "scripts" / "md2doc.py"
FIXTURE = ROOT / "tests" / "fixtures" / "doc_sample.md"

spec = importlib.util.spec_from_file_location("md2doc", SCRIPT)
assert spec and spec.loader, "cannot load converter at %s" % SCRIPT
md2doc = importlib.util.module_from_spec(spec)
sys.modules["md2doc"] = md2doc
spec.loader.exec_module(md2doc)

failures: list[str] = []


def check(condition: bool, message: str) -> None:
    if condition:
        print("  pass  %s" % message)
    else:
        print("  FAIL  %s" % message)
        failures.append(message)


def run_main(argv: list[str]) -> tuple[int | None, str, str]:
    """Run main in process. Returns the exit status, stdout and stderr. If main
    raises, the status is None and the exception is appended to stderr, so a
    broken converter fails its checks instead of crashing this harness."""
    out, err = io.StringIO(), io.StringIO()
    rc: int | None = None
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = md2doc.main(argv)
    except SystemExit as exc:
        err.write("main raised SystemExit(%r) instead of returning\n" % exc.code)
    except Exception as exc:  # noqa: BLE001, the harness must survive any failure
        err.write("main raised %s: %s\n" % (type(exc).__name__, exc))
    return rc, out.getvalue(), err.getvalue()


class AttrCollector(HTMLParser):
    """Collects (tag, attribute names) for every start tag, as a browser would parse them."""

    def __init__(self) -> None:
        super().__init__()
        self.tags: list[tuple[str, list[str]]] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        self.tags.append((tag, [name for name, _ in attrs]))


def attributes(fragment: str) -> list[tuple[str, list[str]]]:
    parser = AttrCollector()
    parser.feed(fragment)
    parser.close()
    return parser.tags


def read(path: Path) -> str:
    """File contents, or an empty string when the file was never written."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def convert(md: str) -> tuple[str, str]:
    """Convert a body in process, returning the HTML and whatever went to stderr."""
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        body = md2doc.convert(md, [], source="t.md")
    return body, err.getvalue()


def run_cli(args: list[str], path_dir: str) -> subprocess.CompletedProcess:
    """Run the script as a program with PATH set to path_dir only."""
    env = dict(os.environ, PATH=path_dir)
    return subprocess.run([sys.executable, "-B", str(SCRIPT)] + args, env=env,
                          capture_output=True, text=True, timeout=60)


def fake_engine(directory: Path, name: str, body: str) -> None:
    exe = directory / name
    exe.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8")
    exe.chmod(0o755)


with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp) / "out.html"
    rc, _, _ = run_main([str(FIXTURE), "-o", str(out), "--toc"])
    check(rc == 0, "converter exits cleanly")
    doc = read(out)
    check(bool(doc), "output file was written")

print("\nstructure")
check("<title>Converter test</title>" in doc, "title comes from frontmatter")
check("version: 1" not in doc, "frontmatter is stripped from the body")
check('class="toc"' in doc and 'href="#lists"' in doc, "table of contents links to slugs")
check('<h2 id="lists">' in doc, "headings carry stable identifiers")
check("@media print" in doc and "@page" in doc, "print rules are embedded")
check("<style>" in doc, "stylesheet is inlined, so the file is self contained")

print("\ninline markup")
check("<strong>bold</strong>" in doc, "bold")
check("<em>italic</em>" in doc, "italic")
check("<del>strike</del>" in doc, "strikethrough")
check("<code>inline code</code>" in doc, "inline code")
check('<a href="https://example.com">link</a>' in doc, "explicit link")
check('<a href="https://example.org/page">' in doc, "bare URL becomes a link")
check("</a>." in doc, "trailing full stop stays outside the link")

print("\nblocks")
check(re.search(r"<li>second item\s*<ul>\s*<li>nested item</li>\s*</ul>\s*</li>", doc)
      is not None, "nested unordered list sits inside its parent <li>")
check("<ol>" in doc and "step one" in doc, "ordered list")
check("<th>Field</th>" in doc, "table header")
check("<td>primary key</td>" in doc, "table body cell")
check("<code>null</code>" in doc, "inline markup inside a table cell")
check("<blockquote>" in doc and "Continued on the next line." in doc, "blockquote joins lines")
check("<pre><code" in doc, "fenced code block")

print("\nescaping, the part that matters")
check("x &lt; 3 and x &gt; 1" in doc, "angle brackets inside code are escaped")
check("<script>alert" not in doc, "raw script tag does not survive")
check("&lt;script&gt;alert(1)&lt;/script&gt;" in doc, "raw HTML is shown as text")
check("6 &amp; 7" in doc, "ampersand is escaped")

print("\nlinks and URL filtering")
img = md2doc.inline('![x" onerror="alert(1)](a.png)')
check(attributes(img) == [("img", ["src", "alt"])], "image alt cannot inject an attribute")
check('alt="x&quot; onerror=&quot;alert(1)"' in img, "image alt is escaped with quotes")
link = md2doc.inline('[a" onclick="x](https://a.com/"q)')
check(attributes(link) == [("a", ["href"])], "link text and href cannot inject an attribute")
for bad in ("[x](javascript:alert%281%29)", "[x]( JaVaScRiPt:alert(1))",
            "[x](java\tscript:alert(1))", "[x](&#106;avascript:alert(1))",
            "[x](vbscript:msgbox)", "[x](file:///etc/passwd)"):
    got = md2doc.inline(bad)
    check("<a" not in got and "href" not in got, "not a link: %r" % bad)
got = md2doc.inline("[x](javascript:alert%281%29)")
check(got == "[x](javascript:alert%281%29)", "a refused link is shown as its source text")
got = md2doc.inline("![p](data:image/png;base64,AAAA)")
check("<img" not in got and "src=" not in got, "data: image is not rendered")
check("<a" not in md2doc.inline("[x](data:text/html,<b>hi</b>)"), "data: link is not a link")
for ok in ("[m](mailto:a@b.co)", "[r](docs/guide.md)", "[h](#usage)", "[s](http://a.com)"):
    check("<a href=" in md2doc.inline(ok), "allowed target is a link: %r" % ok)
amp = md2doc.inline("[q](https://a.com/?a=1&b=2) ![i](i.png?a=1&b=2)")
check('href="https://a.com/?a=1&amp;b=2"' in amp and "&amp;amp;" not in amp,
      "& in a link URL is escaped exactly once")
check('src="i.png?a=1&amp;b=2"' in amp, "& in an image URL is escaped exactly once")
same = md2doc.inline("[https://a.com](https://a.com)")
check(same.count("<a ") == 1 and same == '<a href="https://a.com">https://a.com</a>',
      "a URL used as link text gives one anchor, not nested anchors")
angle = md2doc.inline("see <https://x.y/p?a=1&b=2>.")
check(angle == 'see <a href="https://x.y/p?a=1&amp;b=2">https://x.y/p?a=1&amp;b=2</a>.',
      "angle bracket autolink gives a clean link")
wiki = "https://en.wikipedia.org/wiki/Foo_(bar)"
got = md2doc.inline("[W](%s) and %s." % (wiki, wiki))
check(got.count('href="%s"' % wiki) == 2, "URLs with balanced parentheses are not truncated")
check(md2doc.inline("(see https://a.com/x)") == '(see <a href="https://a.com/x">https://a.com/x</a>)',
      "an unbalanced closing parenthesis stays outside a bare URL")
titled = md2doc.inline('[t](#a "q&quot; onclick=&quot;x")')
check(attributes(titled) == [("a", ["href", "title"])],
      "a link title cannot inject an attribute")
check('<a href="#top" title="Top">up</a>' in md2doc.inline('[up](#top "Top")'), "link title")

print("\ncode blocks")
body, _ = convert("para\n\n    code <x>\n    more\n\nafter\n")
check("<pre><code>code &lt;x&gt;\nmore</code></pre>" in body, "indented code block")
check("<p>after</p>" in body, "indented code ends at the first unindented line")
body, _ = convert("- item\n    still the item\n")
check("<pre>" not in body and "still the item" in body, "indented line inside a list is not code")
body, _ = convert("~~~python\nx = 1 < 2\n~~~\nafter\n")
check('<pre><code class="language-python">x = 1 &lt; 2</code></pre>' in body, "tilde fence")
check("<p>after</p>" in body, "tilde fence closes")
body, _ = convert("````\n```\ninner\n```\n````\n")
check("```\ninner\n```" in body, "a longer fence can contain a shorter one")
body, err = convert("text\n\n```\nnever closed\n\nmore\n")
check("<pre><code>never closed\n\nmore</code></pre>" in body, "unclosed fence runs to the end")
check("warning" in err and "t.md:3" in err, "unclosed fence prints a warning with the line")

print("\nlists")
body, _ = convert("- item one\n  continued\n- two\n")
check(body == "<ul>\n<li>item one continued</li>\n<li>two</li>\n</ul>",
      "lazy continuation joins the current <li>")
check("<p>" not in body, "no paragraph directly inside a list")
body, _ = convert("3. c\n4. d\n")
check(body.startswith('<ol start="3">'), "ordered list start number")
body, _ = convert("1. a\n\n2. b\n")
check(body.count("<ol") == 1 and body.count("<li>") == 2, "blank line between items keeps one list")
body, _ = convert("- a\n  1. x\n  2. y\n- b\n")
check(re.search(r"<li>a\s*<ol>\s*<li>x</li>\s*<li>y</li>\s*</ol>\s*</li>\s*<li>b</li>", body)
      is not None, "nested ordered list inside an unordered item")

print("\ntables")
body, _ = convert("| a | b |\n|---|---|\n| `x|y` | p\\|q |\n")
check("<td><code>x|y</code></td>" in body, "pipe inside a code span does not split the cell")
check("<td>p|q</td>" in body, "escaped pipe does not split the cell")
body, _ = convert("| l | c | r | n |\n|:--|:-:|--:|---|\n| 1 | 2 | 3 | 4 |\n")
check('<th style="text-align: left">l</th>' in body, "left alignment")
check('<td style="text-align: center">2</td>' in body, "centre alignment")
check('<td style="text-align: right">3</td>' in body, "right alignment")
check("<td>4</td>" in body, "no colon, no alignment style")
body, _ = convert("| a | b |\n| - | - |\n| 1 | 2 |\n")
check("<table>" in body and "<td>2</td>" in body, "single hyphen delimiter cells")
body, _ = convert("a | b\n-\n")
check("<table>" not in body, "delimiter with the wrong cell count is not a table")

print("\nheadings")
body, _ = convert("## Title ##\n# C#\n")
check('<h2 id="title">Title</h2>' in body, "closing hashes are stripped")
check(">C#</h1>" in body, "a hash that is part of the text stays")
heads: list = []
md2doc.convert("## See [the guide](https://example.com/very/long)\n", heads)
check(heads[0][2] == "see-the-guide", "heading slug excludes the link URL")

print("\nfrontmatter and line endings")
meta, body = md2doc.split_frontmatter("---\r\ntitle: T\r\n---\r\nBody\r\n")
check(meta.get("title") == "T" and body.strip() == "Body", "CRLF frontmatter")
meta, body = md2doc.split_frontmatter("---\ntitle: T\n----\nBody\n")
check(meta == {}, "---- does not close frontmatter")
meta, body = md2doc.split_frontmatter("---\ntitle: T\n---x\nBody\n")
check(meta == {}, "---x does not close frontmatter")
meta, body = md2doc.split_frontmatter("---\ntitle: T\nnote: a\n---b\n---\nBody\n")
check(meta.get("title") == "T" and body == "Body\n", "only a line that is exactly --- closes")

with tempfile.TemporaryDirectory() as tmp:
    tmpdir = Path(tmp)
    crlf = tmpdir / "crlf.md"
    crlf.write_bytes(b"---\r\ntitle: Windows file\r\n---\r\n# Head\r\n\r\n- a\r\n- b\r\n\r\n"
                     b"line one\r\nline two\r\n")
    rc, _, _ = run_main([str(crlf), "-o", str(tmpdir / "crlf.html")])
    html_out = read(tmpdir / "crlf.html")
    check(rc == 0 and "<title>Windows file</title>" in html_out, "CRLF file: title from frontmatter")
    check("\r" not in html_out and "<p>line one line two</p>" in html_out, "CRLF input normalised")
    check("<li>a</li>" in html_out and "title: Windows" not in html_out, "CRLF file: body intact")

    print("\nmultiple inputs")
    first, second = tmpdir / "a.md", tmpdir / "b.md"
    first.write_text("---\ntitle: Manual\n---\n## Setup\n\nfirst body\n", encoding="utf-8")
    second.write_text("---\ntitle: Other\n---\n## Setup\n\nsecond body\n", encoding="utf-8")
    rc, _, _ = run_main([str(first), str(second), "-o", str(tmpdir / "m.html")])
    manual = read(tmpdir / "m.html")
    check(rc == 0 and "<title>Manual</title>" in manual, "title comes from the first file")
    check(0 < manual.find("first body") < manual.find("second body"), "inputs concatenated in order")
    check('id="setup"' in manual and 'id="setup-2"' in manual, "slugs unique across files")
    check("title: Other" not in manual, "frontmatter of later files is removed")

    print("\ncommand line")
    rc, _, err = run_main([str(tmpdir / "missing.md")])
    check(rc == 2 and "no such file" in err, "missing input exits 2")
    check(not (tmpdir / "missing.html").exists(), "a failing run writes nothing")
    rc, _, _ = run_main(["--no-such-flag", str(first)])
    check(rc == 2, "bad argument exits 2 and main returns instead of raising")
    rc, _, _ = run_main([])
    check(rc == 2, "no inputs exits 2")
    rc, _, err = run_main([str(first), "-o", str(tmpdir / "x.pdf"), "--pdf"])
    check(rc == 2 and not (tmpdir / "x.pdf").exists(), "-o x.pdf is refused and writes nothing")
    named_html = tmpdir / "notes.html"
    named_html.write_text("# Notes\n", encoding="utf-8")
    rc, _, err = run_main([str(named_html)])
    check(rc == 2 and read(named_html) == "# Notes\n", "never overwrites an input file")
    rc, _, err = run_main([str(first), "-o", str(tmpdir / "toc.html"), "--toc"])
    check(rc == 0 and "--toc" in err and "note" in err, "--toc with too few headings prints a note")
    real_convert = md2doc.convert
    md2doc.convert = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    try:
        rc, _, err = run_main([str(first), "-o", str(tmpdir / "crash.html")])
    finally:
        md2doc.convert = real_convert
    check(rc is None and "RuntimeError: boom" in err and read(tmpdir / "crash.html") == "",
          "a crashing main is reported, and the harness carries on")
    proc = run_cli(["--bogus"], tmp)
    check(proc.returncode == 2, "bad argument exits 2 as a program")

    print("\nPDF engines")
    empty = tmpdir / "emptybin"
    empty.mkdir()
    proc = run_cli([str(first), "-o", str(tmpdir / "p.html"), "--pdf"], str(empty))
    check(proc.returncode == 3, "no PDF engine exits 3")
    check((tmpdir / "p.html").is_file(), "HTML is still written when no engine is found")
    check("no PDF engine" in proc.stderr, "missing engine is explained on stderr")

    if os.name == "posix":
        fakes = tmpdir / "fakebin"
        fakes.mkdir()
        fake_engine(fakes, "weasyprint", 'printf "%%PDF-1.4 fake" > "$2"')
        proc = run_cli([str(first), "-o", str(tmpdir / "w.html"), "--pdf"], str(fakes))
        check(proc.returncode == 0 and (tmpdir / "w.pdf").is_file(), "fake engine produces a PDF")
        check("using weasyprint" in proc.stdout, "the engine used is named")

        lazy = tmpdir / "lazybin"
        lazy.mkdir()
        fake_engine(lazy, "chromium", "exit 0")
        stale = tmpdir / "s.pdf"
        stale.write_text("old", encoding="utf-8")
        proc = run_cli([str(first), "-o", str(tmpdir / "s.html"), "--pdf"], str(lazy))
        check(proc.returncode == 3, "a stale PDF is not mistaken for fresh output")
        check(not stale.exists(), "the stale PDF is removed before the engine runs")

        record = tmpdir / "args.txt"
        argbin = tmpdir / "argbin"
        argbin.mkdir()
        fake_engine(argbin, "google-chrome-stable",
                    'for a in "$@"; do echo "$a"; done > "%s"\n'
                    'for a in "$@"; do case "$a" in --print-to-pdf=*) '
                    'printf "%%%%PDF" > "${a#--print-to-pdf=}";; esac; done' % record)
        proc = run_cli([str(first), "-o", str(tmpdir / "c.html"), "--pdf"], str(argbin))
        passed = read(record).splitlines()
        check(proc.returncode == 0 and "google-chrome-stable" in proc.stdout,
              "google-chrome-stable is found")
        check("--no-pdf-header-footer" in passed, "Chromium runs without headers and footers")
        root_linux = sys.platform.startswith("linux") and os.geteuid() == 0
        check(("--no-sandbox" in passed) == root_linux, "--no-sandbox only as root on Linux")

        pandir = tmpdir / "panbin"
        pandir.mkdir()
        fake_engine(pandir, "pandoc",
                    'for a in "$@"; do echo "$a"; done > "%s"\n'
                    'while [ "$1" != "-o" ]; do shift; done; printf "%%%%PDF" > "$2"' % record)
        proc = run_cli([str(first), str(second), "-o", str(tmpdir / "pd.html"), "--pdf"],
                       str(pandir))
        passed = read(record).splitlines()
        check(proc.returncode == 0 and str(first) in passed and str(second) in passed,
              "pandoc fallback converts every input")
        check("CSS is ignored" in proc.stderr, "pandoc fallback says the print CSS is ignored")

        slow = tmpdir / "slowbin"
        slow.mkdir()
        fake_engine(slow, "weasyprint", "exec %s 5" % (shutil.which("sleep") or "/bin/sleep"))
        saved_path, saved_timeout = os.environ.get("PATH", ""), md2doc.PDF_TIMEOUT
        os.environ["PATH"] = str(slow)
        md2doc.PDF_TIMEOUT = 1
        err = io.StringIO()
        try:
            with contextlib.redirect_stderr(err):
                engine = md2doc.to_pdf(tmpdir / "w.html", tmpdir / "slow.pdf", [first])
        finally:
            os.environ["PATH"], md2doc.PDF_TIMEOUT = saved_path, saved_timeout
        check(engine is None and "did not finish within 1 s" in err.getvalue(),
              "a hung engine is stopped by the timeout with a clear error")
    else:
        print("  skip  fake engine checks need a POSIX shell")

print("\nunit level behaviour")
check(md2doc.slugify("Hello, World!") == "hello-world", "slugify strips punctuation")
check(md2doc.slugify("") == "section", "slugify has a fallback")
meta, body = md2doc.split_frontmatter("---\ntitle: T\n---\nBody\n")
check(meta.get("title") == "T" and body.strip() == "Body", "frontmatter parsing")
meta2, body2 = md2doc.split_frontmatter("No frontmatter here\n")
check(meta2 == {} and body2.startswith("No frontmatter"), "missing frontmatter is fine")
check("<code>a &lt; b</code>" in md2doc.inline("`a < b`"), "code span escaped on its own")
check(md2doc.inline("**a** and *b*") == "<strong>a</strong> and <em>b</em>", "inline combination")

print("\n%d check(s) failed" % len(failures))
sys.exit(1 if failures else 0)
