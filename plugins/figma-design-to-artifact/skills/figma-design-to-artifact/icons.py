#!/usr/bin/env python3
"""Pick the vector layers worth exporting from a layer tree, and save their SVGs.

  python icons.py list LAYERS.json [--max-size 64]
      Prints the distinct layers to export, as JSON: each topmost layer whose
      subtree has vector shapes but no text or image. Ones that fit in
      max-size × max-size are "icon", larger ones "graphic" (logos, background
      shapes); a larger one holding instances or frames is split into them
      instead. Repeats (same name and size) are listed once; lines (≤ 1 px
      thick) and system chrome (status bar, home indicator, keyboard) are
      skipped.
  python icons.py save BUNDLE.json OUT_DIR
      Writes each {name: svg} entry of the in-page download to OUT_DIR/<name>.svg
      and prints what it wrote, as JSON.
"""
import argparse
import json
import re
import sys
from pathlib import Path

VECTOR_TYPES = {"VECTOR", "BOOLEAN_OPERATION", "STAR", "REGULAR_POLYGON", "ELLIPSE", "LINE"}
CONTAINER_TYPES = {"INSTANCE", "FRAME", "COMPONENT"}
SYSTEM_CHROME = re.compile(r"status\s*bar|home\s*indicator|keyboard", re.I)


def size_of(node):
    layout = node.get("properties", {}).get("Layout")
    if not isinstance(layout, dict):
        return None
    dims = []
    for key in ("Width", "Height"):
        m = re.search(r"([\d.]+)px", str(layout.get(key, "")))
        if not m:
            return None
        dims.append(float(m.group(1)))
    return tuple(dims)


def scan(node):
    """Returns (has_vector, has_text_or_image) for the subtree."""
    kind = node.get("type") or node.get("uiType")
    vec, blocked = kind in VECTOR_TYPES, kind == "TEXT" or kind == "Image"
    for kid in node.get("children", []):
        v, b = scan(kid)
        vec, blocked = vec or v, blocked or b
    return vec, blocked


def list_icons(root, max_size):
    found = {}

    def walk(node, is_root):
        if SYSTEM_CHROME.search(node["name"]):
            return
        vec, blocked = scan(node)
        if not is_root and vec and not blocked:
            size = size_of(node)
            if size and min(size) <= 1:
                return  # dividers and other lines: the tree describes them better
            oversized = not size or max(size) > max_size
            if oversized and any(k.get("type") in CONTAINER_TYPES for k in node.get("children", [])):
                for kid in node["children"]:  # e.g. a toolbar row of icon buttons
                    walk(kid, False)
                return
            key = (node["name"], size)
            if key in found:
                found[key]["count"] += 1
            else:
                found[key] = {"id": node["id"], "rowId": node["id"].split(";")[-1],
                              "name": node["name"],
                              "kind": "icon" if size and max(size) <= max_size else "graphic",
                              "width": size[0] if size else None,
                              "height": size[1] if size else None, "count": 1}
            return
        for kid in node.get("children", []):
            walk(kid, False)

    walk(root, True)
    return list(found.values())


def safe_name(name, taken):
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-").lower() or "icon"
    out, n = base, 2
    while out in taken:
        out, n = f"{base}-{n}", n + 1
    taken.add(out)
    return out


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_list = sub.add_parser("list")
    p_list.add_argument("layers")
    p_list.add_argument("--max-size", type=float, default=64)
    p_save = sub.add_parser("save")
    p_save.add_argument("bundle")
    p_save.add_argument("out_dir")
    args = ap.parse_args(argv[1:])

    if args.cmd == "list":
        tree = json.loads(Path(args.layers).read_text(encoding="utf-8"))
        icons = list_icons(tree["document"], args.max_size)
        print(json.dumps(icons, ensure_ascii=False, indent=1))
        print(f"{len(icons)} layer(s) to export", file=sys.stderr)
        return 0

    bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    taken, written = set(), []
    for name, svg in bundle.items():
        if not str(svg).lstrip().startswith("<svg"):
            print(f"  [SKIP] {name}: not SVG text", file=sys.stderr)
            continue
        path = out / (safe_name(name, taken) + ".svg")
        path.write_text(svg, encoding="utf-8")
        written.append({"name": name, "file": str(path)})
    print(json.dumps(written, ensure_ascii=False, indent=1))
    print(f"{len(written)} SVG file(s) written to {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
