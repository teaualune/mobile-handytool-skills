---
name: store-submission-prep
description: Prepare a first-time App Store / Google Play submission handover sheet from a mobile app codebase (native iOS Swift/Objective-C, native Android Kotlin/Java, React Native/Expo, Flutter). Scans the project and writes a prefilled checklist table covering every field on the App Store Connect version and App Information pages and the Play Console App content and Publishing pages, for the app or company owner to complete. Use when the user mentions store submission, App Store Connect, Play Console, app review, store listing, data safety, app privacy labels, a release checklist, or handing submission info to a client or owner.
---

# Store submission prep

Produce a handover sheet that an app/company owner can work through to complete a **first-time** submission on App Store Connect (ASC) and Play Console. The sheet is both a data table (values to paste) and a checklist (every page and field listed, nothing silently skipped). You fill what the codebase can prove, suggest what it implies, and leave the rest clearly marked for the owner. Code-side problems you notice go in a separate notes file for the developer, so the owner's sheet stays about the owner's job.

Assume a TestFlight build and a Play internal-testing build are already uploaded, and treat the release as a first submission even if the version number is past 1.0 (say so under assumptions). You are not uploading, building, or submitting anything.

Catalog date: **2026-10**. Console UIs drift. If the developer says a label differs, the console wins: keep the row, fix the label. Never drop a row because you are unsure it still exists; mark it "confirm in console". Option lists given below (categories and the like) are as of the catalog date.

## Inputs

Arguments are optional and free-form. Recognise: a platform filter (only when stated as scope, such as "ios only" or "android"), ASC app ID, Play developer ID and Play app ID (the long numbers in console URLs), output path, output language, `csv`. A store name next to a number labels that number ("play dev id 55…" is an ID, not a filter).

Do not block on missing inputs. Unknown IDs stay as `{appID}` / `{devID}` placeholders in URLs. Ask a question only when the answer changes the whole sheet and the repo cannot settle it: several shippable apps/targets/flavors with no obvious production one. Otherwise pick the production configuration, say which you picked, and continue.

## Workflow

### 1. Identify the project

| Ecosystem | Tell-tale | Where iOS facts live | Where Android facts live |
|---|---|---|---|
| Flutter | `pubspec.yaml` with a `flutter` dependency | `ios/Runner/`, `ios/Runner.xcodeproj` | `android/app/` |
| React Native (bare) | `package.json` has `react-native`, and `ios/` + `android/` exist | `ios/<App>/`, `ios/<App>.xcodeproj` | `android/app/` |
| Expo (managed / CNG) | `expo` dependency + `app.json` or `app.config.(js\|ts)`, no native folders | app config `expo.ios.*`, `expo.plugins` | app config `expo.android.*` |
| Native iOS | `*.xcodeproj` / `*.xcworkspace`, `Package.swift`, `Podfile` | the app target's folder | n/a |
| Native Android | `settings.gradle(.kts)` and a module applying `com.android.application` | n/a | that module |

A repo may hold both native apps side by side, or one platform only. Cover the stores for the platforms that exist (or that the developer asked for) and omit the other store's sections entirely, saying so in the summary.

Skip vendored and generated folders when searching app code (`node_modules`, `Pods`, `build`, `.gradle`, `.dart_tool`, `DerivedData`, `.symlinks`). Go into them only for the two purposes named in step 3 (SDK privacy manifests, merged Android manifest). If they are absent, do not install dependencies or build to create them; note what could not be read.

### 2. Collect identity facts

