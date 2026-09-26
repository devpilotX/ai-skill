---
name: security-hardening
description: Find and fix the security defects attackers actually reach, on systems the user owns or is authorised to test. Use when the user asks how to secure or harden an application or API, or asks about authentication, authorisation, password storage, sessions, cookies, JWT, CORS, security headers, injection, XSS, CSRF, SSRF, file uploads, mass assignment, secrets, dependency vulnerabilities or supply chain risk, or asks whether their setup is safe. Works from a short threat model, checks object level authorisation first, ranks findings by reachability, and retrieves advisories instead of recalling them. For a whole release readiness audit use ship-audit instead. For review of a single change or pull request use code-review. Triggers on security review, harden my app, is this secure, OWASP, IDOR, BOLA, SQL injection, XSS, CSRF, SSRF, password hashing, JWT, CORS error, CSP, cookie flags, file upload security, npm audit, pip-audit, secrets leaked, penetration test my own app.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Security hardening

The failure this corrects: a security review that walks a generic checklist, reports twenty theoretical
issues, and misses the one an attacker uses, which is usually a request where changing one identifier
returns someone else's data. Start from what an attacker would try against this specific system, test
it, and rank by what they can reach.

## When to use and when to stay off

Run when the user asks to secure, harden or review the security of a system they own or are authorised
to test, or asks about any control named in the description. Also run before a launch that handles
personal data, money or credentials.

Scope: the user's own systems and code, and systems they have written authorisation to test. This skill
does not help with access to systems the user does not control. If ownership is unclear, ask first.

Stay off, or hand over, when:

- The user wants a ship or do not ship verdict on a whole release, where security is one gate. Use `ship-audit`.
- The user wants review of one diff or pull request for correctness and style as well as security. Use `code-review`.
- The concern is prompt injection, tool misuse or data leakage through an LLM feature. Use `ml-build`, then return here for the surrounding web controls.

