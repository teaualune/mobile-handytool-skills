# Intake: Crashlytics through the Firebase MCP server

Checked against firebase-tools v15.36 (2026-11). Firebase labels its Crashlytics MCP features *experimental*. If a tool name or input below doesn't match what the server exposes, the tool's own schema wins.

Tool names below are the server's own (`crashlytics_get_issue`, …). In Claude Code they carry an `mcp__…__` prefix that depends on how the server was installed. They may be listed only as deferred tools: load them (e.g. with ToolSearch) before deciding they're missing.

## 1. Check the server

- **No Firebase tools, loaded or deferred:** the server isn't installed. Continue with the browser route (`intake-crashlytics-browser.md`) or, without the Chrome tools, the paste route (`intake-paste.md`). Mention once how to add the server:
  - as a Claude Code plugin: `claude plugin marketplace add firebase/firebase-tools`, then `claude plugin install firebase@firebase`;
  - or as a plain MCP server: `claude mcp add firebase -- npx -y firebase-tools@latest mcp`.

  Either way, the session must restart before the tools appear.
- **Firebase tools, but no `crashlytics_*` ones:** the server enables Crashlytics only when the project directory shows a Crashlytics dependency, in a `build.gradle*` file, `Podfile`, `Package.swift`, `project.pbxproj` or `pubspec.yaml`. Fix it one of these ways:
  - start Claude Code from the app's root;
  - point the server at the root with `--dir <path>`;
  - force Crashlytics on with `--only core,crashlytics`.
- **Not signed in:** `firebase_get_environment` shows no user, or calls fail with auth errors. Ask the caller to sign in **in a separate terminal**:
  - `firebase login`, or `npx -y firebase-tools@latest login` if `firebase` isn't on the PATH;
  - for a project that belongs to another Google account, `firebase login:add`. Then, after asking, select that account for this directory with `firebase_update_environment` (`active_user_account`).

  These commands don't work through Claude Code's `!` prefix. The CLI detects a non-interactive shell: `login:add` refuses to run, and `login` falls back to printing a URL and asking for a second `firebase login <authorization code>` command. Never handle the caller's credentials.

## 2. Resolve the App ID

Every Crashlytics tool needs two inputs, and none of them accepts a console URL:
- `appId`: the Firebase App ID, `1:<projectNumber>:<ios|android>:<hex>`;
- `issueId`: the hex issue ID.

Resolve the App ID in this order:

1. **The caller gave an App ID:** use it.
2. **Match against the repo:** take `platform` and `bundle_id` from `parse_issue_url.py`. Match them against the App IDs `firebase_get_environment` detected in the repo from `google-services.json` and `GoogleService-Info.plist`. Apps often have several flavors (dev, staging, prod), so match the bundle ID exactly.
3. **List the project's apps:** with no match in the repo, `firebase_list_apps` lists the apps of the *active* Firebase project. If the URL's `project_id` isn't the active project, ask before switching it (`firebase_update_environment` with `active_project`).
4. **Bare issue ID and several apps:** ask which app.

## 3. Fetch

**Time range:** everything here defaults to the last 7 days, which hides an issue not seen this week.
- On **every** `crashlytics_list_events` and `crashlytics_get_report` call, set `filter.intervalStartTime` to about 89 days ago (the limit is 90) and `filter.intervalEndTime` to now. Reports need both whenever the range is custom.
- Record the period in the issue file and in `releases.md`.

**Per issue:**

1. **`crashlytics_get_issue`** returns:
   - title and subtitle;
   - error type (`FATAL`, `NON_FATAL` or `ANR`);
   - first and last seen, by version and time;
   - state and signals;
   - variants;
   - `sampleEvent` (an event resource name);
   - the console `uri`.
2. **`crashlytics_batch_get_events`** with `names: [<sampleEvent>]` returns one full event: stack, custom keys, logs, breadcrumbs, device, OS, memory and process state.
3. **`crashlytics_list_events`** fetches more events. Set `filter.issueId` and the time range, and a `pageSize` of 5–10 (the default is 1) to see what varies between events. If the variants' top frames differ, fetch one event per variant (`filter.issueVariantId`).
4. **Distribution:** the `crashlytics_get_report` tool requires reading its guide first: the resource `firebase://guides/crashlytics/reports`, via `firebase_read_resources`. Then get the issue's version, OS and device breakdowns, with `filter.issueId` and the time range.
5. **`crashlytics_list_notes`:** the team may already have written down what it knows.

**Once per app, for `releases.md`:** get the `releaseVersions` report with no issue filter. It groups by the latest release versions and gives `totalUsersCount`, the active users per version, which the exposure test in `investigate.md` §2 needs. Don't use `topVersions` for this: it ranks versions by crash volume, so a fresh release with few crashes can be missing. Then fill in the git ref for each version from the repo.

Write the issue file as you go. Record which event the stack came from.

## 4. What the event output leaves out

- **Stacks are cut to 19 frames** per thread, exception or error, followed by `... frames omitted ...`. The cut is common in React Native and Flutter, where engine frames pile up. If it hides the app's frame, read the full trace in the console (`intake-crashlytics-browser.md`), or ask the caller to paste it (`intake-paste.md` §Filling gaps).
- **`FATAL` and `ANR` events show only the crashed or blamed thread.** For ANRs and deadlocks, the thread holding the lock matters, so get all threads the same way if needed.
- **Logs and breadcrumbs are truncated** to the last 100 logs and the last 10 breadcrumbs.
- **Data covers the last 90 days only.**

## 5. Top issues (no IDs given)

When the caller asks for "top crashes" or similar:

1. Get the `topIssues` report (filter `FATAL` for crashes, or what the caller asked for), with an explicit time range, by default the last 7 days. Also get `releaseVersions`.
2. Rank the issues: first whether they appear in the latest version, then users affected, then event count.
3. Show the top 5 with their numbers and the period, and let the caller pick which ones to take in. Then continue with §3 for each pick.
