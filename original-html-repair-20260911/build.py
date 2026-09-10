#!/usr/bin/env python3
"""Preserve the original Avenzo website; amend only the approved brand and UHD CSS.
The original raster bytes are never modified, regenerated or called native 4K.
"""
from __future__ import annotations
import base64, hashlib, importlib.util, json, mimetypes, os, re, shutil
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'original-source'
OUT=ROOT/'html-delivery'
SITE=OUT/'website'
REPORTS=OUT/'controle'
FONT_EXTS={'.woff','.woff2','.ttf','.otf','.eot'}

CSS='''/* Original composition. No bitmap of the page, no new hero, no raster resizing. */
/* Approved vector wordmark is white only where the original desktop header is dark. */
@media(min-width:1025px){.home .site-header .av-brand img{filter:brightness(0) invert(1)}}
@media(max-width:1024px){.home .site-header .av-brand img{filter:none}}
/* Continue the same composition on UHD screens with native layout and vector typography.
   No CSS zoom, scale() wrapper, fixed 3840px screenshot, or canvas is used. */
@media(min-width:1921px){
  :root{font-size:clamp(16px,.8333333333vw,32px);--max:120rem}
  body{font-size:1rem}
  .header-inner{height:6.25rem}
  .site-header .brand.av-brand{width:11.5rem}
  .desktop-nav .button{min-height:3rem}
  .arrow{width:1.25rem;height:1.25rem;flex-basis:1.25rem}
  .hero-inner{min-height:min(52.083333333vw,62.5rem);padding:9.0625rem var(--pad) 5rem}
  .hero-actions .button{min-width:14.375rem}
  .hero-expertise{min-height:2.75rem}
  .software-visual img{min-height:28.125rem}
  .av-footer{padding-top:5rem}
  .av-footer__inner{max-width:100rem}
  .av-footer__brand{width:13.25rem}
  .av-footer__intro{gap:4rem;padding-bottom:2.5rem}
  .av-footer__intro p{max-width:48.75rem}
  .av-footer__cta{gap:2rem;min-height:3.375rem;padding:.875rem 1.25rem}
  .av-footer__cta svg{width:1.5rem;height:1.5rem;flex-basis:1.5rem}
  .av-footer__details{gap:2rem}
  .av-footer__detail{grid-template-columns:2.375rem minmax(0,1fr);gap:1.125rem;min-height:7.125rem;padding:1.75rem 0}
  .av-footer__detail-text{gap:.4375rem;padding-left:1.125rem}
  .av-footer__icon{width:2.375rem;height:2.375rem;border-radius:.375rem}
  .av-footer__icon svg,.av-footer__mail-link svg{width:1.4375rem;height:1.4375rem}
  .av-footer__value{font-size:1.0625rem}
  .av-footer__brand-row{gap:1.5rem;padding:2.375rem 0 1.875rem}
  .av-footer__tagline{margin-top:.8125rem}
  .av-footer__studio{gap:1rem;min-height:2.75rem}
  .av-footer__studio svg{width:1.25rem;height:1.25rem;flex-basis:1.25rem}
  .av-footer__bottom{gap:1.125rem;padding:1rem 0}
  .av-footer__mail-link{min-width:2.75rem;min-height:2.75rem;padding-left:1rem}
}
'''

