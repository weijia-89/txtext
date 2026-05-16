#!/usr/bin/env python3
"""
Content extraction for txtext.
Usage: curl -s -L --proto-redir https --max-redirs 5 "$url" -H "User-Agent: Mozilla/5.0" | python3 content-extraction.py "$url"
Outputs: Source/Extracted header + filtered body text (~75-85% token reduction vs raw HTML).
See: link-detection.py (nested pages), utils.py (sanitize/progress)
"""
import sys, re, html as html_module, unicodedata, datetime

_MAX_URL_ARG = 2048
url = sys.argv[1] if len(sys.argv) > 1 else ""
if not url:
    sys.stderr.write("usage: content-extraction.py <url>\n")
    sys.exit(1)
if len(url) > _MAX_URL_ARG or re.search(r"[\x00-\x20\x7f]", url):
    sys.stderr.write("error: URL rejected (length or control characters)\n")
    sys.exit(1)
if not re.match(r'^https?://', url, re.I):
    sys.stderr.write("error: unsupported URL scheme (only http and https)\n")
    sys.exit(1)

_MAX_INPUT = 10 * 1024 * 1024  # 10MB cap — prevents OOM on oversized pages
try:
    raw = sys.stdin.buffer.read(_MAX_INPUT + 1)
    if len(raw) > _MAX_INPUT:
        sys.stderr.write("warning: input >10MB; truncating\n")
        raw = raw[:_MAX_INPUT]
    html = raw.decode('utf-8', errors='replace')
except Exception as e:
    sys.stderr.write(f"read error: {e}\n")
    sys.exit(1)

try:
    # 1. Subject keywords from URL path + page title
    subject_words = set()
    for segment in re.findall(r'[a-z\-]+', url.lower()):
        if len(segment) > 3:
            subject_words.update(segment.split('-'))
    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.I)
    if title_match:
        subject_words.update(re.findall(r'\b[a-z]{4,}\b', title_match.group(1).lower()))

    # 2. Remove chrome — multi-pass handles nesting; attr pattern handles > in quoted values
    for _ in range(3):
        _new, _n = re.subn(
            r'<(script|style|nav|footer|aside|modal|dialog)'
            r'(?:[^>]|"[^"]*"|\'[^\']*\')*>.*?</\1>',
            '', html, flags=re.DOTALL|re.I)
        if _n == 0:
            break
        html = _new

    # 3. Mark tables for preservation
    html = re.sub(r'<table[^>]*>', '\n[TABLE_START]\n', html, flags=re.I)
    html = re.sub(r'</table>', '\n[TABLE_END]\n', html, flags=re.I)
    html = re.sub(r'<tr[^>]*>', '', html, flags=re.I)
    html = re.sub(r'</tr>', '\n', html, flags=re.I)
    html = re.sub(r'<(td|th)[^>]*>', '', html, flags=re.I)
    html = re.sub(r'</(td|th)>', ' | ', html, flags=re.I)

    # 4. Strip remaining tags
    text = re.sub(r'<[^>]+>', '\n', html)

    # 5. Decode entities — bounds check prevents ValueError on codepoints >0x10FFFF
    text = html_module.unescape(text)
    text = re.sub(r'&#x([0-9a-fA-F]+);',
        lambda m: chr(int(m.group(1), 16)) if int(m.group(1), 16) <= 0x10FFFF else '', text)
    text = re.sub(r'&#(\d+);',
        lambda m: chr(int(m.group(1))) if int(m.group(1)) <= 0x10FFFF else '', text)

    # 6. Normalize Unicode
    text = re.sub(r'[\u200b\u200c\u200d\u200e\u200f\u2060\ufeff]', '', text)
    text = text.replace('\u00ad', '')
    for char, rep in {'\u201c': '"', '\u201d': '"', '\u2018': "'", '\u2019': "'",
                      '\u2013': '-', '\u2014': '--', '\u2026': '...', '\u00a0': ' '}.items():
        text = text.replace(char, rep)
    text = text.replace('\ufffd', '?')
    text = re.sub(r'[\u061c\u2061\u2062\u2063\u2064]', '', text)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # 7. Boilerplate pattern
    boilerplate = r'(cookie|consent|privacy|terms|eula|copyright|©|disclaimer|legal|back to top|skip to|return to|next|previous|pagination|breadcrumb|home|products|solutions|company|resources|pricing|contact|careers|blog|share|follow|subscribe|newsletter|twitter|facebook|linkedin|instagram|search|language|dark mode|accessibility|print)'

    # 8. Deduplicate + filter lines
    seen_lines = set()
    lines = []
    part_chapter_count = {}
    in_table = False
    # Pre-compile per-word boundary patterns once; avoids re-compiling per line in the hot loop
    _kw_patterns = [re.compile(r'\b' + re.escape(w) + r'\b') for w in subject_words]

    for line in text.split('\n'):
        line = line.strip()
        if '[TABLE_START]' in line: in_table = True; continue
        if '[TABLE_END]' in line: in_table = False; continue
        if len(line) < 20 and not in_table: continue
        if re.search(boilerplate, line, re.I): continue
        if line in seen_lines: continue
        seen_lines.add(line)

        # Deduplicate repeated structural labels (Part 1, Chapter 2, etc.)
        if re.match(r'^(part|chapter|section|module|unit|step|lesson)\s+\d+', line, re.I):
            key = re.match(r'^(\w+\s+\d+)', line, re.I).group(1)
            part_chapter_count[key] = part_chapter_count.get(key, 0) + 1
            if part_chapter_count[key] > 1: continue

        # Word-boundary matching prevents false positives ("api" != "applicable")
        _ll = line.lower()
        keyword_count = sum(1 for p in _kw_patterns if p.search(_ll))
        if keyword_count >= (1 if in_table or '|' in line else 2):
            lines.append(line)

    text = re.sub(r'\n{3,}', '\n\n', '\n'.join(lines))

    # Warn if output contains likely credentials
    if re.search(
        r'(?:api[_-]?key|apikey|secret|bearer|password|passwd|token|auth)\s*[=:]\s*["\']?[A-Za-z0-9+/]{16,}',
        text, re.I):
        sys.stderr.write("WARNING: extracted content may contain credentials -- review before storing\n")

    # 9. Output
    print(f"Source: {url}")
    print(f"Extracted: {datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print()
    print(text)

except Exception as e:
    sys.stderr.write(f"extraction error: {e}\n")
    sys.exit(1)
