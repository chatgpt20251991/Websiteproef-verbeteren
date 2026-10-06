#!/usr/bin/env python3
"""Generate responsive WebP files from REAL master images; never invent 4K via upscaling.
Manifest input: {"hero-desktop-apps": "/path/to/original-4k.png", ...}.
Images are resized only downward. Keep original artwork and aspect ratio.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from PIL import Image, ImageOps
WIDTHS = (640, 960, 1280, 1600, 1920, 2560, 3200, 3840)

def export_one(name: str, source: Path, output: Path) -> dict:
    if not re.fullmatch(r'[a-z][a-z0-9-]{1,70}', name):
        raise ValueError('Invalid asset name')
    with Image.open(source) as original:
        image = ImageOps.exif_transpose(original).convert('RGB')
    if image.width < 640 or image.width * image.height > 100_000_000:
        raise ValueError('Invalid master dimensions')
    output.mkdir(parents=True, exist_ok=True)
    candidates = sorted(set([w for w in WIDTHS if w <= image.width] + [min(image.width,3840)]))
    versions = []
    for w in candidates:
        h = round(image.height * w / image.width)
        target = output/f'{name}-{w}.webp'
        image.resize((w,h),Image.Resampling.LANCZOS).save(target,'WEBP',quality=90,method=6)
        versions.append({'file':target.name,'width':w,'height':h,'bytes':target.stat().st_size})
    return {'name':name,'source_width':image.width,'source_height':image.height,
            'native_4k_width_available':image.width >= 3840,'upscaled':False,'versions':versions,
            'srcset':', '.join(f'/assets/precision-hires/{v["file"]} {v["width"]}w' for v in versions)}

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--masters',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists() and any(args.output.iterdir()):raise SystemExit('Use an empty output directory')
    manifest=json.loads(args.masters.read_text())
    result=[export_one(name,Path(path),args.output) for name,path in manifest.items()]
    (args.output/'media-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
