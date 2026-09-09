#!/usr/bin/env python3
"""Read current public Avenzo pages and prepare a patch artifact. Never publish."""
from __future__ import annotations
import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlparse
from apply import apply_directory

HERE=Path(__file__).resolve().parent
REPO=HERE.parent
ORIGIN='https://avenzodigital.nl'
PAGES=['/','/contact/','/studio/','/expertise/websites-conversie/',
       '/expertise/ai-automatisering/','/expertise/software-portalen/',
       '/expertise/data-dashboards/','/expertise/vindbaarheid-onderzoek/',
       '/expertise/testen-doorontwikkeling/']
LIMIT=2*1024*1024


def read_page(path: str) -> tuple[str,dict]:
    request=Request(ORIGIN+path,headers={'User-Agent':'AvenzoApprovedBrandRefresh/1.0'})
    with urlopen(request,timeout=25) as response:
        data=response.read(LIMIT+1)
        if response.status!=200 or 'text/html' not in response.headers.get('Content-Type',''):
            raise RuntimeError('Unexpected public page response: '+path)
        if urlparse(response.geturl()).hostname not in {'avenzodigital.nl','www.avenzodigital.nl'}:
            raise RuntimeError('Unexpected redirect: '+path)
    if len(data)>LIMIT:raise RuntimeError('Page exceeds safety size limit: '+path)
    text=data.decode('utf-8')
    return text,{'path':path,'status':200,'sha256':hashlib.sha256(data).hexdigest(),
                 'already_has_brand_refresh': 'data-avenzo-brand-refresh="20260909"' in text}


def main() -> None:
    output=REPO/'brand-refresh-candidate'
    observations=[]
    with tempfile.TemporaryDirectory() as temp:
        source=Path(temp)/'public-html';source.mkdir()
        for path in PAGES:
            text,observation=read_page(path)
            target=source/path.strip('/')/'index.html'
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(text,encoding='utf-8')
            observations.append(observation)
        manifest=apply_directory(source,output)
    for page in manifest['pages']:
        text=(output/page['path']).read_text(encoding='utf-8')
        assert text.count('<img src="/assets/avenzo-wordmark-20260909.svg"')==2
        assert text.count('data-avenzo-brand-refresh="20260909"')==1
        assert 'mailto:info@avenzodigital.nl' in text
        assert 'mailto:avenzodigitalgroup@gmail.com' in text
        assert '94554692' in text
        assert '__CF$cv$params' not in text
    report={'checked_at_utc':datetime.now(timezone.utc).isoformat(),
            'deployment_performed':False,'candidate_pages':len(manifest['pages']),
            'all_candidate_pages_validated':True,
            'current_public_pages':observations,
            'limitation':'Candidate patch, not a live deployment. Existing images/fonts/CSS/JS are not bundled. Original main content and form code preserved. Publish through the existing ChatGPT Site.'}
    (output/'validation-report.json').write_text(json.dumps(report,indent=2)+'\n')
    (output/'READ-ME-FIRST.txt').write_text('PATCH ONLY - NOT A COMPLETE WEBSITE\n\nThese nine HTML files and two new assets belong to the existing Avenzo site. Preserve all existing assets and routes. Do not replace the full site root with this folder. No fonts or existing images are bundled. Prefer applying the change to canonical source templates in the original ChatGPT Sites environment, then publish the existing Site. No DNS or mail changes are needed.\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
