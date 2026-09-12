"""Fetch a primary source to a local text file so the model reads only the lines it needs.

Order of attempts: urllib (browser UA) -> PowerShell Invoke-WebRequest (Windows) ->
give up with a hint that the page needs the browser pane (WAF sites such as
EUR-Lex, iso.org, meti.go.jp). A WAF/consent/index page that comes back as
"success" is detected by its size and title and treated as a failure. PDFs are
converted with `pdftotext` when on PATH; e-Gov law JSON is flattened one article
/ paragraph per line; HTML is reduced to visible text. The text is never printed
in full: --grep prints a window of +-WINDOW characters around each match, at
most --max-matches matches, so a 1 MB regulation costs a few hundred tokens.
--grep-only skips the download and greps a text file saved earlier (e.g. by the
browser pane). Python 3.10+, standard library only.
"""
import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'
BLOCKED_TITLES = ['official journal', 'request unsuccessful', 'incapsula', 'just a moment', 'access denied', 'attention required', 'captcha', 'todays oj']
EGOV_LAW = re.compile(r'https?://laws\.e-gov\.go\.jp/law/([0-9A-Z]+)')


def normalize_url(url):
    m = EGOV_LAW.match(url)
    if m:  # the /law/ page is a JS application; the API returns the full text
        return f'https://laws.e-gov.go.jp/api/2/law_data/{m.group(1)}?response_format=json'
    return url


def download(url, out):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'ja,en;q=0.8'})
        with urllib.request.urlopen(req, timeout=90) as r:
            data = r.read()
            status = getattr(r, 'status', 200)
        if status == 200 and len(data) > 800:
            out.write_bytes(data)
            return 'urllib'
    except Exception:  # noqa: BLE001
        pass
    if sys.platform.startswith('win'):
        cmd = ['powershell', '-NoProfile', '-NonInteractive', '-Command',
               f"try {{ Invoke-WebRequest -Uri '{url}' -OutFile '{out}' -UseBasicParsing -TimeoutSec 120; exit 0 }} catch {{ exit 1 }}"]
        if subprocess.run(cmd, capture_output=True).returncode == 0 and out.is_file() and out.stat().st_size > 800:
            return 'powershell'
    return None


def egov_lines(node, out, buf):
    """Flatten e-Gov law_full_text ({tag, attr, children}) into one line per article/paragraph/item."""
    if isinstance(node, str):
        buf.append(node)
        return
    if isinstance(node, list):
        for c in node:
            egov_lines(c, out, buf)
        return
    tag = node.get('tag', '')
    if tag in ('Article', 'Paragraph', 'Item', 'Chapter', 'Section', 'Subsection', 'SupplProvision', 'TOC', 'Preamble'):
        if buf:
            out.append(''.join(buf).strip())
            buf.clear()
    for c in node.get('children', []) or []:
        egov_lines(c, out, buf)
    if tag in ('ArticleTitle', 'ArticleCaption', 'ChapterTitle', 'SectionTitle', 'ParagraphNum', 'ItemTitle'):
        buf.append('　')


def json_to_text(obj):
    if isinstance(obj, dict) and 'law_full_text' in obj:
        out, buf = [], []
        egov_lines(obj['law_full_text'], out, buf)
        if buf:
            out.append(''.join(buf).strip())
        return '\n'.join(l for l in out if l)
    lines = []

    def walk(o):
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, str) and o.strip():
            lines.append(o.strip())
    walk(obj)
    return '\n'.join(lines)


