# Web controls baseline

Reference for step 3, 4 and 6 of the procedure. Each section is a baseline to compare the system
against, with the reason for each item so a deviation can be judged rather than flagged by rote.

## Headers

Source: [OWASP HTTP Headers Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html).

`Content-Security-Policy`. Start from `default-src 'self'; object-src 'none'; base-uri 'none'` and a
nonce or hash based script-src. `'unsafe-inline'` in script-src removes most of the XSS protection.
Roll out with `Content-Security-Policy-Report-Only` first and read the reports.

frame-ancestors in the CSP (`'none'` or `'self'`) controls who may frame the page, against
clickjacking. `X-Frame-Options: DENY` is the legacy equivalent for old browsers.

`Strict-Transport-Security` with max-age and `includeSubDomains` once every subdomain serves HTTPS.
HSTS is defined in [RFC 6797](https://www.rfc-editor.org/rfc/rfc6797). Before adding `preload`, retrieve
the current submission requirements from hstspreload.org, because removal from browser preload lists is
slow.

`X-Content-Type-Options: nosniff` on every response, so a browser does not execute a file as a type it
guessed.

`Referrer-Policy: strict-origin-when-cross-origin` or stricter, so tokens in URLs do not leak to third
parties.

Remove headers that announce versions (`Server`, `X-Powered-By`). Low value, but free.

## Cookies

Session and auth cookies: `HttpOnly` (no script access), `Secure` (HTTPS only), `SameSite=Lax` or
`Strict` (limits cross site sending, which supports CSRF defence), and the narrowest `Path` and `Domain`
that work. A `__Host-` name prefix forces `Secure`, `Path=/` and no `Domain`, so a sibling subdomain cannot
overwrite the cookie. `SameSite=None` requires `Secure` and needs a stated reason.

## CORS

CORS relaxes the browser's same origin policy. It is not access control; a non browser client ignores it
entirely, so the server still authorises every request.

Never reflect the request `Origin` into `Access-Control-Allow-Origin` while sending
`Access-Control-Allow-Credentials: true`. That lets any site make authenticated requests and read the
responses. Browsers refuse `*` with credentials, which is why this reflection pattern appears.

Compare the origin against an exact allowlist of full origins (scheme, host, port). Suffix or substring
checks such as "ends with example.com" accept `evil-example.com`. Unanchored regexes have the same
problem.

Do not allow the `null` origin; sandboxed iframes and local files send it.

Send `Vary: Origin` when the header value depends on the request origin, so caches do not serve one
origin's answer to another.

Keep `Access-Control-Allow-Methods` and `Access-Control-Allow-Headers` to what the API uses.

## Password hashing

Parameters come from the [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html).
Retrieve the current values before configuring anything; the figures below are what the cheat sheet
stated at the time of writing and are listed so a reviewer knows what shape to look for.

Argon2id first choice. Cheat sheet minimum: 19 MiB memory, 2 iterations, parallelism 1, with other
memory and iteration trade-offs listed there.

scrypt if Argon2id is unavailable. Cheat sheet minimum: N = 2^17, r = 8, p = 1.

bcrypt for legacy systems. Cheat sheet: work factor 10 or more. bcrypt uses at most 72 bytes of input,
and some libraries truncate silently, so either cap password length at 72 bytes with a clear error or
follow the cheat sheet's guidance on pre-hashing, which has its own pitfalls.

PBKDF2 where FIPS 140 validated algorithms are required. Cheat sheet: 600,000 iterations with
HMAC-SHA-256, or 210,000 with HMAC-SHA-512.

Rehash on login when stored parameters are below the current setting. Each hash stores its own
algorithm and parameters, so upgrades can be gradual.

A pepper, if used, lives outside the database, in a secrets manager or HSM.

## JWT validation checklist

Guidance: [RFC 8725, JSON Web Token Best Current Practices](https://www.rfc-editor.org/rfc/rfc8725).

- The accepted algorithm list is fixed in server configuration. `none` is rejected.
- The key and its type come from configuration, never from the token header. This prevents key confusion, where a token signed with HS256 using the server's RSA public key as the HMAC secret passes a verifier that trusted the header's `alg`.
- `kid` selects only among keys already configured. `jku`, `x5u` and embedded `jwk` headers are not used to fetch or accept keys.
- The signature is verified before any claim is used.
- `exp` is required and checked, `nbf` checked if present, with a small stated clock skew.
- `iss` and `aud` are checked against exact expected values, so a token issued for another service is refused.
- Access token lifetime is short, with a refresh token that is rotated on use and revocable server side.
- The payload is encoded, not encrypted. Nothing secret goes in it.
- The library is maintained and current; retrieve its advisories from the GitHub Advisory Database.

## Upload handling

- Allowlist extensions, and check content by parsing or decoding with a real library (for images, decode and re-encode, which also strips metadata). Extension alone is trivially renamed; magic bytes alone accept polyglots, files valid as two types at once.
- Because polyglots can pass both checks, containment matters more than detection: serve user files from a separate origin that shares no cookies with the application, with `Content-Disposition: attachment`, a `Content-Type` set by the server from the allowlist, and `X-Content-Type-Options: nosniff`.
- Treat SVG and HTML as active content. Either refuse them or serve them only as attachments from the separate origin.
- Enforce the size limit at the proxy and the application, before the body is buffered.
- Generate the stored filename. Never use the client supplied name or type for storage or for the response `Content-Type`.
- For archives, check every entry path for traversal (zip slip) and cap the total decompressed size.
- If files are shared between users, scan them for malware before they become visible to others.

## SSRF defence

1. Parse the URL with a standard library parser. Allow only `http` and `https`, and only expected ports.
2. If there is a host allowlist, check it first. That is the strongest control.
3. Resolve the hostname and check every returned address against blocked ranges: loopback (127.0.0.0/8, ::1), private (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, fc00::/7), link local (169.254.0.0/16, which includes the cloud metadata address 169.254.169.254, and fe80::/10), shared address space 100.64.0.0/10, 0.0.0.0/8, and IPv4 mapped IPv6 (::ffff:0:0/96). Parsing addresses with an IP library after resolution also handles decimal and octal encodings.
4. Connect to the exact IP that passed the check, sending the original hostname as the Host header and TLS SNI. Resolving again at connect time is the DNS rebinding hole: the first answer is public, the second is internal.
5. Disable automatic redirects. If redirects are needed, run every hop through steps 1 to 4.
6. Enforce the same rule at the network layer with an egress proxy or firewall, so an application bug is not the only control.
7. On AWS, require IMDSv2 (`HttpTokens=required`) on every instance and keep the metadata hop limit at 1 unless containers need more, so a plain GET cannot read instance credentials. Retrieve the current equivalent for other clouds from their documentation.

## Audit command matrix

| Ecosystem | Command | Gotchas |
| --- | --- | --- |
| Node | `npm audit --omit=dev` | Reads the lockfile; without `package-lock.json` results are incomplete. `npm audit fix --force` can apply major version upgrades. Drop `--omit=dev` to see build tooling risk separately. |
| Python | `pip-audit -r requirements.txt` | With no arguments it audits the environment it runs in, not the project. Audit a pinned or locked file; unpinned requirements resolve to whatever is newest today. Alternatively run inside the project virtual environment. |
| Any | `osv-scanner scan source -r .` | Scans lockfiles across ecosystems against [OSV](https://osv.dev). Version 1 used `osv-scanner -r .`; check the installed version. |
| Rust | `cargo audit` | Needs `Cargo.lock`; for a library without one, generate it first. Uses the RustSec database. |
| Go | `govulncheck ./...` | Reports by default only vulnerabilities in code the program calls, so a vulnerable module that is imported but unreached is not listed. That is usually the right signal, but say so in the report. |
| Ruby | `bundle audit check --update` | Without `--update` the advisory database may be stale. |

Record the command, the tool version, the date and the full output. A clean result from a tool that
read the wrong manifest is worse than no result.

## Secret scanning

```
gitleaks git -v .
trufflehog git file://.
```

Older gitleaks releases use `gitleaks detect --source .`. Both tools scan full history. Run one in CI
on every push, and treat any hit on a live credential as an incident: rotate first, then clean history.