| Fact | iOS source | Android source | Cross-platform source |
|---|---|---|---|
| App ID | `PRODUCT_BUNDLE_IDENTIFIER` (Release config of the app target, or `.xcconfig`) | `applicationId` in the app module's Gradle file, plus the production flavor's suffix. `namespace` is not the ID | Expo: `ios.bundleIdentifier`, `android.package` |
| Version / build | `MARKETING_VERSION`, `CURRENT_PROJECT_VERSION` (Info.plist often only references them) | `versionName`, `versionCode` | Flutter: `version: x.y.z+build` in pubspec. Expo: `version`, `ios.buildNumber`, `android.versionCode` (EAS may auto-increment remotely; then the console's build number is authoritative) |
| Display name | `CFBundleDisplayName`, `INFOPLIST_KEY_CFBundleDisplayName`, localized `InfoPlist.strings` / `.xcstrings` | `android:label` → `res/values*/strings.xml` | Expo: `name`, `locales` |
| Device families | `TARGETED_DEVICE_FAMILY` (1 iPhone, 2 iPad) | `uses-feature`, `supports-screens`, form-factor modules | Expo: `ios.supportsTablet` |
| OS levels | `IPHONEOS_DEPLOYMENT_TARGET` | `minSdk`, `targetSdk`, `compileSdk` | Flutter/Expo may inherit defaults from the framework: write "inherited from Flutter/Expo SDK x" instead of guessing a number, and list it under "Could not verify" in the developer notes |
| Languages | `developmentRegion`, `knownRegions`, `*.lproj`, `.xcstrings`, `CFBundleLocalizations` | default `res/values/` language, `res/values-xx/`, `localeConfig`, `resourceConfigurations` | Flutter `l10n/*.arb`; RN i18n resource folders; Expo `locales` (first key as default when nothing else says). Name languages the way the stores do ("English (U.S.)", "Chinese (Traditional)"); plain `en` means English (U.S.) unless the repo says otherwise |
| Console IDs | `DEVELOPMENT_TEAM`; `fastlane/Appfile` (`app_identifier`, `itc_team_id`); `eas.json` `submit.*.ios.ascAppId` | `fastlane/Appfile` `package_name` | Account login emails found in these files are not needed in the sheet; leave them out |
| Store copy already written | `fastlane/metadata/<locale>/*.txt`, `fastlane/metadata/review_information/` | `fastlane/metadata/android/<locale>/`, `src/main/play/` (Gradle Play Publisher) | README, landing-page copy, onboarding strings |
| Company / links | `NSHumanReadableCopyright`, LICENSE | | `package.json` author, pubspec, and any privacy / terms / support / contact URL or email constant in source or string resources |

Copy that already exists in `fastlane/metadata` or similar is the best prefill there is: a person wrote it for exactly this field. Use it verbatim. Copy written for the other store's equivalent field is source material: reuse it as `SUGGESTED`.

### 3. Detect capabilities

Read dependency manifests first (`Podfile.lock`, `Package.resolved`, Gradle files and `libs.versions.toml`, `pubspec.yaml`, `package.json`), then confirm with a targeted search of app code. For each capability record: present or not, the evidence path, and anything that changes an answer (for example "login is optional, guest mode exists"). A dependency that is declared but never called in app code is a finding for the developer notes (if the repo looks partial, with referenced files missing, file it under "Could not verify" instead and still treat the capability as present).

| Capability | Signals | Drives |
|---|---|---|
| Accounts and login | Auth SDKs (Firebase Auth, Supabase, Auth0, Cognito/Amplify, Clerk, Google Sign-In, Facebook Login, `AuthenticationServices`, `sign_in_with_apple`, `expo-apple-authentication`, MSAL, AppAuth), screens named login / sign in / register, OTP flows. Work out: is login needed before any feature, which methods, is there a delete-account flow, and can an account come into existence from inside the app (a sign-up form, or a social / OTP login that creates the account on first use, both count; accounts provisioned only by an administrator outside the app do not, so mark those "confirm") | ASC Sign-in required + review notes; Play Sign-in details; Play Data safety account-deletion rows; developer-notes checks |
| Ads | Google Mobile Ads / AdMob, AppLovin, ironSource/LevelPlay, Unity Ads, Meta Audience Network, Liftoff/Vungle, InMobi, Mintegral; `GADApplicationIdentifier`; `com.google.android.gms.ads.APPLICATION_ID` | Play Ads; Play Advertising ID; ASC age-rating "Advertising" heads-up; privacy tables |
| Tracking / ad identifier | `NSUserTrackingUsageDescription`, `ATTrackingManager`, `ASIdentifierManager`; `com.google.android.gms.permission.AD_ID` (note if removed via `tools:node="remove"` or Expo `blockedPermissions`); attribution SDKs (AppsFlyer, Adjust, Branch, Singular, Kochava); Meta SDK | ASC App Privacy "used for tracking"; Play Advertising ID |
| Analytics and diagnostics | Firebase Analytics, Crashlytics, Sentry, Bugsnag, Datadog, Amplitude, Mixpanel, PostHog, Segment | privacy tables |
| Push notifications | APNs entitlement (`aps-environment`), FCM, OneSignal, Braze, `expo-notifications`, `POST_NOTIFICATIONS` | privacy tables (device token = device ID, when a token is registered with a server); review notes |
| Store purchases | StoreKit usage, `.storekit` files (list product IDs and types), Play Billing, `in_app_purchase`, `react-native-iap`, `expo-iap`, RevenueCat, Adapty, Qonversion, Superwall | ASC In-App Purchases / Subscriptions rows, Paid Apps Agreement; Play payments profile and products; subscription checks |
| Other payments | Stripe, PayPal/Braintree, Adyen, regional gateways, Apple Pay (`PassKit`), Google Pay | privacy tables; if it sells digital content outside store billing, raise it in the developer notes |
| Location | `NSLocation*UsageDescription`, `UIBackgroundModes` location; `ACCESS_FINE/COARSE/BACKGROUND_LOCATION`; location packages | privacy tables; Play background-location declaration; review notes |
| Device data access | Other `NS*UsageDescription` keys; Android dangerous permissions (camera, mic, contacts, calendar, photos/media, Bluetooth, body sensors) | privacy tables, subject to the collection rule below |
| User-generated content, chat, social | feeds, comments, posts, public profiles; chat SDKs (Stream, Sendbird, Agora, Twilio); report/block features. Private content a user syncs to their own account is user content for the privacy tables but not a social feature | heads-up on both rating questionnaires; Play Child safety standards; developer-notes checks |
| Health | HealthKit entitlement, `NSHealth*`; `android.permission.health.*`, Health Connect client, Google Fit; a medical category | ASC Regulated Medical Device status; Play Health apps; Play organisation-account rule |
| Financial | banking, lending, trading, crypto, wallet, insurance features or SDKs (Plaid, WalletConnect, web3 libraries) | Play Financial features; Play organisation-account rule |
| Children | Kids category, child-directed ad flags, COPPA settings | ASC Made for Kids; Play Target audience |
| Open web access | a WebView that can load arbitrary URLs or a built-in browser | ASC age-rating "Unrestricted Web Access" heads-up |
| Encryption | `ITSAppUsesNonExemptEncryption` (Expo: `ios.config.usesNonExemptEncryption`); non-OS crypto (CryptoSwift, libsodium, bundled OpenSSL, SQLCipher, Signal protocol, custom E2EE) versus only HTTPS / CryptoKit / CommonCrypto | ASC export compliance |
| News, government | app is a news publisher/aggregator; app is built for or on behalf of a government body | Play News apps; Play Government apps |
| Platform extras | App Clip target, iMessage extension, watchOS app, Game Center entitlement, `MKDirectionsApplicationSupportedModes` | conditional rows of the ASC version page |
| Sensitive Android permissions | see B1 "Conditional declarations" | the matching Play declaration |

**Two sources that beat inference, when present:**

- *Apple privacy manifests.* `PrivacyInfo.xcprivacy` in the app target (Expo: `expo.ios.privacyManifests` in the app config), and the SDKs' own copies under `ios/Pods/**`, `node_modules/**/ios/**`, or Flutter plugin folders. `NSPrivacyCollectedDataTypes` entries map one-to-one onto App Privacy data types, with purposes, linked and tracking flags. `NSPrivacyTracking` answers the tracking question. If the app's manifest omits data that a bundled SDK typically collects, list both in the privacy table and add a developer-notes item about the mismatch.
- *Merged Android manifest.* The source manifest undercounts: SDKs add permissions at build time (ad and analytics SDKs commonly add `AD_ID`). If a build output exists, read `**/intermediates/merged_manifest*/**/AndroidManifest.xml`. If not, list source-manifest permissions and note that the true list is visible in Play Console's bundle explorer.

**The collection rule.** Both stores define "collected" as data leaving the device from the app. So:
- app code that uploads the data, or an SDK whose purpose is to transmit it (crash reporter → crash data), is evidence: "Yes";
- a type that appears only in the typical-disclosures table below: "Yes (typical for <SDK>, confirm)";
- a code comment or README claim is weaker than code: "Yes (confirm)";
- a permission or usage string alone is not evidence: "Possible, confirm". Keep such rows in the privacy tables; if the store has no matching data type (biometric unlock, for instance), mention it in a line under the table instead;
- records that originate on the server and are only displayed (a prescription, a report) are not collected from the user;
- what users type or upload into the app's own backend is collected. Classify it by what the app asks for: a field that asks for symptoms is health data, a free-text note is other user content. When the content could be sensitive, say so and let the owner choose.

**Typical SDK disclosures** (starting points; each vendor publishes its own disclosure, which the developer should check before the owner signs off):

| SDK family | Apple data types | Play data types | Usual purposes |
|---|---|---|---|
| Firebase / Google Analytics | Device ID, Product Interaction | Device or other IDs, App interactions | Analytics |
| Crashlytics, Sentry, Bugsnag, Datadog | Crash Data, Performance Data, Other Diagnostic Data (+ User ID if the app sets one) | Crash logs, Diagnostics | App functionality, Analytics |
| Push (FCM, OneSignal, Braze) | Device ID (+ User ID, contact info if synced) | Device or other IDs | App functionality; marketing if used for campaigns |
| Auth providers and own account system | Email Address / Phone Number / Name, User ID | Email address / Phone number / Name, User IDs | App functionality; Account management (Play) |
| Ad networks | Device ID, Advertising Data, Product Interaction, Coarse Location, diagnostics | Device or other IDs, App interactions, Approximate location, Diagnostics | Third-party advertising; tracking usually yes |
| Attribution and Meta SDK | Device ID, Product Interaction, Purchase History if revenue events are sent | Device or other IDs, App interactions, Purchase history | Analytics, advertising; tracking depends on configuration |
| Product analytics (Amplitude, Mixpanel, PostHog, Segment) | Product Interaction, Device ID, User ID, Coarse Location | App interactions, Device or other IDs, User IDs, Approximate location | Analytics, Product personalization |
| Purchase SDKs (RevenueCat, Adapty) or own purchase backend | Purchase History, User ID | Purchase history, User IDs | App functionality, Analytics |
| Store billing library alone, no backend record | none by the developer: "Possible, confirm" | same | |
| Payment processors | Payment Info, Name, Email, Physical Address | User payment info, Name, Email address, Address | App functionality |
| Maps with user location | Precise / Coarse Location | Precise / Approximate location | App functionality |
| Support chat (Intercom, Zendesk) | Customer Support, Name, Email, User ID | Other in-app messages, Name, Email address, User IDs | App functionality |
| HealthKit / Health Connect data sent to a server | Health (Apple counts HealthKit data as Health); Fitness for exercise data from other sources | Fitness info for steps and exercise; Health info for medical records, symptoms, vitals | App functionality |

Per-type answers the tables need:
- *Linked to the user (Apple).* Suggest Yes when the app has accounts and the data is stored against the account or the SDK is given a user identifier (`identify`, `setUser`, `setUserId`). Suggest No for SDK data keyed only to an anonymous installation. Otherwise "Confirm".
- *Used for tracking (Apple).* Yes only when data is combined with other companies' data for advertising or shared with data brokers: ad networks, attribution with ad partners. Otherwise No.
- *Processed ephemerally (Play).* Yes only if the data stays in memory and is kept no longer than needed to serve the request. Default "No" for anything stored or logged.
- *Required or optional (Play).* Optional when the user can decline or skip the feature that collects it (an optional profile field, a permission the app works without); otherwise Required.

### 4. Build the sheet

Walk the catalogs below in order and emit one row per catalog row. Decide each row's status with the "Filling rules", then write the files described in "Output".

### 5. Check and hand back

Before finishing, verify with a quick script rather than by eye: every catalog row for the included stores appears at least once (a row you split still counts); every PREFILLED row cites a path and every SUGGESTED row gives its basis; each draft fits its limit (characters, except ASC keywords: 100 **bytes**, CJK characters take 3 each); status counts in the summary match the emitted rows; no password, key or token from the repo appears in either file.

Then tell the developer, briefly: where the two files are, the status counts, the developer to-do items (these are theirs, not the owner's), and the assumptions you made (chosen flavor, primary language, suggested category).

## Filling rules

| Status | Meaning | When to use |
|---|---|---|
| `PREFILLED` | Read directly from the codebase | Config, code or a metadata file states the value. Cite the path |
| `SUGGESTED` | Inferred from code, drafted by you, or a sensible default | Owner confirms or edits. Give the basis: the evidence path, "drafted from README", or "usual choice for a first launch" for catalog defaults that no code can prove |
| `OWNER` | Only the owner knows | Value empty; Notes say what is needed and in what format. A candidate you found but cannot vouch for goes in Notes, not Value |
| `IN CONSOLE` | A questionnaire or wizard completed in the console | Do not expand it into questions or answer it. One row, plus an optional "be ready for" note listing detected features the questionnaire asks about |
| `AUTO` | Set by the console or fixed at app creation | Show the value if known |
| `N/A` | Does not apply to this app | Keep the row and give the reason, so the owner can see it was considered |

- **Why suggestions and not answers.** Store declarations are statements the owner makes to Apple and Google, and wrong ones get apps rejected or removed. You can see code, not business facts. Legal names, addresses, phone numbers, licences, target age groups, pricing, countries, and whether a regulated category applies are the owner's calls: suggest where the code gives a real basis, otherwise leave `OWNER`.
- **Why questionnaires stay closed.** Rating questionnaires branch on earlier answers and change often; a transcribed copy goes stale and invites answering on paper instead of in the console.
- **The two privacy forms are the exception worth the effort.** App Privacy and Data safety are where the codebase knows more than the owner. Give the top-level questions as rows and add a suggested data-type table built from step 3.
- **Conditions decide before Fill does.** The catalog's Fill column describes the row when it applies. If the repo settles that the row's condition is not met (no purchases, feature absent, a parent answer you suggested as "No"), the status is `N/A` with the reason, whatever Fill says. If the condition hangs on something only the owner or the console can settle (the target age they pick, countries they ship to, "if shown"), keep `If …` in Req and use the Fill status. If a "No" answer is itself a declaration the owner must make (not a government app, no financial features), it is `SUGGESTED`, not `N/A`.
- **Resolve `Req` for this app.** Write `Yes`, `No`, or `Yes (reason)` / `No (reason)` when the repo settles a condition ("Yes (app runs on iPad)"). When the repo settles only part of it, state the part that remains ("If shipping in EU/EEA, UK or US; category condition is met").
- **Split rows whose parts differ.** When one catalog row bundles fields that end up with different statuses, or the repo has human-written copy for a localized field in some languages, emit one row per part ("Description (English (U.S.))" PREFILLED, "Description (Chinese (Traditional))" SUGGESTED draft). Do not add rows for languages that have neither repo copy nor a draft, and do not repeat a row for a language whose value is identical.
- **Evidence strength.** Config, code constants and metadata files give `PREFILLED`. Comments, README text and names inferred from context give `SUGGESTED`.
- **Placeholders are not values.** Reserved or non-production values (`*.example`, `localhost`, staging hosts, `xxx` keys, sample ad unit IDs) are never `PREFILLED`. Use `OWNER`, mention what was found in Notes, and add a developer-notes item.
- **Credentials.** Never copy passwords, keys or tokens out of the repo, including test accounts found in code or `.env` files. Reviewer login rows get an empty value and a note to enter credentials in the console directly.
- **Localized fields.** Draft in the primary language. Other shipped languages are named in the "Languages" rows, with a note on which required fields (description, keywords, screenshots) will need translating; do not draft them unless the developer asks.
- **Primary language.** Each store has its own default: suggest ASC's from the iOS development region and Play's from the Android default resources. If they disagree, or the only human-written store copy is in another language, say so in Notes and let the owner pick.
- **One draft, two stores.** Where both stores want the same text (description), write one draft and note only the platform-specific differences.
- **Read-only.** Apart from writing the output files, change nothing in the project.

## Output

Write two files in the project root unless a path was given:

- `store-submission-sheet.md`: for the owner. Sections 0, A, B and the drafts.
- `store-submission-dev-notes.md`: for the developer. To-do list, evidence index, assumptions.

Language: write Notes, headings and the legend in the language the developer is using (translate the skeleton headings below too). Keep in English: console page and field labels (so the owner can match them on screen), the six status words, and any text a reviewer will read (App Review notes, Play access instructions, permission justifications). Section 0 rows are prose, not console labels: shorten or translate them freely.

```markdown
# {App name}: store submission sheet
Generated {date} from {repo name} @ {short commit, or "no git"} · version {version} ({build}) · field catalog 2026-10

## How to use this sheet
{legend of the six statuses, one line each; tick the box when the field is saved in the console}

## Summary
{table: one line each for section 0, App Store Connect, Play Console; columns Rows, PREFILLED, SUGGESTED, OWNER, IN CONSOLE, AUTO, N/A; Rows counts emitted rows}
{the 3-5 things most likely to hold up submission, worded for the owner}

## 0. Before you open the consoles
## A. App Store Connect
### A1. Version page: {url}
### A2. App Information: {url}
### A3. Other pages needed for the first submission
## B. Play Console
### B1. App content: {url}
### B2. Publishing overview: {url}
### B3. Other pages needed for the first production release
## Drafts
```

```markdown
# {App name}: submission notes for the developer
## To do before submission
### Found
### Could not verify from the repo
## Assumptions to confirm
## Evidence
```

Every table in sections 0, A and B uses these columns:

| ☐ | Field | Req | Status | Value | Notes |
|---|---|---|---|---|---|

- First column: `☐` for rows that need an action, `–` for `AUTO` and `N/A` rows.
- Notes carry the format or limit from the catalog's Input column (shortened), the evidence path, and what the owner must do.
- A Value longer than about 120 characters goes in Drafts under an ID and the cell says `see D1` (this includes review notes, access instructions and declaration justifications). Head each draft with its measured length, for example `### D2. Description (English (U.S.)): 812 / 4000 characters`, or just the count when the catalog gives no limit.
- In A3, B1 and B3, give each page or declaration its own sub-heading and table; the two privacy data-type tables sit directly under their page's table. The B1 conditional declarations share one table.
- Evidence in the developer notes is a short index of detected capabilities with file paths, so the developer can audit the suggestions; do not repeat row-level notes there.

If `csv` was requested, also write `store-submission-sheet.csv`: UTF-8 with BOM, one row per field, columns `Store,Page,Section,Field,Required,Status,Value,Notes`.
- `Store`: `Prerequisites`, `App Store Connect` or `Play Console`.
- `Page`: the console page. Each A3/B3 sub-heading is a page ("App Privacy", "Main store listing"); section 0 rows use "Before the consoles".
- `Section`: the B1 declaration name, or empty.
- Inline draft text in `Value` instead of `see D1`.
- Add the privacy data-type suggestions as extra rows: Section "{declaration or page} data types (suggested)", Field = the data type, Status `SUGGESTED`, Value = the per-type answers joined as "Collected: …; Purposes: …". They are not counted in the summary.

## Catalog 0: before the consoles

| Field | Req | Fill |
|---|---|---|
| Apple Developer Program membership active; organisation enrolment needs a D-U-N-S number | Yes | OWNER |
| ASC > Business > Agreements: Paid Apps Agreement signed by the Account Holder, with banking and tax information | If paid app or any in-app purchase | OWNER; resolve Req from purchase detection |
| ASC > Business > Agreements > Compliance: Digital Services Act trader status (a trader provides verified phone and email, address, proof document, payment account) | Yes, even without EU distribution; unanswered status removes the app from EU storefronts | OWNER |
| ASC user access for the developer (a role that can edit app information) | No | OWNER |
| Play developer account identity verification complete (personal: ID, contact details, device verification; organisation: D-U-N-S, organisation document, website, phone) | Yes | OWNER |
| Play account type suits the app: finance, health, VPN and government apps need an organisation account | If such features | SUGGESTED "organisation account required" when health or financial features are detected |
| Play personal accounts created after 13 Nov 2023: closed test with at least 12 opted-in testers for 14 continuous days, then "Apply for production access". Internal testing does not count | If personal account | OWNER. Always show; this is the most common first-release surprise |
| Play payments profile (merchant account) | If paid app or in-app products | OWNER; resolve Req from purchase detection |
| Android developer verification: app registered (package name + signing key); usually automatic through Play App Signing, status on the console home page | Yes | OWNER to confirm status; give the package name in Notes |

## Catalog A: App Store Connect

URLs: A1 `https://appstoreconnect.apple.com/apps/{appID}/distribution/ios/version/inflight`, A2 `https://appstoreconnect.apple.com/apps/{appID}/distribution/info`.

### A1. Version page (top to bottom)

| Field | Input | Req | Fill |
|---|---|---|---|
| Languages (localizations of this page) | language menu | Yes (at least the primary) | SUGGESTED list from app languages: "Primary: …; also localize for: …" |
| Previews and Screenshots: iPhone | 1–10 images per localization; `.png`/`.jpg`, no transparency. A 6.9" set (1320×2868, 1290×2796 or 1260×2736; landscape allowed) satisfies the iPhone requirement and is scaled for other sizes; the console flags any set it still wants | Yes | OWNER. In Notes suggest 4–6 screens to capture, from the app's main routes (or the README when routes are not visible) |
| Previews and Screenshots: iPad 13" | 2064×2752 or 2048×2732 | If the app runs on iPad | OWNER; resolve from device families |
| App Previews | up to 3 per size and language, 15–30 s, `.mov`/`.mp4`/`.m4v` | No | OWNER |
| Apple Watch screenshots | | If watchOS app | OWNER |
| Promotional Text | 170 chars, localizable, editable without a new version | No | SUGGESTED draft |
| Description | 4000 chars, plain text, localizable | Yes | PREFILLED from store copy in repo, else SUGGESTED draft from README and feature set |
| Keywords | 100 bytes, comma-separated, localizable; no app name, no competitor names | Yes | PREFILLED from repo copy, else SUGGESTED |
| Support URL | full URL; must lead to real contact information | Yes | PREFILLED if a support page URL exists in code; a bare website or support email is only a candidate: OWNER with the candidate in Notes |
| Marketing URL | full URL | No | PREFILLED if a website URL exists in code; SUGGESTED if only the domain can be inferred; else OWNER |
| Version | | Yes | PREFILLED |
| Copyright | "{year} {rights holder}", no © symbol | Yes | PREFILLED from `NSHumanReadableCopyright` (strip the symbol) or SUGGESTED from the company name found |
| Routing App Coverage File | `.geojson` | If routing app (`MKDirectionsApplicationSupportedModes`) | OWNER |
| App Clip | header image, subtitle, action | If App Clip target | OWNER |
| iMessage App | screenshots | If iMessage extension | OWNER |
| Build | pick the uploaded build | Yes | PREFILLED "{version} ({build})"; SUGGESTED when EAS or CI assigns the build number, since the repo's number may be stale |
| Export compliance (asked when picking a build) | Does the app use encryption beyond what the OS provides, and is it exempt | If Info.plist lacks `ITSAppUsesNonExemptEncryption` | Key present: N/A "not asked, key is set to NO/YES". Key absent: SUGGESTED plain-language answer from encryption detection ("only HTTPS / OS encryption" or "uses <library>"). Non-OS or proprietary crypto needs documentation (French declaration when distributing in France; US CCATS for proprietary algorithms) |
| Game Center | toggle and components | If Game Center entitlement | OWNER |
| In-App Purchases and Subscriptions for review | the first product of each type must be submitted together with an app version: on Monetization > In-App Purchases / Subscriptions, "Add for Review" and choose this version | If purchases exist | SUGGESTED list of products found; details in A3 |
| App Review Information: Sign-in required | checkbox | Yes | SUGGESTED with a one-line reason. Ticked when any feature needs an account, including optional accounts that gate paid or synced features |
| App Review Information: User name, Password | demo account that does not expire | If sign-in required | OWNER, value empty. Notes: which login method the reviewer should use; OTP or social logins need a workaround described in Notes |
| App Review Information: Contact first name, last name | | Yes | OWNER |
| App Review Information: Contact phone | international format starting with + | Yes | OWNER |
| App Review Information: Contact email | | Yes | OWNER |
| App Review Information: Notes | 4000 bytes, English | No, but strongly advised | SUGGESTED draft: what the app does, how to reach gated features, why each sensitive permission and background mode is used, hardware or region needs, where account deletion is. Leave `[Owner: …]` gaps for facts you lack |
| App Review Information: Attachment | file | No | OWNER; suggest a demo video if a feature needs hardware or a specific location |
| App Store Version Release | Manually / Automatically after approval / Automatically, no earlier than a date | Yes | SUGGESTED "Manually release this version" for a first launch so the go-live day is chosen; owner decides |
| What's New in This Version | | No (not shown for the first version) | N/A |
| Phased Release for Automatic Updates | | No (updates only) | N/A |
| Reset rating | | No (updates only) | N/A |
| Add for Review → Submit for Review | final buttons | Yes | OWNER; last step, after A2 and A3 are complete |

### A2. App Information

| Field | Input | Req | Fill |
|---|---|---|---|
| Name | 2–30 chars, localizable | Yes | PREFILLED display name if it fits (one row per language that has a localized display name); an in-app title string that differs by language is source material for a SUGGESTED localized name; warn if over 30 |
| Subtitle | 30 chars, localizable | No | PREFILLED from repo copy, else SUGGESTED |
| Bundle ID | locked after first upload | Yes | PREFILLED |
| SKU | fixed at app creation | Auto | AUTO |
| Apple ID | numeric app ID | Auto | PREFILLED if `ascAppId` or the argument is known, else AUTO |
| Primary Language | | Yes | SUGGESTED from development region / default locale; if the only human-written store copy is in another language, say so in Notes |
| Category: Primary | one of: Books, Business, Developer Tools, Education, Entertainment, Finance, Food & Drink, Games, Graphics & Design, Health & Fitness, Lifestyle, Magazines & Newspapers, Medical, Music, Navigation, News, Photo & Video, Productivity, Reference, Shopping, Social Networking, Sports, Travel, Utilities, Weather | Yes | PREFILLED from `LSApplicationCategoryType` if set (`public.app-category.medical` → Medical), else SUGGESTED with reason. Mention side effects: Health & Fitness or Medical brings the medical-device declaration |
| Category: Secondary | same list | No | SUGGESTED or OWNER |
| Subcategories | | If Games or Stickers | OWNER |
| Content Rights | does the app contain, show or access third-party content, and do you hold the rights | Yes | SUGGESTED "No" when the app shows only its own and its users' content; "Yes" when it shows licensed or aggregated media, feeds or catalogues from others, and then the owner confirms the rights |
| Age Ratings | "Set Up Age Ratings" dialog: in-app controls, capabilities, content descriptors; result is 4+, 9+, 13+, 16+ or 18+ | Yes | IN CONSOLE. "Be ready for" note: detected capabilities among Unrestricted Web Access, User-Generated Content, Social Media, Messaging and Chat, Advertising, medical/wellness content, chance-based mechanics |
| Age Ratings: Age Categories and Override | Not Applicable / Made for Kids / Override to Higher Age Rating. Made for Kids cannot be undone after approval; override is mandatory when the terms set a higher minimum age | Yes | SUGGESTED "Not Applicable" unless children detection says otherwise |
| Age Suitability URL | | No | OWNER |
| License Agreement | Apple's standard EULA, or a custom one | Yes (standard applies by default) | SUGGESTED "Apple's standard EULA"; if the app has its own terms (file or URL), say the owner may paste them as a custom EULA |
| App Encryption Documentation | upload | If non-exempt encryption | OWNER |
| App Store Tags | deselect auto-generated tags; US storefront | No | IN CONSOLE |
| Digital Goods and Services in Your Apps | questionnaire, only if it appears | If shown | IN CONSOLE; note whether digital purchases were detected |
| App Store Regulations & Permits: Digital Services Act | per-app trader status | Yes | OWNER (see section 0) |
| App Store Regulations & Permits: Regulated Medical Device | declaration | If category is Health & Fitness or Medical, or medical content is frequent, and the app ships in EU/EEA, UK or US | Not triggered: N/A. Triggered: OWNER, with what the code shows the app does in Notes |
| Republic of Korea: Rating Classification Number (GRAC) | | If a game or mature entertainment app | OWNER |
| China mainland: ICP Filing Number; game approval number; publishing, religious or news permits | number + documents | If distributing in China mainland | OWNER; say it becomes N/A if China mainland is excluded under availability |
| Vietnam: game licence | | If a game distributed in Vietnam | OWNER |
| App Store Server Notifications: Production / Sandbox URL | | No | No purchases: N/A. Purchases and an endpoint evident: PREFILLED. Purchases, none evident: OWNER (optional) |

### A3. Other ASC pages needed for the first submission

**App Privacy**

| Field | Input | Req | Fill |
|---|---|---|---|
| Privacy Policy URL | public URL | Yes | PREFILLED if found in code, else OWNER |
| User Privacy Choices URL | | No | OWNER |
| "Do you or your third-party partners collect data from this app?" | Yes / No | Yes | SUGGESTED |
| Data types, then per type: purposes, linked to the user's identity, used for tracking | wizard | If collecting | SUGGESTED "see table below" |
| Publish | button | Yes | OWNER |

Suggested table directly below:

| Data type | Collected | Purposes | Linked to user | Used for tracking | Evidence |
|---|---|---|---|---|---|

Use Apple's names: Contact Info (Name, Email Address, Phone Number, Physical Address, Other User Contact Info); Health & Fitness (Health, Fitness); Financial Info (Payment Info, Credit Info, Other Financial Info); Location (Precise, Coarse); Sensitive Info; Contacts; User Content (Emails or Text Messages, Photos or Videos, Audio Data, Gameplay Content, Customer Support, Other User Content); Browsing History; Search History; Identifiers (User ID, Device ID); Purchases (Purchase History); Usage Data (Product Interaction, Advertising Data, Other Usage Data); Diagnostics (Crash Data, Performance Data, Other Diagnostic Data); Surroundings; Body; Other Data. Purposes: Third-Party Advertising; Developer's Advertising or Marketing; Analytics; Product Personalization; App Functionality; Other Purposes. List types with evidence ("Yes", "Yes (confirm)" or "Possible, confirm"), then one closing line naming the categories with nothing found.

**Pricing and Availability**

| Field | Input | Req | Fill |
|---|---|---|---|
| Price Schedule | base country/region and price | Yes | SUGGESTED "Free" when no paid-download signal; otherwise OWNER |
| App Availability | all 175 countries/regions, specific ones, or pre-order | Yes | OWNER; mention languages shipped and any region-bound backend |
| Tax Category | | Yes (default applies) | SUGGESTED "App Store software" |
| App Distribution Methods | Public / Private | Yes | SUGGESTED Public; cannot be switched after approval |
| iPhone and iPad Apps on Apple Silicon Mac | available by default | No | SUGGESTED keep available, unless the app depends on hardware or SDKs a Mac lacks (cellular, some sensors, some ad SDKs): then suggest opting out. When unsure, suggest keeping it and say what to test |
| iPhone and iPad Apps on Apple Vision Pro | available by default | No | same reasoning |
| Education volume discount | checkbox | No | OWNER |

**App Accessibility**

| Field | Input | Req | Fill |
|---|---|---|---|
| Accessibility Nutrition Labels per device (VoiceOver, Voice Control, Larger Text, Dark Interface, Differentiate Without Color Alone, Sufficient Contrast, Reduced Motion, Captions, Audio Descriptions) | Yes / No per feature | No (voluntary for now) | SUGGESTED only where code shows support (Dynamic Type, dark-mode assets); otherwise OWNER |
| Accessibility URL | | No | OWNER |

**In-App Purchases and Subscriptions** (Monetization)

| Field | Input | Req | Fill |
|---|---|---|---|
| Per product: Product ID, type | | If purchases exist | PREFILLED when IDs are in code or a `.storekit` file; SUGGESTED when only a comment or README names them; OWNER when purchases are detected but no ID is found (and add a developer-notes item) |
| Per product: Reference Name, price, availability, localized display name and description, review screenshot, review notes | | If purchases exist | OWNER |
| Subscription group | | If subscriptions | OWNER |
| Terms of Use and Privacy Policy links in store metadata | privacy policy in its field; Terms of Use either as a custom License Agreement or, when using Apple's standard EULA, as a link in the Description | If subscriptions | PREFILLED URLs if found; flag if missing |

## Catalog B: Play Console

URLs: B1 `https://play.google.com/console/u/0/developers/{devID}/app/{appID}/app-content/overview`, B2 `https://play.google.com/console/u/0/developers/{devID}/app/{appID}/publishing`.

### B1. App content

One sub-heading and table per declaration, in this order.

**Privacy policy**

| Field | Input | Req | Fill |
|---|---|---|---|
| Privacy policy URL | public page, not a PDF, not geo-blocked | Yes | PREFILLED if found, else OWNER |

**Ads**

| Field | Input | Req | Fill |
|---|---|---|---|
| Does your app contain ads? | Yes / No; Yes shows a "Contains ads" label | Yes | SUGGESTED from ads detection |

**Sign-in details** (older name: App access)

| Field | Input | Req | Fill |
|---|---|---|---|
| Access | "All functionality is available without special access" / "All or some functionality is restricted" | Yes | SUGGESTED. Restricted when any feature needs an account, even an optional one |
| Instructions (up to 5 sets): username or phone number, password | reusable credentials, valid from any location | If restricted | OWNER, value empty |
| Instructions: any other instructions | free text, English | If the reviewer needs more than a username and password | SUGGESTED draft describing which login method to use and any OTP/MFA workaround, with `[Owner: …]` gaps. N/A when plain credentials are enough |
| "No other information is required to access my app" | checkbox: tick when username and password alone are enough | If restricted | SUGGESTED: ticked when the reviewer can use a plain email/password login (even if social logins also exist), unticked whenever you drafted other instructions |

**Content ratings**

| Field | Input | Req | Fill |
|---|---|---|---|
| Email address | for IARC correspondence | Yes | OWNER |
| Category | Game / Social or Communication / All other app types (confirm labels in console) | Yes | SUGGESTED with reason |
| Questionnaire → Summary → Submit | IARC questions | Yes | IN CONSOLE. "Be ready for" note: user interaction, shared location, purchases, user-generated content, ads if detected |

**Target audience and content** (needs Ads, Sign-in details and Privacy policy done first)

| Field | Input | Req | Fill |
|---|---|---|---|
| Target age | checkboxes: Ages 5 and under / 6-8 / 9-12 / 13-15 / 16-17 / 18 and over | Yes | OWNER. Note: any band under 13 brings the Families policy and longer review; do not suggest child bands unless the app is clearly for children |
| Restrict minors | optional checkbox, offered when only 18 and over is selected | No | OWNER |
| Appeal to children | Yes / No | Yes | SUGGESTED No unless child-directed signals |
| Ads and store presence follow-ups (Families ads SDK, neutral age screen, Teacher Approved) | | If children targeted | OWNER |

**Data safety**

| Field | Input | Req | Fill |
|---|---|---|---|
| Does your app collect or share any of the required user data types? | Yes / No | Yes | SUGGESTED |
| Is all of the user data collected by your app encrypted in transit? | Yes / No | If collecting | SUGGESTED Yes when all endpoints are HTTPS and cleartext traffic is not enabled; cite |
| Do you provide a way for users to request that their data is deleted? | Yes / No | If collecting | SUGGESTED Yes when a delete flow exists; otherwise OWNER (a website or support process may cover it) |
| Account creation: does the app let users create an account, and by which methods | options in console | Yes | SUGGESTED from login detection; when accounts are provisioned outside the app, suggest "no in-app account creation (confirm)" |
| Delete account URL | a web page where users can request account deletion without the app | If users can create an account | PREFILLED if such a URL exists, else OWNER plus a developer-notes item (under "Could not verify" when account creation itself is unconfirmed) |
| Data types, then per type: collected / shared, processed ephemerally, required or optional, purposes | wizard | If collecting | SUGGESTED "see table below" |
| Store listing preview → Submit | | Yes | OWNER |

Suggested table directly below:

| Data type | Collected | Shared | Ephemeral | Required / optional | Purposes | Evidence |
|---|---|---|---|---|---|---|

Use Play's names: Location (Approximate, Precise); Personal info (Name, Email address, User IDs, Address, Phone number, Race and ethnicity, Political or religious beliefs, Sexual orientation, Other info); Financial info (User payment info, Purchase history, Credit score, Other financial info); Health and fitness (Health info, Fitness info); Messages (Emails, SMS or MMS, Other in-app messages); Photos and videos; Audio files (Voice or sound recordings, Music files, Other audio files); Files and docs; Calendar events; Contacts; App activity (App interactions, In-app search history, Installed apps, Other user-generated content, Other actions); Web browsing history; App info and performance (Crash logs, Diagnostics, Other app performance data); Device or other IDs. Purposes: App functionality; Analytics; Developer communications; Advertising or marketing; Fraud prevention, security, and compliance; Personalization; Account management. Leave "Shared" as "Confirm" unless data plainly goes to another company for its own use (ad networks): transfers to service providers acting for the developer are generally not "sharing", and that line is the owner's call.

**Advertising ID**

| Field | Input | Req | Fill |
|---|---|---|---|
| Does your app use an advertising ID? | Yes / No | Yes | SUGGESTED from `AD_ID` in the manifest (source or merged) and ad/analytics SDKs. A "No" while the bundle still carries the permission blocks the release: add a developer-notes item when they disagree |
| Purposes | checkboxes such as App functionality, Advertising or marketing, Analytics | If Yes | SUGGESTED |

**Government apps**

| Field | Input | Req | Fill |
|---|---|---|---|
| Is your app developed by or on behalf of a government? | Yes / No; proof may be requested | Yes | SUGGESTED No unless evident |

**Financial features**

| Field | Input | Req | Fill |
|---|---|---|---|
| Financial features | checkboxes in groups (Banking and loans; Payments and transfers; Purchase agreements; Trading and funds; Support services) or "My app doesn't provide any financial features" | Yes | SUGGESTED. Store billing and ordinary checkout for goods are not financial features; lending, banking, wallets, money transfer, trading, crypto, insurance are |
| Lender details, licences per country | | If loans or regulated features | OWNER |

**Health apps**

| Field | Input | Req | Fill |
|---|---|---|---|
| Health features | checkboxes. Health and fitness: Activity and Fitness; Nutrition and Weight Management; Period Tracking; Sleep Management; Stress Management, Relaxation, Mental Acuity. Medical: Diseases and Conditions Management; Clinical Decision Support; Disease Prevention and Public Health; Emergency and First Aid; Healthcare Services and Management; Mental and Behavioral Health; Medical Reference and Education; Medication and Treatment Management; Physical Therapy and Rehabilitation; Reproductive and Sexual Health. Also: Medical Device Apps; Health subjects research. Or "My app doesn't provide any health features" | Yes | SUGGESTED from health detection and what the app does |
| Follow-up questions (regulated medical device details and similar) | | If triggered by the selection | OWNER |

**News and Magazine apps**

| Field | Input | Req | Fill |
|---|---|---|---|
| Is your app a news app? | Yes / No | Yes | SUGGESTED No unless evident |
| Publisher details (contact URL, owning entity type, aggregator, content types, editorial guidelines) | | If Yes | OWNER |

**COVID-19 contact tracing and status apps**

| Field | Input | Req | Fill |
|---|---|---|---|
| Statements that apply | checkboxes; legacy item, may no longer be shown | If shown | SUGGESTED "not a contact tracing or status app" unless evident |

**Conditional declarations.** These appear under "Needs attention" only when the uploaded bundle or the app's category triggers them; since a build is already uploaded, the owner can see which are live. Put all of them in one table, one row each. Triggered: `Req` "Yes (if shown)", Status `SUGGESTED`, Value "Will appear" plus a one-line English justification draft, Notes with the triggering permission and file. Not triggered by anything found: `N/A`, adding "confirm in console" when a near-miss permission is present.

| Declaration | Trigger | What it asks |
|---|---|---|
| Permissions declaration form | SMS or Call Log permissions | core functionality, video link, reviewer access; slow review |
| Location permissions (background) | `ACCESS_BACKGROUND_LOCATION` | the feature needing background location, video demonstration |
| Foreground service permissions | `FOREGROUND_SERVICE_*` types with target API 34+ | per type: description, user impact, video link, use case |
| Photo and video permissions | `READ_MEDIA_IMAGES` / `READ_MEDIA_VIDEO` | why the system photo picker is not enough |
| All files access | `MANAGE_EXTERNAL_STORAGE` | core use case |
| Exact alarm | `USE_EXACT_ALARM`. Play reserves it for alarm-clock and calendar apps, so in any other app also add a developer-notes warning. `SCHEDULE_EXACT_ALARM` alone is user-granted and is a near miss, not a trigger | alarm or calendar core functionality |
| Full-screen intent | `USE_FULL_SCREEN_INTENT` | calling or alarm core functionality |
| Package visibility | `QUERY_ALL_PACKAGES` | core use case |
| Install packages | `REQUEST_INSTALL_PACKAGES` | core use case |
| Accessibility API | an `AccessibilityService` | whether it is an accessibility tool; use case, video |
| VPN service | a `VpnService` | core use case |
| Health Connect | `android.permission.health.*` | per data type justification |
| Child safety standards | Social or Dating category, or anonymous/random chat. If the app has social features and the category is still the owner's choice: Req "If Social or Dating is chosen as category", Status `OWNER` | published standards URL, in-app reporting, point of contact |
| External offers / external apps | enrolled programmes only | N/A for nearly all first releases |

### B2. Publishing overview

| Field | Input | Req | Fill |
|---|---|---|---|
| Managed publishing | on / off. On: approved changes wait for "Publish changes" | Yes | SUGGESTED On for a first launch so the go-live moment is chosen; owner decides |
| Changes not yet sent for review | list; nothing is sent automatically | Yes | OWNER: check that it contains the release, store listing and all App content items |
| Pre-review checks | run automatically; "View issues"; critical issues block sending | Yes | OWNER; point to the developer for issues already known from code |
| Save for later | holds back selected changes | No | N/A for a first release |
| Send for review | button | Yes | OWNER; last step |
| Changes in review / Changes ready to publish → Publish changes | | If managed publishing is on | OWNER |

### B3. Other Play pages needed for the first production release

**Main store listing**

| Field | Input | Req | Fill |
|---|---|---|---|
| App name | 30 chars | Yes | PREFILLED label if it fits; localized labels as for the ASC Name |
| Short description | 80 chars | Yes | PREFILLED from Play copy in repo, else SUGGESTED (an iOS subtitle is source material, not a prefill) |
| Full description | 4000 chars | Yes | PREFILLED from Play copy in repo, else SUGGESTED; share the ASC text or draft |
| App icon | 512×512 PNG, up to 1024 KB | Yes | OWNER; cite the highest-resolution icon source in the repo if any |
| Feature graphic | 1024×500 JPEG or 24-bit PNG | Yes | OWNER |
| Phone screenshots | 2–8, JPEG or 24-bit PNG, sides 320–3840 px | Yes | OWNER; same suggested screens as ASC |
| 7-inch tablet, 10-inch tablet, Chromebook screenshots | | No | OWNER |
| Video | YouTube URL | No | OWNER |
| Default language | set when the app was created; changeable under Manage translations | Yes | SUGGESTED from the Android default resources |
| Languages (translations of the listing) | | No | SUGGESTED list from app languages |

**Store settings**

| Field | Input | Req | Fill |
|---|---|---|---|
| App or game | | Yes | SUGGESTED |
| Category | apps: Art & Design, Auto & Vehicles, Beauty, Books & Reference, Business, Comics, Communication, Dating, Education, Entertainment, Events, Finance, Food & Drink, Health & Fitness, House & Home, Libraries & Demo, Lifestyle, Maps & Navigation, Medical, Music & Audio, News & Magazines, Parenting, Personalization, Photography, Productivity, Shopping, Social, Sports, Tools, Travel & Local, Video Players & Editors, Weather | Yes | SUGGESTED with reason; mention side effects (Social or Dating brings Child safety standards) |
| Tags | up to 5, picked from the console's list | No | SUGGESTED themes; the owner picks matching tags in the console |
| Contact details: Email | | Yes | PREFILLED only for a real support address; a developer or author email is a candidate for Notes |
| Contact details: Phone | | No | OWNER |
| Contact details: Website | | No | PREFILLED if found |

**App pricing**

| Field | Input | Req | Fill |
|---|---|---|---|
| Free or paid | a free app can never become paid | Yes | SUGGESTED Free when no paid-download signal |

**Production**

| Field | Input | Req | Fill |
|---|---|---|---|
| Countries / regions | | Yes | OWNER |
| Release: app bundle | promote from testing or upload | Yes | PREFILLED "{versionName} ({versionCode})"; SUGGESTED when CI assigns the version code |
| Release name | internal | Auto | AUTO from version name |
| Release notes | 500 chars per language | Yes | SUGGESTED short first-release note in the primary language |
| Apply for production access | questionnaire | If personal account under the testing rule | IN CONSOLE |

**App integrity, Monetize, Settings**

| Field | Input | Req | Fill |
|---|---|---|---|
| Play App Signing | | Auto | AUTO; note that the upload key must be kept safe |
| In-app products: product ID, name, description, price | | If one-time products exist | product ID as in A3; rest OWNER |
| Subscriptions: product ID, name, benefits, base plan (billing period, price), offers | | If subscriptions exist | product ID as in A3; rest OWNER |
| Catalog settings (US developers: sharing the listing with third-party stores) | | If shown | OWNER |

## Developer to-do checks

The developer notes file is for the developer, not the owner: things in the code that will fail review or contradict a declaration. Use the three lists below, and include only items that apply.

**Found** (evidence in the repo; give the file and the fix):

iOS
- Accounts can be created in the app but there is no in-app account deletion, or deletion removes only the auth record (guideline 5.1.1(v)).
- Third-party or social login is offered without an equivalent privacy-focused option such as Sign in with Apple (guideline 4.8); an app using only its own account system is exempt.
- No privacy policy link reachable inside the app, or URL constants defined but never shown.
- Public user-generated content without report, block or filter mechanisms (guideline 1.2).
- Tracking SDKs present but no App Tracking Transparency prompt is called, or a prompt with nothing that tracks.
- Vague permission purpose strings that do not say why; purpose strings missing for a shipped language.
- No app privacy manifest, required-reason APIs without declared reasons, or a manifest that omits what bundled SDKs collect.
- Purchases without a restore action; subscriptions without terms and privacy links on the paywall.
- Digital content sold through a non-store payment SDK.
- `ITSAppUsesNonExemptEncryption` absent, so the export question is asked on every upload.

Android
- `targetSdk` below 36: new apps must target Android 16 (API 36) since 31 Aug 2026.
- `AD_ID` permission present without an ads/analytics reason, or blocked while an SDK needs it.
- Accounts can be created but no web URL for deletion requests exists.
- Permissions declared but unused in code; broad media permissions where the photo picker would do.
- Cleartext traffic enabled while Data safety will claim encryption in transit.
- A B1 conditional declaration will be triggered: the owner needs a justification and usually a short screen recording.

Both
- Reviewer access: login needs OTP, SSO, pre-registration or region-locked numbers, so a demo account or bypass is required.
- Placeholder or non-production values in the release configuration (URLs, keys, ad unit IDs, test endpoints).
- A dependency declared for a store-facing capability (purchases, tracking prompt, ads) with no code that uses it.
- Product IDs missing from the repo or present only in comments.
- App name over 30 characters, or different names across the two stores.

**Could not verify from the repo** (state each as a question for the developer). Anything above that you can only infer from absence in a repo that looks partial (referenced files missing, no UI code) belongs here, not under Found. Also: build toolchain (uploads need Xcode 26 / iOS 26 SDK or later); inherited `targetSdk`; 16 KB page-size support when native libraries are present (required for apps targeting API 35+); merged manifest permissions; SDK privacy manifests when dependency folders are absent; release signing done in CI; whether data behind a permission leaves the device.

**Assumptions to confirm**: chosen flavor or target, primary language, suggested categories.

## Sources for a refresh

When the catalog date is old or the developer reports mismatches, re-read these before trusting the tables: Apple "Platform version information", "App information", "Screenshot specifications", "Manage app privacy", "Set an app age rating" (developer.apple.com/help/app-store-connect); Google "Prepare your app for review", "Provide information for Google Play's Data safety section", "Publishing overview", "Target API level requirements" (support.google.com/googleplay/android-developer).
