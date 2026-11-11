# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A Claude Code plugin **marketplace** (name: `mobile-handytool-skills`, catalog in `.claude-plugin/marketplace.json`) of standalone tools for problems that come up during mobile development — **one plugin per tool**. There is no buildable app: the content is `SKILL.md` prompts, reference docs, and helper scripts run in place from the installed skill directory. There are no build, lint, or test commands.

```
.claude-plugin/marketplace.json             lists every plugin explicitly (plugins are not auto-discovered)
plugins/<tool>/.claude-plugin/plugin.json   name, version, description
plugins/<tool>/skills/<tool>/SKILL.md       plus whatever files the skill needs
```

### Verifying a change

Validate the manifests:

```bash
claude plugin validate .
```

The only end-to-end check is loading the plugin from a real target project and invoking the skill:

```bash
cd /path/to/an-app && claude --plugin-dir /path/to/mobile-handytool-skills/plugins/<tool>
```

To test the marketplace entry itself: `/plugin marketplace add /path/to/mobile-handytool-skills`, then `/plugin install <tool>@mobile-handytool-skills`.

## What belongs here

A tool takes one recurring mobile-development chore off the developer's hands. Fixes for a specific platform or device change belong in `mobile-compat-skills`, and stack-specific workflows in their own repos (`flutter-feature-skills`).

## Plugin rules

- **Self-contained**: an installed plugin is copied to the plugin cache on its own, so nothing may reference files outside its plugin folder (no `../`). Shared scripts are duplicated per plugin.
- **Bump `version` in the plugin's `plugin.json` on every change** — installed users don't receive changes otherwise. The version lives in `plugin.json` only, not in the marketplace entry.
- **Adding a tool**: create `plugins/<tool>/` with `.claude-plugin/plugin.json` and `skills/<tool>/`, add an entry to `marketplace.json`, add a row to README's plugin table.
- **Renaming** the marketplace or a published plugin breaks existing installs, which reference `<plugin>@mobile-handytool-skills`.
- **Project-agnostic**: never hardcode a target project's names, paths or rules.
- **`description:` frontmatter is the auto-trigger**: list the phrases and situations users actually say; stay under 1024 characters.

## Tool notes

- **`figma-design-to-artifact`** is browser-driven on purpose: don't replace it with the Figma MCP or Dev Mode API, which produce different artifacts. Its no-Dev-Mode fallback stays in the browser too: never the REST API (free and view-only seats get a handful of calls a month), and never workarounds for Figma's permission gates. `figma-browser-navigation.md` documents the live figma.com UI, so it is the file to update when Figma changes. The helper scripts sit beside `SKILL.md` (no `scripts/` folder), use only the Python standard library, and print JSON.
- **`store-submission-prep`** is a single `SKILL.md` containing the field catalog. It prepares a handover sheet only and never uploads, builds, or submits. Console labels stay English on purpose: owners with a translated console get matching aids (switch-to-English steps, localized help links), not per-locale label maps.
