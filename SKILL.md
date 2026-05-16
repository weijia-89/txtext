---
name: txtext
description: Quick-access command for batch URL text extraction. Automatically discovers and follows links on index/tutorial pages. Uses curl + Python natively; Playwright-MCP for JS-heavy content as second-to-last resort. Applies efficient-and-secure principles to minimize noise and token usage.
repo: https://github.com/weijia-89/txtext
---

# Batch URL Text Extraction with Link Discovery

Clean text from URLs; auto-follow links on index/tutorial pages. Strip nav/footer/boilerplate.

**Input:** One URL or a list (newline or comma separated).

## Workflow (one screen)

1. **Index detection** — If path hints (`tutorial`, `guide`, `overview`, `introduction`, `getting-started`, `about`, `resources`, `docs`, `part-`, `chapter-`) or numbered sidebar → treat as docs index → link discovery (no extra confirm).
2. **Links (index only)** — `http`/`https` only; refuse `file://`, `ftp://`, etc. **curl first:** JSON keys (`collectionReferences`, `pageTree`, `children`), else `<a>`. **Playwright** only if JS/AJAX lists. **Filter** Part/Chapter/Step/API; skip nav/footer/social/breadcrumbs. **Dedupe** strip fragments. **Show** ≤8 groups; user picks.
3. **Non-index** — Ask “Follow links?” No → main page only.
4. **JSON scan order (first hit wins):** `<script type="application/json">` → `collectionReferences` / `pageTree` / `children` → `window.__INITIAL_STATE__`, `window.pageData` → `data-config`, `data-page-tree`. Skip JSON >500KB; else parse `<a>`.
5. **Nested link pages** — If >70% link-text and <30% body → ask to unfurl; if yes, curl each (≤8 topics). Logic: `reference/link-detection.py` (`is_nested_link_page`, `group_links_by_topic`).
6. **Progress** — Before: show estimate `(total/8)*2.5*1.2s` sample line. During: `[n/total] title... done (elapsed, ETA)`. Helpers: `reference/utils.py` (`estimate_time`, `show_progress`).
7. **Output** — Folder? (default `<subject>-docs/`). Single file vs one-per-URL. Names from `<h1>`/`<title>`; script adds `Source:` / `Extracted:` headers (`sanitize_filename`, `sanitize_text`).
8. **Security** — Warn stderr on credential-like patterns; delete scratch output; do not commit extracts. Policy: [SECURITY.md](SECURITY.md).

## Content filtering

**Drop:** nav/header/footer/script/style; boilerplate (cookie/consent/privacy/terms/social/search/breadcrumb); exact dup lines; repeated “Part N / Chapter N” labels.

**Keep:** `<article>`, `<main>`, headings, `<p>`, lists, `<pre>`, `<code>`, tables.

**Subject filter:** Keywords from URL + `<title>`; keep paragraphs with ≥2 hits; table rows ≥1. (~75-85% fewer tokens vs raw HTML.) Full rules: `reference/content-extraction.py`.

## Method priority

**curl → xmllint/jq/node → Support Platform API → Playwright-MCP → Trafilatura → PyMuPDF**

1. **curl + Python stdlib** (preferred)

   ```bash
   curl -s -L --proto-redir https --max-redirs 5 "$url" -H "User-Agent: Mozilla/5.0" | python3 ~/.claude/skills/txtext/reference/content-extraction.py "$url"
   ```

2. **Native tools** (if curl incomplete)

   ```bash
   curl -s "$url" | xmllint --html --xpath "//article//text() | //main//text()" - 2>/dev/null | tr -s ' \n'
   curl -s "$api_url" | jq '.articles[].body // .items[].content // .results[].text'
   node -e "fetch(process.argv[1],{headers:{'User-Agent':'Mozilla/5.0'}}).then(r=>r.text()).then(h=>process.stdout.write(h))" -- "$url"
   ```

3. **Support Platform API** — Zendesk/Confluence/Notion/Gitbook when user confirms (faster than scrape).

4. **Playwright-MCP** (second-to-last) — Only if curl + natives fail. Discovery: `browser_navigate` → `browser_wait(3-5s)` → `browser_snapshot` → parse.

5. **Trafilatura** (last resort text) — `pipx install trafilatura` after user OK.

6. **PyMuPDF** (PDF only) — `pip install pymupdf` after user OK.

## Task constraints

- ~5 min cap per batch; dedupe URLs (strip fragments); reuse one browser session when possible; echo final file paths in the reply when done.
