---
name: figma-design-to-artifact
description: Export Figma design nodes into technical-requirement artifacts by driving Chrome. With Dev Mode, each Figma node URL gets labeled reference code from the "Figma to Code" plugin plus a 2x PNG screenshot. Without Dev Mode (free Starter plan, View/Collab seat, view-only file) it first checks which signed-in Figma account to use, then falls back to Figma's built-in CSS for all layers plus a JSON layer tree of every sublayer's properties, beside the 2x PNG (callers with Dev Mode can choose this too). Use this whenever the caller wants to turn Figma designs, nodes, or frames into code samples, design references, spec artifacts, layer trees, or screenshots — including "export this Figma node", "Figma to code", "generate sample code from these Figma links", "turn these Figma URLs into artifacts", "export Figma frames as 2x PNGs", "I don't have Dev Mode", or "dump the layers of this view-only Figma file". Requires the Claude-in-Chrome browser tools and a filesystem for writing artifacts.
---

# Figma Design → Technical Requirement Artifact

Turn Figma nodes into reference artifacts. For every valid Figma node URL, one
of two outputs (or both — Step 1):
- **Plugin output** (default with Dev Mode) — two files side by side:
  1. **Sample code** from the "Figma to Code" plugin, saved as a *labeled
     reference file* (a spec artifact — not working source to drop into the app).
  2. **A 2x PNG screenshot** of the same node.