Off switch: the user says "stop", "I've decided", or "just execute". Comply at once and stay off for
the rest of the session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Check object level authorisation first. Broken access control is ranked first in the [OWASP Top 10 2021 (A01)](https://owasp.org/Top10/A01_2021-Broken_Access_Control/), and broken object level authorisation is ranked first in the [OWASP API Security Top 10 2023 (API1)](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/). Retrieve the current editions when reporting.
2. Retrieve advisories, never recall them. Use the ecosystem audit tools, the [GitHub Advisory Database](https://github.com/advisories), [OSV](https://osv.dev) and the [NVD](https://nvd.nist.gov/vuln), with dates. NVD enrichment has had a backlog since 2024, so a CVE there may lack a score or affected versions; do not read a missing score as low risk.
3. Never invent a vulnerability identifier, a severity score or a compliance requirement. Cite it or mark it unverified.
4. Rank by reachability, then consequence. State what an attacker needs before each finding is usable.
5. A live secret goes in the first line of the report, and the fix includes rotation. Deleting it from code leaves it in history and in every clone.
6. Fix the class, not only the instance.
7. No security theatre. Composition rules, forced periodic rotation and security questions make things worse. Say so.

## Procedure

Controls, parameters and command gotchas referenced below are in `references/web-controls.md`.

### Step 1, threat model briefly

Ten minutes, method in `references/threat-model.md`. Name what is worth taking, who would want it, how
they reach it, and what stops them today. Later steps test those controls.

### Step 2, map the attack surface

Every entry point: public and authenticated endpoints, admin interfaces, webhooks, file uploads,
consumers reading external data, scheduled jobs, and debug or metrics endpoints left reachable. For each,
record who can call it, what it trusts, and what it can reach. Look for the forgotten ones: old API
versions still routed, a public staging environment with production data, an open database port, a
public bucket.

### Step 3, authorisation and authentication

For every endpoint touching user owned data, confirm ownership is checked on the object. Test it: as user
A, request user B's resource by identifier.

Check property level authorisation too: a client must not be able to set fields it does not own (mass
assignment, such as sending `"role": "admin"` or `"price": 0` in an update), or read fields it is not
entitled to. This is broken object property level authorisation, [API3:2023](https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/).
Bind requests to an explicit allowlist of writable fields and serialise responses from an explicit
allowlist.

Role checks exist on the server, not only in the interface.

Passwords are hashed with Argon2id, or scrypt, or bcrypt (which ignores input beyond 72 bytes, so reject
or pre-handle longer passwords deliberately), or PBKDF2 where FIPS 140 validation is required. Take the
parameters from the [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html),
retrieved at the time of review. Never a general purpose digest, salted or not.

Session cookies set `HttpOnly`, `Secure` and `SameSite`. Sessions are invalidated on logout, password
change and permission change, and rotated on privilege change.

JWT: the server pins the accepted algorithm list and rejects `none`; the key type is fixed by
configuration so an RS256 public key can never be used as an HS256 secret (key confusion); signature,
`exp`, `iss` and `aud` are validated before any claim is read. Checklist in `references/web-controls.md`.

Account recovery and multi factor enrolment are tested, since they are the usual bypass. Rate limits
cover login, password reset, token refresh, and anything sending mail or costing money.

### Step 4, input, output and browser controls

Parameterised queries everywhere, including ORM raw query escape hatches. No shell built from user
input; pass arguments as a list. No deserialisation of untrusted data into objects.

Output escaped for its context (HTML body, attribute, JavaScript, URL, CSS). Find every raw HTML bypass
and justify each one.

Security headers: a Content Security Policy, frame-ancestors to control framing, HSTS, and
`X-Content-Type-Options: nosniff`. CORS: never reflect the request `Origin` while sending
`Access-Control-Allow-Credentials: true`; compare against an exact allowlist. Baselines in
`references/web-controls.md`.

File uploads: an allowlist of extensions and a content check (decode or parse with a real library), since
either check alone is bypassable and polyglot files pass both. Cap size before reading, generate the
stored name, store outside the web root, and serve user files from a separate origin with
`Content-Disposition: attachment`, a `Content-Type` you set, and `X-Content-Type-Options: nosniff`.

Server side request forgery on any feature that fetches a user supplied URL: resolve the host, validate
every resolved IP against internal and metadata ranges, then connect to that validated IP so a second DNS
answer cannot rebind it; disable redirects or revalidate each hop; allow only http and https. On AWS,
require IMDSv2 on every instance. Details in `references/web-controls.md`.

Redirect targets checked against an allowlist. CSRF protection on state changing requests, with a
`SameSite` policy that supports it.

### Step 5, data protection

TLS everywhere with no mixed content. Encryption at rest for sensitive data with a key rotation path.
Least privilege on database accounts, cloud roles and API tokens. A personal data inventory: what is
collected, where, who reads it, how long it is kept, and whether deletion works. Logs, error reports and
analytics payloads checked for personal data and secrets.

### Step 6, secrets, code scanning and supply chain

Scan the full git history for secrets with `gitleaks` or `trufflehog`, and add the scan to CI. Run a
static analysis tool the team will read, such as Semgrep or CodeQL, and triage its output rather than
pasting it.

Run the ecosystem audit against the project's real dependency set and report the real output:

```
npm audit --omit=dev
pip-audit -r requirements.txt
osv-scanner scan source -r .
cargo audit
govulncheck ./...
```

Plain `pip-audit` with no arguments audits whatever environment it runs in, which is often not the
project; use `-r` or run it inside the project virtual environment. Gotchas per tool in
`references/web-controls.md`.

Separate runtime from development findings. Lockfile committed. Review install scripts on new
dependencies. Pin CI actions and base images by digest. Restrict who can push to the default branch and
publish releases.

### Step 7, verify and report

Try the attacks on the user's own system: the identifier swap, the extra field in an update, the missing
role check, the unescaped field, the oversized or polyglot upload, the expired or `alg: none` token, the
cross origin request with credentials.

Report in this format, ordered by reachability (anonymous remote, then authenticated, then admin, then
requires existing compromise), and within that by consequence (code execution, money movement or bulk
data exposure, then single record exposure, then information disclosure):

```
LIVE SECRETS: none found / list with rotation steps
SCOPE: what was reviewed, commands run, what was not reviewed

1. [reachability: anonymous remote] [consequence: bulk data exposure]
   Where: path/to/handler.py:88, GET /api/invoices/{id}
   Attacker needs: any account
   Attacker gets: every customer's invoices by incrementing the id
   Evidence: request and response from the test
   Fix: ownership check in the query; class fix is a shared loader that requires the tenant
```

## Self-audit

- Object level authorisation was tested by swapping an identifier, and property level by sending an unowned field.
- Every advisory cites a source and a date; none was recalled.
- Live secrets, if any, are in the first line with rotation in the fix.
- Findings are ordered by reachability then consequence, each with the attacker's prerequisites.
- Password hashing parameters were retrieved from the OWASP cheat sheet, not recalled.
- Upload handling checks extension and content and serves from a separate origin.
- SSRF defence validates the connected IP and handles redirects.
- CORS never reflects arbitrary origins with credentials; headers and cookie flags were checked.
- Audit commands ran against the project's dependency set, with real output included.
- No security theatre recommended, and anything not reviewed is disclosed.

## What this cannot do

A static review is not a penetration test. It cannot find defects that only appear at runtime, under
load or in combination with infrastructure it was not shown, and it cannot see cloud IAM, network rules,
WAF or CDN configuration unless the user provides them. Say which of these were out of view, and
recommend a penetration test by a qualified tester for anything handling money or sensitive personal
data.

Compliance needs a professional. This skill can map controls, but it cannot certify them.

- Card data: ask a PCI Qualified Security Assessor (QSA): "Given this payment flow (describe where card data is entered, transmitted and whether it touches our servers), which PCI DSS self-assessment questionnaire applies to us, and which requirements are in scope?"
- Personal data of people in the EU or UK: ask a privacy lawyer: "For these categories of personal data (list them), processed for these purposes (list them) with these processors (list them), what is our lawful basis, do we need a DPIA, and what must our privacy notice and data processing agreements contain?"
- Health data in the US: ask healthcare compliance counsel: "Are we a covered entity or business associate under HIPAA for this data flow (describe it), and which safeguards and agreements are required before launch?"
