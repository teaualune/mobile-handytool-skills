# Hand-off: GitHub issues

Used in Step 7 when the caller picks GitHub issues. It creates one GitHub issue per group (one bug), and sets each issue's state from the outcome. Choosing this option counts as approval to create the issues, except on a public repo (§1).

## 1. Check access

Check this before offering the option in Step 7:

- Run `gh auth status` and `gh repo view --json nameWithOwner,visibility,hasIssuesEnabled,defaultBranchRef`. A connected GitHub MCP server with issue tools works too; use its equivalents of the commands below.
- If neither the `gh` CLI nor an MCP server reaches the repo, or issues are disabled, don't offer the option.
- **Public repo:** its issues are public. Show the caller the drafts (title, state, body) and wait for an explicit OK before creating anything.

## 2. Avoid duplicates

Each body starts with a marker listing the group's Crashlytics issue IDs. Before creating an issue, search for an existing one, once per member ID:

`gh issue list --state all --search "<crashlytics issue id> in:body" --json number,title,state,url`

When one exists, comment on it with this run's outcome instead of creating a new issue. Reopen it if the crash came back (regressed) while it was closed.

## 3. Content

- **Title:** `Crash: <exception type> in <function or file>`, kept short.
- **Labels:** add `bug` or `crash` only if the label already exists (`gh label list`). Never create labels unless the caller asks.
- **Body:** built from `report.md` and the lead's Investigation and Plan, with no field data:
  - no log lines, custom key values, or user or device identifiers;
  - the exception message only with its values replaced by placeholders (`<email>`, `<id>`, `<url>`).

  Stack frames from the app's own code are fine.

~~~markdown
<!-- crash-issue-fixer: <crashlytics issue id>[, <crashlytics issue id>…] -->
**Crash:** `<exception type>: <message, values replaced by placeholders>` · <error type> · <platform / framework>
**Crashlytics:** [<short id>](<console link>) (one per issue in the group)
**Affected versions:** <first seen> – <last seen> · **Volume:** <events> events, <users> users (<period>)

### Verdict
<verdict> · confidence <level>

### Cause
<the story, with file:line>

### Fix
<the plan's Fix line>
**Status:** <applied in commit <sha> / on branch `crash-fix/<group-slug>` / uncommitted / not applied> · verification: <result>

### Confirm in production
<the plan's Production check line>
~~~

Create the issue with `gh issue create --title "<title>" --body-file <file> [--label <label>]`, writing the body file into the working folder.

## 4. State from the outcome

| Outcome | GitHub issue |
|---|---|
| `fix` applied and verified, in a commit that is on the remote default branch | Closed as completed (`gh issue close <n> --reason completed --comment "<commit>"`) |
| `fix` applied on a branch, uncommitted, or not pushed | Open. Comment with the branch name, and tell the caller to put `Fixes #<n>` in the pull request description, so that merging the pull request closes the issue. |
| `fix` applied, but verification failed or couldn't run | Open, with what failed or wasn't run |
| `fix` or `instrument` not approved in Step 5 | Open, with the plan |
| `instrument` applied | Open. The next occurrence's data belongs in this issue. |
| `needs-symbols` | Open, with what to upload |
| `already-fixed` | Created, then closed as completed, naming the version or commit that fixed it. Skip it if the caller wants issues only for open work. |
| `fixed-unreleased`, with the commit on the remote default branch | Created, then closed as completed, naming the commit and the release it will ship in |
| `fixed-unreleased`, with the commit on an unmerged branch | Open. Comment with the branch name, and tell the caller to put `Fixes #<n>` in that branch's pull request. |
| `no-action` | Created, then closed as not planned (`--reason "not planned"`), with the reason |

A GitHub issue tracks the code, so it closes once the fix is on the default branch. The Crashlytics issue closes later, once the release ships (SKILL.md Step 7). To tell whether a commit is on the remote default branch, run `git merge-base --is-ancestor <sha> origin/<default branch>`. It reflects the last fetch; don't fetch without asking.

## 5. Finish

- Add each GitHub issue URL to `report.md` and to the lead issue files' **Outcome** lines, before `report.md` is copied anywhere.
- If the caller approved Crashlytics notes, put the GitHub issue link in the note. The notes are posted after the GitHub issues exist.
- List the URLs in the final summary.
