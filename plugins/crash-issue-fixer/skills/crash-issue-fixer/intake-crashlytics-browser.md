# Intake: the Crashlytics console in Chrome

This is the second route. Use it when the Firebase MCP's Crashlytics tools aren't available, or to fill what the MCP leaves out: complete stacks and all threads. It drives the caller's own Chrome session through the Claude-in-Chrome tools, so it sees exactly what the caller sees in the console.

The console notes below were observed in 2026-11. When the live UI differs, the live UI wins. Find controls by what they do, not by an exact label.

## Tools and safety

- **Tools:** this route needs the Claude-in-Chrome tools (`tabs_context_mcp`, `tabs_create_mcp`, `navigate`, `get_page_text`, `find`, `read_page`, `computer`, `tabs_close_mcp`). If they are deferred, load them all in one ToolSearch call. If they can't be loaded, use the paste route.
- **Tabs:** work in a new tab, and close it when done. Don't touch the caller's other tabs.
- **Sign-in:** the caller signs in; never type their Google credentials. If the page asks for a sign-in or says there's no access, stop and ask the caller to sign in or switch accounts. The `/u/<n>/` part of the URL picks which signed-in Google account the console uses.
- **Read-only by default:** don't use these controls: Close/Reopen issue, notes, mute, regression or alert settings, anything under project settings. The only exception is the Crashlytics actions the caller approved in Step 7 (§Writes).
- **Text over pixels:** read with `get_page_text`, `find` and `read_page` rather than screenshots. After each navigation, wait a few seconds: the console loads its data after the page shell.

## The URL

`https://console.firebase.google.com/[u/<n>/]project/<projectId>/crashlytics/app/<platform>:<bundleId>/issues/<issueId>` opens an issue. Query parameters that work:

- `time=7d`, `time=90d`: the time range. Use `time=90d`, the maximum, so that older issues still show their events and the full spread of versions.
- `sessionEventKey=<key>`: opens one specific event. Keep it when the caller's URL has one (`parse_issue_url.py` returns it as `event_key`): it is the event the caller was looking at.

**Bare issue ID:** build the URL from the repo's Firebase config. Take `PROJECT_ID` and `BUNDLE_ID` from `GoogleService-Info.plist`, or `project_info.project_id` and the client's `package_name` from `google-services.json`. If there are several flavors, ask which app.

## What to collect, per issue

1. **Issue page:** open the issue URL with `time=90d`, then run `get_page_text`. It returns the title, error type, event and user counts, first and last seen versions, state, and the current event's stack trace.
2. **Versions:** read the legend of the events-by-version chart (`find` it). It lists every version with events, and `investigate.md` §2 needs it. Read the OS and device distributions the same way, if the page shows them.
3. **Event tabs:** next to the stack trace, the event has tabs for **Keys**, **Logs & Breadcrumbs** and **Data** (device, OS, memory, disk, app state). `find` each tab, click it by ref, then read its panel with `read_page` or `get_page_text`.
4. **Stack:**
   - The default view shows the crashed thread. Copy it verbatim.
   - For ANRs and deadlocks, use the page's control for showing all threads, if it has one.
   - If frames are collapsed, expand them before reading.
5. **More events:** if the page lets you step between events, read 2–5 of them to see what varies: device, OS, keys, breadcrumbs.
6. **Notes:** the notes control shows a count ("0 notes"). If the count isn't zero, open it and read the notes.

Set Source to `Crashlytics (browser)`. When this route fills gaps in an MCP issue, set it to `Crashlytics (MCP) + browser`.

**Once per app, for `releases.md`:** you need active users per version. That means all users, not users who crashed; the issue's version chart counts only crash events. If the console shows active users per release version, read them there, with the time range set to 90 days. Otherwise, ask the caller for the newest store release and rough adoption numbers, e.g. from App Store Connect or Play Console. If neither is possible, mark the numbers missing. Fill in the git refs from the repo.

## Top issues

When there's no issue ID, open the app's issue list: the issue URL without `/<issueId>`, or an `issue_lists` entry from `parse_issue_url.py`, with `time=7d` or as the caller asks. Read it with `get_page_text` and rank as in `intake-crashlytics-mcp.md` §5. For every pick, continue with "What to collect".

## Writes (only when approved in Step 7)

- **Note:** open the notes control, click into its text field, type the note, and post it. Confirm the note appears, then press Escape to close the popover.
- **Close issue:** the control is in the issue header. **Click it once, then reload the page and check the state before doing anything else.** The control toggles between Close and Reopen, so a second click undoes the first.
