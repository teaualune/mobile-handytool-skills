#!/usr/bin/env python3
"""Validate Figma URLs and classify each as a node-export target or excluded.

A valid target is an *editable* Figma design file URL that points at a specific
node: the host is figma.com (or a subdomain), the path starts with /design/ or
/file/, and the URL carries a non-empty node-id query parameter. Everything else
(non-figma domains, plain file links with no node-id, prototypes, marketing
pages) is excluded so it can be reported to the caller before any browser work.

Usage:
  python validate_figma_urls.py URL [URL ...]
  printf '%s\n' URL1 URL2 | python validate_figma_urls.py -   # read from stdin

Prints a JSON report to stdout and a human-readable summary to stderr.
"""
import json
import re
import sys
from urllib.parse import urlparse, parse_qs, unquote

EDITABLE_PATH_TYPES = {"design", "file"}


def slugify(text: str) -> str:
    text = unquote(text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-{2,}", "-", text).strip("-")


def classify(url: str) -> dict:
    result = {
        "url": url,
        "valid": False,
        "reason": "",
        "file_key": None,
        "file_name": None,
        "node_id": None,
        "slug": None,
    }
    try:
        parsed = urlparse(url.strip())
    except Exception as exc:  # noqa: BLE001
        result["reason"] = f"unparseable URL ({exc})"
        return result

    host = (parsed.netloc or "").lower().split("@")[-1].split(":")[0]
    if not (host == "figma.com" or host.endswith(".figma.com")):
        result["reason"] = f"not a figma.com URL (host: {host or 'none'})"
        return result

    segments = [s for s in parsed.path.split("/") if s]
    path_type = segments[0] if segments else ""
    if path_type not in EDITABLE_PATH_TYPES:
        result["reason"] = (
            f"not an editable design file (path starts with '/{path_type}', "
            "expected '/design/' or '/file/')"
        )
        return result

    qs = parse_qs(parsed.query)
    node_values = qs.get("node-id") or qs.get("node_id") or []
    node_id = node_values[0] if node_values else ""
    if not node_id:
        result["reason"] = "no node-id parameter (URL points at a file, not a node)"
        return result

    file_key = segments[1] if len(segments) > 1 else ""
    file_name = unquote(segments[2]) if len(segments) > 2 else ""
    norm_node = unquote(node_id).replace(":", "-")

    result.update(
        valid=True,
        reason="valid node target",
        file_key=file_key,
        file_name=file_name or None,
        node_id=unquote(node_id),
        slug=slugify(f"{file_name}-{norm_node}") or slugify(norm_node) or file_key,
    )
    return result


def main(argv):
    args = argv[1:]
    if not args:
        print("usage: validate_figma_urls.py URL [URL ...] (or - for stdin)",
              file=sys.stderr)
        return 2
    if args == ["-"]:
        urls = [line.strip() for line in sys.stdin if line.strip()]
    else:
        urls = args

    results = [classify(u) for u in urls]
    valid = [r for r in results if r["valid"]]
    excluded = [r for r in results if not r["valid"]]

    report = {
        "total": len(results),
        "valid_count": len(valid),
        "excluded_count": len(excluded),
        "targets": valid,
        "excluded": excluded,
    }
    print(json.dumps(report, indent=2))

    print("\n=== Figma URL validation ===", file=sys.stderr)
    print(f"{len(valid)} valid node target(s), {len(excluded)} excluded.",
          file=sys.stderr)
    for r in valid:
        print(f"  [OK]   {r['url']}  ->  slug: {r['slug']}", file=sys.stderr)
    for r in excluded:
        print(f"  [SKIP] {r['url']}  ->  {r['reason']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
