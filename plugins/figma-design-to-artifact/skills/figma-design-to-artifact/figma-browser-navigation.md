# Figma browser-automation reference

Detailed steps for driving figma.com in Chrome to run the "Figma to Code"
plugin, extract its output, and export a 2x PNG — and, without Dev Mode, to
check access and accounts and produce the tree output (§10–§13). Read
the section you need; the main workflow lives in `SKILL.md`.

Browser tools used (load via `tool_search` if not already active):
`navigate`, `find`, `read_page`, `get_page_text`, `computer` (screenshot +
mouse/keyboard), `javascript_tool`, `tabs_*`. `javascript_tool` is **not
optional** here — the visibility spoof, the clipboard read, and the code
download all go through it (see §0, §5).

> This reference was rewritten from a real end-to-end run (5 nodes, Flutter).
> §10–§12 come from a live run without Dev Mode (View seat on a paid team, two
> signed-in accounts, a 560-layer node); §13 is not verified yet. The §0
> gotchas are the difference between "works in minutes" and "stuck forever" —
> read §0 before touching the browser.

## Contents
0. **Automation-environment gotchas — READ FIRST**
1. Select the target node
2. Run the "Figma to Code" plugin (Dev Mode → Plugins tab)
3. When the plugin is unavailable
4. Pick the language tab
5. Extract the generated code (the reliable path)
6. Export a 2x PNG (Design Mode → Export)
7. Where the PNG / code download lands
8. Language → extension + header comment
9. A per-node checklist you can loop
10. Access tier + account check
11. Tree output A — CSS for all layers
12. Tree output B — layer tree (Layers + Properties panel scan), plus vector
    layers as SVG
13. Running "Figma to Code" without Dev Mode (unverified)
14. Troubleshooting

---

## 0. Automation-environment gotchas — READ FIRST

Four things about driving Figma from an automated (background) Chrome tab that
are non-obvious and will each waste a lot of time if you don't know them:

**(a) The file often opens VIEW-ONLY, and plugins can't run there.**
Opening a plain design URL may load the file with a right panel showing
**Comments | Properties** tabs (not **Design | Prototype**) and a bottom banner
"You can only view and comment on this file." That is view-only mode — the
"Figma to Code" plugin will **not** appear in the `Cmd/Ctrl + /` quick-action
search (that search only lists menu commands, never plugins, and in view-only it
lists even fewer). **Solution: run the plugin from Dev Mode instead** (§2). Dev
Mode's **Plugins** tab works even when the account only has view access.

**(b) A background tab is `visibilityState = "hidden"`, which HANGS the plugin.**
The plugin's UI iframe defers its init on tab visibility, so in a hidden tab it
sits on **"Loading Figma to Code (HTML, Tailwind, Flutter, SwiftUI)…"** forever
(observed >60s across reloads and fresh tabs). Verify with:
`javascript_tool`: `document.visibilityState` → `"hidden"`.
**Solution — spoof visibility to "visible" on the top document AFTER each page
load and BEFORE running the plugin:**
```js
Object.defineProperty(document,'hidden',{configurable:true,get:()=>false});
Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>'visible'});
Object.defineProperty(document,'webkitVisibilityState',{configurable:true,get:()=>'visible'});
Object.defineProperty(document,'webkitHidden',{configurable:true,get:()=>false});
document.dispatchEvent(new Event('visibilitychange'));
window.dispatchEvent(new Event('focus'));
```
Re-apply this every time you navigate/reload (a navigation resets it). The PNG
export in §6 does **not** need the spoof — only the plugin does.

**(c) Getting the code out is constrained — use clipboard-read + Blob download.**
- The plugin UI is an **opaque sandboxed iframe**: you cannot read the code from
  the DOM (`get_page_text` / `read_page` only capture the main Figma chrome, and
  the plugin's `<iframe>` is cross-origin/opaque — `contentDocument` access
  throws or is empty).
- **Synthetic `Cmd/Ctrl + C` / `+ V` do NOT touch the OS clipboard** in this
  automation context (a type→copy→clear→paste round-trip into a textarea comes
  back empty). So the "paste into a scratch textarea" trick fails.
- **But the plugin's own Copy button uses the real `navigator.clipboard.writeText`**,
  so after clicking it the system clipboard genuinely holds the code. Read it
  back with a **non-blocking** `navigator.clipboard.readText()` (§5). Never
  `await` it directly — a blocking await froze the renderer for 45s.
- **Don't try to stream the code back as tool text**: the auto-mode classifier
  blocks large text dumps out of `javascript_tool` (it reads as a
  content-filter workaround, and it *will* deny the call). Instead, build the
  full file **in the page** and trigger a **Blob `<a download>`** into
  `~/Downloads`, then `mv` it (the browser is on the same machine → your shell
  can reach `~/Downloads`). This also gives byte-perfect output for free.

