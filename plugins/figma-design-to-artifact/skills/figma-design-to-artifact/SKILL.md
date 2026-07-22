---
name: figma-design-to-artifact
description: Export Figma design nodes into technical-requirement artifacts. For each Figma node URL, drive Chrome to run the "Figma to Code" plugin and save its output as a labeled reference code file, plus export a 2x PNG screenshot beside it. Use this whenever the caller wants to turn Figma designs, nodes, or frames into code samples, design references, spec artifacts, or screenshots via browser automation — including requests like "export this Figma node", "Figma to code", "generate sample code from these Figma links", "turn these Figma URLs into artifacts", or "export Figma frames as 2x PNGs". Requires the Claude-in-Chrome browser tools and a filesystem for writing artifacts.
---

# Figma Design → Technical Requirement Artifact

Turn Figma nodes into paired reference artifacts. For every valid Figma node
URL, produce two files side by side:
1. **Sample code** from the "Figma to Code" plugin, saved as a *labeled
   reference file* (a spec artifact — not working source to drop into the app).
2. **A 2x PNG screenshot** of the same node.

Work through the four steps in order. Respect the STOP conditions.

## Tools & safety
- Needs the **Claude-in-Chrome** tools (`navigate`, `find`, `read_page`,
  `get_page_text`, `computer`, `javascript_tool`, `tabs_*`). If they are not
  active, try loading them with `tool_search`. This skill is entirely
  browser-driven: if these tools cannot be loaded, it cannot run — stop at the
  Step 2 gate.
- **Do NOT use the Figma MCP / Dev Mode MCP tools** (e.g. `get_design_context`,
  `get_screenshot`, `download_assets`) at any point, even if they are connected
  and would be easier. The caller wants the *"Figma to Code" plugin* output and
  Figma's own *export* PNG; the MCP produces different artifacts and would
  defeat the skill's purpose. Every step here goes through the browser.
- **Never type the caller's Figma email, password, or any credentials.** Always
  have the caller log in themselves.
- Both the **code files** and the **2x PNGs** reach disk as browser
  **downloads** into `~/Downloads` — the code via an in-page Blob download
  (streaming the code back as tool text is blocked; see reference §0c/§5), the
  PNG via Figma's exporter. Get the caller's OK before the first download,
  stating that code files and PNGs will download to `~/Downloads` and then be
  moved into the artifact folder.

## Helpers in this skill
These files live alongside this `SKILL.md` in the skill's own directory — invoke
them by that path (the skill's base directory is given to you when the skill is
loaded), not from the caller's project.
- `validate_figma_urls.py URL [URL ...]` — classify URLs as valid node
  targets vs. excluded; emits file key, node id, and a `slug` per target.
- `detect_tech_stack.py [REPO_DIR]` — map the repo to one plugin
  language (`flutter|swiftui|tailwind|html`, HTML fallback) with evidence.
- `figma-browser-navigation.md` — detailed Figma UI steps: running
  the plugin, extracting code, exporting 2x PNG, download handling,
  language→extension table, troubleshooting. **Read it before Step 3.**

---

## Step 1 — Collect requirements
Gather three things; ask only for what is missing.

1. **Target nodes** — one or more Figma URLs, each pointing directly at a node.
   Run `validate_figma_urls.py` on them.
2. **Artifact location** — folder to write outputs into. Default to
   `./figma-artifacts` if the caller has no preference.
3. **Tech stack** — run `detect_tech_stack.py` on the repo where the skill was
   called. Show the detected language + evidence and let the caller override.
   Falls back to HTML.

**Then STOP and report** to the caller, before any browser work:
- the list of **valid node targets** (with slugs), and
- every **excluded URL** with its reason (non-figma domain, no `node-id`,
  prototype/community link, etc.).

Exclude the non-target URLs from the run. Proceed only after the caller
confirms the target list and the chosen language.

