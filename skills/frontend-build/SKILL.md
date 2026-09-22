---
name: frontend-build
description: Build user interfaces that hold up on real networks, real devices and real input. Use when the user asks to build a UI, a web app, a page, a component, a dashboard, a form or a design system, asks about React, Vue, Svelte, Angular, Next.js or any frontend framework, asks about state management, routing, styling, responsive layout, accessibility or client performance, or asks why their interface is slow or broken on mobile. Covers the states most interfaces omit, which are loading, empty, error, partial and offline, keeps state in the narrowest scope that works, treats accessibility and keyboard operation as part of the build rather than a later pass, and budgets bundle size in kilobytes before adding a dependency. Triggers on build a UI, build a frontend, React component, state management, responsive design, accessibility, my site is slow, form validation, design system, dashboard.
license: MIT
metadata:
  version: 1.0.0
  suite: ai-skill
---

# Frontend build

Most interface defects are not layout. They are states nobody implemented and inputs nobody expected.

## Non-negotiables

1. Every view that fetches data implements five states: loading, empty, error, partial, and success. Shipping only the success state is the most common frontend defect, and it is the one users hit first.
2. Keyboard operation of every interactive path, verified by actually tabbing through it. An interface that needs a mouse excludes people and fails most accessibility requirements.
3. Server side validation for everything validated in the browser. Client validation is a convenience for the user, never a control.
4. Check the real rendered output before claiming it works. Say which command was run or which page was opened. A component that compiles has not been seen.
5. Budget the bundle. State the size cost in kilobytes before adding a dependency, and check whether the platform already does it.
6. Never invent an API shape. Read the contract, or agree it with the backend and write it down.
7. No secret in client code. Anything shipped to a browser is public, including values injected at build time.

## Procedure

### Step 1, work out the data and the states

Before any markup, list what each view needs, where it comes from, and what happens when it is absent,
slow, stale or wrong. This list is the actual design work.

Decide who owns each piece of data. Server state that happens to live in a component is the root of most
state management pain.

### Step 2, choose state placement, narrowest first

Local component state for anything one component uses. Most state is this, and treating it otherwise
creates work.

Lifted to a common parent when siblings share it.

URL for anything a user should be able to link to, refresh into, or navigate back to. Filters, tabs,
pagination and selected item belong in the URL far more often than they are put there.

Server cache layer for data fetched from an API, using a library built for it, since caching,
revalidation, deduplication and stale handling are where hand rolled code goes wrong.

Global store only for genuinely cross cutting client state such as theme, locale, or the current user.
A global store used for server data is a cache with no invalidation strategy.

The ordering matters. Reaching for a global store first produces the tangle people blame on frameworks.

### Step 3, build the component boundaries

Split on data ownership and reuse, not on file length. A long component doing one thing is easier to
work with than six coupled ones.

Keep presentation components free of fetching, so they can be rendered in any state for testing.

Push conditional rendering to the edges. Deeply nested conditionals in markup are where states get lost.

### Step 4, forms, which deserve their own step

Forms carry more edge cases than the rest of the interface combined. The checklist is in
`references/checklist.md`, covering validation timing, error announcement, submission state, double
submit, unsaved changes, and browser autofill.

### Step 5, accessibility during the build

Semantic elements first. A button element behaves correctly with no work, and a div with a click handler
needs role, tabindex, key handling and focus styling to reach the same place.

Labels associated with inputs. Errors linked to their field and announced, not only coloured.

Focus managed on route change, on dialog open, and on dialog close. Focus trapped inside a modal.

Contrast checked against current [WCAG guidance](https://www.w3.org/WAI/standards-guidelines/wcag/)
rather than judged by eye.

Reduced motion preference respected.

Retrofitting accessibility costs several times more than building it in, because it changes markup
structure.

### Step 6, performance with measurement

Measure before optimising. Use the browser profiler and a network throttle, and report the numbers.

The usual wins, in order: send less JavaScript, split by route, load below the fold content lazily, size
and format images correctly, and avoid layout shift by reserving space.

Watch for the waterfall, meaning a request that waits for a component that waits for another request.
Fetching at the route level removes most of these.

Virtualise long lists rather than rendering thousands of rows.

Memoisation is a last step, applied to a measured problem. Applied everywhere it adds code and slows
things down.

### Step 7, verify on real conditions

Throttled network and a mid range device, not a fast laptop on office wifi.

Small viewport and 200 percent zoom.

Keyboard only.

Long content, empty content, and content in a language that expands, such as German, which breaks fixed
width layouts.

Slow API, failing API, and an API returning an unexpected shape.

## Self-audit

- All five states implemented for every data view.
- State sits in the narrowest scope that works, and linkable state is in the URL.
- Keyboard path tested by tabbing through it.
- Labels, focus management and contrast done.
- Bundle size cost of each dependency stated.
- Performance claims backed by measured numbers.
- Tested at small viewport, throttled network, and with a failing API.
- No secret in anything shipped to the browser.