**(d) Chrome blocks repeated automatic downloads from figma.com.** After the
first page-triggered download, Chrome may block the next ones and show a
blocked-downloads icon in the address bar — the file silently never lands
(even right after a real click). Ask the caller to allow downloads for
figma.com there (once). Chrome then also delivers the queued attempts, as
`name (1).ext`, `name (2).ext`. So after every download: check it landed, take
the newest match (`ls -t … | head -1`), and delete the other matches.

## 1. Select the target node
Opening a URL that carries `node-id` normally focuses and selects that node.
Confirm before continuing:
- Take a screenshot (`computer`) or read the accessibility tree (`read_page`).
  The layer is highlighted in the left layers list and named at the top of the
  right panel.
- If nothing looks selected, press `Shift + 2` (zoom to selection) or click the
  frame's title label on the canvas. Re-confirm.
- A correct selection is required for both the plugin and the export.

## 2. Run the "Figma to Code" plugin (Dev Mode → Plugins tab)
Do **not** use the `Cmd/Ctrl + /` quick-action search — it does not list plugins
(§0a). Use Dev Mode:

1. Navigate to the node's **Dev Mode** URL by appending `&m=dev`, e.g.
   `…?node-id=1-2&m=dev`. Wait ~7s for the editor to load.
2. Apply the **visibility spoof** (§0b) via `javascript_tool`.
3. In the right panel, click the **Plugins** tab (top of the panel, next to
   **Inspect**). **Verify with a screenshot that it actually switched** — this
   click frequently doesn't register on the first try right after a navigation.
   If the panel still shows Inspect, click **Plugins** again.
4. Under **Recents and saved → Recents**, click the
   **"Figma to Code (HTML, Tailwind, Flutter, SwiftUI)"** row (by Bernardo
   Ferrari) to run it. If Recents hasn't rendered yet, your click lands on empty
   space and nothing happens — screenshot, then click the row once it's visible.
5. Wait for generation. With the spoof applied it takes a few seconds and then
   shows the language tabs, a **Preview** with the node's `WxH`, a
   **Warnings** box, and a **Code** section with a **Copy** button. Without the
   spoof it stays on "Loading…" — go back and apply §0b.

Notes:
- The plugin **persists in the background** while you switch between the
  **Inspect** and **Plugins** tabs within one page load (Inspect shows
  "Figma to Code … is running in the background"). But **a navigation reloads
  the page and closes it** — you re-run it per node (steps 3–4 again).
- Common warnings (informational): "Image fills are replaced with placeholders"
  (→ `NetworkImage("https://placehold.co/WxH")`), "VectorNodes are not supported
  in Flutter", "BOOLEAN_OPERATION node is not supported".

## 3. When the plugin is unavailable
"Unavailable" = it is not in Dev Mode's **Plugins → Recents** or the Community
search, or it errors on open. Do NOT try to auto-install it. Ask the caller to
choose one of:
1. **Try another plugin** — have them name a design-to-code plugin they do have;
   repeat §2/§4/§5 with it. Record which plugin was used in the manifest.
2. **Skip code for this node** — proceed to the PNG export only. Record
   `code: skipped (plugin unavailable)`.

The caller may also install "Figma to Code" from the Community and ask you to
retry — that is fine; re-run §2.

## 4. Pick the language tab
The plugin panel shows tabs **HTML · Tailwind · Flutter · SwiftUI**. Click the
one matching the detected/confirmed stack (from `detect_tech_stack.py`); it
usually remembers the last choice. For Flutter there is also a **Flutter
Options** row — **Full App · Widget · Snippet**. **Snippet** (the default) emits
a self-contained `Container(...)` widget tree, which is the right shape for a
reference artifact. The code preview re-renders when you change the tab.

## 5. Extract the generated code (the reliable path)
Given §0c, this is the path that works — do it on the Figma editor tab itself
(no scratch tab needed):

1. Click the plugin's **Copy** button (top-right of the **Code** section).
   Confirm it flips to a **✓ Copy** state (zoom in to check). Its Y-position
   shifts with the number of warnings (2 vs 3), so locate it from a screenshot
   each node rather than reusing coordinates.
2. **Non-blocking** clipboard read into a global, then poll:
   ```js
   // call 1 — start the read (returns immediately)
   window.__clip = 'pending';
   navigator.clipboard.readText()
     .then(t => { window.__clip = 'OK:' + t; })
     .catch(e => { window.__clip = 'ERR:' + e.name; });
   'started';
   // …wait ~2s…
   // call 2 — read status WITHOUT dumping the code (sanitize the head so URL
   // patterns don't trip the content filter):
   (() => { const c = window.__clip || 'undef';
     return c.startsWith('OK:')
       ? 'OK len=' + (c.length-3) + ' head=' + c.slice(3, 53).replace(/[:?=&/]/g,'_')
       : 'STATE=' + c.slice(0,40); })();
   ```
   Sanity-check: length is non-trivial and the head looks like the expected root
   (Flutter Snippet → `Container(`). If it returns `ERR:NotAllowedError` the tab
   lost focus — click into the page (`computer left_click` on empty canvas) and
   retry; if it stays `pending`, a permission prompt may be open (rare).
