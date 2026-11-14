---
name: crash-issue-fixer
description: Investigate and fix crash, non-fatal and ANR issues from Firebase Crashlytics, or pasted from any crash reporter (Sentry, Bugsnag, Play Console, Xcode Organizer). Takes Crashlytics issue URLs or IDs, read through the Firebase MCP server or the Crashlytics console in Chrome, or pasted stack traces. For each issue it checks whether the crash still happens or was already fixed in a later version, traces native Swift/Objective-C/Kotlin/Java stacks back to the app's own code (including React Native and Flutter apps), and proposes root-cause fixes that are applied only after approval. Results can become GitHub issues. Use when the user shares a Crashlytics link or issue ID, pastes a stack trace or crash log, or says "fix this crash", "look at these Crashlytics issues", "fix our top crashes", "why does the app crash", "is this crash already fixed", or mentions an ANR, a non-fatal, EXC_BAD_ACCESS, SIGABRT, NullPointerException, or a watchdog termination.
---

# Crash issue fixer

Turn crash reports into verdicts and, where the app's code is at fault, root-cause fixes. Two phases:

1. **Intake:** collect each issue's data into an *issue file*, and each app's release data into `releases.md` (both formats are in `issue-file-template.md`). For Crashlytics, use the first route that works:
   1. the Firebase MCP server;
   2. the Crashlytics console in the caller's Chrome;
   3. text the caller pastes.

   Pasting also covers Sentry and every other crash reporter.
2. **Investigate and fix:** per *group* of issues that are one bug, work out whether it still happens, where and why, and what to do about it. Every group ends with a verdict, and a code change is only one of the possible verdicts.

Phase 2 reads only the issue files, `releases.md` and the codebase, so it works the same whatever the source.

Work through the steps in order. Respect the STOP points.

## Rules

- **No edits before Step 6.** Investigation reads code and git history and may run existing tests or analyzers. It changes nothing except the Investigation sections of the issue files. Code changes happen only for plans the caller approved in Step 5.
- **A group may need no change.** `already-fixed`, `fixed-unreleased`, `needs-symbols` and `no-action` are complete answers. Never invent a fix to have something to show.
- **No symptom patches.** `investigate.md` §Fix rules apply to every plan and every change.
- **Outward-facing actions only when the caller chooses them in Step 7:**
  - **Crashlytics:** closing issues, or adding and deleting notes, through the MCP or the console. These change what the whole team sees.
  - **GitHub:** creating, commenting on, closing or reopening issues.
- **Ask first, at any step,** before switching the Firebase CLI's active project or account. The switch changes the caller's CLI configuration.
- **Git:**
  - Never push, open pull requests or rewrite history unless asked.
  - Commit only as part of the apply mode the caller picks in Step 5.
  - Stage files by path, never with `git add -A` or `git add .`.
- **Credentials:** never ask for or type passwords or tokens. The caller signs in themselves: for Firebase, in a separate terminal (`intake-crashlytics-mcp.md` §1); for the console, in Chrome.
- **Field data stays in the working folder.** Logs, custom keys, breadcrumbs and exception messages can contain user IDs, emails, URLs or tokens.
  - Never copy field data into code, tests, commit messages, `report.md`, GitHub issues or Crashlytics notes.
  - Outside the working folder, quote an exception message only with its values replaced by placeholders (`<email>`, `<id>`, `<url>`).

## Files in this skill

These files sit beside this `SKILL.md`. Use them from the skill's base directory (given when the skill loads), not from the caller's project.

