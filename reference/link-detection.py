#!/usr/bin/env python3
"""
Nested link page detection for txtext.
is_nested_link_page(html, text) -> (bool, groups)   — >70% link density = intermediate page
group_links_by_topic(links, html, max_display=8) -> (groups, has_more)
Both return safe fallback values on error.
"""
import re

_MAX_URL_LEN = 2048


def _safe_http_url(raw):
    """Allow only http(s) URLs; drop javascript:, data:, whitespace, and control chars."""
    if not raw:
        return None
    u = raw.strip()
    if len(u) > _MAX_URL_LEN:
        return None
    if re.search(r"[\x00-\x20\x7f]", u):
        return None
    if not re.match(r"^https?://", u, re.I):
        return None
    return u


def _extract_links(html):
    """Extract (url, text) pairs — handles double-quoted, single-quoted, unquoted href."""
    out = []
    for dq, sq, uq, txt in re.findall(
        r'<a[^>]*\bhref=(?:"([^"]*)"|\'([^\']*)\'|([^\s>]*))[^>]*>([^<]+)</a>',
        html,
        re.I,
    ):
        raw = dq or sq or uq
        safe = _safe_http_url(raw)
        t = txt.strip()
        if safe and t:
            out.append((safe, t))
    return out


def is_nested_link_page(html, text):
    """Returns (True, groups) if >70% of visible text is link text and page has >=3 links."""
    try:
        links = _extract_links(html)

        total_text = len(text)
        link_text_length = sum(len(link_text) for _, link_text in links)
        link_density = link_text_length / max(total_text, 1)

        if link_density > 0.7 and len(links) >= 3:
            groups, _ = group_links_by_topic(links, html)
            return True, groups

        return False, []
    except Exception:
        return False, []


def group_links_by_topic(links, html, max_display=8):
    """Group links by h2/h3 headings; falls back to ~8 generic chunks if no headings found."""
    try:
        heading_pattern = r'<h[23][^>]*>([^<]+)</h[23]>.*?(?=<h[23]|$)'

        groups = []
        for match in re.finditer(heading_pattern, html, re.DOTALL | re.I):
            heading = match.group(1).strip()
            section_links = _extract_links(match.group(0))
            if section_links:
                groups.append({
                    'topic': heading,
                    'count': len(section_links),
                    'links': [{'url': url, 'title': title} for url, title in section_links],
                })

        if not groups:
            chunk_size = max(1, len(links) // 8)
            for i in range(0, len(links), chunk_size):
                chunk = links[i:i + chunk_size]
                if chunk:
                    groups.append({
                        'topic': f'Group {i // chunk_size + 1}',
                        'count': len(chunk),
                        'links': [{'url': url, 'title': title} for url, title in chunk],
                    })

        has_more = len(groups) > max_display
        return groups[:max_display], has_more
    except Exception:
        return [], False
