# Accessibility

The standard is WCAG 2.2 at level AA ([W3C Recommendation](https://www.w3.org/TR/WCAG22/)). Criterion
numbers below refer to it. Widget behaviour follows the
[WAI-ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/).

## Criteria that fail in practice, with thresholds

The yearly [WebAIM Million](https://webaim.org/projects/million/) scan of home pages ranks detected
failures. Its recent reports put low contrast text, missing image alternative text, missing form labels,
empty links, empty buttons and a missing page language at the top. Retrieve the current report for the
current ranking and percentages. The list below covers those plus the AA criteria new in 2.2.

- 1.1.1 Non-text content. Every meaningful image has alternative text, and decorative images have `alt=""`.
- 1.3.1 Info and relationships. Headings, lists, tables and labels are in the markup, not only in the styling.
- 1.4.3 Contrast (minimum). 4.5:1 for text, 3:1 for large text, which WCAG defines as at least 18 point, or 14 point bold.
- 1.4.4 Resize text. Usable at 200 percent zoom with no loss of content or function.
- 1.4.10 Reflow. No horizontal scrolling at 320 CSS pixels wide, except for content such as data tables and maps that needs two dimensions.
- 1.4.11 Non-text contrast. 3:1 for input borders, focus indicators, icons that carry meaning, and chart elements.
- 1.4.12 Text spacing. Nothing breaks when users increase line, paragraph, letter and word spacing to the values the criterion lists.
- 1.4.13 Content on hover or focus. Tooltips can be dismissed without moving the pointer, can be hovered, and stay until dismissed.
- 2.1.1 Keyboard. Everything works from the keyboard, with no keyboard trap (2.1.2).
- 2.4.3 Focus order and 2.4.7 Focus visible. Focus moves in a logical order and is always visible.
- 2.4.11 Focus not obscured (minimum), new in 2.2. A sticky header or cookie banner must not fully hide the focused element.
- 2.5.7 Dragging movements, new in 2.2. Anything done by dragging also works with single pointer clicks.
- 2.5.8 Target size (minimum), new in 2.2. At least 24 by 24 CSS pixels, or spaced so a 24 pixel circle centred on the target touches no other target. Inline links in text are exempt.
- 3.3.1 Error identification and 3.3.2 Labels or instructions. Errors are described in text, and inputs have visible labels.
- 3.3.8 Accessible authentication (minimum), new in 2.2. No cognitive test to log in, and paste and password managers must work.
- 4.1.2 Name, role, value. Custom controls expose all three to assistive technology.
- 4.1.3 Status messages. Results, errors and progress that appear without a focus change are announced through a live region.

## Widget patterns

Prefer a native element when one exists. Use the APG pattern when it does not, including its keyboard
model, since users expect the keys it defines.

Dialog. Use the native `dialog` element opened with `showModal()`. It makes the rest of the page inert,
closes on Escape, and places focus inside. Give it an accessible name with `aria-labelledby="heading-id"` pointing at
its heading. On close, return focus to the control that opened it. Check the focus behaviour in each
target browser, since initial focus placement has differed between engines.

Menu. The APG menu and menubar patterns are for application style command menus, with arrow key
navigation and `role="menu"`. A site navigation list with dropdowns is a disclosure: a `button` with
`aria-expanded="false"` (toggled on open) controlling a list of links. Using `role="menu"` for site navigation changes how screen
readers present it and breaks Tab navigation expectations.

Tabs. `role="tablist"`, `role="tab"` and `role="tabpanel"`, with `aria-selected="true"` on the active tab and `aria-controls="panel-id"` on each. Only
the active tab is in the Tab sequence (roving tabindex). Arrow keys move between tabs. Decide between
automatic activation on arrow and manual activation with Enter or Space, and use manual when a panel is
slow to load.

Combobox. An input with `role="combobox"`, `aria-expanded="true"` while open, and `aria-controls="listbox-id"` pointing at a
`role="listbox"` popup. Keep DOM focus in the input and indicate the highlighted option with
`aria-activedescendant="option-id"`. Announce the result count through a polite live region as the user types.
This is the pattern with the most ways to go wrong, so prefer a maintained, tested component.

## Focus management recipes

Route change in a single page app. After the new view renders, move focus to its main heading, given
`tabindex="-1"` so it can take focus, and update `document.title`. Without this, a screen reader user
hears nothing and keyboard focus stays on a link that no longer exists.

Dialog open and close. Focus goes to the first control, or to the heading if the content needs reading
first. On close, focus returns to the element that opened the dialog, or to a sensible successor if that
element was removed.

Toast or notification. Do not move focus. Render the text into a live region that already exists in the
DOM before the message is inserted, since a region added along with its content is often not announced.
Use `role="status"` for information and `role="alert"` only for errors that need attention now. A toast
that holds an action must not disappear on a timer (2.2.1 Timing adjustable), and its action must also
be reachable somewhere persistent.

Deleting an item from a list. Move focus to the next item, or to the previous one if the last was
removed, or to the list heading when the list becomes empty.

Form submit with errors. Move focus to an error summary with links to each field, or to the first
invalid field.

## Test protocol

1. Automated scan with axe (browser extension, or axe-core in the test suite) on every view and in each of the six data states. Fix everything it reports. It catches only the machine checkable portion of WCAG, so continue.
2. Keyboard pass with the mouse unplugged or ignored. Reach and operate every control, see the focus indicator at every stop, confirm no traps, and confirm Escape closes overlays.
3. Zoom to 200 percent, then set the viewport to 320 CSS pixels wide. Nothing overlaps, truncates, or needs horizontal scrolling.
4. One screen reader per platform the product supports: NVDA with Firefox or Chrome on Windows, VoiceOver with Safari on macOS and iOS, TalkBack with Chrome on Android. Walk the main task end to end, listening for names, roles, states and announcements of errors and status messages.
5. Operating system settings: reduced motion, forced colours or Windows contrast themes, and increased text size.
6. Record which views, browsers and assistive technologies were tested, and which were not.
