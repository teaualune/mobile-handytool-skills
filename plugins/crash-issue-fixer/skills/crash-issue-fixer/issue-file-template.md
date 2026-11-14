# Issue file and releases templates

Two formats live in the working folder:
- **Issue files**, one per issue at `<working folder>/<issue-slug>.md`. Intake fills everything above **Investigation**, and phase 2 fills the rest.
- **`releases.md`**, with one section per app, filled once during intake.

Write `—` for values the source doesn't have, and list each one under **Missing**. Keep stack traces verbatim: don't reformat, reorder or shorten frames.

## Issue file

~~~markdown
# <exception type>: <short message or issue title>

| Field | Value |
|---|---|
| Source | Crashlytics (MCP) / Crashlytics (browser) / pasted (<service>); join with `+` when one route filled another's gaps |
| Issue | <issue id> · <console or service link> |
| App | <Firebase App ID or bundle ID / package name> · <ios / android> · <native / React Native / Flutter> |
| Error type | crash / non-fatal / ANR / hang / watchdog / memory |
| State | open / closed / regressed · signals: <fresh, regressed, repetitive, early> |
| First seen | <version> · <date> |
| Last seen | <version> · <date> |
| Volume | <events> events · <users> users · <period> |
| Variants | <count, and how their top frames differ> |
| Group | lead / member of <lead-slug> · other members: <slugs, or —> |

## Distribution
- Versions: <version: events / users, …>
- OS: <version: share, …>
- Devices: <model: share, …>
- Other: <foreground / background, free memory or disk, orientation, rooted / jailbroken, …>

## Stack trace
Sample: <event id or "pasted"> · symbolicated: yes / partly / no · frames: complete / cut after <n>

```text
<crashed thread or exception, verbatim, including every "Caused by" section>
```

<Other threads, only when relevant: ANRs, deadlocks, lock contention.>

## Context from events
- Custom keys: <key: value (seen in k of n events)>
- Logs: <relevant lines, newest last>
- Breadcrumbs: <relevant entries>
- What varies between events: <device, OS, keys, screens, …>
- Team notes: <existing Crashlytics notes or comments>

## Missing
- <field>: <what the gap weakens, e.g. "no version data, so the already-fixed check can't run">

## Investigation
<In a member's file, only: "Group <lead-slug>: <verdict>. Same cause because <one line>. See <lead-slug>.md.">

- **Verdict:** fix / already-fixed / fixed-unreleased / instrument / needs-symbols / no-action · **Confidence:** high / medium / low
- **Still happening?** <R, L, H, and what git shows between them; for fixed-unreleased, whether the commit is on the default branch>
- **App frame:** <file:line, function>
- **Fault:** app / dependency <name@version> / platform / unknown
- **Cause:** <the story, with file:line references>
- **Evidence:** <what supports it, and what explains each strong skew, across all members>
- **Other causes:** <runners-up, and what would tell them apart>

### Plan
- **Fix:** <what changes and where; what the user sees in that situation afterwards>
- **Test:** <test to add / manual steps / why it can't be tested locally>
- **Same pattern elsewhere:** <locations, or none found>
- **Production check:** <version to watch, expected signal>

### Outcome
- <files changed · branch and worktree · tests added · verification commands and results · Crashlytics actions taken · GitHub issue link>
~~~

## releases.md

~~~markdown
# Releases

## <bundle ID / package name> (<ios / android>)

Source: Crashlytics `releaseVersions` report / console / caller / store console · period: <start> – <end>
Default branch: <name> · Version at HEAD (H): <version> · Minimum OS at HEAD: <iOS deployment target / minSdk>
Newest store release (R): <version>, because <tags, adoption, or the caller said so>

| Version | Users in period | Kind | Git ref |
|---|---|---|---|
| <version> | <total active users, not crashed users> | store / pre-release / unknown | <tag, release branch, or version-bump commit> |

Missing: <e.g. "no user counts, so the exposure test can't run">
~~~

Crashlytics also counts TestFlight and internal builds. A version newer than the others with few users is probably a pre-release; confirm it with tags or the caller when the answer changes a verdict.