## Step 2 — Open Figma in Chrome + authenticate
1. **STOP gate — browser tools:** confirm the Claude-in-Chrome tools are
   available (load via `tool_search` if needed). If they cannot be loaded, stop
   the workflow here and tell the caller the skill requires Claude-in-Chrome. Do
   **not** fall back to the Figma MCP or any other approach.
2. Open the browser and `navigate` to the first valid target URL.
3. If Figma shows a login screen or redirects to `/login`, **ask the caller to
   log in themselves** in the browser, then confirm when done. Re-check that the
   editor loaded.
4. **STOP condition:** if the caller cannot log in, stop here. Do not attempt
   Steps 3–4. Report what was and was not completed.

## Step 3 — Run "Figma to Code" and save the code
Read `figma-browser-navigation.md` first — its **§0 gotchas are
load-bearing** (view-only mode, the visibility spoof, and how to get the code
out). For each valid target:

1. `navigate` to the node's **Dev Mode** URL (`…?node-id=<id>&m=dev`) and confirm
   the node is selected. The `Cmd/Ctrl + /` quick-action search does **not** list
   plugins, and a plain design URL may open **view-only** — Dev Mode is the way.
2. **Spoof tab visibility to "visible"** via `javascript_tool` (reference §0b),
   or the plugin UI hangs on "Loading…" forever in a background tab. Re-apply
   after every navigation.
3. Right panel → **Plugins** tab (verify it switched) → run **"Figma to Code"**
   from **Recents** (verify it finished generating, not still "Loading…").
4. **Plugin-unavailable branch:** if "Figma to Code" is not in Recents/Community
   or errors, ask the caller to either (1) name another plugin to try, or
   (2) skip code for this node. Honor the choice and record it.
5. Select the language tab matching the detected/confirmed stack (for Flutter,
   keep **Snippet** mode).
6. Extract the code (reference §5): click the plugin's **Copy** button, then a
   **non-blocking** `navigator.clipboard.readText()` into a page global — never
   `await` it, never try to paste it, never stream the code back as tool text
   (all three fail; the last is classifier-blocked). Sanity-check length + root.
7. Save it by building `header + code` **in the page** and triggering a Blob
   `<a download>` into `~/Downloads`, then `mv` to
   `<artifact_location>/<slug>/<slug><ext>` (extension per language). Use the
   "GENERATED DESIGN REFERENCE — NOT PRODUCTION CODE" header from the reference.
   **Do not** place it into application source.

## Step 4 — Export a 2x PNG screenshot
Dev Mode cannot export a PNG **file** (only "Copy as PNG" → clipboard, 1x) — use
**Design mode** (reference §6). For each node where code was produced or
attempted:
1. `navigate` to the node's design URL (drop `&m=dev`); the frame auto-selects.
   Export works even when the file is view-only.
2. Right panel → **Properties** tab → **Export** section → scale **2x**, format
   **PNG** (verify it reads 2x · PNG). Confirm the download with the caller the
   first time.
3. Click **Export <name>**, then place the result at
   `<artifact_location>/<slug>/<slug>@2x.png`. **A "/" in the frame name yields a
   ZIP** (`Name/Sub.png`), not a bare PNG — unzip + rename (reference §7). Verify
   it is truly 2x with `sips` (= 2 × the design WxH). If the download landed
   somewhere your shell cannot reach (browser on another machine), tell the
   caller the filename and ask them to move it; record `png: manual-move-needed`.

## Finish
Write `<artifact_location>/manifest.md` listing every node: source URL,
language, code filename, screenshot filename, and per-node status (code:
ok/skipped; png: ok/manual-move-needed). Then present the artifacts to the
caller (e.g. via `present_files` if available).

## Side-note recap (do not skip)
- Exclude non-Figma-node URLs and tell the caller **before** Step 2.
- Stop at Step 2 if the Claude-in-Chrome tools are unavailable, or if the caller
  cannot log in to Figma.
- Never use the Figma MCP / Dev Mode tools — this workflow is browser-only.
- If "Figma to Code" is unavailable: offer another-plugin retry or skip-code for
  that node.
