#!/usr/bin/env python3
"""Add a file://-compatible preview; keep the clean production routes untouched."""
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit,unquote
from bs4 import BeautifulSoup
import os,json,shutil

root=Path('release').resolve();site=root/'website';pages=sorted(site.rglob('*.html'))
mapping={}
for src in pages:
    rel=src.relative_to(site)
    route='/'+rel.as_posix().removesuffix('index.html')
    target=root/'BEKIJK-WEBSITE.html' if route=='/' else root/'preview'/rel
    mapping[route]=target
    mapping['/'+rel.as_posix()]=target

def relative(target,directory):return os.path.relpath(target,directory).replace(os.sep,'/')
def convert(ref,directory):
    if not ref.startswith('/') or ref.startswith('//'):return ref
    u=urlsplit(ref);path=unquote(u.path)
    if path.startswith('/assets/'):target=site/path.lstrip('/')
    elif path in mapping:target=mapping[path]
    else:return ref
    return urlunsplit(('', '', relative(target,directory),u.query,u.fragment))

manifest=[]
for src in pages:
    route='/'+src.relative_to(site).as_posix().removesuffix('index.html');dest=mapping[route];dest.parent.mkdir(parents=True,exist_ok=True)
    doc=BeautifulSoup(src.read_text(),'html.parser');before=doc.main.get_text(' ',strip=True)
    for el in doc.select('[src],[href],[srcset]'):
        for attr in ('src','href'):
            if el.get(attr):el[attr]=convert(el[attr],dest.parent)
        if el.get('srcset'):
            parts=[]
            for item in el['srcset'].split(','):
                words=item.strip().split()
                if words:parts.append(' '.join([convert(words[0],dest.parent)]+words[1:]))
            el['srcset']=', '.join(parts)
    assert doc.main.get_text(' ',strip=True)==before
    dest.write_text(str(doc),encoding='utf-8');manifest.append({'production_route':route,'preview':dest.relative_to(root).as_posix()})
(root/'reports'/'portable-preview.json').write_text(json.dumps(manifest,indent=2))
notes=root/'LEESMIJ.txt'
notes.write_text('DIRECT BEKIJKEN ZONDER INSTALLATIE\nPak het ZIP-bestand eerst helemaal uit. Open daarna BEKIJK-WEBSITE.html.\nAlle negen pagina\u2019s en nieuwe beelden zijn vanuit die pagina bereikbaar.\nDe map website blijft de aparte publicatiemap met de oorspronkelijke nette routes.\n\n'+notes.read_text(),encoding='utf-8')
shutil.copy2(__file__,root/'source'/'portable_preview.py')
print('Direct-open preview created for all nine pages; no Python needed for viewing.')
