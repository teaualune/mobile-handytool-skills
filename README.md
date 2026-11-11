# mobile-handytool-skills

A Claude Code plugin **marketplace** of handy tools for problems that come up during mobile development. Each plugin is one self-contained tool, installed and versioned on its own.

## Plugins

| Plugin | What it does | Requires |
|---|---|---|
| `figma-design-to-artifact` | Turns Figma node URLs into reference artifacts by driving Chrome: labeled sample code from the "Figma to Code" plugin plus a 2x PNG — or, without Dev Mode, Figma's CSS for all layers plus a JSON layer tree. [Details](plugins/figma-design-to-artifact/skills/figma-design-to-artifact/README.md) | Claude-in-Chrome, a Figma login, Python 3 |
| `store-submission-prep` | Scans a mobile codebase and writes a prefilled handover sheet covering the App Store Connect and Play Console fields for a first-time submission | An iOS, Android, React Native/Expo, or Flutter project |

## Installation

Prerequisite: [Claude Code](https://claude.com/claude-code) installed and working.

```
/plugin marketplace add teaualune/mobile-handytool-skills
/plugin install figma-design-to-artifact@mobile-handytool-skills
/plugin install store-submission-prep@mobile-handytool-skills
```

Install only the tools you need; each is updated on its own (`/plugin update <plugin>`). Skills trigger automatically when you describe the task, or invoke them by namespaced name, e.g. `/store-submission-prep:store-submission-prep`.

To try a local checkout without installing anything:

```bash
cd /path/to/your-app && claude --plugin-dir /path/to/mobile-handytool-skills/plugins/<plugin>
```

Without the plugin system, copy a skill folder (`plugins/<plugin>/skills/<skill>/`) into a project's `.claude/skills/` or into `~/.claude/skills/`.

## License

[WTFPL](LICENSE)
