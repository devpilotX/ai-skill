# Frontend checklist

## Forms

Validate each field on blur the first time, and the whole form on submit. Once a field shows an error,
re-validate it on every input so the message disappears as soon as the value is fixed. Validating an
untouched field on every keystroke tells people their email is invalid while they are still typing it.

Show the error next to the field and link it with `aria-describedby="field-error-id"`, and set `aria-invalid="true"`, so a
screen reader announces it. Colour alone is not an error message. On submit with errors, move focus to
the first invalid field or to an error summary that links to each field.

Keep the submit control enabled and focusable while the request is in flight. A disabled button loses
focus and may not be announced. Ignore repeat submits in the handler, show the pending state visibly,
and announce it with `aria-busy="true"` on the form or a polite live region. Announce the result when it
arrives.

Make submission idempotent on the server. The client will send it twice regardless of what the button
does.

Preserve what the user typed when submission fails. Clearing a form on error makes them start over.

Warn before navigating away from unsaved changes, and do not warn when nothing changed.

Use correct input types and `autocomplete` attributes, so browsers and password managers can fill the
form.

Never disable paste on a password or code field. WCAG 2.2 success criterion 3.3.8 (Accessible
Authentication, Minimum) treats blocking paste into a password field as a failure.

Handle the case where the server rejects something the client considered valid. The server is the
authority and its message has to be displayable next to the right field.

For multi step forms, keep state where a refresh does not destroy it.

## Mutations

Optimistic updates keep the previous value, restore it if the request fails, and tell the user what did
not save. An optimistic update with no rollback shows data the server never accepted.

Cancel or ignore responses to requests that a newer request superseded, so an old response cannot
overwrite a newer value.

## The six data states

Every data view handles loading, empty, error, partial, offline or stale, and success.

Loading shows a skeleton matching the eventual layout, so content arriving does not shift the page.
Time out a request instead of spinning forever.

Empty says what it is, why it is empty, and what to do about it. An empty table with no message looks
broken.

Error says what failed and what the user can do, with a retry control on anything transient. Keep
loading, empty and error visually distinct, since all three tend to render as a blank area.

Partial handles one source failing among several. When one of four panels fails, three still work and
the fourth says why.

Offline or stale covers data that loaded and is now out of date, or a network that dropped. Show the
cached data with its age and a refresh control, and queue or block writes explicitly.

Success is the state everyone builds first. It still needs long content, many items, and a language that
expands.

## Lists and tables

Paginate or virtualise anything unbounded. A list built against fifty rows will eventually receive
fifty thousand.

Put sort, filter and page in the URL so the view can be shared and survives a refresh.

Keep row actions reachable by keyboard.

Provide a loading state that does not collapse the layout.

Say how many results there are, and what the filter excluded.

## Responsive behaviour

Design the narrow viewport first, since it forces priority decisions that the wide layout hides.

Test at 200 percent zoom (WCAG 1.4.4) and at 320 CSS pixels wide with no horizontal scrolling (WCAG
1.4.10). Both break fixed heights and fixed widths.

Targets at least 24 by 24 CSS pixels (WCAG 2.5.8), and 44 to 48 on touch screens following the Apple and
Material platform guidelines. Criteria and thresholds are in `references/accessibility.md`.

Nothing important behind hover, because touch devices have no hover.

Test with long strings and with a language that expands.

## Client performance

Measure with the profiler and a throttled network before changing anything, and report the numbers.
Targets and field versus lab data are in `references/web-vitals.md`.

Ship less JavaScript before optimising the JavaScript you ship.

Split by route, and lazily load anything below the fold or behind an interaction.

Serve images at display size in a modern format, with width and height set to reserve space.

Reserve space for anything that loads late, including fonts and advertisements, to avoid layout shift.

Fetch at the route level instead of deep in the tree, to avoid request waterfalls.

Debounce input driven requests, and cancel superseded ones.

Apply memoisation to a measured re-render problem, not as a habit.

## Dependencies

Measure the bytes the dependency adds to the shipped bundle after tree shaking, minified and compressed
with gzip or brotli, the way the server sends it. The install size on disk and the published package
size both mislead: they include files that never ship, and they ignore how much of the package your
imports actually pull in. Measure with the bundler's analyser or by diffing a production build before
and after, and state the number.

Check whether the platform already does it. Date formatting, unique identifiers, deep cloning, fetching
and form state all have native or near native options now.

Check maintenance status and how many transitive dependencies arrive with it.

Prefer one utility you understand over a framework you adopt for one function.

## Before calling it done

Keyboard only pass through every path, including modals and menus.

One screen reader pass, following the protocol in `references/accessibility.md`.

Small viewport and 320 pixel reflow pass.

Throttled network pass, and an offline pass.

Failing API pass, and an API returning the wrong shape.

Empty data pass.

Console clean of errors and warnings.

No secret or internal endpoint visible in the shipped bundle, and no untrusted string reaching an HTML
sink.
