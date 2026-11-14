#!/usr/bin/env python3
"""Split Crashlytics console issue URLs, or bare issue IDs, into their parts.

An input is either a console URL such as
  https://console.firebase.google.com/u/0/project/<projectId>/crashlytics/app/<platform>:<bundleId>/issues/<issueId>
or a bare issue ID (32 hex characters). A Crashlytics URL without an issue
(the app's issue list) is reported under "issue_lists", usable for a
top-issues request. Anything else (Sentry links, other console pages) is
excluded. The same issue given twice (e.g. as a URL and as an ID) is kept once.

Usage:
  python3 parse_issue_url.py INPUT [INPUT ...]
  printf '%s\n' INPUT1 INPUT2 | python3 parse_issue_url.py -

Prints a JSON report to stdout and a human-readable summary to stderr.
"""
import json
import re
import sys
from urllib.parse import parse_qs, urlparse, unquote

ISSUE_ID = re.compile(r"^[0-9a-f]{32}$", re.IGNORECASE)
CONSOLE_HOST = "console.firebase.google.com"


def clean(raw: str) -> str:
    text = raw.strip()
    md_link = re.fullmatch(r"\[[^\]]*\]\((.+)\)", text)
    if md_link:
        text = md_link.group(1)
    text = text.strip("<>\"'`").rstrip(").,;:!?").lstrip("(")
    if text.lower().startswith(CONSOLE_HOST):
        text = "https://" + text
    return text


def segment_after(segments: list, name: str):
    if name in segments[:-1]:
        return segments[segments.index(name) + 1]
    return None


def parse(raw: str) -> dict:
    text = clean(raw)
    result = {
        "input": raw.strip(),
        "valid": False,
        "reason": "",
        "kind": None,
        "project_id": None,
        "platform": None,
        "bundle_id": None,
        "issue_id": None,
        "short_id": None,
        "event_key": None,  # sessionEventKey: the specific event the caller was viewing
    }

    if ISSUE_ID.match(text):
        issue_id = text.lower()
        result.update(valid=True, reason="bare issue id (app must come from elsewhere)",
                      kind="id", issue_id=issue_id, short_id=issue_id[:8])
        return result

    try:
        parsed = urlparse(text)
    except ValueError as exc:
        result["reason"] = f"unparseable input ({exc})"
        return result

    host = (parsed.hostname or "").lower()
    if host != CONSOLE_HOST:
        result["reason"] = (f"not a Firebase console URL or a 32-hex issue id "
                            f"(host: {host or 'none'}); paste the report instead")
        return result

    segments = [unquote(s) for s in parsed.path.split("/") if s]
    if len(segments) >= 2 and segments[0] == "u":  # account switcher prefix /u/<n>/
        segments = segments[2:]

    project_id = segment_after(segments, "project")
    if "crashlytics" not in segments or not project_id:
        result["reason"] = "Firebase console URL, but not a Crashlytics page"
        return result

    app = segment_after(segments, "app") or ""
    platform, _, bundle_id = app.partition(":")
    result.update(project_id=project_id,
                  platform=(platform or None) if bundle_id else None,
                  bundle_id=bundle_id or (app or None))

    issue_id = segment_after(segments, "issues")
    if not issue_id:
        if bundle_id:
            result.update(reason="Crashlytics issue list (no issue id)", kind="issue_list")
        else:
            result["reason"] = "Crashlytics URL without an app or issue"
        return result
    if not ISSUE_ID.match(issue_id):
        result["reason"] = f"issue segment is not a 32-hex issue id: {issue_id}"
        return result

    issue_id = issue_id.lower()
    event_key = (parse_qs(parsed.query).get("sessionEventKey") or [None])[0]
    result.update(valid=True, reason="console issue URL", kind="url",
                  issue_id=issue_id, short_id=issue_id[:8], event_key=event_key)
    return result


def dedupe(issues: list) -> tuple:
    # Prefer a URL over a bare id for the same issue: it carries the app.
    by_id, dropped = {}, []
    for r in issues:
        kept = by_id.get(r["issue_id"])
        if kept is None:
            by_id[r["issue_id"]] = r
        elif kept["kind"] == "id" and r["kind"] == "url":
            by_id[r["issue_id"]] = r
            dropped.append(kept)
        else:
            dropped.append(r)
    return list(by_id.values()), dropped


def main(argv):
    args = argv[1:]
    if not args:
        print("usage: parse_issue_url.py INPUT [INPUT ...] (or - for stdin)", file=sys.stderr)
        return 2
    inputs = [line.strip() for line in sys.stdin if line.strip()] if args == ["-"] else args

    results = [parse(i) for i in inputs]
    issues, duplicates = dedupe([r for r in results if r["valid"]])
    lists = [r for r in results if r["kind"] == "issue_list"]
    excluded = [r for r in results if not r["valid"] and r["kind"] != "issue_list"]
    print(json.dumps({
        "total": len(results),
        "issue_count": len(issues),
        "excluded_count": len(excluded),
        "issues": issues,
        "issue_lists": lists,
        "duplicates": duplicates,
        "excluded": excluded,
    }, indent=2))

    print(f"\n{len(issues)} issue(s), {len(lists)} issue list(s), "
          f"{len(duplicates)} duplicate(s), {len(excluded)} excluded.", file=sys.stderr)
    for r in issues:
        where = f"{r['platform']}:{r['bundle_id']} in {r['project_id']}" if r["kind"] == "url" else "app unknown"
        print(f"  [OK]   {r['short_id']}  {where}", file=sys.stderr)
    for r in lists:
        print(f"  [LIST] {r['platform']}:{r['bundle_id']} in {r['project_id']}", file=sys.stderr)
    for r in duplicates:
        print(f"  [DUP]  {r['input']}", file=sys.stderr)
    for r in excluded:
        print(f"  [SKIP] {r['input']}  ->  {r['reason']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
