---
name: frontend-build
description: Build web interfaces that hold up on real networks, devices and input. Use when the user asks to build a UI, web app, page, component, dashboard, form or design system, asks about React, Vue, Svelte, Angular, Next.js, state management, routing, CSS, Tailwind, responsive layout, SSR, hydration, accessibility, WCAG, screen readers, Core Web Vitals, Lighthouse or layout shift, or asks why a page is slow or broken on mobile. Implements six data states (loading, empty, error, partial, offline or stale, success), keeps state in the narrowest scope, builds keyboard and screen reader support in from the start, and budgets the compressed bytes each dependency adds. Triggers on build a UI, build a frontend, React component, state management, CSS, Tailwind, SSR, hydration, Core Web Vitals, Lighthouse, WCAG, screen reader, layout shift, form validation, design system, dashboard. For React Native use mobile-build. For whole app slowness diagnosis use performance-tuning. For multi component builds use build-pilot.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Frontend build

Interfaces get built for the success state on a fast laptop with a mouse, then fail for the person on a
slow phone network, the keyboard or screen reader user, the empty account, and the API that returns an
error. Those failures are states nobody implemented and inputs nobody tried. This skill implements them
during the build.

## When to use and when to stay off

Run when the user is building or fixing a web interface: views, components, forms, state, styling,
rendering strategy, accessibility, or client performance.

Stay off when:

