#!/usr/bin/env python3
"""Assemble a layers-panel capture into a nested Figma layer tree (JSON).

Input is the file the layer scan in figma-browser-navigation.md downloads:
{"target": "<node id>", "rows": [{"ri", "id", "depth", "pos", "size", "type",
"name", "ok", "panel"}, ...]} in layers-panel order. Structure uses
Figma REST API node keys (id, name, type, characters, children); the viewer
Properties panel values are kept as shown, under "properties".

Usage:
  python build_layer_tree.py CAPTURE.json [--source-url URL] [--pretty] > tree.json

Prints the tree to stdout — compact, one value per line, unless --pretty —
and a summary plus warnings to stderr; exits 1 if the capture cannot form a
tree.
"""
import argparse
import json
import sys
from collections import Counter

REST_TYPES = {
    "Section": "SECTION", "Frame": "FRAME", "Auto layout": "FRAME",
    "Component": "COMPONENT", "Component set": "COMPONENT_SET",
    "Instance": "INSTANCE", "Text": "TEXT", "Vector": "VECTOR",
    "Rectangle": "RECTANGLE", "Ellipse": "ELLIPSE", "Line": "LINE",
    "Polygon": "REGULAR_POLYGON", "Star": "STAR", "Group": "GROUP",
    "Slice": "SLICE", "Boolean operation": "BOOLEAN_OPERATION",
    "Union": "BOOLEAN_OPERATION", "Subtract": "BOOLEAN_OPERATION",
    "Intersect": "BOOLEAN_OPERATION", "Exclude": "BOOLEAN_OPERATION",
}
SECTIONS = {
    "Component properties", "Layout", "Content", "Typography", "Colors",
    "Borders", "Shadows and blurs", "Effects", "Export", "Code & measurements",
}
SKIPPED_SECTIONS = {"Export", "Code & measurements"}
NOISE = {"Color format", "Hex", "RGB", "HSL", "HSB", "CSS", "?", "View documentation"}
LAYOUT_KEYS = {
    "Flow", "Width", "Height", "Top", "Left", "Right", "Bottom", "Radius",
    "Rotation", "Gap", "Padding", "Border", "Inner alignment", "Justify",
    "Alignment", "Opacity", "Min width", "Max width", "Min height",
    "Max height", "Clip content", "Columns", "Rows", "Column gap", "Row gap",
}
PADDING_SIDES = {"Top", "Right", "Bottom", "Left", "Horizontal", "Vertical"}
TYPOGRAPHY_KEYS = {
    "Name", "Font", "Weight", "Style", "Size", "Line height", "Letter spacing",
    "Paragraph spacing", "Paragraph indent", "Horizontal alignment",
    "Vertical alignment", "Decoration", "Case", "Numeric figure",
    "Numeric spacing", "Truncation", "Max lines", "List style",
}
AUTO_LAYOUT_FLOWS = {"Horizontal", "Vertical", "Wrap", "Grid"}
BOGUS = "[object Object]"  # Figma's panel sometimes prints this instead of a value


def pairs(lines, keys):
    """Key/value dict when every line pairs up cleanly, else the lines as-is."""
    out, i = {}, 0
    while i < len(lines):
        key = lines[i]
        if key not in keys or key in out:
            return lines
        if key == "Padding" and i + 1 < len(lines) and lines[i + 1] in PADDING_SIDES:
            sides, i = {}, i + 1
            while i + 1 < len(lines) and lines[i] in PADDING_SIDES and lines[i] not in sides:
                sides[lines[i]] = lines[i + 1]
                i += 2
            sides = {s: v for s, v in sides.items() if BOGUS not in v}
            if sides:
                out[key] = sides
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else None
        if nxt is None or nxt in keys:
            out[key] = True  # shown as a control, no text value
            i += 1
        else:
            if BOGUS not in nxt:
                out[key] = nxt
            i += 2
    return out


def parse_panel(text, name):
    lines = [l.replace("\xa0", " ").strip() for l in (text or "").split("\n")]
    lines = [l for l in lines if l and not l.startswith(("To measure", "Need a code snippet"))]
    props, header, sections, current = {}, [], {}, None
    for line in lines:
        if line in SECTIONS:
            current = line
            sections.setdefault(current, [])
        elif current is None:
            header.append(line)
        elif current not in SKIPPED_SECTIONS:
            sections[current].append(line)

    if header[:2] == ["Text", name]:
        header = header[2:]  # text layers show a "Text" badge above the name
    elif header[:1] == [name]:
        header = header[1:]
    if header[:1] == ["Parent component"] and len(header) > 1:
        props["Parent component"] = header[1]
        header = header[2:]
    header = [l for l in header if l not in NOISE]
    if header:
        props["Description"] = "\n".join(header)

    characters = None
    for section, body in sections.items():
        if section in SKIPPED_SECTIONS:
            continue
        body = [l for l in body if l not in NOISE]
        if section == "Content":
            characters = "\n".join(body)
        elif section == "Layout":
            props[section] = pairs(body, LAYOUT_KEYS)
        elif section == "Typography":
            props[section] = pairs(body, TYPOGRAPHY_KEYS)
        else:
            props[section] = [l for l in body if BOGUS not in l]
    bogus = sum(BOGUS in l for l in lines)
    return props, characters, bogus