- **`intake-crashlytics-mcp.md`:** the first intake route. Firebase MCP setup and sign-in, mapping a URL to an App ID, which calls to make, and what the output leaves out.
- **`intake-crashlytics-browser.md`:** the second intake route. The Crashlytics console in Chrome: what to read, where it is, and how to make Crashlytics writes safely through the UI.
- **`intake-paste.md`:** the third intake route, which also works for other services. What to ask for, and how to fill gaps the other routes leave.
- **`issue-file-template.md`:** the issue file and `releases.md` formats.
- **`investigate.md`:** the per-group procedure, the verdicts, the fix rules and the verification step. Read it before Step 4. Subagents read it too.
- **`reading-crashes.md`:** platform reference covering symbols, iOS and Android crash kinds, finding the app's own frame, React Native and Flutter bridges, and what skews in the data point to. Read it during Step 4.
- **`report-to-github.md`:** Step 7's GitHub option, covering the access check, duplicates, issue content and issue state by outcome.
- **`parse_issue_url.py INPUT [INPUT ...]`:** splits Crashlytics console URLs or bare issue IDs into project ID, platform, bundle ID, issue ID and event key, and removes duplicates. It lists Crashlytics issue-list URLs separately and excludes anything else. Prints JSON.

## Step 1: Inputs and project

Gather the following. Ask only for what is missing and blocks the work.

1. **Issues:** any mix of Crashlytics console URLs, issue IDs, a request for top issues ("our top 5 crashes"), and pasted reports. Run `parse_issue_url.py` on any URLs and IDs, and tell the caller about anything it excluded. A non-Crashlytics link, such as a Sentry URL, goes to the paste route.
2. **Working folder** for issue files, `releases.md`, plans and the report:
   - **Default:** a new folder outside the repo, `crash-issue-fixer/<YYYY-MM-DD>-<HHMM>/` inside the session's scratchpad directory if the harness provides one, otherwise a fresh `mktemp -d`.
   - **In the repo:** use a folder inside the repo only if the caller names one. Then add it to `.git/info/exclude`, so it can't be committed by accident.
   - Tell the caller the folder's absolute path. Step 7 decides what survives it.
3. **Project facts**, read from the repo without asking:
   - Platforms and framework: native iOS, native Android, React Native/Expo, or Flutter.
   - Where the app version lives at HEAD: `MARKETING_VERSION` / `Info.plist`, `versionName`, `pubspec.yaml`, `app.json` or `package.json`.
   - The minimum OS: iOS deployment target and Android `minSdk`.
   - The default branch: `git symbolic-ref refs/remotes/origin/HEAD`, else `main` or `master`.
   - How releases are marked in git: tags like `v1.2.3`, release branches, or only version-bump commits.

## Step 2: Intake

**Issue files.** For each issue, write `<working folder>/<issue-slug>.md` from `issue-file-template.md`. The slug is the 8-character short ID plus 2–4 words naming the exception, for example `a1b2c3d4-npe-checkout-adapter`. For pasted issues without an ID, use the date and the words.

**Crashlytics inputs** (URLs, IDs, top issues): use the first route available. A tool counts as available when it is loaded, or listed as a deferred tool. Load deferred tools first, e.g. with ToolSearch.

1. **The Firebase MCP's `crashlytics_*` tools** → follow `intake-crashlytics-mcp.md`.
2. **Otherwise, the Claude-in-Chrome tools** → follow `intake-crashlytics-browser.md`. Mention once that the Firebase MCP makes intake faster and more complete, pointing to `intake-crashlytics-mcp.md` §1 for the setup. Don't wait for the caller to install it.
3. **Otherwise** → follow `intake-paste.md`, and mention both options above once.

**Pasted reports** → follow `intake-paste.md`.

Fill only what the source supports. Put every absent field under **Missing**, saying what the gap weakens.

**Releases.** Once per app, write that app's section in `<working folder>/releases.md`. It holds the newest store release, users per version, the git ref for each version, the version at HEAD, the minimum OS and the default branch. Each intake file says where to get the numbers. Investigation can't fetch them itself, so get them now.