- The question is a syntax or API lookup. Answer it.
- The app is React Native or another native mobile stack. That belongs to `mobile-build`.
- The user wants a whole app's slowness diagnosed across client, network and server. That belongs to `performance-tuning`. This skill still applies to the frontend fixes that come out of it.
- The work spans several components such as frontend, backend and data. `build-pilot` coordinates it, and this skill handles the frontend part.
- The API itself is being designed. That belongs to `backend-build`.

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of the
session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Every view that fetches data implements six states: loading, empty, error, partial, offline or stale, and success.
2. Every interactive path works by keyboard, verified by tabbing through it, and meets WCAG 2.2 AA ([W3C](https://www.w3.org/TR/WCAG22/)).
3. The server validates everything the browser validates. Client validation is a convenience, never a control.
4. Check the rendered output before claiming it works, and say which command was run or which page was opened.
5. State the minified and compressed bytes a dependency adds to the shipped bundle before adding it.
6. Never invent an API shape. Read the contract, or agree it with the backend and write it down.
7. No secret in client code, and no untrusted string into an HTML sink. Anything shipped to a browser is public.

## Procedure

### Step 1, work out the data and the six states

Before any markup, list what each view needs, where it comes from, and what it shows in each of the six
states. Offline or stale covers data that loaded and is now out of date or unreachable, which needs a
refresh affordance and a visible age, not an error screen. Partial covers one of several sources failing
while the rest work.

Decide who owns each piece of data. Server state copied into a component is where most state
management pain starts.

### Step 2, choose the rendering strategy per route

Decide per route, not per app. Client side rendering suits authenticated, highly interactive views.
Server side rendering suits content that must be visible fast and indexed. Static generation suits
content that changes rarely. Streaming server rendering sends the shell first and fills slow parts later.

Count the hydration cost. Server rendered HTML is visible before it is interactive, and hydrating a large
tree blocks the main thread, which shows up in Interaction to Next Paint. Hydrate less: smaller client
components, server components or islands where the framework supports them, and no client JavaScript on
parts that never change.

### Step 3, place state, narrowest first

Local component state for anything one component uses. Lift to a common parent when siblings share it.
Put anything a user should be able to link to, refresh into, or go back to in the URL: filters, tabs,
pagination, selected item. Use a server cache library for API data, since caching, revalidation,
deduplication and staleness are where hand rolled code goes wrong. Use a global store only for client
state that is truly global, such as theme, locale, or the current user. A global store holding server
data is a cache with no invalidation strategy.

### Step 4, build the component boundaries

Split on data ownership and reuse, not on file length. Keep presentation components free of fetching,
so each can be rendered in every state for testing. Push conditional rendering to the edges, since
deeply nested conditionals in markup are where states get lost.

### Step 5, forms and mutations

Validate a field on blur the first time. Once it shows an error, re-validate on every input so the error
clears as soon as the value is fixed. Validate the whole form on submit.

Do not rely on disabling the submit button during a request. A disabled button drops keyboard focus and
may not be announced. Keep it enabled, ignore repeat submits while one is in flight, and announce the
pending state with `aria-busy="true"` on the form or a polite live region. The server makes submission
idempotent regardless.

Optimistic updates need a rollback: keep the previous value, restore it on failure, and tell the user
what did not save.

The full checklist, including unsaved changes, autofill and server rejection, is in
`references/checklist.md`.

### Step 6, accessibility during the build

Semantic elements first. A `button` element behaves correctly with no work. A `div` with a click
handler needs a role, tabindex, key handling and focus styling to reach the same place.

WCAG 2.2 AA thresholds to build to ([WCAG 2.2](https://www.w3.org/TR/WCAG22/)):

- Text contrast at least 4.5:1, large text at least 3:1 (1.4.3).
- Non-text contrast at least 3:1 for UI component boundaries, focus indicators and meaningful graphics (1.4.11).
- Pointer targets at least 24 by 24 CSS pixels, or spaced so a 24 pixel circle does not overlap another target (2.5.8). That is the floor. On touch screens aim for the platform guidelines: 44 by 44 points in Apple's Human Interface Guidelines and 48 by 48 dp in Material Design.
- Content usable at 200 percent zoom (1.4.4) and reflowing without horizontal scrolling at 320 CSS pixels wide (1.4.10).

Labels tied to inputs. Errors linked to their field and announced, not only coloured. Focus moved on
route change and into and out of dialogs. Reduced motion respected. Patterns, focus recipes and the test
protocol are in `references/accessibility.md`.

### Step 7, client security

Never pass untrusted strings to an HTML sink: `dangerouslySetInnerHTML` in React, `v-html` in Vue,
`innerHTML` and `outerHTML`, `document.write`, or `eval`. If HTML must be rendered, sanitise it with a
maintained sanitiser first. See the
[OWASP XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html).

Send a Content Security Policy that forbids inline script, using nonces or hashes for what must run
inline.

Store session tokens in an `HttpOnly`, `Secure`, `SameSite` cookie, which script cannot read, and add
CSRF protection for cookie authenticated writes. A token in `localStorage` is readable by any script that
runs on the page, so one XSS bug exposes it. Deeper review belongs to `security-hardening`.

### Step 8, performance with measurement

Core Web Vitals, judged at the 75th percentile of field data
([web.dev](https://web.dev/articles/vitals)): Largest Contentful Paint 2.5 s or less, Interaction to Next
Paint 200 ms or less, Cumulative Layout Shift 0.1 or less. INP replaced First Input Delay as a Core Web
Vital in March 2024. Lighthouse is a lab tool: use it to debug, and use field data from real users to
judge. Details and fixes per metric are in `references/web-vitals.md`.

Measure before optimising. Then, in order: send less JavaScript, split by route, lazy load below the
fold content, size and format images, and reserve space for anything that loads late. Fetch at the route
level to avoid request waterfalls. Virtualise long lists. Memoise only a measured re-render problem.

### Step 9, verify on real conditions

A throttled network and a mid range device. Small viewport, 320 CSS pixels wide, and 200 percent zoom.
Keyboard only, then one screen reader. Long content, empty content, and a language that expands, such
as German. A slow API, a failing API, an API returning an unexpected shape, and the browser offline.

## Self-audit

- All six states implemented for every data view, and the list is the same everywhere it appears.
- Rendering strategy chosen per route, with the hydration cost considered.
- State sits in the narrowest scope that works, and linkable state is in the URL.
- Keyboard path tested by tabbing, and one screen reader pass done.
- Contrast, non-text contrast, target size and reflow checked against the WCAG 2.2 numbers above.
- Submit stays focusable during a request, repeat submits are ignored, and the pending state is announced.
- Every optimistic update has a rollback.
- No untrusted string reaches an HTML sink, a CSP is set, and tokens are not in `localStorage`.
- Compressed bytes added by each new dependency stated.
- Web Vitals claims name their source, field or lab.
- Tested at small viewport, throttled network, offline, and with a failing API.

## What this cannot do

It cannot see the rendered page unless someone opens it and reports what happened. It cannot produce
field Web Vitals data, which only comes from real users over time.

Automated accessibility checkers find only a portion of WCAG failures. Passing axe is not conformance,
and nothing here replaces testing with disabled users.

Legal accessibility obligations vary by market and sector. Ask a lawyer who practises accessibility or
consumer law: "Which accessibility standard and conformance level must this product meet in each market
where we sell it, from what date, and what documentation, such as an accessibility statement, must we
publish?"
