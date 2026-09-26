# Store review

Store rules change several times a year, and guideline numbers move. Everything here is a map of what to
look up. Retrieve the current text on the day you submit, note the retrieval date in the release notes,
and trust the retrieved text over this file.

Sources:

- [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- [Google Play Developer Policy Center](https://play.google.com/about/developer-content-policy/)

## Recurring rejection causes

App Store, by guideline section as named in the App Review Guidelines (retrieve to confirm numbering):

| Cause | Guideline |
|---|---|
| Crash, broken link, placeholder content, no demo account | 2.1 App Completeness |
| Screenshots or description that do not match the app | 2.3 Accurate Metadata |
| Private or undocumented API use | 2.5.1 Software Requirements |
| Digital goods sold outside In-App Purchase | 3.1.1 In-App Purchase |
| A thin wrapper around a website | 4.2 Minimum Functionality |
| Third party login offered without an equivalent privacy focused option | 4.8 Login Services |
| Missing privacy policy, data collection not disclosed, no account deletion | 5.1.1 Data Collection and Storage |
| Tracking without App Tracking Transparency consent | 5.1.2 Data Use and Sharing |

Google Play, by policy area as named in the Policy Center:

| Cause | Policy area |
|---|---|
| Data safety form does not match actual collection, including SDKs | User Data |
| Sensitive permissions (SMS, call log, location in background, all files) without an approved use | Permissions and APIs that Access Sensitive Information |
| Digital goods sold outside Google Play Billing where not permitted | Payments |
| No in-app deletion, or no web deletion link | Account deletion requirement under User Data |
| Target API level below the current floor | Target API level requirement |
| Misleading metadata or functionality | Deceptive Behavior |

## Apple privacy manifest

Apps and third party SDKs include a `PrivacyInfo.xcprivacy` file declaring collected data types, tracking
domains, and the reason for each use of a required reason API (for example file timestamp, system boot
time, disk space and UserDefaults APIs). Retrieve the current list of required reason APIs and approved
reason codes from Apple's developer documentation on privacy manifests. Check that every SDK you ship has
its own manifest, and update SDKs that do not.

## Tracking consent (ATT)

If the app or any SDK links user or device data with data from other companies' apps or sites for
advertising, or shares it with data brokers, it must show the ATT prompt and respect the answer. Reading
the IDFA requires authorisation. Declare the purpose string in `Info.plist`. Tracking domains listed in the
privacy manifest are blocked until the user allows tracking.

## Google Play data safety form

Declare what is collected and shared, whether it is encrypted in transit, and whether users can request
deletion. It covers SDK behaviour, so inventory each SDK's data collection from its vendor documentation.
A mismatch between the form and observed behaviour is a policy violation even if the app itself collects
nothing.

## Account deletion

Both stores require deletion to be started from inside the app if the app supports account creation.
Google Play also requires a web resource where users can request account and data deletion without
reinstalling, and the link goes in the data safety section. Retrieve the current text for what must be
deleted versus what may be retained for legal reasons, and say which applies in the app's deletion screen.

## SDK and target API floors

Apple sets a minimum Xcode and SDK version for uploads, and Google Play sets a minimum target API level
for new apps and updates, both raised on a yearly cadence. Retrieve the current values and their
enforcement dates from the Apple Developer news page and the Play Console Help article on target API level
requirements. Plan the upgrade before the enforcement date, because a target API bump changes runtime
behaviour (permissions, background limits, intents) and needs testing.

## In-app purchase and digital goods

The general rule on both stores: digital content and features consumed in the app are sold through the
platform billing system. Physical goods and services consumed outside the app, such as a ride or a
delivery, use any processor. Reader apps, person to person services, and enterprise apps have specific
carve-outs.

Regional exceptions exist and change with regulation and litigation, including alternative billing and
external purchase links in some jurisdictions. Retrieve the current rules for each region you ship to from
the App Review Guidelines section 3.1, Apple's developer pages on alternative payment entitlements, and the
Play Console Help pages on alternative billing and the Payments policy. Commission rates and entitlements
differ by region and programme, so retrieve them, never recall them.

## Reviewer notes template

Fill in each line with real values before submitting.

```
Purpose: one sentence on what the app does and who it is for.
Demo account: username and password for a seeded account that stays valid for the whole review.
Steps to reach the main feature: numbered steps from launch.
Features behind hardware, location or a subscription: how the reviewer can see them, with a video link if they cannot.
Permissions: each permission requested and the screen where it is used.
Payments: what is sold, and whether it uses In-App Purchase or why it does not.
Account deletion: the path in the app, for example Settings, Account, Delete account.
Changes since the last review: what changed, especially anything tied to a previous rejection.
Contact: a phone number and email monitored during review.
```