def to_text(raw_path, text_path):
    data = raw_path.read_bytes()
    if data[:4] == b'%PDF':
        exe = shutil.which('pdftotext')
        if not exe:
            return 'pdf (pdftotext not found; read with the Read tool by pages)'
        subprocess.run([exe, '-enc', 'UTF-8', str(raw_path), str(text_path)], capture_output=True)
        return 'pdf->text'
    txt = data.decode('utf-8', errors='ignore')
    head = txt.lstrip()[:1]
    if head in ('{', '['):
        try:
            text_path.write_text(json_to_text(json.loads(txt)), encoding='utf-8')
            return 'json->text'
        except ValueError:
            pass
    if '<html' in txt[:5000].lower() or '<body' in txt.lower():
        txt = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', txt, flags=re.S | re.I)
        txt = re.sub(r'<br\s*/?>|</p>|</div>|</tr>|</h\d>|</li>', '\n', txt, flags=re.I)
        txt = html.unescape(re.sub(r'<[^>]+>', ' ', txt))
        txt = re.sub(r'[ \t\xa0]+', ' ', txt)
        txt = re.sub(r'\n\s*\n+', '\n', txt)
    text_path.write_text(txt, encoding='utf-8')
    return 'html->text'


def looks_blocked(raw_path, text_path):
    """True when the 'successful' download is a WAF challenge, consent page or an index page."""
    if not text_path.is_file():
        return 'no text extracted'
    text = text_path.read_text(encoding='utf-8', errors='ignore')
    raw = raw_path.read_bytes()[:4000].decode('utf-8', errors='ignore').lower()
    title = re.search(r'<title[^>]*>(.*?)</title>', raw, re.S)
    title = (title.group(1) if title else '').strip().lower()
    for marker in BLOCKED_TITLES:
        if marker in title:
            return f'page title "{title[:60]}" looks like a block/index page'
    if len(text.strip()) < 2000:
        return f'only {len(text.strip())} characters of text extracted'
    return None


def grep(text_path, patterns, window=200, max_matches=30):
    text = text_path.read_text(encoding='utf-8', errors='ignore')
    starts = [0] + [m.end() for m in re.finditer(r'\n', text)]
    shown, count = [], 0
    for pat in patterns:
        for m in re.finditer(pat, text):
            count += 1
            if count > max_matches:
                continue
            a, b = max(0, m.start() - window), min(len(text), m.end() + window)
            if any(s <= m.start() < e for s, e in shown):
                continue
            shown.append((a, b))
            line = sum(1 for s in starts if s <= m.start())
            snippet = text[a:b].replace('\n', ' ⏎ ')
            print(f'L{line} [{pat}]: …{snippet}…')
    if count > max_matches:
        print(f'-- {count} matches; showed {max_matches}. Narrow the pattern (article number, exact phrase).')
    elif count == 0:
        print(f'-- no match for {patterns} in {text_path.name} ({len(text)} chars)')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    p = argparse.ArgumentParser()
    p.add_argument('url')
    p.add_argument('--out', type=Path, required=True, help='directory for the raw file and extracted text')
    p.add_argument('--name', help='base file name (default: derived from URL)')
    p.add_argument('--grep', nargs='*', help='regex patterns; only a window around each match is printed')
    p.add_argument('--window', type=int, default=200, help='characters of context on each side of a match')
    p.add_argument('--max-matches', type=int, default=30)
    p.add_argument('--grep-only', action='store_true', help='do not download; grep the text file saved earlier under --out')
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    url = normalize_url(args.url)
    name = args.name or re.sub(r'[^A-Za-z0-9._-]+', '_', args.url.split('//', 1)[-1])[:80]
    raw = args.out / (name + '.raw')
    text = args.out / (name + '.txt')
    if not args.grep_only:
        how = download(url, raw)
        blocked = looks_blocked(raw, text) if how and (conv := to_text(raw, text)) else 'download failed'
        if not how or blocked:
            print(f'FETCH FAILED: {url} ({blocked})\nThis site blocks scripted access. Open it in the browser pane, slice document.body.innerText '
                  f'around the needed heading (one article at a time), save the text to\n  {text}\nand rerun with --grep-only --grep PATTERN.')
            raise SystemExit(2)
        print(f'fetched via {how}; {conv}; text={text} ({text.stat().st_size} bytes)')
    elif not text.is_file():
        print(f'FETCH FAILED: --grep-only but {text} does not exist')
        raise SystemExit(2)
    if args.grep:
        grep(text, args.grep, args.window, args.max_matches)
