#!/usr/bin/env python3
"""Detect the target tech stack for the 'Figma to Code' plugin from a repo.

Maps the repository to one of the plugin's four output languages:
  flutter | swiftui | tailwind | html      (html is the fallback)

Precedence rationale: Flutter and SwiftUI are strong, framework-defining
signals, so they win first. Tailwind beats plain HTML because it is the more
specific web target. HTML is the fallback when nothing else is found.

Usage:
  python detect_tech_stack.py [REPO_DIR]     # defaults to the current directory
"""
import json
import os
import sys

# language -> (plugin tab label, output file extension)
PLUGIN_META = {
    "flutter": ("Flutter", ".dart"),
    "swiftui": ("SwiftUI", ".swift"),
    "tailwind": ("Tailwind", ".html"),
    "html": ("HTML", ".html"),
}

SKIP_DIRS = {".git", "node_modules", "build", "dist", ".dart_tool", "Pods",
             ".next", "out", "vendor", ".venv", "venv", "__pycache__"}
MAX_FILES = 20000


def walk(root):
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            count += 1
            if count > MAX_FILES:
                return
            yield dirpath, name


def read_head(path, limit=4000):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read(limit)
    except OSError:
        return ""


def detect(root):
    evidence = {"flutter": [], "swiftui": [], "tailwind": [], "html": []}

    for dirpath, name in walk(root):
        full = os.path.join(dirpath, name)
        lower = name.lower()

        if lower == "pubspec.yaml":
            evidence["flutter"].append(f"{name} present")
        elif lower.endswith(".dart"):
            evidence["flutter"].append(name)

        if lower == "package.swift":
            evidence["swiftui"].append(f"{name} present")
        elif lower.endswith(".swift"):
            head = read_head(full)
            label = f"{name} (SwiftUI)" if ("import SwiftUI" in head or
                                            "some View" in head) else name
            evidence["swiftui"].append(label)
        elif name.endswith(".pbxproj") or lower.endswith((".xcodeproj",
                                                          ".xcworkspace")):
            evidence["swiftui"].append(name)

        if lower.startswith("tailwind.config."):
            evidence["tailwind"].append(f"{name} present")
        elif lower == "package.json":
            if "tailwindcss" in read_head(full):
                evidence["tailwind"].append("tailwindcss in package.json")
        elif lower.endswith(".css"):
            head = read_head(full)
            if "@tailwind" in head or '@import "tailwindcss"' in head:
                evidence["tailwind"].append(f"@tailwind in {name}")

        if lower.endswith((".html", ".htm")):
            evidence["html"].append(name)

    if evidence["flutter"]:
        choice = "flutter"
    elif evidence["swiftui"]:
        choice = "swiftui"
    elif evidence["tailwind"]:
        choice = "tailwind"
    elif evidence["html"]:
        choice = "html"
    else:
        choice = "html"  # fallback

    tab, ext = PLUGIN_META[choice]
    trimmed = {k: v[:5] for k, v in evidence.items() if v}
    return {
        "detected": choice,
        "is_fallback": choice == "html" and not evidence["html"],
        "plugin_tab": tab,
        "file_extension": ext,
        "evidence": trimmed,
        "scanned_dir": os.path.abspath(root),
    }


def main(argv):
    root = argv[1] if len(argv) > 1 else "."
    if not os.path.isdir(root):
        print(json.dumps({"error": f"not a directory: {root}"}))
        return 2
    print(json.dumps(detect(root), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
