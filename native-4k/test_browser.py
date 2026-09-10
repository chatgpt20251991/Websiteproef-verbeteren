#!/usr/bin/env python3
"""Exercise only the local release. Never submits mail, changes DNS or publishes."""
from __future__ import annotations
import argparse,json,threading,urllib.parse,time,shutil
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from PIL import Image
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

CONFIGS=[(320,780,1),(390,844,3),(768,1024,2),(1440,1000,1),(1920,1080,2),(3840,2160,1)]
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

def main():
    p=argparse.ArgumentParser();p.add_argument('--release',type=Path,default=Path('release'));args=p.parse_args()
    site=(args.release/'website').resolve();reports=args.release/'reports';reports.mkdir(exist_ok=True)
    pages=sorted(site.rglob('*.html'));assert len(pages)==9
    routes=['/'+f.relative_to(site).as_posix().removesuffix('index.html') for f in pages]
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(site)))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(server.server_port)
    results={'deployment_performed':False,'checks':[],'interaction_checks':[],'errors':[],'font_note':'Original font is fetched from existing live host. No font binaries are distributed. Fallback font is allowed and reported.','visual_review':'Screenshots recorded. Automated tests do not constitute a human visual design approval.','browser':'Chromium'}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch()
            results['browser_version']=browser.version
            for width,height,dpr in CONFIGS:
                context=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=dpr,reduced_motion='reduce')
                page=context.new_page();js_errors=[];local_http_errors=[]
                page.on('pageerror',lambda error:js_errors.append(str(error)))
                page.on('response',lambda response:local_http_errors.append({'url':response.url,'status':response.status}) if response.url.startswith(base) and response.status>=400 else None)
                for route in routes:
                    js_errors.clear();local_http_errors.clear();record={'route':route,'viewport_width':width,'viewport_height':height,'device_pixel_ratio':dpr}
                    response=page.goto(base+route,wait_until='domcontentloaded',timeout=45000);record['status']=response.status
                    page.evaluate("""async () => {
                        document.documentElement.style.scrollBehavior='auto';
                        for (const img of document.images) img.loading='eager';
                        await Promise.all(Array.from(document.images).map(i=>i.decode().catch(()=>{})));
                        await Promise.race([document.fonts.ready,new Promise(r=>setTimeout(r,4000))]);
                    }""")
                    page.wait_for_timeout(150)
                    data=page.evaluate("""() => ({
                        scrollWidth:document.documentElement.scrollWidth,
                        clientWidth:document.documentElement.clientWidth,
                        h1:document.querySelectorAll('h1').length,
                        logoCount:document.querySelectorAll('img[src*="avenzo-wordmark-20260909.svg"]').length,
                        fontStatus:Array.from(document.fonts).map(f=>({family:f.family,status:f.status})),
                        images:Array.from(document.images).map(i=>{const r=i.getBoundingClientRect();return {src:i.currentSrc||i.src,complete:i.complete,naturalWidth:i.naturalWidth,naturalHeight:i.naturalHeight,width:r.width,height:r.height,fit:getComputedStyle(i).objectFit};})
                    })""")
                    record.update(data);record['js_errors']=list(js_errors);record['local_http_errors']=list(local_http_errors)
                    errors=[]
                    if response.status!=200:errors.append('Page HTTP status not 200')
                    if data['scrollWidth']>data['clientWidth']+1:errors.append('Horizontal overflow')
                    if data['h1']!=1:errors.append('Expected one h1')
                    if data['logoCount']!=2:errors.append('Approved header/footer logos missing')
                    if js_errors:errors.append('JavaScript exception')
                    if local_http_errors:errors.append('Missing local resource')
                    for image in record['images']:
                        if not image['complete'] or not image['naturalWidth']:errors.append('Image failed to decode: '+image['src'])
                        path=urllib.parse.unquote(urllib.parse.urlparse(image['src']).path)
                        local=site/path.lstrip('/')
                        if '/native-4k/' not in path or not local.exists() or image['width']==0 or image['height']==0:continue
                        with Image.open(local) as im:iw,ih=im.size
                        image['source_pixels']=[iw,ih]
                        ratio=iw/ih
                        need_w=image['width']*dpr;need_h=image['height']*dpr
                        if image['fit']=='cover':need_w=max(need_w,need_h*ratio)
                        image['required_source_width']=round(need_w,2)
                        image['pixel_coverage']=round(iw/max(1,need_w),3)
                        if iw+3<need_w:errors.append('Image source below displayed pixel budget: '+path)
                    if route=='/' and ((width==3840 and dpr==1) or (width==1920 and dpr==2)):
                        hero=page.locator('.hero-picture img').evaluate('(i)=>i.currentSrc')
                        record['hero_source_at_4k']=hero
                        if not hero.endswith('hero-desktop-apps-3840.webp'):errors.append('4K viewport did not load 3840px hero')
                    record['passed']=not errors;record['errors']=errors;results['checks'].append(record)
                    results['errors'].extend([{'route':route,'width':width,'dpr':dpr,'error':e} for e in errors])
                    if route=='/' and width in (390,1440,3840):
                        page.screenshot(path=str(reports/('homepage-'+str(width)+'-dpr'+str(dpr)+'.png')),full_page=(width!=3840),animations='disabled')
                    if width==390 and route=='/contact/':page.screenshot(path=str(reports/'contact-mobile.png'),full_page=True,animations='disabled')
                context.close()
            # The original menu and accordion controls must still work.
            context=browser.new_context(viewport={'width':390,'height':844},reduced_motion='reduce');page=context.new_page()
            page.goto(base+'/',wait_until='domcontentloaded')
            menu=page.locator('.menu-toggle');menu.click();opened=menu.get_attribute('aria-expanded')=='true' and page.locator('#mobile-menu').is_visible()
            page.keyboard.press('Escape');closed=menu.get_attribute('aria-expanded')=='false' and page.locator('#mobile-menu').is_hidden()
            results['interaction_checks'].append({'name':'Mobile menu open and Escape close','passed':opened and closed})
            page.goto(base+'/expertise/websites-conversie/',wait_until='domcontentloaded')
            details=page.locator('details').first
            if details.count():
                was=details.get_attribute('open') is not None;details.locator('summary').click();now=details.get_attribute('open') is not None
                results['interaction_checks'].append({'name':'Service accordion toggles','passed':was!=now})
            page.goto(base+'/contact/?dienst=software-portalen',wait_until='domcontentloaded')
            selected=page.locator('#project-form select[name=dienst]').input_value()
            results['interaction_checks'].append({'name':'Contact service preselection','passed':selected=='software-portalen'})
            email_links=page.locator('a[href^="mailto:"]').count()
            results['interaction_checks'].append({'name':'Existing email links present','passed':email_links>0})
            results['interaction_checks'].append({'name':'No form or email submitted','passed':True})
            context.close();browser.close()
        # All internal navigation destinations and anchors must exist in the package.
        links_checked=0
        for pagefile in pages:
            doc=BeautifulSoup(pagefile.read_text(),'html.parser');route='/'+pagefile.relative_to(site).as_posix().removesuffix('index.html')
            for a in doc.select('a[href]'):
                href=a['href']
                if href.startswith(('mailto:','tel:','https:','http:')):continue
                parsed=urllib.parse.urlparse(urllib.parse.urljoin(base+route,href));relative=urllib.parse.unquote(parsed.path).lstrip('/');dest=site/relative
                if dest.is_dir():dest=dest/'index.html'
                if not dest.is_file():results['errors'].append({'route':route,'error':'Internal destination missing: '+href});continue
                if parsed.fragment and dest.suffix=='.html':
                    target=BeautifulSoup(dest.read_text(),'html.parser')
                    if not target.find(id=urllib.parse.unquote(parsed.fragment)):results['errors'].append({'route':route,'error':'Internal anchor missing: '+href})
                links_checked+=1
        results['internal_links_checked']=links_checked
        for c in results['interaction_checks']:
            if not c['passed']:results['errors'].append({'error':c['name']})
    except Exception as exc:
        results['errors'].append({'exception':type(exc).__name__,'error':str(exc)})
        raise
    finally:
        server.shutdown();server.server_close()
        results['passed']=len(results['checks'])==54 and not results['errors']
        (reports/'browser-validation.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
        shutil.copy2(__file__,args.release/'source'/'test_browser.py')
        print(json.dumps({'page_viewport_checks':len(results['checks']),'passed':results['passed'],'errors':results['errors'],'deployment_performed':False},indent=2))
    if not results['passed']:raise SystemExit(1)

if __name__=='__main__':main()