- **Tree output** (works with any access; the only one without Dev Mode, since
  plugins can't run on a view-only file):
  1. **`<slug>.css`** — Figma's built-in *Copy as code → CSS (all layers)*.
  2. **`<slug>.layers.json`** — the node's layer tree: every sublayer's id,
     type, name, text and Properties-panel values.
  3. **`icons/`** — the node's vector icons and graphics as SVG files.
  4. **The 2x PNG**, as above.

In testing, both outputs led a coding agent to an equally faithful screen. The
tree output doesn't depend on a third-party plugin, isn't limited to the
plugin's four languages, and keeps variable, style and component names; it is
slower to produce and larger.

Work through the steps in order. Respect the STOP conditions.

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
  ("Figma to Code" plugin:
  <https://www.figma.com/community/plugin/842128343887142055>.)
- **Do NOT call the Figma REST API either**, in any mode. Starter plans and
  View/Collab seats get only a handful of file/image calls per month, and the
  caller may need them elsewhere.
- **Never work around Figma's permission gates** — no restoring the `figma`
  console global on view-only pages, no extensions or scripts that patch
  Figma's permission checks. Never click **Request access**, **Upgrade**, or
  **Ask to edit** unless the caller asks: they notify the file's admins or
  owner, or start a purchase.
- **Never type the caller's Figma email, password, or any credentials.** Always
  have the caller log in, or switch accounts, themselves.
- Every artifact reaches disk as a browser **download** into `~/Downloads` —
  code, CSS, layer captures and SVG bundles via an in-page Blob download (streaming them
  back as tool text is blocked; see reference §0c/§5), the PNG via Figma's
  exporter. Get the caller's OK before the first download, stating that files
  will download to `~/Downloads` and then be moved into the artifact folder.
  Chrome may block repeated downloads from figma.com until the caller allows
  them (reference §0d).

## Helpers in this skill
These files live alongside this `SKILL.md` in the skill's own directory — invoke
them by that path (the skill's base directory is given to you when the skill is
loaded), not from the caller's project.
- `validate_figma_urls.py URL [URL ...]` — classify URLs as valid node
  targets vs. excluded; emits file key, node id, and a `slug` per target.
- `detect_tech_stack.py [REPO_DIR]` — map the repo to one plugin
  language (`flutter|swiftui|tailwind|html`, HTML fallback) with evidence.
- `build_layer_tree.py CAPTURE.json [--source-url URL] [--pretty]` — turn the
  layer scan's download into the `<slug>.layers.json` tree; prints warnings to
  stderr.
- `icons.py list LAYERS.json` / `icons.py save BUNDLE.json OUT_DIR` — pick the
  vector layers to export as SVG, then write the downloaded bundle out as files.
- `figma-browser-navigation.md` — detailed Figma UI steps: access and account
  check, running the plugin, extracting code, the tree output,
  exporting 2x PNG, download handling, language→extension table,
  troubleshooting. **Read it before Step 2.**

---

## Step 1 — Collect requirements
Gather four things; ask only for what is missing.

1. **Target nodes** — one or more Figma URLs, each pointing directly at a node.
   Run `validate_figma_urls.py` on them.
2. **Artifact location** — folder to write outputs into. Default to
   `./figma-artifacts` if the caller has no preference.
3. **Tech stack** — run `detect_tech_stack.py` on the repo where the skill was
   called. Show the detected language + evidence and let the caller override.
   Falls back to HTML.
4. **Output** — `auto` (default: plugin output when the account has Dev Mode or
   edit access, tree output otherwise), `tree` (tree output even with Dev
   Mode — e.g. for a stack the plugin doesn't cover), or `both`.

**Then STOP and report** to the caller, before any browser work:
- the list of **valid node targets** (with slugs),
- every **excluded URL** with its reason (non-figma domain, no `node-id`,
  prototype/community link, etc.), and
- the chosen language and output.

Exclude the non-target URLs from the run. Proceed only after the caller
confirms the target list, the language and the output.

## Step 2 — Open Figma, authenticate, check access
1. **STOP gate — browser tools:** confirm the Claude-in-Chrome tools are
   available (load via `tool_search` if needed). If they cannot be loaded, stop
   the workflow here and tell the caller the skill requires Claude-in-Chrome. Do
   **not** fall back to the Figma MCP or any other approach.
2. Open the browser and `navigate` to the first target's **Dev Mode** URL
   (`…?node-id=<id>&m=dev`).
3. If Figma shows a login screen or redirects to `/login`, **ask the caller to
   log in themselves** in the browser, then confirm when done. Re-check that the
   editor loaded.
4. **STOP condition:** if the caller cannot log in, stop here. Do not attempt
   Steps 3–4. Report what was and was not completed.
5. **Access tier** (reference §10) — once per Figma file, on its first target:
   `dev` (Dev Mode opens), `edit` (no Dev Mode, can edit), or `view` (no Dev
   Mode, view-only). Dismiss a Dev Mode dialog with **Not now** only.
6. **STOP gate — account:** if the tier is not `dev` and the output is not
   `tree`, read the signed-in accounts from the file browser's account menu
   (reference §10). If **more than one** is signed in, **stop and ask** the
   caller: name the active account, say it has no Dev Mode on this file, list
   the other signed-in accounts by display name, and ask whether to switch to
   one that has Dev Mode. The caller switches themselves; then repeat steps
   2–6. If they decline, or only one account is signed in (say so once),
   continue with the tier as found.
7. Tell the caller what the run will produce, then continue:
   - plugin output — tier `dev`: Step 3; tier `edit`: Step 3 via Design mode
     (reference §13, unverified); tier `view`: not possible, so Step 3F instead;
   - tree output — Step 3F, in any tier;
   - always Step 4 for the PNG.

## Step 3 — Run "Figma to Code" and save the code (plugin output)
Read `figma-browser-navigation.md` first — its **§0 gotchas are
load-bearing** (view-only mode, the visibility spoof, and how to get the code
out). For tier `edit`, run the plugin from Design mode instead (reference §13)
and continue at item 4. For each valid target:

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

## Step 3F — CSS + layer tree + SVGs (tree output)
Build the code-side artifacts from what Design mode shows (the URL without
`&m=dev`; if Figma reopens Dev Mode anyway, press `Shift + D`). The scan reads
the **view-only** Properties panel — what viewers
and Dev-seat accounts see. An account that can edit the file sees the editable
Design panel instead, which the scan isn't verified on: check the first build's
output for empty `properties` before trusting it. For each valid target:

1. **CSS for all layers** (reference §11): right-click the frame's name label
   → Copy as → Copy as code → **CSS (all layers)** → non-blocking clipboard
   read → Blob download with the reference header in `/* … */` comments →
   `<artifact_location>/<slug>/<slug>.css`.
2. **Layer tree** (reference §12): reveal the node's row in Layers, start the
   in-page scan, poll until done, download the capture, then run
   `build_layer_tree.py` → `<artifact_location>/<slug>/<slug>.layers.json`.
   Read its warnings; rescan on gaps or missing children. It runs at roughly
   10 layers/s — for a node with thousands of layers, tell the caller the
   expected time first and offer to scan a smaller child node instead.
3. **Vector layers as SVG** (reference §12, right after the scan on the same
   page load): `icons.py list` the tree, copy each listed layer as SVG into a
   page global, download them as one bundle, then `icons.py save` →
   `<artifact_location>/<slug>/icons/`. About 3 round trips per layer; if the
   list is long, tell the caller and let them trim it.
4. Continue with Step 4 for the PNG.

Opt-in only: if the caller wants the real "Figma to Code" output anyway, they
can copy the file into their own drafts (reference §13, unverified). Ask before
creating anything in their account, and offer to trash the copy afterwards.

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
Write `<artifact_location>/manifest.md`: the output, the access tier per file
and the account used (display name only), then every node — source URL, language,
filenames, and per-node status (code: ok/skipped/n.a.; css: ok/failed/n.a.;
layers: ok (<n> nodes, <w> warnings)/skipped/n.a.; icons: <n> SVGs/skipped/n.a.; png:
ok/manual-move-needed). Then present the artifacts to the caller (e.g. via
`present_files` if available).

## Side-note recap (do not skip)
- Exclude non-Figma-node URLs and tell the caller **before** Step 2.
- Stop at Step 2 if the Claude-in-Chrome tools are unavailable, or if the caller
  cannot log in to Figma.
- No Dev Mode, plugin output wanted, and several signed-in accounts → stop and
  ask whether to switch to an account with Dev Mode before falling back.
- Never use the Figma MCP / Dev Mode tools or the REST API — this workflow is
  browser-only — and never work around Figma's permission gates.
- If "Figma to Code" is unavailable: offer another-plugin retry or skip-code for
  that node.
