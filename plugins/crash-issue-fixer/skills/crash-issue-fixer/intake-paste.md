# Intake: pasted reports

Use this route for any crash reporter: Sentry, Bugsnag, Play Console Android vitals, Xcode Organizer, TestFlight feedback, raw `.ips` / `.crash` files, Android tombstones or logcat. Use it for Crashlytics when neither the Firebase MCP nor the Chrome tools are available. It also fills gaps the other routes leave.

## What to ask for

Ask once, as a checklist, for whatever is missing. In priority order:

1. **The full stack trace** of the crashed thread, every frame, symbolicated. On Android, include every `Caused by:` section; on iOS, the exception backtrace. Ask for the raw or full view: most services collapse system frames by default.
2. **The exception type and message**, and the error type: crash, non-fatal, ANR or hang.
3. **Versions**: the first and last app version the issue was seen in, plus the per-version breakdown if the service shows one. Without them, the already-fixed check (`investigate.md` §2) can't run.
4. **OS and device breakdown**: the top few, with shares.
5. **Counts**: events and users, over what period.
6. **For one or two events**: custom keys or tags, logs, and breadcrumbs.
7. **For ANRs and deadlocks**: all threads.
8. **The issue link or ID**, used only as a reference in the report.
9. **Once per app, for `releases.md`:** the newest version in the stores, and users per version if the caller can see them (the crash service, App Store Connect or Play Console).

Say what each missing item costs instead of insisting, and continue with what there is.

## Turning it into an issue file

- Set Source to `pasted (<service>)`.
- Read the platform from the frames (Swift/Objective-C or Java/Kotlin, JS or Dart). Read the framework from the repo.
- Copy the stack verbatim into a fenced block. Note whether it looks symbolicated (`reading-crashes.md` §Symbols).
- Several crashes in one paste: split them at each exception or thread header, one issue file each. Ask the caller only if it's unclear which parts belong together.
- Fill in **Missing** honestly; it drives the confidence of the investigation.

## Filling gaps

When an MCP-sourced issue needs more (see `intake-crashlytics-mcp.md` §4) and the browser route can't get it, ask for exactly what's missing and say where to find it. For example: "the crashed thread's frames after the first 19, from the issue's console page". Give the `uri` from `crashlytics_get_issue`. Add what the caller pastes to the existing issue file, mark it as pasted, and change Source to `Crashlytics (MCP) + pasted`.

## Privacy

Pasted logs and keys may contain user data: emails, user IDs, tokens or addresses. Keep only what the investigation needs. Never repeat such data in code, tests, commit messages or Crashlytics notes.
