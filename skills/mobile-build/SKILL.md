---
name: mobile-build
description: Build mobile applications that survive a bad network, a killed process, a store review and a release you cannot roll back. Use when the user asks to build an iOS or Android app, asks about Swift, SwiftUI, Kotlin, Jetpack Compose, Kotlin Multiplatform, React Native, Flutter or Expo, asks about offline support, push notifications, permissions, deep links, universal links, secure token storage or Keychain, in-app purchase, TestFlight, Play Console, or app store submission, or says the app was rejected by Apple, crashes on launch, is slow, or drains battery. Plans offline behaviour first, keeps secrets out of the binary, plans for old versions living for years, and retrieves current store rules. Triggers on build an iOS app, build an Android app, app store rejection, rejected by Apple, deep linking, forced update, mobile performance, battery drain. For staged rollout and release trains use release-manage; for web apps use frontend-build.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Mobile build

The failure this corrects: building a mobile app as if it were a web app. A web deploy can be reverted in
minutes. A shipped binary stays on phones for years, runs against your API long after you changed it,
gets killed by the operating system mid task, and has to pass a reviewer before any fix reaches users.

## When to use and when to stay off

Run when the user is building, architecting, debugging or submitting a native or cross platform mobile
app, or choosing between native, cross platform and an installable web app.

Stay off for a responsive website or a web app that will never be packaged for a store; that goes to
`frontend-build`. Stay off for a pure store listing copy question with no technical consequence.

Routing. Phased rollout, release trains, versioning and rollback plans go to `release-manage`. Threat
modelling, attestation backends and credential handling in depth go to `security-hardening`. The API the
app talks to, including versioning and the minimum version endpoint, goes to `backend-build`.

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of the
session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Decide the offline behaviour before building screens. Read only cache, queued writes, and full sync with conflict resolution are three different applications.
2. Assume the process is killed at any moment. Anything not persisted is gone.
3. No secret in the binary. Third party API keys go behind your own backend proxy. Tokens go in the Keychain on iOS and the Keystore backed encrypted storage on Android, never in AsyncStorage, SharedPreferences or UserDefaults.
4. A shipped binary cannot be rolled back. Ship crash reporting, a server driven minimum version check, and backward compatible APIs before the first release.
5. State the minimum OS version and oldest target device, and retrieve API availability and current store floors for them. Recall about platform versions and store rules is often wrong.
6. Request each permission at the moment it is needed, with an explanation. Denial is a normal path that has to work.
7. Verify the release build on a real device on a slow connection.

## Procedure

### Step 1, decide the platform strategy honestly

Native (Swift, Kotlin) gives the best performance, first access to new platform features, and the best
debugging. It costs two codebases when both platforms are needed.

React Native and Flutter share most code and suit interface heavy apps. React Native's New Architecture
(JSI, Fabric, TurboModules) is the default since 0.76, so native calls no longer go through the old
asynchronous bridge. The costs that remain for both are a harder path to platform specific features,
larger binaries, and waiting on the framework and its libraries after each OS release. Check that every
native library you need supports the architecture you are on. Kotlin Multiplatform shares business logic
and keeps native UI on each side.

An installable web app is far cheaper. iOS supports Web Push for web apps added to the Home Screen since
iOS 16.4, and not in a browser tab. Background work and hardware access stay limited on both platforms.

Pick on the constraint that binds: team skill, required platform features, and whether one or two
platforms must ship. Say which constraint decided it.

### Step 2, plan data and sync first

List what the user can do with no connection. That list sets the storage design.

For queued writes, decide the conflict rule now. Last write wins loses data silently. Server authority
can discard user work. Merge is correct and the most work. Say what the user sees when a change is
rejected.

Give every queued operation an idempotency key. Store queued work durably. Show sync state in the
interface.

### Step 3, plan for versions you cannot recall

Old versions keep running for years. Every API change the app depends on must stay backward compatible,
or be versioned, for as long as the oldest supported build is in use.

Add a minimum supported version check at launch, driven by the server, with a soft prompt and a hard
block. It is the only way to retire a build with a security bug.

Ship crash reporting and symbol upload from the first build, so a crash on launch in the field is
diagnosable. Release through phased rollout on the App Store and staged rollout in Play Console, and halt
when crash-free sessions drop. Rollout mechanics are in `release-manage`.