def is_auto_layout(node):
    layout = node.get("properties", {}).get("Layout")
    flow = layout.get("Flow") if isinstance(layout, dict) else None
    if isinstance(layout, list) and "Flow" in layout[:-1]:
        flow = layout[layout.index("Flow") + 1]
    return node.get("_ui") == "Auto layout" or flow in AUTO_LAYOUT_FLOWS


def finish(node):
    kids = node.get("children")
    if kids:
        if not is_auto_layout(node):
            kids.reverse()  # panel lists top-most first; REST lists bottom-most first
        for kid in kids:
            finish(kid)
    node.pop("_ui", None)


def build(capture):
    rows = capture.get("rows") or []
    errors, warnings = [], []
    if not rows:
        return None, ["capture has no rows"], warnings
    if capture.get("target") and rows[0]["id"] != capture["target"]:
        errors.append(f"first row {rows[0]['id']} is not the target {capture['target']}")

    stack, root, kid_rows = [], None, {}
    unverified = repeats = gaps = dropped = 0
    for idx, row in enumerate(rows):
        if idx and row["ri"] != rows[idx - 1]["ri"] + 1:
            gaps += 1
        if idx and row.get("panel") == rows[idx - 1].get("panel"):
            repeats += 1
        while stack and stack[-1][0]["depth"] >= row["depth"]:
            stack.pop()
        if stack and row["depth"] != stack[-1][0]["depth"] + 1:
            errors.append(f"row {row['id']} jumps from depth {stack[-1][0]['depth']} to {row['depth']}")
        chain = [r["id"] for r, _ in stack if r.get("type") == "Instance"]

        props, characters, bogus = parse_panel(row.get("panel"), row["name"])
        dropped += bogus
        ui = row.get("type") or ""
        node = {"id": "I" + ";".join(chain + [row["id"]]) if chain else row["id"],
                "name": row["name"]}
        if ui in REST_TYPES:
            node["type"] = REST_TYPES[ui]
        else:
            node["uiType"] = ui
        if characters is not None:
            node["characters"] = characters
        if props:
            node["properties"] = props
        if not row.get("ok", True):
            node["_unverified"] = True
            unverified += 1
        node["_ui"] = ui

        if stack:
            stack[-1][1].setdefault("children", []).append(node)
            kid_rows.setdefault(stack[-1][0]["ri"], []).append(row)
        elif root is None:
            root = node
        else:
            errors.append(f"row {row['id']} is outside the target subtree")
        stack.append((row, node))

    short = sum(1 for kids in kid_rows.values()
                if any(k.get("size") not in (None, len(kids)) for k in kids))
    if short:
        warnings.append(f"{short} layer(s) have fewer captured children than the panel lists; rescan")
    if gaps:
        warnings.append(f"{gaps} gap(s) in row indexes: rows were skipped while scrolling; rescan")
    if unverified:
        warnings.append(f"{unverified} row(s) not confirmed selected when read (marked _unverified)")
    if repeats:
        warnings.append(f"{repeats} row(s) read the same panel text as the previous row (possible stale read)")
    if dropped:
        warnings.append(f"{dropped} value(s) Figma's panel showed as '{BOGUS}' were dropped")
    if root:
        finish(root)
    return root, errors, warnings


def stats(root):
    types, count, depth = Counter(), 0, 0
    todo = [(root, 0)]
    while todo:
        node, d = todo.pop()
        count, depth = count + 1, max(depth, d)
        types[node.get("type") or node.get("uiType")] += 1
        todo.extend((k, d + 1) for k in node.get("children", []))
    return {"nodes": count, "maxDepth": depth, "types": dict(types.most_common())}


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("capture")
    ap.add_argument("--source-url")
    ap.add_argument("--pretty", action="store_true", help="indent for human reading")
    args = ap.parse_args(argv[1:])
    with open(args.capture, encoding="utf-8") as fh:
        capture = json.load(fh)

    root, errors, warnings = build(capture)
    for e in errors:
        print(f"  [ERROR] {e}", file=sys.stderr)
    for w in warnings:
        print(f"  [WARN]  {w}", file=sys.stderr)
    if errors or root is None:
        return 1

    summary = stats(root)
    print(json.dumps({
        "source": {"url": args.source_url, "nodeId": capture.get("target"),
                   "capturedFrom": "figma.com Layers panel + Properties panel (view access)"},
        "conventions": {
            "structure": "Figma REST API node keys: id, name, type, characters, children",
            "childOrder": "REST order: auto-layout children in flow order, others bottom-most first",
            "ids": "layers inside instances use Figma's I<instance>;<layer> form",
            "properties": "values exactly as Figma's Properties panel shows them; "
                          "a section that does not pair up cleanly keeps its lines in order",
        },
        "stats": summary,
        "document": root,
    }, ensure_ascii=False, **(  # short lines keep it readable by line-based tools
        {"indent": 1} if args.pretty else {"indent": 0, "separators": (",", ":")})))
    print(f"\n=== Layer tree: {summary['nodes']} nodes, depth {summary['maxDepth']}, "
          f"{len(warnings)} warning(s) ===", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
