# Investigating a crash group

The per-group procedure for phase 2, used by the main agent or by a subagent. A group is one bug, which may span several Crashlytics issues. Its lead is the first issue file listed.

- **Input:** the group's issue files, `releases.md` and the repo.
- **Output:**
  - the group's Investigation and Plan, in the lead's issue file;
  - a one-line pointer in each other member's Investigation section;
  - the summary lines in §Report.

You may read code, git history and dependency lockfiles, and run read-only commands: `git log`, `git show`, `git grep`, dependency listings, and the project's existing tests or analyzers. Change no file except the Investigation sections. If a test would prove the cause, describe it in the plan; it is written in Step 6.

Platform details for every section below are in `reading-crashes.md`.

## §1 Readable?

Unreadable app frames look like this (`reading-crashes.md` §Symbols):
- **iOS:** bare addresses or `<AppBinary> + 123456`.
- **Android:** obfuscated names such as `a.b.c`.
- **Flutter:** address-only Dart frames (`abs … virt …`) from `--split-debug-info` builds, or obfuscated names from `--obfuscate` builds.
- **React Native:** minified JS or Hermes bytecode offsets.

If the app frames are unreadable, the verdict is `needs-symbols`, stating what to upload. One exception: when the rest of the evidence is enough to locate the cause, continue with lower confidence. That evidence includes the exception message, readable system frames, logs and breadcrumbs.

## §2 Still happening?

**From `releases.md`,** which intake fills once per app:
- **R:** the newest store release.
- **Users per version.**
- **H:** the version at HEAD.
- **Git refs:** one per version.
- **The minimum OS at HEAD.**
- **The default branch.**

**From the issue files:**
- **F / L:** the first and last version each member was seen in;
- **Per-version counts:** events and users per version.

If `releases.md` has no user counts, the exposure test below can't run. Say so, and don't conclude `already-fixed` from absence alone.

Then work through these cases:

- **L is older than R:** the issue stopped appearing before the latest release.
  1. Look for changes to the blamed files or symbols in `git log <L-ref>..<R-ref>`, including bumps of a blamed dependency in the lockfiles.
  2. Check exposure. If the issue hit k users per 1,000 on L, expect about k × (R's users) / 1,000 users on R.
     - If that is well above zero and R shows none, the absence counts as evidence.
     - If R is only days old or has few users, the absence proves nothing.
  3. A plausible change plus enough exposure → `already-fixed`, naming the version and commit. With no relevant change, the code path may have been removed, or R may not yet have reached the conditions. Say which, and don't conclude "fixed" from absence alone.
- **L is R (seen in the latest release):** the issue is live in production. Look for a fix not yet released:
  - in `git log <R-ref>..<default branch>` on the same files;
  - on the current branch, if it isn't the default branch.

  A change that removes the cause → `fixed-unreleased`, naming the commit. Check whether that commit is on the default branch (`git merge-base --is-ancestor <sha> <default branch>`). If it isn't, say it is unmerged and name its branch. Otherwise continue.
- **L is newer than R:** the issue was seen only in a pre-release build (TestFlight, an internal track, or a version newer than R with few users), so the crash is in code not yet released.
  1. Find what introduced it in `git log <R-ref>..<L-ref>`.
  2. Look for a later fix in `git log <L-ref>..<default branch>` → `fixed-unreleased`.
  3. Otherwise continue: fixing it before release is the cheapest moment.
- **Regressed** (state or signal): the issue was closed and came back. Find what the earlier fix did, from team notes or `git log`, and why it didn't hold.
- **Code gone:** if the blamed function or file no longer exists at HEAD, trace where it went (`git log --follow`, `git log -S'<symbol>'`) before deciding anything.
- **OS floor:** if every affected OS version is below HEAD's minimum (`minSdk` or the iOS deployment target), the issue can't recur. The verdict is `already-fixed` if the raise shipped in R, `fixed-unreleased` if not; either way, name the commit that raised the floor.
- **No version data** (common for pasted issues): say the check couldn't be made, and continue.

## §3 Locate and attribute

1. **Classify the crash kind** (`reading-crashes.md` §iOS crash kinds, §Android crash kinds): exception, signal, Swift trap, ANR, watchdog or memory kill. ANRs, watchdog kills and memory kills have no throwing line. The stack shows where the main thread was when the system gave up, not what blocked it or what used the memory.
2. **Find the app frame:** the first frame from the app's own code (`reading-crashes.md` §Whose frame). Crashlytics' blamed frame is a hint, not the answer. Read the code there, and walk up through the callers to the entry point: a lifecycle method, user action, callback, notification or background job. For React Native and Flutter, cross to the JS or Dart side (`reading-crashes.md` §React Native, §Flutter).
3. **Attribute the fault**, as one of:
   - `app`: this repo's code;
   - `dependency`: an SDK, library or plugin, with its name and the version from the lockfile;
   - `platform`: the OS, or the React Native/Flutter framework or engine;
   - `unknown`.

   When the fault isn't `app`, check whether the dependency's changelog or issue tracker knows the signature, if a web tool is available. Even a `dependency` or `platform` crash often has an app-side trigger, such as calling an SDK on the wrong thread or before it is initialized.

## §4 Hypothesize

1. List up to 5 candidate causes. Each one is a concrete story: this state and this sequence reach this line, which crashes this way.
2. Test each candidate against all the evidence, from every member of the group:
   - the exception message and the crashing thread;
   - the version, OS and device distribution;
   - custom keys, logs and breadcrumbs;
   - foreground or background state, and time since launch;
   - users versus events: one user crashing repeatedly differs from many users crashing once.

   A cause that can't explain a strong skew is incomplete: why only Android 14, only iPad, or only since 3.2? `reading-crashes.md` §Skews lists what common skews point to.
3. Pick the candidate that explains the most, and keep the runners-up for **Other causes**. Don't settle on your first idea, and don't accept a cause that contradicts the trace.

## §5 Confirm

- **Trace the path:** show the code path from an entry point to the crashing line, the condition that makes it crash, and why that condition happens in the field. For example: a callback arrives after the screen was dismissed, or a response field is null for accounts created before some date.
- **Reproduce if cheap:** if a unit test can drive the path, describe that test as the plan's **Test**. An existing test or analyzer that already exposes the problem may be run now.
- **Set the confidence:**
  - `high`: the path is traced, the evidence fits, and the triggering condition is explained;
  - `medium`: the path is traced, but the condition is plausible rather than proven;
  - `low`: several candidates remain.

## §6 Verdict

One verdict per group.

| Verdict | When | What to propose |
|---|---|---|
| `fix` | The cause is in code this repo controls. This includes upgrading a dependency or working around one. | The plan (§7). |
| `already-fixed` | §2 found a change in a store release that removes the cause, or a raised OS floor that shipped. | No code change. Recommend closing the Crashlytics issue, and name the version to watch. |
| `fixed-unreleased` | §2 found a change that removes the cause but isn't in a store release yet, on the default branch or on a named unmerged branch. | No code change. Recommend a Crashlytics note now and closing after that release ships. If the commit is unmerged, say so and recommend merging it. |
| `instrument` | The available data can't settle the cause. | Custom keys, logs or breadcrumbs at named points, so the next occurrence carries the missing facts (within Fix rule 8). Say which hypotheses each one tells apart. |
| `needs-symbols` | The app frames are unreadable (§1). | What to upload and how (`reading-crashes.md` §Symbols). Re-run the investigation afterwards. |
| `no-action` | A change isn't possible or isn't worth it. Examples: an OS or vendor bug with no workaround; only rooted, jailbroken, modified or emulator devices; negligible volume on versions no longer supported. | Why. For a vendor bug, draft a short report the caller can file. |

A low-confidence `fix` should come paired with instrumentation; say so in the plan.

**A member that doesn't fit:** if the evidence shows a member has a different cause, split it out of the group. Note why in its Investigation section, investigate it as its own group, and report it on its own summary line.

## §7 Plan

Required for `fix` and `instrument`. Fill these fields in the lead's issue file:

- **Cause:** the story from §4, with `file:line` references.
- **Fault:** `app`, `dependency name@version`, or `platform`.
- **Fix:** what changes and where, and what the user experiences in the crashing situation after the fix.
- **Test:** the test to add (name the case), manual steps, or why it can't be tested locally.
- **Same pattern elsewhere:** other places with the same mistake (`git grep`).
- **Other causes:** the runners-up, and what evidence would tell them apart.
- **Production check:** the version to watch, and the signal expected.

In each other member's Investigation section, write: `Group <lead-slug>: <verdict>. Same cause because <one line>. See <lead-slug>.md.`

## Fix rules

These apply to every plan and every change.

1. **Remove the cause, not the crash.** None of these is acceptable as the whole fix: a try/catch around the crash site; a null, bounds, `isAdded` or `isViewLoaded` guard that returns early; `?.` or `?:` that swallows the case; or replacing a force-unwrap with a silent `return`. The one exception is when the analysis shows the state is legitimate (for example, a callback that arrives after its screen is gone) and the plan's Fix line says what the user sees instead. A guard that hides a state from the code that should handle it is a symptom patch.
2. **Keep the behaviour.** The fix must not avoid the crash by removing functionality, such as skipping the save or not showing the screen. If it trades something off, the plan says so.
3. **Don't downgrade the signal.** Turning a crash into a silently logged non-fatal is a symptom patch, unless the caller asks for it.
4. **Make the smallest change** that removes the cause, with no refactoring on the side.
5. **Dependency faults:** prefer upgrading to a version whose changelog names the fix. A workaround in app code carries a one-line comment linking the upstream issue.
6. **Threading fixes** state which thread or queue owns the state after the change.
7. **Tests:** don't change an existing test's expectations to make the fix pass, unless that test encoded the bug.
8. **Instrumentation records state, not user data.**
   - **Allowed:** enums, counts, flags, sizes, error codes, screen or step names.
   - **Never, not even hashed:** user identifiers, emails, names, tokens, free-form text, request or response bodies.
   - New keys and logs must stay within what the app's privacy disclosures (App Store privacy labels, Play Data safety) already declare for crash data.

## Verify

Use the project's own commands, found in the README, scripts, Makefile, CI config, `package.json` scripts or Gradle tasks. Examples: `./gradlew :app:testDebugUnitTest`, `xcodebuild test -scheme <Scheme> -destination …`, `flutter analyze && flutter test`, `npx tsc --noEmit && npm test`. At minimum, compile the touched module.

If something can't run here (no simulator, missing secrets or signing, dependencies not installed in a worktree), say what wasn't run. Report failures exactly as they are, and never weaken a test to make it pass.

## Report

Write one line per group: `<lead-slug> [+ <member slugs>] | <verdict> | <confidence> | <one-line cause> | <one-line proposed change>`. Add a line for each member you split off. A subagent returns these lines as its final message; the main agent uses them for the Step 5 table. The details stay in the issue files.