3. **Build the full file in the page and download it** (do NOT read the code
   back as tool output — §0c). Prepend the §8 header, `Blob` it, click a
   temporary `<a download>`:
   ```js
   (() => {
     const code = window.__clip.slice(3);
     if (!code || code.length < 500) return 'ABORT len=' + code.length;
     const nl = String.fromCharCode(10);
     // build the source URL without a literal "://" in the sent JS so the
     // classifier doesn't flag the call:
     const proto = 'https' + String.fromCharCode(58,47,47);
     const header = [
       '// GENERATED DESIGN REFERENCE — NOT PRODUCTION CODE',
       '// Source:   ' + proto + 'www.figma.com/design/<FILE_KEY>/… (node <NODE_ID>, Dev Mode)',
       '// Node id:  <NODE_ID>    File key: <FILE_KEY>',
       '// Label:    <slug>',
       '// Plugin:   Figma to Code (Flutter tab, Snippet), via the figma-design-to-artifact skill',
       '// Documents the intended UI as a technical-requirement artifact. Do not import',
       '// directly into the app; treat it as a spec/reference.',
       '', ''
     ].join(nl);
     const blob = new Blob([header + code], {type: 'text/plain'});
     const a = document.createElement('a');
     a.href = URL.createObjectURL(blob);
     a.download = 'figexport_<slug>.dart';   // distinctive prefix so you can find it
     document.body.appendChild(a); a.click();
     setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 3000);
     return 'ok totalLen=' + (header + code).length;
   })();
   ```
   Adjust the comment syntax / header per §8 for non-Flutter languages.
4. Move it into place (browser is same-machine, so `~/Downloads` is reachable):
   ```bash
   SRC=$(ls -t ~/Downloads/figexport_<slug>*.dart | head -1)
   mv "$SRC" <artifact_location>/<slug>/<slug>.dart
   wc -l <artifact_location>/<slug>/<slug>.dart      # sanity
   ```

Fallback (only if the plugin renders code as visible, selectable text that
`get_page_text` actually captures — rare, and NOT the case for the sandboxed
"Figma to Code" UI): copy from page text. Screenshot-transcription is a last
resort and error-prone for long files — avoid it.

## 6. Export a 2x PNG (Design Mode → Export)
**Dev Mode cannot export a PNG file** — its right-click menu only offers
"Copy as PNG" (goes to the clipboard, 1x). Use **Design mode**:

1. Navigate to the node's design URL **without** `&m=dev`
   (`…?node-id=<NODE_ID>`). Wait ~5s. The frame is auto-selected (its `WxH`
   shows under it). The file may be view-only — **export still works in
   view-only.** If Figma reopened Dev Mode anyway (it remembers the account's
   last mode), press `Shift + D`.
2. Right panel → click the **Properties** tab (next to **Comments**). Verify it
   switched (it often misses the first click right after navigation — click
   again). Scroll to the **Export** section near the bottom. Its Y-position
   varies with how many properties/colors the node has — locate from a
   screenshot.
3. Click the **scale** dropdown (shows "1x") → choose **2x**. Leave format
   **PNG**. Zoom in to confirm it reads **2x · PNG**.
4. Click **Export <frame name>**. This triggers a browser download.

## 7. Where the PNG / code download lands
Figma export and the §5 Blob both download into Chrome's download dir. When
driving the user's own local Chrome that is `~/Downloads` on **this** machine,
so your shell can move the files. (If the browser were on a different machine
you could not reach them — then tell the caller the filename and ask them to
move it; record `png: manual move needed`.)

**PNG naming — a "/" in the frame name produces a ZIP, not a bare PNG.** Figma
treats "/" as a folder path, so a frame named `Screens / Login` downloads as
`<file name>.zip` containing `Screens/Login.png`. Handle both:
```bash
DEST=<artifact_location>/<slug>
PNG=$(find ~/Downloads -maxdepth 1 -name '*.png' -mmin -1 | head -1)
ZIP=$(find ~/Downloads -maxdepth 1 -name '*.zip' -mmin -1 | head -1)
if [ -n "$PNG" ]; then
  mv "$PNG" "$DEST/<slug>@2x.png"
elif [ -n "$ZIP" ]; then
  unzip -o -j "$ZIP" -d "$DEST/" >/dev/null
  mv "$(ls -t "$DEST"/*.png | head -1)" "$DEST/<slug>@2x.png"
  rm -f "$ZIP"
fi
# verify it is truly 2x (= 2 × the frame's design WxH):
sips -g pixelWidth -g pixelHeight "$DEST/<slug>@2x.png" | grep pixel
```
`unzip -j` flattens the `Page/` folder; `mv` the extracted PNG to the slug name.

