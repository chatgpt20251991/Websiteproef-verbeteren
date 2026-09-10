#!/usr/bin/env python3
from __future__ import annotations
import io,json,re,shutil,threading
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'html-delivery';SITE=OUT/'website';REPORT=OUT/'controle'

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

def serve(root):
    s=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(root)))
    threading.Thread(target=s.serve_forever,daemon=True).start()
    return s,'http://127.0.0.1:'+str(s.server_port)

def ready(page):
    page.evaluate("""async()=>{
      for(const img of document.images) img.loading='eager';
      await Promise.all(Array.from(document.images, i=>i.decode().catch(()=>{})));
      await Promise.race([document.fonts.ready,new Promise(r=>setTimeout(r,6000))]);
    }""")

def snapshot(page):
    return page.evaluate("""()=>({
      title:document.title,
      overflow:document.documentElement.scrollWidth>innerWidth+1,
      viewport:innerWidth,documentWidth:document.documentElement.scrollWidth,
      brokenImages:Array.from(document.images).filter(i=>!i.complete||!i.naturalWidth).map(i=>i.getAttribute('data-original-asset')||i.getAttribute('src')),
      bodyFont:Array.from(document.fonts).filter(f=>f.family==='Body').map(f=>({family:f.family,status:f.status})),
      headerLogoCount:document.querySelectorAll('.site-header .av-brand img').length,
      footerLogoCount:document.querySelectorAll('.av-footer__brand img').length,
      heading:document.querySelector('h1')?.innerText,
      forms:document.querySelectorAll('form').length,
      canvasCount:document.querySelectorAll('canvas').length
    })""")

def main():
    server,base=serve(SITE)
    pages=sorted(SITE.rglob('index.html'))
    records=[];interactions=[];pixel={}
    try:
      with sync_playwright() as p:
        browser=p.chromium.launch()
        context=browser.new_context(device_scale_factor=1,locale='nl-NL',reduced_motion='reduce')
        page=context.new_page();page.set_default_timeout(15000)
        for width,height in [(320,820),(390,844),(768,1024),(1440,900),(3840,2160)]:
          page.set_viewport_size({'width':width,'height':height})
          for path in pages:
            route='/'+path.relative_to(SITE).as_posix().removesuffix('index.html')
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            response=page.goto(base+route,wait_until='domcontentloaded',timeout=30000);ready(page)
            state=snapshot(page);state.update(kind='hosting-html',route=route,width=width,http_status=response.status,js_errors=list(errors))
            records.append(state)
            assert response.status==200 and not state['overflow'] and not state['brokenImages'],json.dumps(state)
            assert state['headerLogoCount']==1 and state['footerLogoCount']==1 and state['canvasCount']==0
            assert not errors,errors
            if route=='/' and width in (390,1440,3840):
              page.screenshot(path=str(REPORT/('voorpagina-'+str(width)+'.png')),full_page=False)
          page.remove_all_listeners('pageerror')
        for width,height in [(390,844),(1440,900)]:
          page.set_viewport_size({'width':width,'height':height})
          direct=[OUT/'AVENZO.html']+sorted((OUT/'paginas').rglob('*.html'))
          assert len(direct)==9
          for path in direct:
            page.goto(path.as_uri(),wait_until='domcontentloaded');ready(page)
            state=snapshot(page);state.update(kind='direct-open-html',file=path.relative_to(OUT).as_posix(),width=width)
            records.append(state)
            assert not state['overflow'] and not state['brokenImages'],json.dumps(state)
            assert state['headerLogoCount']==1 and state['footerLogoCount']==1
        # Real local navigation, not a picture with decorative buttons.
        page.set_viewport_size({'width':390,'height':844})
        page.goto((OUT/'AVENZO.html').as_uri());ready(page)
        page.locator('.menu-toggle').click()
        assert page.locator('#mobile-menu').is_visible()
        page.keyboard.press('Escape')
        assert not page.locator('#mobile-menu').is_visible()
        interactions.append({'test':'mobile menu and Escape','passed':True})
        page.locator('.hero-actions a').click();page.wait_for_load_state('domcontentloaded');ready(page)
        assert page.locator('#project-form').count()==1
        interactions.append({'test':'homepage CTA opens the actual local contact form','passed':True})
        page.goto((OUT/'AVENZO.html').as_uri());ready(page)
        page.locator('.service-list-home a').first.click();page.wait_for_load_state('domcontentloaded');ready(page)
        assert page.locator('.service-detail').count()>0
        detail=page.locator('.service-detail').first
        original_open=detail.get_attribute('open') is not None
        detail.locator('summary').click()
        assert (detail.get_attribute('open') is not None)!=original_open
        interactions.append({'test':'service card opens actual local detail page; accordion works','passed':True})
        # Compare the original hero below the overlaid logo, with identical font loading.
        baseline=ROOT/'qa-original-baseline';shutil.copytree(ROOT/'original-source',baseline)
        for css in (baseline/'assets').rglob('*.css'):
          s=css.read_text();s=s.replace("url('/assets/body.woff')","url('https://avenzodigital.nl/assets/body.woff')");css.write_text(s)
        home=(baseline/'index.html').read_text()
        home=home.replace('href="/assets/body.woff"','href="https://avenzodigital.nl/assets/body.woff"')
        home=re.sub(r'<script\b[^>]*>(?:(?!</script>).)*__CF\$cv\$params(?:(?!</script>).)*</script>','',home,flags=re.S)
        (baseline/'index.html').write_text(home)
        bs,burl=serve(baseline)
        try:
          page.set_viewport_size({'width':1440,'height':900})
          pictures=[];geometries=[]
          for url in [burl+'/',base+'/']:
            page.goto(url);ready(page);box=page.locator('.home-hero').bounding_box()
            clip={'x':0,'y':120,'width':1440,'height':max(1,box['height']-120)}
            pictures.append(Image.open(io.BytesIO(page.screenshot(clip=clip))).convert('RGB'))
            geometries.append(page.locator('.hero-picture').bounding_box())
          difference=ImageChops.difference(pictures[0],pictures[1]);bbox=difference.getbbox()
          pixel={'viewport_width':1440,'compared_area':'Original hero below y=120; changed header/logo excluded','same_hero_geometry':geometries[0]==geometries[1],'pixel_identical_in_compared_area':bbox is None,'difference_bbox':bbox,'reference':'Unmodified preserved original hero, not the rejected native-4k renders'}
        finally:bs.shutdown()
        context.close();browser.close()
    finally:server.shutdown()
    summary={'hosting_page_checks':sum(x['kind']=='hosting-html' for x in records),'direct_open_page_checks':sum(x['kind']=='direct-open-html' for x in records),'all_layout_checks_passed':True,'interaction_checks':interactions,'original_hero_comparison':pixel,'raster_images_native_4k':False,'raster_images_modified':False,'deployed':False}
    (REPORT/'browsercontroles.json').write_text(json.dumps({'summary':summary,'checks':records},indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