### Step 4, build for interruption and background limits

Save draft input as it is typed. Restore navigation, scroll position and forms after a cold start.

Handle a resume after days: tokens expired, cached data stale.

Handle a launch from a notification or deep link into an arbitrary screen, with no navigation history.

Background work is not guaranteed. iOS `BGTaskScheduler` runs tasks when the system chooses, possibly
never. Android Doze and App Standby defer work; use WorkManager for deferrable work. Android 14 requires a
declared foreground service type and matching permission for every foreground service. Design so a task
that never ran in the background runs on next launch.

### Step 5, security on the device

Tokens and keys: Keychain on iOS, Android Keystore (directly or through an encrypted storage library that
uses it). Plain preferences files and AsyncStorage are readable on a rooted or backed up device.

Keys for third party services go on your server, and the app calls your server. To make it harder for
scripts to impersonate the app, use App Attest or DeviceCheck on iOS and the Play Integrity API on Android,
verified on the server. Attestation raises cost for an attacker, it does not make the client trusted.

Deep links. Use Universal Links (an `apple-app-site-association` file on your domain) and Android App Links
(`assetlinks.json` under `/.well-known/`, with `autoVerify`). Custom URL schemes can be registered by any
app and hijacked. Treat every link parameter as untrusted input: validate it, and never perform an action
such as a payment or login from a link without confirmation.

### Step 6, notifications

Android 13 and later need the `POST_NOTIFICATIONS` runtime permission. iOS needs authorisation before
alerts show. Ask in context, after the user has a reason to say yes, and keep the feature usable when
refused.

Push tokens change. Handle the refresh callback (FCM `onNewToken`, the APNs registration callback on
every launch) and update the server, or delivery fails silently.

### Step 7, respect the shared resources

Network: batch, deduplicate, cache with a stated freshness, timeout and retry with backoff.

Battery: background work through the platform scheduler; location at the lowest accuracy that works.

Data: assume a metered connection and size images for the device.

Storage: cap the cache and evict. Memory: downsample large images before display.

### Step 8, the paths that get skipped

Permission denied, or granted then revoked in settings. Storage full. No network on first run. Token
expired while backgrounded. OS older than the newest API used.

Accessibility: screen reader labels, reduced motion, and large text. Test the largest Dynamic Type sizes
on iOS and the largest font scale on Android, since fixed height layouts clip text at both.

### Step 9, submission

Read the current rules at the source on the day you submit: the
[App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) and
[Google Play policies](https://play.google.com/about/developer-content-policy/). Rejection causes per store,
the privacy manifest, App Tracking Transparency, the Play data safety form, account deletion, SDK and
target API floors, in-app purchase rules, and a reviewer notes template are in
`references/store-review.md`.

If the app lets users create accounts, both stores require in-app account deletion, and Google Play also
requires a web link where users can request deletion without the app installed.

Test the release build, not the debug build.

## Self-audit

- Offline behaviour and conflict rule written down; queued work durable and idempotent.
- State restored after a process kill.
- No secret in the binary; third party keys behind a proxy; tokens in Keychain or Keystore.
- Crash reporting, server driven minimum version, and backward compatible APIs in place before release.
- Phased or staged rollout planned, with a halt condition.
- Minimum OS stated; current SDK and target API floors retrieved, with the date.
- Background work tolerates never running; Android 14 foreground service types declared.
- Deep links verified by domain; link parameters validated.
- Notification permission requested in context; token refresh handled.
- Largest Dynamic Type and Android font scale checked, with screen reader.
- Privacy manifest, ATT and data safety form match what the app and its SDKs collect.
- Account deletion in app, plus the web deletion link for Google Play.
- Release build tested on a real device, with a demo account prepared.

## What this cannot do

It cannot tell you the current store rules, SDK floors, or fees from memory with confidence. Those change
yearly, so it will tell you where to retrieve them.

It cannot predict a specific reviewer's decision. Reviews vary, and an appeal is sometimes the only path.

It does not give legal advice on privacy law or payment rules. For an app handling health, children's or
financial data, or selling digital goods through an external payment link, ask a lawyer who handles app
store and privacy matters: "Given the data this app collects and the regions it ships to, which consent,
disclosure and payment rules apply, and does our store listing and in-app flow satisfy them?"