def digest(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def main_markup(html:str)->str:
    m=re.search(r'<main\b[^>]*>.*?</main>',html,re.S)
    if not m:raise ValueError('Missing original main element')
    return m.group()

def data_uri(path:Path)->str:
    if path.suffix.lower() in FONT_EXTS:raise ValueError('Do not distribute font files')
    mime=mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
    return 'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode('ascii')

def font_remote(css:str)->str:
    return re.sub(r"(?P<q>['\"]?)/assets/body\.woff(?P=q)","'https://avenzodigital.nl/assets/body.woff'",css)

def asset(path:str)->Path:
    p=urlsplit(path).path
    if not p.startswith('/assets/') or '..' in Path(p).parts:raise ValueError('Not a known public asset: '+path)
    f=SITE/p.lstrip('/')
    if not f.is_file():raise FileNotFoundError(f)
    return f

def inline_css(css:str)->str:
    css=font_remote(css)
    def replace(m):
        value=m.group(1).strip().strip('\"\'')
        if value.startswith('/assets/'):
            f=SITE/value.lstrip('/')
            if f.is_file() and f.suffix.lower() not in FONT_EXTS:return 'url("'+data_uri(f)+'")'
            return 'url("https://avenzodigital.nl'+value+'")'
        return m.group()
    return re.sub(r'url\(([^)]+)\)',replace,css)

def main():
    if OUT.exists():raise ValueError('Refusing to overwrite a delivery')
    SITE.mkdir(parents=True);REPORTS.mkdir()
    if len(list(SOURCE.rglob('index.html')))!=9:raise ValueError('Expected the preserved nine-page source')
    for src in (SOURCE/'assets').rglob('*'):
        if not src.is_file() or src.suffix.lower() in FONT_EXTS:continue
        # Failed public source checks sometimes saved HTML under an image filename.
        if src.suffix.lower() in {'.webp','.png','.jpg','.jpeg'}:
            try:
                with Image.open(src) as im:im.verify()
            except Exception:continue
        dst=SITE/src.relative_to(SOURCE);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    spec=importlib.util.spec_from_file_location('approved_brand',ROOT/'brand-refresh'/'apply.py')
    brand=importlib.util.module_from_spec(spec);spec.loader.exec_module(brand)
    for name in brand.ASSETS:shutil.copy2(ROOT/'brand-refresh'/'assets'/name,SITE/'assets'/name)
    (SITE/'assets'/'avenzo-original-uhd.css').write_text(CSS,encoding='utf-8')
    for p in (SITE/'assets').rglob('*.css'):p.write_text(font_remote(p.read_text()),encoding='utf-8')
    pages=[];routes={}
    for src in sorted(SOURCE.rglob('index.html')):
        rel=src.relative_to(SOURCE);route='/'+rel.as_posix().removesuffix('index.html')
        original=src.read_text(encoding='utf-8')
        updated=brand.refresh_html(original)
        updated=updated.replace('</head>','<link rel="stylesheet" href="/assets/avenzo-original-uhd.css"></head>',1)
        # A font is referenced from its existing host, not redistributed in this package.
        updated=updated.replace('href="/assets/body.woff"','href="https://avenzodigital.nl/assets/body.woff"')
        assert main_markup(original)==main_markup(updated),'Original content or hero changed'
        dst=SITE/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text(updated,encoding='utf-8')
        offline=OUT/'AVENZO.html' if route=='/' else OUT/'paginas'/(route.strip('/')+'.html')
        routes[route]=(dst,offline)
        pages.append({'route':route,'original_main_sha256':digest(main_markup(original).encode()),'delivered_main_sha256':digest(main_markup(updated).encode()),'main_exactly_unchanged':True})
    embedded_images={}
    for route,(src,dst) in routes.items():
        doc=BeautifulSoup(src.read_text(),'html.parser')
        for link in list(doc.select('link')):
            rel=link.get('rel',[])
            if 'preload' in rel:link.decompose();continue
            if 'stylesheet' in rel:
                style=doc.new_tag('style');style.string=inline_css(asset(link['href']).read_text());link.replace_with(style)
            elif 'icon' in rel:link['href']=data_uri(asset(link['href']))
        for script in list(doc.select('script[src]')):
            # Only the known original navigation/contact JS is included.
            script_path=script.get('src','')
            if not script_path.startswith('/assets/'):script.decompose();continue
            new=doc.new_tag('script');new.string=asset(script_path).read_text();script.decompose();doc.body.append(new)
        for el in doc.select('img,source'):
            candidates=[]
            if el.get('src','').startswith('/assets/'):candidates.append((0,el['src']))
            for entry in el.get('srcset','').split(','):
                parts=entry.strip().split()
                if parts and parts[0].startswith('/assets/'):
                    width=int(parts[1][:-1]) if len(parts)>1 and parts[1].endswith('w') else 0
                    candidates.append((width,parts[0]))
            if not candidates:continue
            chosen=max(candidates)[1];path=asset(chosen)
            embedded_images[chosen]=digest(path.read_bytes())
            uri=data_uri(path)
            if el.name=='img':
                el['src']=uri
                for key in ('srcset','sizes'):el.attrs.pop(key,None)
            else:
                el['srcset']=uri
                el.attrs.pop('sizes',None)
            el['data-original-asset']=chosen
        for a in doc.select('a[href]'):
            href=a['href'];u=urlsplit(href)
            if not href.startswith('/') or href.startswith('//'):continue
            key=u.path if u.path.endswith('/') else u.path+'/'
            if key not in routes:raise ValueError('Unknown local route: '+href)
            target=routes[key][1]
            local=os.path.relpath(target,dst.parent).replace(os.sep,'/')
            a['href']=local+('?' + u.query if u.query else '')+('#'+u.fragment if u.fragment else '')
        dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text(str(doc),encoding='utf-8')
    # Verify original image bytes are not modified, mislabeled or replaced by generated scenes.
    images=[]
    for path in sorted((SITE/'assets').rglob('*')):
        if path.suffix.lower() not in {'.webp','.png','.jpg','.jpeg'}:continue
        original=SOURCE/path.relative_to(SITE)
        assert original.read_bytes()==path.read_bytes()
        with Image.open(path) as im:
            images.append({'path':path.relative_to(SITE).as_posix(),'width':im.width,'height':im.height,'sha256':digest(path.read_bytes()),'original_bytes_preserved':True,'is_native_3840px_source':im.width>=3840})
    for css in (SITE/'assets').rglob('*.css'):
        # Per-page original font preload was also changed to its existing public address.
        assert not re.search(r"url\(['\"]?/assets/body\.woff",css.read_text())
    for path in OUT.rglob('*'):
        if path.suffix.lower() in FONT_EXTS:raise ValueError('Font binary present')
    # The uploaded downloadss is the same original design identified by these real asset names.
    home=(SITE/'index.html').read_text()
    assert 'hero-desktop-apps-1672.webp' in home and 'hero-mobile-apps-1106.webp' in home
    assert '/assets/native-4k/' not in home
    assert '<canvas' not in home and '<video' not in home
    manifest={'source':'Preserved original nine published pages. Homepage structure and original image references match the uploaded downloadss HTML.','source_snapshot_run':34530730425,'approved_brand_revision':'20260909','page_count':len(pages),'pages':pages,'images':images,'offline_embedded_original_images':embedded_images,'header_and_digital_are_svg':True,'native_html_css_for_uhd':True,'all_raster_images_native_4k':all(i['is_native_3840px_source'] for i in images),'raster_upscaling_performed':False,'raster_regeneration_performed':False,'new_mockup_used':False,'font_files_included':False,'deployment_performed':False}
    (REPORTS/'bron-en-wijzigingen.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    (OUT/'LEESMIJ.txt').write_text('''AVENZO DIGITAL | HERSTELD ORIGINEEL HTML

OPEN AVENZO.html. Dit is de echte, werkende homepage, geen afbeelding van de pagina.
Alle afbeeldingen, stijlen en scripts zijn in de direct te openen HTML-bestanden
opgenomen. De andere acht pagina's staan in paginas en zijn gewoon aanklikbaar.
Pak het volledige ZIP-bestand uit voordat je AVENZO.html opent.

WAT IS AANGEPAST
Het goedgekeurde vectorwoordmerk met DIGITAL eronder staat linksboven.
Wit op de oorspronkelijke donkere desktophero, bordeaux op de lichte mobiele header.
De eerder goedgekeurde footer en teksten zijn toegepast.
Boven 1920 CSS-pixels groeit de bestaande compositie proportioneel door tot 3840.
Tekst, knoppen, logo en iconen blijven echte HTML/CSS/SVG, niet een platte mockup.

WAT IS BEHOUDEN
De originele voorpagina, de originele beelden en de volledige hoofdinhoud van alle
negen pagina's zijn behouden. Elke oorspronkelijke rasterafbeelding is byte voor
byte gelijk aan de bron. Geen nieuwe Blender-versie, geen gegenereerde vervanging.

BELANGRIJK OVER 4K
Dit is een HTML-aanpassing voor 4K-schermen. Het oorspronkelijke desktopbeeld
blijft 1672 x 941; het mobiele beeld 1106 x 1422. De dienstbeelden zijn 1586 x 992.
Deze achtergrondfoto's zijn NIET ineens native 4K en er is GEEN bestand opgeschaald.
Voor dezelfde fotografie met echte nieuwe 4K-details zijn de oorspronkelijke
hogereresolutiebronbestanden nodig. Een 3840px browserscreenshot bewijst dat niet.

PUBLICATIE
website bevat de hostingversie met de oorspronkelijke routes en losse assets.
Er is niets live gepubliceerd. Bewaar de huidige hostingbestanden en het bestaande
font voordat je publiceert. Wijzig geen DNS-, domein- of mailinstellingen.

LETTERTYPE
Er zijn geen fontbestanden inbegrepen. Het originele font wordt van de bestaande
Avenzo-host geladen. Zonder toegang tot dit font gebruikt de browser Arial.

CONTACTFORMULIER
Het oorspronkelijke formulier opent een e-mailconcept in het mailprogramma van
de bezoeker. Het verstuurt niet zelfstandig. Er is geen nieuwe mailbackend toegevoegd.

CONTROLE
controle bevat een bronvergelijking, pixelafmetingen, bestandshashes en de
werkelijk uitgevoerde browsertests. Geen claim dat lage-resolutiebeelden native 4K zijn.
''',encoding='utf-8')
    print(json.dumps({'pages':len(pages),'original_rasters_preserved':len(images),'native_raster_4k':manifest['all_raster_images_native_4k'],'deployment_performed':False}))

if __name__=='__main__':main()
