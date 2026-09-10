#!/usr/bin/env python3
"""Build a deployable static Avenzo site from the preserved public snapshot.
No deployment, credentials, font distribution, generated marketing claims or image upscaling.
"""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,re,shutil
from pathlib import Path
from PIL import Image
from bs4 import BeautifulSoup

STEMS=('hero-desktop-apps','hero-mobile-apps','service-web','service-ai','service-software','service-data','service-search','service-testing','software-closeup')
WIDTHS=(640,960,1280,1672,1920,2560,3840)
FORBIDDEN_FONTS={'.woff','.woff2','.ttf','.otf','.eot'}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def resize_down(image,width):
    if width<1 or width>image.width:raise ValueError('Image enlargement forbidden')
    if width==image.width:return image.copy()
    return image.resize((width,round(image.height*width/image.width)),Image.Resampling.LANCZOS)

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--renders',type=Path,required=True);p.add_argument('--output',type=Path,default=Path('release'));args=p.parse_args()
    if args.output.exists():raise ValueError('Refusing to overwrite output directory')
    expected_source=Path(__file__).parent/'render.py'
    source_hash=sha(expected_source)
    verified={}
    for stem in STEMS:
        f=args.renders/(stem+'.png');e=args.renders/(stem+'.json');evidence=json.loads(e.read_text())
        if evidence['upscaling'] is not False or evidence['input_raster_textures']!=0:raise ValueError('Unverified render origin: '+stem)
        if evidence['source_sha256']!=source_hash:raise ValueError('Render source does not match packaged source: '+stem)
        if evidence['output_sha256']!=sha(f):raise ValueError('Render hash mismatch: '+stem)
        with Image.open(f) as im:
            if im.width!=3840 or im.size!=(evidence['native_render_width'],evidence['native_render_height']):raise ValueError('Not a native 3840px render: '+stem)
        verified[stem]=(f,evidence)
    pages=sorted(args.source.rglob('*.html'))
    if len(pages)!=9:raise ValueError('Expected exactly the nine original public pages')
    refresh_path=Path(__file__).parents[1]/'brand-refresh'/'apply.py'
    spec=importlib.util.spec_from_file_location('approved_brand_refresh',refresh_path);brand=importlib.util.module_from_spec(spec);spec.loader.exec_module(brand)
    out=args.output;site=out/'website';assets=site/'assets';reports=out/'reports';sources=out/'source'
    assets.mkdir(parents=True);reports.mkdir();sources.mkdir()
    for f in (args.source/'assets').rglob('*'):
        if not f.is_file() or f.suffix.lower() in FORBIDDEN_FONTS:continue
        if 'precision' in f.relative_to(args.source/'assets').parts:continue
        if f.suffix.lower() not in ('.css','.js','.svg'):continue
        target=assets/f.relative_to(args.source/'assets');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
    for name in brand.ASSETS:shutil.copy2(refresh_path.parent/'assets'/name,assets/name)
    # The original font stays on its existing host; never distribute a font binary.
    for css in assets.rglob('*.css'):
        value=css.read_text();value=value.replace("url('/assets/body.woff')","url('https://avenzodigital.nl/assets/body.woff')")
        css.write_text(value)
    native=assets/'native-4k';native.mkdir()
    manifest={'release':'Avenzo Digital native 4K','deployment_performed':False,'image_upscaling':False,'new_raster_sources':9,'source_sha256':source_hash,'layout_and_main_copy_preserved':True,'contact_behavior':'Original mailto draft, not server-side delivery','font_files_distributed':False,'images':[],'pages':[]}
    sizes={}
    for stem,(path,evidence) in verified.items():
        with Image.open(path) as src:
            im=src.convert('RGB');sizes[stem]=im.size
            variants=[]
            for width in WIDTHS:
                dest=native/(stem+'-'+str(width)+'.webp');thumb=resize_down(im,width);thumb.save(dest,'WEBP',quality=94,method=6)
                variants.append({'width':thumb.width,'height':thumb.height,'bytes':dest.stat().st_size,'sha256':sha(dest),'path':dest.relative_to(site).as_posix()})
        manifest['images'].append({'stem':stem,'native_render':evidence,'variants':variants})
        shutil.copy2(args.renders/(stem+'.json'),reports/(stem+'.json'))
    pattern=re.compile(r'/assets/precision/('+'|'.join(map(re.escape,STEMS))+r')-\d+\.webp')
    all_used=set()
    for original in pages:
        html=brand.refresh_html(original.read_text())
        soup=BeautifulSoup(html,'html.parser');before=soup.main.get_text(' ',strip=True);changes=0
        for el in soup.select('img,source'):
            match=pattern.search(el.get('src','')+' '+el.get('srcset',''))
            if not match:continue
            stem=match.group(1);all_used.add(stem)
            if el.name=='img':el['src']='/assets/native-4k/'+stem+'-1920.webp'
            el['srcset']=', '.join('/assets/native-4k/'+stem+'-'+str(w)+'.webp '+str(w)+'w' for w in WIDTHS)
            el['width'],el['height']=map(str,sizes[stem])
            if stem=='software-closeup':el['sizes']='(min-width: 761px) 65vw, 100vw'
            elif stem.startswith('hero-'):el['sizes']='100vw'
            changes+=1
        if soup.main.get_text(' ',strip=True)!=before:raise ValueError('Main copy changed')
        if len(soup.select('img[src*="avenzo-wordmark-20260909.svg"]'))!=2:raise ValueError('Approved logo missing')
        if '/assets/precision/' in str(soup):raise ValueError('Low-resolution reference remains')
        rel=original.relative_to(args.source);dest=site/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(str(soup),encoding='utf-8')
        manifest['pages'].append({'path':rel.as_posix(),'native_image_elements':changes,'original_sha256':sha(original),'built_sha256':sha(dest),'main_text_preserved':True})
    if all_used!=set(STEMS):raise ValueError('One of the native scenes is not used by the website')
    # Validate every local stylesheet, script, image and image candidate resolves.
    for page in site.rglob('*.html'):
        doc=BeautifulSoup(page.read_text(),'html.parser')
        for el in doc.select('[src],[href],[srcset]'):
            refs=[el.get('src',''),el.get('href','')]+[part.strip().split()[0] for part in el.get('srcset','').split(',') if part.strip()]
            for ref in refs:
                if ref.startswith('/assets/') and not (site/ref.lstrip('/')).is_file():raise ValueError('Missing asset: '+ref)
    if any(f.suffix.lower() in FORBIDDEN_FONTS for f in out.rglob('*')):raise ValueError('Font binary must not be packaged')
    (reports/'build-manifest.json').write_text(json.dumps(manifest,indent=2))
    shutil.copy2(expected_source,sources/'render.py');shutil.copy2(__file__,sources/'assemble.py')
    # A new native render can always be reproduced from this source; no AI image API is needed.
    (sources/'requirements.txt').write_text('Pillow==11.3.0\nbeautifulsoup4==4.13.4\n')
    (out/'BEKIJK-LOKAAL.py').write_text('''from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from pathlib import Path
import threading, webbrowser
root=Path(__file__).resolve().parent/'website'
server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(root)))
url='http://127.0.0.1:'+str(server.server_port)+'/'
print('Avenzo Digital native 4K: '+url+'  | Sluiten met Ctrl+C')
threading.Timer(.5,lambda:webbrowser.open(url)).start()
try: server.serve_forever()
except KeyboardInterrupt: server.server_close()
''')
    (out/'START-WEBSITE.cmd').write_text('@echo off\r\ncd /d "%~dp0"\r\npy -3 BEKIJK-LOKAAL.py\r\nif errorlevel 1 pause\r\n')
    (out/'LEESMIJ.txt').write_text('''AVENZO DIGITAL | NATIVE 4K WEBSITE

De website-map bevat alle negen oorspronkelijke openbare pagina's, met
het goedgekeurde SVG-logo en de footer. Indeling en hoofdteksten zijn behouden.
Alle negen rasterbeelden zijn NIEUW gerenderd vanuit oorspronkelijke
3D-geometrie, vectorletters, procedurele materialen en belichting.
Geen oude afbeelding is vergroot of als texture gebruikt.

Dit zijn nieuwe 3D-interpretaties van de bestaande beeldrichting, geen
pixelidentieke reconstructies van de vroegere fotografische beelden.
Desktop-hero en softwareclose-up: 3840 x 2160.
Dienstbeelden: 3840 pixels breed in de oorspronkelijke beeldverhouding.
Mobiele hero: 3840 pixels breed, afzonderlijk gekadreerd voor de mobiele pagina.
De browser kiest uit kleinere WebP-varianten waar dat voldoende is.
De maximale variant blijft 3840 pixels breed; er wordt niet opgeschaald.

LOKAAL BEKIJKEN
Met Python 3: dubbelklik START-WEBSITE.cmd (Windows), of start BEKIJK-LOKAAL.py.
Er zijn geen pip-pakketten nodig om de website te bekijken.
De server is uitsluitend op 127.0.0.1 bereikbaar. Ctrl+C sluit hem af.

PUBLICATIE
Dit pakket is NIET live gepubliceerd. De map website is de publicatiemap.
Maak eerst een back-up van de huidige hosting. Vervang alleen bijbehorende
pagina's en voeg de assets toe; verwijder geen bestaande hostingbestanden,
font, DNS-, mail-, certificaat- of serverconfiguratie.
Gebruik dezelfde documentroot en bestaande routes. Er is geen nieuw CMS nodig.

LETTERTYPE
Fontbestanden zijn niet inbegrepen. Het originele font wordt vanaf de
bestaande Avenzo-host geladen. Behoud dit bestand bij publicatie.
Bij blokkering of geen internet gebruikt de browser de bestaande Arial-fallback.

CONTACT
Het bestaande formulier stelt een mailto-concept samen. Het verzendt geen
bericht zelfstandig. Er is geen mailbackend toegevoegd of bezorging geclaimd.

BEWIJS EN BRONNEN
reports bevat beeldafmetingen, SHA-256-hashes, renderinstellingen en uitgevoerde
browsercontroles. source/render.py bevat de reproduceerbare 3D-broncode.
Er zijn geen inloggegevens, API-sleutels, betaalmiddelen of fontbestanden inbegrepen.
''',encoding='utf-8')
    print(json.dumps({'pages':len(pages),'native_sources':9,'responsive_assets':len(STEMS)*len(WIDTHS),'deployment_performed':False,'release':str(out)},indent=2))

if __name__=='__main__':main()
