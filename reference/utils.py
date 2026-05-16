#!/usr/bin/env python3
"""
Utility functions for txtext: estimate_time, show_progress, sanitize_filename, sanitize_text.
"""
import re, sys, unicodedata


def estimate_time(num_articles):
    """Estimate extraction time: (articles / 8) * 2.5s/article * 1.2 buffer"""
    base_time = (num_articles / 8) * 2.5 * 1.2
    minutes, seconds = int(base_time / 60), int(base_time % 60)
    return f"{minutes}m {seconds}s"


def show_progress(current, total, category, title, elapsed_sec):
    """Print real-time progress line to stdout."""
    percent = (current / total) * 100
    remaining_sec = (elapsed_sec / max(1, current)) * (total - current)
    speed = elapsed_sec / max(1, current)
    print(f"[{current}/{total}] {category[:30]}... {percent:3.0f}% | {title[:45]}")
    print(f"  {int(elapsed_sec//60):2d}m {int(elapsed_sec%60):2d}s elapsed | ~{int(remaining_sec//60)}m {int(remaining_sec%60):2d}s remain | {speed:.2f}s/item")
    sys.stdout.flush()


def sanitize_filename(title, max_length=200):
    """Convert title to safe cross-platform filename. NFKD lowercase, hyphens, Windows reserved names protected, max 200 chars + .txt."""
    if not isinstance(title, str):
        title = str(title) if title is not None else 'untitled'
    filename = unicodedata.normalize('NFKD', title).lower()
    filename = re.sub(r'[/\\:|\*?"<>]', '-', filename)
    filename = re.sub(r'[\x00-\x1f]', '', filename)
    filename = re.sub(r'\s+', '-', filename)
    filename = re.sub(r'-+', '-', filename)
    filename = filename.strip('.- ')

    reserved = {'con','prn','aux','nul','com1','com2','com3','com4','com5',
                'com6','com7','com8','com9','lpt1','lpt2','lpt3','lpt4','lpt5',
                'lpt6','lpt7','lpt8','lpt9'}
    if filename.split('.')[0].lower() in reserved:
        filename = filename + '_'

    return filename[:max_length] + '.txt'


def sanitize_text(content):
    """Clean extracted text: strips control chars, zero-width chars, normalizes CRLF, collapses blank lines. Preserves structure."""
    if not isinstance(content, str):
        return ''
    content = unicodedata.normalize('NFC', content)
    content = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', content)
    content = re.sub(r'[\u200b\u200c\u200d\u200e\u200f\ufeff\u061c]', '', content)
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    content = '\n'.join(line.rstrip() for line in content.split('\n'))
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.rstrip('\n') + '\n'