**Data gaps (STOP for that issue).** A gap exists when an exception, signal or Swift trap has a native stack that never reaches the app's own code, because it was cut off or only system or engine frames are shown. These are not gaps:
- **A JS or Dart stack inside the message:** React Native JS errors and Flutter Dart errors carry their stack there, and it counts as reaching app code.
- **ANRs, watchdog kills and memory kills:** they have no throwing line by design. For ANRs and deadlocks, get all threads if the issue file lacks them.
- **Unsymbolicated app frames:** neither the console nor a paste fixes them. They go to `investigate.md` §1, unless the caller has a symbolicated copy elsewhere, e.g. Xcode Organizer with the build's archive.

Fill a real gap from the console (`intake-crashlytics-browser.md`) if the Chrome tools are available. Otherwise, ask the caller to paste the trace (`intake-paste.md` §Filling gaps). Continue intake for the other issues meanwhile. If the gap can't be filled, investigate with what exists and expect low confidence.

## Step 3: Group and dispatch

Group issues that are likely one bug: the same app frame, the same exception type at the same call site, or the same custom-key or breadcrumb pattern. Crashlytics' grouping is heuristic: one bug can appear as several issues when OS versions or compiler inlining change the top frames.

**A group is the unit for everything that follows:** one investigation, one verdict, one plan, one branch, one GitHub issue. Its *lead* is the member with the most users. The group's slug is the lead's slug, and the group's Investigation and Plan live in the lead's issue file. A single issue is a group of one.

Show the caller the groups in a short list, then:

- **One group:** investigate it in the main conversation.
- **Several groups, with a subagent tool available:** run one subagent per group in parallel, up to about 5 at a time, in waves beyond that. Brief each subagent with:
  - the absolute paths of `investigate.md` and `reading-crashes.md`;
  - its issue file paths (lead first), `releases.md` and the repo root;
  - the project facts from Step 1;
  - this instruction: "Follow investigate.md for this group. Change no file except the Investigation sections of these issue files. Return the summary lines from investigate.md §Report."
- **No subagent tool:** investigate the groups one after another.

## Step 4: Investigate

For each group, follow `investigate.md` §1–§7: readable, still happening, locate and attribute, hypothesize, confirm, verdict, plan.

If investigation shows a member has a different cause, it is split into its own group, and the report says so (`investigate.md` §6).

## Step 5: Review (STOP)

Show the caller one table with a row per group:

| Group (lead + members) | Verdict | Confidence | Cause (one line) | Proposed change |
|---|---|---|---|---|

Below it, list the plans in short form (the Fix and Test lines) for `fix` and `instrument` verdicts.

Then ask, in one message:

1. **Which plans to apply:** all, some or none. The caller may also split a group whose members they think differ. Re-investigate the split-off members before applying anything to them.
2. **How to apply them**, with the trade-off of each:
   - **Current branch, one at a time:** changes land in the working tree in sequence. Commit each group separately if the caller wants commits; otherwise leave them uncommitted.
   - **Worktree and branch per group:** each fix goes on its own branch `crash-fix/<group-slug>`, created from a base the caller names (default: the current branch). Each branch is checked out in its own `git worktree` and committed there, so each can become its own pull request. Mention the cost: a new worktree has no installed dependencies (`node_modules`, `Pods`, `.dart_tool`, Gradle and build caches), so building or testing in it may need an install first.

If no group has a plan, skip the question and go to Step 7. Otherwise wait for the answer, and apply nothing without it.

## Step 6: Apply

**Before the first change,** record `git status --porcelain`. If the tree already holds changes unrelated to the plans, tell the caller:
- they stay untouched;
- commits will stage only each plan's files;
- in current-branch mode, a plan that touches one of those files waits until the caller says how to proceed.

**Per approved group,** follow `investigate.md` §Fix rules and §Verify:

1. Re-read the plan and the files it touches. The tree may have moved since Step 4.
2. If the crash path is testable, write the planned test first and see it fail for the planned reason. Then make the change.
3. Make the smallest change that removes the cause. Fix the same mistake elsewhere if the plan listed it, or list the other places instead.
4. Verify with the project's own build and test commands, and report results as they are.
5. Record the outcome in the lead's issue file: files changed, branch or worktree, tests added, and the verification commands with their results.
6. When committing, stage the plan's files by path (`git add -- <files>`).

