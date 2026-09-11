#!/usr/bin/env python3
"""One original Avenzo visual -> one native QHD image response.
Uses the owner-authorized GitHub Actions secret ONLY for api.openai.com.
No website mockup, raster resizing, secret export, live deployment or billing changes.
"""
from __future__ import annotations
import argparse,base64,hashlib,io,json,os,re,sys,time
from pathlib import Path
import requests
from PIL import Image

MODEL='gpt-image-2.5-sunburst'
URL='https://api.openai.com/v1/images/edits'
ASSETS={
 'hero-desktop-apps':('hero-desktop-apps-1672.webp',(2560,1440),
  'Preserve the exact wide architectural photograph: very dark sweeping cantilever of board-formed concrete on the left; glossy black stone floor with warm uplights; the large bordeaux-red curving bridge across the upper half; glass windows and restrained trees. The polished metal 3D Configurator display, AI Studio phone, code enclosure and AI enclosure remain grouped on the RIGHT in precisely the same relative scale and perspective. The left 44 percent stays empty architecture for separate HTML copy. Do not shift the hardware to the center. Keep the building shown INSIDE the configurator screen, readable title 3D Configurator, readable title AI Studio on the phone, original detailed UI and cables.'),
 'hero-mobile-apps':('hero-mobile-apps-1106.webp',(1440,2560),
  'Match this portrait version of the original architecture and hardware group. The same 3D Configurator display and phone must remain prominent, centered in the upper-middle of the portrait, fully visible. Preserve the curved bordeaux bridge above, concrete walls, trees and reflective black floor below. Extend the existing architecture vertically only as necessary for 9:16, never add objects or change the product design. This is only a portrait visual, not a mobile webpage.'),
 'service-web':('service-web-1586.webp',(2560,1440),
  'Recreate exactly this brushed-metal desktop browser display, smaller upright phone in front at right, flat metal plinth and layered panels behind. The screens show the original red architectural bridge website. Preserve the neutral pale stone room, sunlight from upper left, polished reflections, burgundy accents and exact device composition. Extend the existing pale room subtly at the sides for 16:9, do not change the subjects.'),
 'service-ai':('service-ai-1586.webp',(2560,1440),
  'Recreate exactly the low brushed-metal AI compute block on a square base on the left, three burgundy pipes extending right to a thin upright silver workflow panel. The panel has three original steps Analyse, Verbind, Actie and fine outline icons. Same clean pale stone room, daylight upper left, subtle reflections, same exact relative positions and scale. No extra devices. Extend only the plain room at the sides for 16:9.'),
 'service-software':('service-software-1586.webp',(2560,1440),
  'Recreate the exact stack of layered silver software panels: front short wide project and code panel, middle browser panel, taller dashboard behind, and low code enclosure on the right connected with parallel burgundy pipes. Same pale stone studio, sunlight, reflections, brushed aluminium and burgundy details. Preserve front-to-back arrangement, perspective, and product proportions. Extend only plain side background for 16:9.'),
 'service-data':('service-data-1586.webp',(2560,1440),
  'Recreate the exact silver-framed dashboard with burgundy line chart and small lower charts, rear layered metal module and the four physical bar-chart columns on a small metal plinth at front-right. Preserve the pale stone floor and wall, diagonal soft daylight, precise brush-metal surfaces, muted burgundy bars and original arrangement. Extend only neutral side margins for 16:9.'),
 'service-search':('service-search-1586.webp',(2560,1440),
  'Recreate the precise thick upright brushed-metal search ring on the left with a horizontal search field through its center reading Zoeken. On the right keep the two layered silver-framed results panels linked by three parallel burgundy pipes. Same neutral stone room, diagonal sunlight and reflections, exact metal thickness, camera view and scale. Extend only plain side room for 16:9.'),
 'service-testing':('service-testing-1586.webp',(2560,1440),
  'Recreate the exact silver desktop quality-testing UI panel on its stepped metal base, upright phone foreground at right, silver code enclosure and AI/module at right, burgundy connecting pipes. Preserve original monitor/phone placement and testing checklist interface, muted palette, pale stone studio, soft daylight and precise reflections. Extend only neutral margins for 16:9.'),
 'software-closeup':('software-closeup-1672.webp',(2560,1440),
  'Recreate precisely this close elevated macro view of the layered metal application panels, the brushed AI cube behind, and multiple fine burgundy cables connecting modules. Keep the very close diagonal crop of the foreground project interface, metal thicknesses, frame spacing, exact camera angle, tonal contrast and cinematic material details. No zooming out and no rearrangement.')
}
BASE_PROMPT='''Create a NEW, high-detail photorealistic reconstruction of the attached original Avenzo visual at the requested native output dimensions. The reference is the strict composition and art-direction master, NOT loose inspiration. Keep the original visual recognizably one-to-one: same camera viewpoint, same objects, same positions, same background, same lighting direction, same materials and same bordeaux/metal color scheme. Reconstruct fine surface texture, light reflections, polished bevels and legible device interface details directly in the new image. Do not simplify into primitive 3D boxes. Do not invent a different design. No blur, painted styling, exaggerated bloom or cartoon materials.
CRITICAL: Output only the photographic scene. DO NOT add webpage headings, navigation bars, buttons, an Avenzo logo floating over the scene, footer, white page sections, borders or browser chrome outside the physical displays. The actual website text, logo, links and buttons will be separate HTML and SVG. Preserve text and UI that is physically INSIDE the pictured device screens. No watermark or advertising claims.\n'''

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def safe(value,key):
    s=str(value).replace(key,'[redacted]') if key else str(value)
    return re.sub(r'sk-[A-Za-z0-9_\-]+','[redacted]',s)[:500]

