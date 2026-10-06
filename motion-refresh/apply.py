#!/usr/bin/env python3
"""Build a separate motion/brand patch for the existing Avenzo site. Never deploy."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, re, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
VERSION = '20260909'
CSS = f'<link rel="stylesheet" href="/assets/avenzo-motion-{VERSION}.css">'
JS = f'<script src="/assets/avenzo-motion-{VERSION}.js" defer></script>'


def main_fragment(html: str) -> str:
    found = re.search(r'<main\b[^>]*>.*?</main>', html, re.S)
    if not found:
        raise ValueError('Expected main content')
    return found.group()


def enhance_html(html: str) -> str:
    """Idempotent. Keep main HTML, all images, forms and navigation untouched."""
    if not re.search(r'<title[^>]*>[^<]*Avenzo Digital', html):
        raise ValueError('Unknown site; refusing modification')
    if html.count('</head>') != 1 or html.count('</body>') != 1:
        raise ValueError('Unexpected HTML document structure')
    before = main_fragment(html)
    result = html
    for tag in (CSS, JS):
        if tag not in result:
            result = result.replace('</head>', tag + '</head>', 1)
    if before != main_fragment(result):
        raise ValueError('Unexpected main content change')
    return result


def build(source: Path, output: Path) -> dict:
    source, output = source.resolve(), output.resolve()
    if source == output or source in output.parents or output in source.parents:
        raise ValueError('Use a separate, non-nested output directory')
    if not source.is_dir() or (output.exists() and any(output.iterdir())):
        raise ValueError('Source must exist and output must be empty')
    brand = ROOT / 'brand-refresh' / 'apply.py'
    if not brand.is_file():
        raise ValueError('Approved brand-refresh module missing')
    spec = importlib.util.spec_from_file_location('avenzo_approved_brand', brand)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    pages = []
    for path in sorted(source.rglob('*.html')):
        if path.is_symlink():
            raise ValueError('Symlink source is not allowed')
        original = path.read_text(encoding='utf-8')
        if 'Avenzo Digital' not in original: continue
        branded = module.refresh_html(original)
        patched = enhance_html(branded)
        if main_fragment(original) != main_fragment(patched):
            raise ValueError('Main preservation check failed')
        pages.append((path.relative_to(source), original, patched))
    if not pages: raise ValueError('No identified Avenzo pages')
    output.mkdir(parents=True, exist_ok=True)
    report = {'version': VERSION, 'deployment_performed': False, 'pages': [],
              'native_3d_added': False, 'native_4k_rasters_created': False,
              'scope': 'Approved brand + reversible CSS/JS motion layer; main HTML unchanged. Patch, not a complete website.'}
    for relative, original, patched in pages:
        target = output / relative; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(patched, encoding='utf-8')
        report['pages'].append({'path': relative.as_posix(), 'main_preserved': True,
            'before_sha256': hashlib.sha256(original.encode()).hexdigest(),
            'after_sha256': hashlib.sha256(patched.encode()).hexdigest()})
    assets = output/'assets'; assets.mkdir(exist_ok=True)
    for folder in (ROOT/'brand-refresh'/'assets', HERE/'assets'):
        for file in folder.iterdir():
            if file.is_file() and file.suffix in ('.css', '.js', '.svg'):
                shutil.copy2(file, assets/file.name)
    (output/'motion-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    (output/'READ-ME-FIRST.txt').write_text('PATCH ONLY. Preserve all existing assets, fonts, routes and form code. Apply to the canonical existing ChatGPT Site, not a new site. This patch does not deploy anything. No fonts are included. CSS 2.5D is not rigged 3D, and the original rasters are not native 4K.\n')
    return report

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); print(json.dumps(build(a.source,a.output),indent=2))
