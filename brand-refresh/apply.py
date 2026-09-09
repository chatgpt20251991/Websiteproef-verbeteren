#!/usr/bin/env python3
"""Apply the approved Avenzo header/footer to static HTML. No deployment or DNS writes."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERSION = '20260909'
ASSETS = ('avenzo-wordmark-20260909.svg', 'avenzo-brand-refresh-20260909.css')
CSS_LINK = '<link rel="stylesheet" href="/assets/avenzo-brand-refresh-20260909.css">'
HEADER_LOGO = ('<a class="brand av-brand" href="/" aria-label="Avenzo Digital, naar home">'
               '<img src="/assets/avenzo-wordmark-20260909.svg" width="2062" height="509" '
               'alt="Avenzo Digital" decoding="async"></a>')


def refresh_html(html: str, footer: str | None = None) -> str:
    """Fail closed on an unknown template; preserve the entire main area and navigation."""
    footer = (HERE / 'footer.html').read_text(encoding='utf-8').strip() if footer is None else footer.strip()
    title = re.search(r'<title\b[^>]*>(.*?)</title>', html, re.I | re.S)
    if not title or 'Avenzo Digital' not in title.group(1):
        raise ValueError('Not an identified Avenzo Digital page; nothing written.')
    header_re = re.compile(r'<header\b[^>]*\bclass="site-header"[^>]*>.*?</header>', re.S)
    headers = list(header_re.finditer(html))
    if len(headers) != 1:
        raise ValueError('Expected exactly one known site header.')
    header = headers[0].group()
    brand_re = re.compile(r'<a\b[^>]*\bclass="brand(?: av-brand)?"[^>]*>.*?</a>', re.S)
    new_header, count = brand_re.subn(lambda _: HEADER_LOGO, header)
    if count != 1:
        raise ValueError('Expected exactly one header wordmark.')
    result = html[:headers[0].start()] + new_header + html[headers[0].end():]
    footer_re = re.compile(r'<footer\b[^>]*\bclass="(?:site-footer|av-footer)"[^>]*>.*?</footer>', re.S)
    result, count = footer_re.subn(lambda _: footer, result)
    if count != 1:
        raise ValueError('Expected exactly one site footer.')
    if CSS_LINK not in result:
        if result.count('</head>') != 1:
            raise ValueError('Expected one head closing tag.')
        result = result.replace('</head>', CSS_LINK + '</head>', 1)
    # A public HTML snapshot can include a Cloudflare per-request challenge.
    # That platform-generated script is not source code and must not be republished.
    result = re.sub(r'<script\b[^>]*>(?:(?!</script>).)*__CF\$cv\$params(?:(?!</script>).)*</script>',
                    '', result, flags=re.S)
    before_main = re.search(r'<main\b[^>]*>.*?</main>', html, re.S)
    after_main = re.search(r'<main\b[^>]*>.*?</main>', result, re.S)
    if not before_main or not after_main or before_main.group() != after_main.group():
        raise ValueError('Main content changed unexpectedly; refusing output.')
    return result


def apply_directory(source: Path, output: Path) -> dict:
    """Write changed HTML and the two new assets to a separate staging directory."""
    source, output = source.resolve(), output.resolve()
    if source == output or source in output.parents or output in source.parents:
        raise ValueError('Source and output must be separate, non-nested directories.')
    if not source.is_dir():
        raise ValueError('Source directory does not exist.')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Output directory is not empty. Use a new directory.')
    candidates = []
    for path in sorted(source.rglob('*.html')):
        if path.is_symlink():
            raise ValueError('Symlink HTML is not supported.')
        text = path.read_text(encoding='utf-8')
        if '<title>' in text and 'Avenzo Digital' in text:
            candidates.append((path, text, refresh_html(text)))
    if not candidates:
        raise ValueError('No Avenzo HTML pages found.')
    # Validate every page first so a template mismatch never leaves a partial patch.
    output.mkdir(parents=True, exist_ok=True)
    manifest = {'version': VERSION, 'deployment_performed': False,
                'scope': 'HTML header/footer and two new assets only; preserve existing site assets, mail, DNS and forms.',
                'pages': [], 'assets': list(ASSETS)}
    for path, original, updated in candidates:
        relative = path.relative_to(source)
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(updated, encoding='utf-8')
        manifest['pages'].append({'path': relative.as_posix(),
            'before_sha256': hashlib.sha256(original.encode()).hexdigest(),
            'after_sha256': hashlib.sha256(updated.encode()).hexdigest()})
    (output / 'assets').mkdir(exist_ok=True)
    for name in ASSETS:
        shutil.copy2(HERE / 'assets' / name, output / 'assets' / name)
    (output / 'brand-refresh-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    return manifest


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True, help='Existing static HTML root')
    p.add_argument('--output', type=Path, required=True, help='New empty staging directory, not the live root')
    args = p.parse_args()
    print(json.dumps(apply_directory(args.source, args.output), indent=2))


if __name__ == '__main__':
    main()
