#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import urlsplit,unquote
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import json

root=Path('release').resolve();routes=json.loads((root/'reports'/'portable-preview.json').read_text());errors=[];checks=[]
for item in routes:
    file=root/item['preview'];doc=BeautifulSoup(file.read_text(),'html.parser')
    for el in doc.select('[src],[href],[srcset]'):
        refs=[el.get('src',''),el.get('href','')]+[x.strip().split()[0] for x in el.get('srcset','').split(',') if x.strip()]
        for ref in refs:
            u=urlsplit(ref)
            if u.scheme or u.netloc or not u.path:continue
            target=(file.parent/unquote(u.path)).resolve()
            if not target.is_relative_to(root) or not target.is_file():errors.append({'file':item['preview'],'missing':ref})
with sync_playwright() as pw:
    browser=pw.chromium.launch()
    for width,height in [(390,844),(1440,1000)]:
        context=browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce');page=context.new_page()
        for item in routes:
            js=[];page.on('pageerror',lambda e:js.append(str(e)))
            page.goto((root/item['preview']).as_uri(),wait_until='domcontentloaded')
            page.evaluate("async()=>{for(const i of document.images)i.loading='eager';await Promise.all(Array.from(document.images).map(i=>i.decode().catch(()=>{})));}")
            data=page.evaluate("()=>({h1:document.querySelectorAll('h1').length,broken:Array.from(document.images).filter(i=>!i.complete||!i.naturalWidth).map(i=>i.src),overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1})")
            ok=data['h1']==1 and not data['broken'] and not data['overflow'] and not js
            checks.append({'file':item['preview'],'width':width,'passed':ok,**data,'js_errors':list(js)})
            if not ok:errors.append(checks[-1])
        context.close()
    browser.close()
report={'passed':len(checks)==18 and not errors,'checks':checks,'errors':errors,'server_required':False,'deployment_performed':False}
(root/'reports'/'portable-validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'checks':len(checks),'passed':report['passed'],'errors':errors},indent=2))
if not report['passed']:raise SystemExit(1)
