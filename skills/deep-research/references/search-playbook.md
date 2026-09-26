# Search playbook

Where primary evidence lives, how to phrase searches that find it, how to check a source before
trusting it, and what to write when the answer cannot be found.

## Where primary sources live

Company facts and financials. Regulatory filings, not press coverage. US public companies file with
the SEC, searchable in EDGAR ([sec.gov/edgar](https://www.sec.gov/edgar)): annual reports (10-K),
quarterly reports (10-Q), material events (8-K). UK companies file with Companies House. For other
jurisdictions, retrieve the name of the national company registry and securities regulator first.

Standards and protocols. The issuing body: IETF RFCs at [datatracker.ietf.org](https://datatracker.ietf.org),
W3C specifications at [w3.org/TR](https://www.w3.org/TR/), ISO and IEC catalogues (often paywalled,
so cite by standard number, year, and clause), and the WHATWG living standards for HTML and related
web APIs.

Software behaviour and versions. The project's changelog, release notes, and tagged releases in its
repository, then its issue tracker for known bugs. For the latest version, the package registry is
authoritative: PyPI, npm, crates.io, Maven Central, RubyGems, or the language's equivalent. A blog
post naming "the latest version" is stale on the day after the next release.

Prices, limits, and quotas. The vendor's own pricing and limits pages, with the retrieval date. These
are primary for what the vendor charges and change without notice.

Research. The paper itself through its DOI (resolve at [doi.org](https://www.doi.org)), preprint
servers such as [arXiv](https://arxiv.org), and for biomedicine [PubMed](https://pubmed.ncbi.nlm.nih.gov)
and trial registrations at [ClinicalTrials.gov](https://clinicaltrials.gov). Check retractions in the
Retraction Watch database, now hosted by Crossref.

Law and regulation. The official legislation or gazette site for the jurisdiction, for example
[EUR-Lex](https://eur-lex.europa.eu) for EU law. Court decisions from the court's own site or a docket
service such as [CourtListener](https://www.courtlistener.com) for US federal courts. Check that the
text is the current consolidated version.

Statistics. The national statistics office or the international body that publishes the series, with
the table identifier and release date, rather than a chart that reproduces it.

## Query variation templates

Run several of these per sub-question. Each surfaces a different part of the evidence.

- The primary document: `"<product>" changelog`, `"<company>" 10-K <year>`, `RFC "<protocol>"`, `site:<official domain> <term>`.
- The exact claim in quotes, to find where a specific number or phrase started.
- The critic's vocabulary: `<product> problems`, `<product> outage`, `<claim> debunked`, `<method> criticism`, `<drug> adverse events`.
- The failure record: `<product> issue tracker <symptom>`, `<library> regression <version>`, `migrated away from <product>`.
- The comparison without a vendor: `<a> vs <b>` plus `benchmark methodology`, and exclude vendor domains with `-site:`.
- The date bound: add the current year, or use the search tool's date filter, for anything volatile.
- The file type: `filetype:pdf` for reports, standards drafts, and filings.

Write each query into the search log with the date and tool.

## Lateral reading checklist

Adapted from the SIFT method by Mike Caulfield. Do this before reading a source closely, for every
source the answer depends on.

1. Stop. Note what you already believe about the claim and whether the source confirms it too neatly.
2. Investigate the source. Leave the page. Search the publisher and author by name. Who funds them, what else do they publish, does anyone independent describe them?
3. Find better coverage. Search the claim itself and see what independent, primary, or more expert sources say. If better coverage exists, cite that instead.
4. Trace claims, quotes, and media to the original context. Follow each link back until you reach the primary source, then check that it says what the citing source claims.

Record the outcome in the source's one line grade note.

## Web archive usage

Use the Internet Archive's Wayback Machine ([web.archive.org](https://web.archive.org)) when a page
is dead, when a page may have been edited since it was cited, or to see what a pricing or policy page
said on a past date.

Cite the archive URL with its capture timestamp alongside the original URL. If the live page differs
from the capture, say so and say which one the claim relies on. An archive capture shows what a page
said on that date, not what is true now.

To preserve a source you rely on that may change, request a new capture and cite it.

## When the answer cannot be established

Use this shape. It is a result, and it tells the user what to do next.

```
CANNOT ESTABLISH
Question: the sub-question, as asked.
Searched: the sources and query types tried, with dates.
Closest evidence: what was found, with sources and grades, and why it falls short.
Best reading: the most defensible answer on current evidence, labelled as inference, with confidence.
What would settle it: the specific document, dataset, or person, and how to obtain it.
```