**Current-branch mode:** apply one group at a time, in table order. Finish each group, and commit it if wanted, before starting the next.

**Worktree mode:**
1. Create every worktree yourself, before any subagent starts. Per group, run `git worktree add <path> -b crash-fix/<group-slug> <base>`, with an absolute path beside the repo, e.g. `<repo parent>/<repo>-crash-<short-id>`.
2. Apply each group in its worktree, in sequence or in parallel subagents (one per worktree). Brief each subagent with:
   - the absolute paths of `investigate.md` and of the lead's issue file;
   - its worktree's absolute path;
   - this instruction: "Apply the approved plan in <worktree> only. Use absolute paths under <worktree> for every file you read or change. Run git as `git -C <worktree> …`, and run builds and tests with `cd <worktree> && …` in the same command. Never read from or write to <repo root> except the issue file. Don't use the Agent tool's `isolation` option: the worktree already exists. Commit there, staging files by path. Return what changed, the commit and the verification results."
3. Afterwards, check that `git -C <repo root> status --porcelain` matches the record from before the first change. If it doesn't, tell the caller what changed in the main tree.
4. Give the caller the worktree paths and branch names. Don't remove the worktrees.

The issue files stay in the working folder; update them by absolute path.

If, while applying, the evidence contradicts the plan, stop that group and report back instead of improvising a different fix.

## Step 7: Report and hand-off (STOP)

1. **Write `<working folder>/report.md`.** It contains:
   - the date and the source(s);
   - the Step 5 table, updated with outcomes;
   - per group: the verdict, the cause, the change (files, commit or branch), the verification result, and **how to confirm it in production**. Name the version that should show no new events for this issue. Crashlytics marks a closed issue as regressed if it reappears in a newer app version.

   Keep field data out of `report.md`, so it is safe to put in the repo or on GitHub.
2. **Ask, in one message.** Any combination of the first three choices is allowed:
   - **Report in the repo:** copy `report.md` to a path the caller names. Suggest `docs/crash-reports/<YYYY-MM-DD>.md` if the repo has a `docs/` folder, otherwise `crash-reports/<YYYY-MM-DD>.md`. Don't commit it unless asked.
   - **GitHub issues:** one per group, with each issue's state set from the outcome, following `report-to-github.md`. Offer this only if its §1 access check passes.
   - **The working folder:** keep it, or delete it. Deleting removes only what this skill created:
     - a default folder is deleted whole;
     - in a folder the caller named, only the files the skill wrote are deleted, and the folder itself only if it is then empty.
   - **Crashlytics actions**, through the route used in Step 2:
     - close `already-fixed` issues;
     - for `fixed-unreleased`, a note now, and closing after that release ships;
     - notes for the rest.

     A note holds the verdict, the cause and a reference to the fix (commit, branch or GitHub issue link), with no field data. Through the browser, follow `intake-crashlytics-browser.md` §Writes.
3. **Do what the caller chose, in this order:**
   1. GitHub issues;
   2. add their URLs to `report.md`;
   3. copy `report.md` into the repo;
   4. Crashlytics actions, so notes can link the GitHub issues;
   5. delete the working folder, if chosen.
4. **Summarize in chat:**
   - the table;
   - where the results went: the repo path and GitHub issue URLs;
   - the working folder's absolute path, if it was kept.

## Stop conditions (summary)

- **Step 2:** a real data gap can't be filled → investigate with what exists, and expect low confidence.
- **Step 5:** always stop for approval before any change.
- **Step 6:** the evidence contradicts the plan, or a plan touches a file the caller had already changed → stop that group and report.
- **Step 7:** always ask before anything leaves the working folder.