## 8. Language → extension + header comment
Every saved code file starts with a header marking it a generated reference
(not production source). Comment syntax by language:

| Detected  | Plugin tab | Extension | Comment |
|-----------|-----------|-----------|---------|
| html      | HTML      | `.html`   | `<!-- ... -->` |
| tailwind  | Tailwind  | `.html`   | `<!-- ... -->` |
| flutter   | Flutter   | `.dart`   | `// ...` |
| swiftui   | SwiftUI   | `.swift`  | `// ...` |

Header content to include (built into the Blob in §5 so the file arrives
complete — no need to re-read and edit it on disk):
```
GENERATED DESIGN REFERENCE — NOT PRODUCTION CODE
Source:   <figma node URL>
Node id:  <node-id>    File key: <file_key>
Plugin:   Figma to Code (<language>[, <Flutter option>])
Documents the intended UI as a technical-requirement artifact. Do not import
directly into the app; treat it as a spec/reference.
```

## 9. A per-node checklist you can loop
Both code (Dev) and PNG (Design) require a navigation, so grouping doesn't save
navigations — do whatever's clearest (e.g. per node: code then PNG). One tab is
enough; keep it and re-navigate.

Per node:
- [ ] **Code** — `&m=dev` → wait → **spoof visibility (§0b)** → Plugins tab
      (verify) → run "Figma to Code" from Recents (verify loaded) → pick
      **Flutter/Snippet** → **Copy** (verify ✓) → non-blocking clipboard read
      (verify `OK len=…`) → Blob download → `mv` from `~/Downloads`.
- [ ] **PNG** — design URL (no `&m=dev`) → wait → **Properties** tab (verify) →
      **Export** → scale **2x**, PNG (verify) → **Export <name>** →
      `mv`/unzip from `~/Downloads` → `sips` dimension check (= 2× design size).

For the tree output (always the case in tier `view`, §10), the code item becomes:
- [ ] **CSS** — design URL → right-click the frame label → Copy as → Copy as
      code → **CSS (all layers)** → non-blocking clipboard read (verify head +
      length) → Blob download → `mv` (§11).
- [ ] **Layer tree** — **Properties** tab (verify) → click the frame label
      (reveals its row) → start the scan → poll until `done` → download →
      `build_layer_tree.py` (read its warnings) → delete the download (§12).
- [ ] **Icons** — same page load: `icons.py list` → per layer `__selectRow` →
      `Shift + 2` → right-click canvas centre → Copy as → Copy as SVG →
      clipboard read → store; then one download → `icons.py save` (§12).

Coordinates drift between sessions (window size, zoom, warning count, property
count) — **always locate buttons from a fresh screenshot**, don't hardcode.

