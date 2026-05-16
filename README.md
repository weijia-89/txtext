# txtext skill

AI skill for batch URL text extraction with automatic link discovery. Paste a URL and the skill finds all linked pages, extracts the text, and saves everything to files — no manual copy-pasting.

## What It Does

1. Detects if a URL is a documentation index (guides, tutorials, getting-started pages)
2. Discovers and lists all linked pages — you choose which to extract
3. Downloads and saves text with a `Source:` + timestamp header per file
4. Warns if extracted content may contain credentials or sensitive data

**Safety built in:**
- HTTPS only — refuses `file://` and `ftp://` URLs
- Credential pattern detection on extracted content
- 10MB input cap; non-printable character stripping

---

## Install

### Manual (from source)

**Claude Code:**
```bash
mkdir -p ~/.claude/skills/txtext
cp SKILL.md ~/.claude/skills/txtext/SKILL.md
```
Restart Claude Code → type `/txtext`.

**Cursor:**
```bash
cp SKILL.md ~/.cursor/rules/txtext.mdc
```
Restart Cursor → type `/txtext`.

**Windsurf:**
```bash
cat SKILL.md >> ~/.codeium/windsurf/global_rules.md
```
Restart Windsurf → type `/txtext`.

---

## Usage

Type `/txtext` in your IDE chat and paste one or more URLs:

```
/txtext
https://docs.example.com/guides

→ Detected: documentation index
→ Found 12 pages: Getting Started, Installation, Configuration...
→ Extract all? [Y/n]
→ [1/12] Getting Started... done
→ Saved to docs-example.com/
```

---

## Security

See [SECURITY.md](SECURITY.md).

- **Review before sharing:** Extracted files may contain API keys or secrets. The skill prints a warning to the console if it detects credential patterns — always review output before committing to git or sharing.
- **Don't commit output:** Add extracted folders to `.gitignore`:
  ```
  *-docs/
  extracted-content/
  ```

---

## Troubleshooting

| Issue | Fix |
|---|---|
| `/txtext` does nothing | Fully restart your IDE (Cmd+Q, then reopen) |
| Empty or incomplete content | Check your internet connection; try a different page URL |
| Credential warning in output | Review the file for secrets before sharing or committing |
| Frontmatter error | Verify `SKILL.md` starts with `name:` and `description:` fields |