def main():
    p=argparse.ArgumentParser();p.add_argument('--asset',choices=ASSETS,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True)
    key=os.environ.get('OPENAI_API_KEY','').strip()
    if not key:
        print(json.dumps({'error':'OPENAI_API_KEY_missing','image_generated':False}));return 2
    name,size,extra=ASSETS[a.asset]
    src=a.source/'assets'/'precision'/name
    data=src.read_bytes()
    with Image.open(io.BytesIO(data)) as im:
        dims=im.size;buffer=io.BytesIO();im.convert('RGB').save(buffer,'PNG');input_png=buffer.getvalue()
    prompt=BASE_PROMPT+extra+'\nFinal output: '+str(size[0])+' x '+str(size[1])+' pixels.'
    target=a.output/(a.asset+'.png');reportfile=a.output/(a.asset+'.json')
    if target.exists():raise RuntimeError('Refusing a duplicate paid generation over an existing result')
    start=time.monotonic()
    report={'asset':a.asset,'model_requested':MODEL,'endpoint':'/v1/images/edits','requested_dimensions':list(size),'reference_dimensions':list(dims),'reference_sha256':sha(data),'prompt':prompt,'api_key_configured':True,'upscaling_performed_by_build':False,'deployment_performed':False,'image_generated':False}
    for attempt in range(3):
        try:
            response=requests.post(URL,headers={'Authorization':'Bearer '+key},data={'model':MODEL,'prompt':prompt,'size':str(size[0])+'x'+str(size[1]),'quality':'high','n':'1','output_format':'png'},files={'image':('original-reference.png',input_png,'image/png')},timeout=(30,600),allow_redirects=False)
        except requests.RequestException as e:
            report.update(error='transport_error',error_class=type(e).__name__,seconds=round(time.monotonic()-start,2))
            reportfile.write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='prompt'}));return 3
        report['http_status']=response.status_code;report['request_id']=response.headers.get('x-request-id');report['attempt']=attempt+1
        try:payload=response.json()
        except ValueError:payload={}
        if response.status_code!=200:
            err=payload.get('error') or {};code=err.get('code') or err.get('type') or 'http_error'
            report.update(error=safe(code,key),error_message=safe(err.get('message',''),key),seconds=round(time.monotonic()-start,2))
            reportfile.write_text(json.dumps(report,indent=2))
            print(json.dumps({k:v for k,v in report.items() if k!='prompt'}),flush=True)
            # Retry only rejected transient rate limits, not billing/auth errors or timeouts.
            if response.status_code==429 and code not in ('insufficient_quota','billing_hard_limit_reached') and attempt<2:
                time.sleep(35*(attempt+1));continue
            return 4
        entries=payload.get('data') or []
        if len(entries)!=1 or not entries[0].get('b64_json'):raise RuntimeError('No single base64 image result')
        raw=base64.b64decode(entries[0]['b64_json'],validate=True)
        with Image.open(io.BytesIO(raw)) as im:
            actual=im.size;im.verify()
        report.update(image_generated=True,actual_dimensions=list(actual),output_sha256=sha(raw),output_bytes=len(raw),usage=payload.get('usage'),api_size=payload.get('size'),api_quality=payload.get('quality'),seconds=round(time.monotonic()-start,2))
        # Keep exact returned bytes. Never upscale or relabel a smaller image.
        target.write_bytes(raw);reportfile.write_text(json.dumps(report,indent=2))
        print(json.dumps({k:v for k,v in report.items() if k!='prompt'}),flush=True)
        if actual!=size:
            print('ERROR: returned dimensions do not equal requested dimensions; do not publish as QHD.');return 5
        return 0
    return 6

if __name__=='__main__':sys.exit(main())