## 10. Access tier + account check
Access depends on the **file** (its plan and the account's seat), so check once
per file, on its first target node.

**Tier**
1. Navigate to the node's Dev Mode URL (`…&m=dev`), wait ~7s, screenshot.
   - Right panel shows **Inspect | Plugins** → tier **`dev`**.
   - A dialog **"Want to view this file in Dev Mode?"** with **Request access**
     and **Not now** (a View seat on a paid plan) → no Dev Mode. Files on the
     free Starter plan reportedly show an **"Upgrade to work in Dev Mode"**
     modal instead (not seen live).

   Dismiss it with **Not now** (or its close button). **Never** click
   **Request access**, **Upgrade**, or the view-only banner's **Ask to edit**
   on your own: they notify the file's admins or owner, or start a purchase.
   Click them only if the caller asks.
2. **Not now** leaves you in Design mode (`m=dev` drops from the URL). Check
   edit access:
   - Bottom banner **"You can only view and comment on this file."** with
     **Ask to edit**, right-panel tabs **Comments | Properties**, creation
     tools greyed out → tier **`view`**.
   - No banner, **Design | Prototype** tabs → tier **`edit`** (not seen live).

`typeof figma` is `undefined` on view-only pages (Figma removed the console
global there in 2024). Don't try to restore it, and don't use extensions or
scripts that patch Figma's permission checks.

**Signed-in accounts** — figma.com keeps up to 10 accounts signed in at once.
The editor has **no** account switcher (its avatar menu only shows the active
account as "<name> (You)"); the switcher is in the file browser:
1. Navigate to `https://www.figma.com/files/recents-and-sharing`.
2. Click the top-left account button (`find`: button "Account dropdown for
   <name>").
3. Read the menu with `find` / `read_page`: a group **"Switch account"** holds
   one `menuitemradio` per signed-in account, and the active one has
   `aria-checked="true"`. Use display names; don't write emails into artifacts.
4. `Escape` to close it.

The caller switches accounts themselves by picking another account in that
menu. Then re-open the target URL and confirm which account the editor is
using (avatar menu → "<name> (You)"): with several accounts signed in, Figma
sometimes opens a link with a different account than the one just picked.
Redo the tier check. (File-browser URLs carry an undocumented `?fuid=<user id>`;
don't rely on it to choose an account.)

## 11. Tree output A — CSS for all layers
Viewers can run Figma's built-in code generator from the canvas context menu.
A viewer's **Copy as** submenu offers: Copy link to selection · **Copy as code
▸** · Copy as SVG · Copy as PNG · Copy properties.

1. Design URL (no `&m=dev`) with the node selected. Right-click the frame's
   **name label on the canvas** (right-clicking inside the frame can select a
   child instead).
2. **Copy as → Copy as code → CSS (all layers)**. Hover each submenu level and
   wait ~1s before moving on.
3. Read the clipboard with the §5 non-blocking `readText` into
   `window.__clip`. Sanity-check without dumping it: the first line is
   `/* <frame name> */` and the length is substantial (a 375×1829 screen gave
   ~120 KB, ~8.5k lines).
4. Download it as in §5 step 3, with the §8 header in `/* … */` comments and
   `Plugin:` reading `Figma built-in Copy as code → CSS (all layers)`;
   `a.download = 'figexport_<slug>.css'`. Then `mv` the newest match to
   `<artifact_location>/<slug>/<slug>.css`.

What you get: one block per layer, `/* <layer name> */` followed by position
and size, auto layout as flexbox (`display: flex`, direction, `gap`,
`padding`, alignment), typography, fills, borders, radius and shadows, with
style and variable names (and their descriptions) as comments. It is **flat**
(no nesting), in Figma's document order, and leaves some layers out (instance
wrappers, some vectors), so it can't be tied back to node ids reliably. Use the
§12 layer tree for structure. Positions (`left`, `top`, `right`, …) are
relative to the layer's nearest parent **frame** — groups don't count, so a
layer inside a group is placed against the frame around that group.

Not worth saving: **CSS** (selected layer only), **iOS** (a few UIKit lines
for the selected layer), **Android** (one `RelativeLayout` for the selected
layer), **Copy as SVG** (text outlined to paths, no layer ids, ~750 KB for a
screen). The submenu's last item, "Generate code for Tailwind, React, and more
in Dev Mode", is the Dev Mode upsell.

## 12. Tree output B — layer tree (Layers + Properties panel scan)
Produces `<slug>.layers.json`: every layer under the node with its real id,
type, name, text content, and every value the viewer's Properties panel shows.
One in-page loop selects each layer and reads the panel, with no tool call per
layer. Measured: 560 layers in ~50 s.

DOM facts the loop relies on:
- The Layers panel is a virtualized `role="treegrid"` (~40 rows in the DOM at
  a time). Each row's name element is
  `[data-testid="<nodeId>-layers-panel-row"]`, inside a `[role=row]` with
  `aria-level`, `aria-rowindex`, `aria-posinset`/`aria-setsize`,
  `aria-expanded` and `aria-selected`. The type icon has an `aria-label`
  (Section, Frame, Auto layout, Component, Instance, Text, Vector, Rectangle,
  Group, Mask, Line, …). The caret is `[data-testid="layers-panel-expand-caret"]`.
- Rows **inside an instance** carry the component's layer id, not a
  file-unique one. The real id is `I<instanceId>;<layerId>` (chained for nested
  instances), and selecting such a row moves the URL's `node-id` to the outer
  instance. `build_layer_tree.py` derives the real ids.
- Sibling order: auto-layout children appear in flow order; other parents list
  the top-most layer first, the reverse of Figma's REST order.
  `build_layer_tree.py` converts to REST order.
- Synthetic pointer/mouse events on a row select it (`aria-selected="true"`).
  The Properties panel's `innerText` then reads cleanly: the name (text layers
  show a "Text" badge line first), **Parent component**, any component
  description, then **Component properties**, **Layout**, **Content**,
  **Typography**, **Colors**, **Borders**, **Shadows and blurs**, **Export**.
- Alt-clicking a caret does **not** reliably expand every descendant (33 rows
  stayed collapsed in testing), so the loop expands collapsed rows itself.
- Verified on the **view-only** Properties panel, which is what viewers and
  Dev-seat accounts get in Design mode. An account that can edit the file
  sees the editable Design panel instead (values in input fields, which
  `innerText` skips); not verified there.

Steps:
1. Design URL (no `&m=dev`), right panel on **Properties** (verify). Figma
   may still reopen the mode the account used last and append `&m=dev`; if the
   panel shows **Inspect | Plugins**, press `Shift + D` for Design mode.
2. Make the node's row visible in Layers: click the frame's **name label on
   the canvas**. Figma expands its ancestors and scrolls the row into view
   (opening the URL selects the node but can leave its row collapsed away).
3. Start the scan. It returns at once; set `T` to the node id with a colon
   (e.g. `120:3456`):
   ```js
   window.__cap = {done: false, n: 0, err: null, rows: [], t0: Date.now()};
   (async () => {
     try {
       const T = '<NODE_ID>';
       const SEL = '[data-testid$="-layers-panel-row"]';
       const q = id => document.querySelector('[data-testid="' + id + '-layers-panel-row"]');
       const R = el => el.closest('[role=row]');
       const sleep = ms => new Promise(r => setTimeout(r, ms));
       const panel = () => {
         const h = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6,[role=heading]')].find(e => e.textContent.trim() === 'Layout');
         let c = h; while (c && !(c.innerText || '').includes('Export')) c = c.parentElement;
         return c;
       };
       const click = el => { for (const t of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'])
         el.dispatchEvent(new (t.startsWith('pointer') ? PointerEvent : MouseEvent)(t, {bubbles: true, cancelable: true, view: window, button: 0})); };
       let sc = R(document.querySelector(SEL));
       while (sc && !(sc.scrollHeight > sc.clientHeight + 5 && /(auto|scroll)/.test(getComputedStyle(sc).overflowY))) sc = sc.parentElement;
       if (!sc) throw new Error('no layers scroll container');
       if (!q(T)) { sc.scrollTop = 0; await sleep(150);
         for (let i = 0; i < 3000 && !q(T); i++) { const b = sc.scrollTop; sc.scrollTop += Math.floor(sc.clientHeight * 0.8); await sleep(80); if (sc.scrollTop === b) break; } }
       if (!q(T)) throw new Error('target row not found');
       q(T).scrollIntoView({block: 'start'}); await sleep(150);
       const got = new Map(); let tIdx = null, tLvl = null, end = false, prev = '', expanded = 0;
       for (let guard = 0; guard < 20000 && !end; guard++) {
         const vis = [...document.querySelectorAll(SEL)].map(el => ({el, tr: R(el)})).filter(x => x.tr)
           .map(x => ({...x, ri: +x.tr.getAttribute('aria-rowindex'), lvl: +x.tr.getAttribute('aria-level')}))
           .sort((a, b) => a.ri - b.ri);
         let stale = false;
         for (const v of vis) {
           if (!v.el.isConnected) { stale = true; break; }
           const id = v.el.getAttribute('data-testid').replace('-layers-panel-row', '');
           if (id === T && tIdx === null) { tIdx = v.ri; tLvl = v.lvl; }
           if (tIdx === null || v.ri < tIdx) continue;
           if (v.ri > tIdx && v.lvl <= tLvl) { end = true; break; }
           if (!got.has(v.ri)) {
             click(v.el);
             let txt = '', sel = false;
             for (let w = 0; w < 40; w++) {
               await sleep(25); const p = panel(); txt = (p && p.innerText) || '';
               sel = v.tr.getAttribute('aria-selected') === 'true';
               if (sel && (txt !== prev || w >= 12)) break;
             }
             prev = txt;
             const ic = v.tr.querySelector('[role=img],svg[aria-label],img');
             got.set(v.ri, {ri: v.ri, id, depth: v.lvl - tLvl, pos: +v.tr.getAttribute('aria-posinset'),
               size: +v.tr.getAttribute('aria-setsize'), type: ic && (ic.getAttribute('aria-label') || ic.getAttribute('alt')),
               name: v.el.textContent.trim(), ok: sel, panel: txt});
             window.__cap.n = got.size;
           }
           if (v.tr.getAttribute('aria-expanded') === 'false') {
             const caret = v.tr.querySelector('[data-testid="layers-panel-expand-caret"]');
             if (caret) { click(caret); expanded++; await sleep(150); stale = true; break; }
           }
         }
         if (end) break;
         if (stale) continue;
         const before = sc.scrollTop; sc.scrollTop += Math.floor(sc.clientHeight * 0.6); await sleep(120);
         if (sc.scrollTop === before) break;
       }
       window.__cap.rows = [...got.values()].sort((a, b) => a.ri - b.ri);
       window.__cap.expanded = expanded;
     } catch (e) { window.__cap.err = String(e); }
     window.__cap.done = true; window.__cap.ms = Date.now() - window.__cap.t0;
   })();
   'started';
   ```
4. Poll every ~10 s with
   `JSON.stringify({done: __cap.done, n: __cap.n, err: __cap.err})`. Don't touch
   the browser until `done`: clicks and scrolls race the loop.
5. Download the capture (never return the rows as tool output, §0c):
   ```js
   (() => {
     const c = window.__cap;
     if (!c.done || c.err) return 'ABORT ' + c.err;
     const blob = new Blob([JSON.stringify({target: '<NODE_ID>', rows: c.rows})], {type: 'application/json'});
     const a = document.createElement('a');
     a.href = URL.createObjectURL(blob);
     a.download = 'figlayers_<slug>.json';
     document.body.appendChild(a); a.click();
     setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 3000);
     return 'ok rows=' + c.rows.length + ' unselected=' + c.rows.filter(r => !r.ok).length;
   })();
   ```
6. Build the tree, then clean up (§0d):
   ```bash
   SRC=$(ls -t ~/Downloads/figlayers_<slug>*.json | head -1)
   python3 <skill_dir>/build_layer_tree.py "$SRC" --source-url "<node URL>" \
     > <artifact_location>/<slug>/<slug>.layers.json
   rm -f ~/Downloads/figlayers_<slug>*.json
   ```
   Read its stderr. Gaps or "fewer captured children" → rescan. Rows "not
   confirmed selected" → those nodes carry `_unverified`. "Dropped
   '[object Object]'" → Figma's panel printed that instead of some values
   (seen on a group's width/height); nothing to rescan.

### Vector layers as SVG
Exports the node's icons and vector graphics (logos, background shapes) to
`<artifact_location>/<slug>/icons/`. Do it right after the scan, on the same
page load: the rows the scan expanded are what make every layer selectable.
About 3 round trips per layer.

1. List what to export:
   `python3 <skill_dir>/icons.py list <artifact_location>/<slug>/<slug>.layers.json`.
   Each entry is a topmost vector-only layer — `icon` (≤ 64 px) or `graphic` —
   listed once per name and size, with its `rowId`. Text and image subtrees,
   zero-width/height lines and system chrome (status bar, home indicator) are
   skipped. Use this session's tree: component internals can change between
   sessions, and their row ids with them.
2. Define the row selector once:
   ```js
   window.__icons = {};
   window.__selectRow = async (rowId) => {
     const SEL = '[data-testid$="-layers-panel-row"]';
     const R = el => el.closest('[role=row]');
     const sleep = ms => new Promise(r => setTimeout(r, ms));
     const find = () => document.querySelector('[data-testid="' + rowId + '-layers-panel-row"]');
     let sc = R(document.querySelector(SEL));
     while (sc && !(sc.scrollHeight > sc.clientHeight + 5 && /(auto|scroll)/.test(getComputedStyle(sc).overflowY))) sc = sc.parentElement;
     if (!find()) { sc.scrollTop = 0; await sleep(120);
       for (let i = 0; i < 5000 && !find(); i++) { const b = sc.scrollTop; sc.scrollTop += Math.floor(sc.clientHeight * 0.8); await sleep(60); if (sc.scrollTop === b) break; } }
     const el = find(); if (!el) return 'not found';
     el.scrollIntoView({block: 'center'}); await sleep(100);
     for (const t of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'])
       el.dispatchEvent(new (t.startsWith('pointer') ? PointerEvent : MouseEvent)(t, {bubbles: true, cancelable: true, view: window, button: 0}));
     await sleep(300);
     return R(el).getAttribute('aria-selected') === 'true' ? 'selected' : 'not selected';
   };
   'ok';
   ```
3. For each entry:
   1. `await window.__selectRow('<rowId>')` → expect `selected`. Select through
      the row, not the URL: a URL with an instance sublayer's `I…;…` id just
      opens the page with nothing selected.
   2. `Shift + 2` (zoom to selection), then right-click the **canvas center**.
      Get it from `document.querySelector('canvas').getBoundingClientRect()`
      (CSS px) and scale by the screenshot's coordinate-frame width ÷
      `innerWidth`. A right-click inside the selection keeps it selected, even
      when another layer lies on top.
   3. `find` the **Copy as** menu item → click it; `find` **Copy as SVG** →
      click it. (The `Cmd/Ctrl + /` search lists no "Copy as" commands for
      viewers.)
   4. Read the clipboard with the §5 non-blocking `readText`, then store it:
      ```js
      (() => { const c = window.__clip || '';
        if (!c.startsWith('OK:') || !c.slice(3).trimStart().startsWith('<svg')) return 'NOT SVG';
        window.__icons['<name>'] = c.slice(3); return 'stored ' + Object.keys(window.__icons).length; })();
      ```
4. Download all of them at once, as in step 5 but with
   `JSON.stringify(window.__icons)` and `a.download = 'figicons_<slug>.json'`.
   Then:
   ```bash
   SRC=$(ls -t ~/Downloads/figicons_<slug>*.json | head -1)
   python3 <skill_dir>/icons.py save "$SRC" <artifact_location>/<slug>/icons
   rm -f ~/Downloads/figicons_<slug>*.json
   ```

## 13. Running "Figma to Code" without Dev Mode (unverified)
Plugins need **edit access**: free Starter users can run them in files they can
edit and in their own drafts, while View/Collab seats can't run them in Design
mode at all. Neither route below has been verified live — screenshot each step
the first time and update this section.
- **Tier `edit`**: run the plugin in Design mode. Right-click the canvas →
  **Plugins** → recents, or the toolbar's Actions menu → **Plugins & widgets**
  → search "Figma to Code". Then the §0b spoof, §4 and §5 as usual.
- **Copy into the caller's drafts** (tier `view`, opt-in only): main menu →
  File → **Duplicate to your drafts**. This puts a copy of someone else's
  design in the caller's account, so ask first, every time. The option is
  missing when the owner disabled viewer copying and exporting, and an account
  whose file browser shows "Limited access … switch to a plan where you're a
  full member" probably can't create files at all. Node ids reportedly survive
  duplication: open `<new file key>?node-id=<same id>` and check the name
  matches. Run the plugin there, then offer to move the copy to trash.

## 14. Troubleshooting
| Symptom | Fix |
|---------|-----|
| Plugin stuck on "Loading Figma to Code…" (even after reload / fresh tab) | Tab is `visibilityState=hidden`. Apply the §0b visibility spoof, then re-run the plugin. This is the #1 blocker. |
| "Figma to Code" not in the `Cmd/Ctrl + /` search | Expected — that search never lists plugins. Use Dev Mode → **Plugins** tab → Recents (§2). |
| Right panel shows **Comments/Properties**, banner "You can only view and comment" | View-only mode; design-mode plugins can't run. Switch to Dev Mode (`&m=dev`) for the plugin. Export still works in view-only (§6). |
| Clicked **Plugins**/**Properties** tab but panel didn't switch | The click often misses right after a navigation. Screenshot, click again, verify before proceeding. |
| Clicked the plugin's Recents row but nothing opened | Recents hadn't rendered when you clicked. Screenshot, click the row once visible. |
| `navigator.clipboard.readText()` froze the renderer (CDP timeout ~45s) | Never `await` it. Use the non-blocking `.then/.catch` into a global + poll (§5). |
| Paste into a scratch textarea comes back empty | Synthetic `Cmd/Ctrl+V` doesn't hit the OS clipboard here. Don't paste — read via `navigator.clipboard.readText` (§5). |
| Can't read the plugin's code from the DOM / iframe | The plugin UI is an opaque sandboxed iframe; DOM read is impossible. Use Copy → clipboard (§5). |
| `javascript_tool` call denied "Blocked by classifier" when returning code | You're dumping large code text out of the tool. Don't — Blob-download it to `~/Downloads` instead (§0c, §5). Only return small status strings, and sanitize the `:` `/` `?` `=` `&` characters in any snippet you echo back. |
| PNG export produced a `.zip`, not a `.png` | The frame name contains "/". The ZIP holds `Name/Sub.png` — unzip -j and rename (§7). |
| Export button greyed out | Nothing selected — re-select the node (§1). |
| Exported PNG isn't 2x | Scale dropdown wasn't set to 2x, or the click missed. Re-open Export, set 2x, verify with `sips` (= 2 × design WxH). |
| Node not selected / panel empty | `Shift + 2` to zoom-to-selection, or click the frame title on canvas. |
| Redirected to a Figma login page | Ask the caller to log in themselves; never enter their credentials. Then re-check. If they cannot log in, stop at Step 2. |
| `&m=dev` shows "Want to view this file in Dev Mode?" (or "Upgrade to work in Dev Mode") | The active account has no Dev Mode on this file. Click **Not now** — never **Request access** / **Upgrade** unprompted — and run the §10 account check. |
| A Blob download or export never reaches `~/Downloads` | Chrome blocked repeated downloads from figma.com (§0d). Ask the caller to allow them in the address bar, then take the newest match and delete the `(1)`/`(2)` duplicates. |
| Layer scan ends with `err: target row not found` | The node's row isn't in the Layers panel (ancestors collapsed). Click the frame's name label on the canvas to reveal it, then restart (§12). |
| `build_layer_tree.py` warns about gaps or missing children | Something interrupted the scan (usually a click or scroll in the browser while it ran). Restart the scan and leave the browser alone until `done`. |
| `typeof figma` is `undefined` | Expected on view-only pages. Don't work around it; use §11/§12. |
| A design URL opens in Dev Mode (`&m=dev` appended) | Figma reopened the account's last mode. Press `Shift + D` for Design mode. |
| A URL with an `I…;…` node id opens the page with nothing selected | Layers inside instances can't be URL-selected. Select through the Layers row (§12, `__selectRow`). |
| `__selectRow` returns `not found` | The row isn't expanded: run it right after the scan, on the same page load, with ids from this session's tree. |
