"""Native 4K catalog generation with bounded, metered spend and no paid retries.
Credentials remain in the existing GitHub secret. No websites are deployed.
"""
import base64, hashlib, io, json, os, sys, threading, uuid
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime, timezone
from pathlib import Path
import requests
from PIL import Image

ROOT=Path('trapstudio-max-generation'); OUT=Path('trapstudio-max-output'); OUT.mkdir(exist_ok=True)
PLAN=json.loads((ROOT/'plan.json').read_text())
KEY=os.environ.get('OPENAI_API_KEY','').strip()
LOCK=threading.Lock()
MANIFEST=json.loads((OUT/'manifest.json').read_text()) if (OUT/'manifest.json').exists() else {}
LEDGER=json.loads((OUT/'cost-ledger.json').read_text()) if (OUT/'cost-ledger.json').exists() else {'attempted':0,'estimatedUSD':0.0,'entries':[]}
def now(): return datetime.now(timezone.utc).isoformat()
def digest(raw): return hashlib.sha256(raw).hexdigest()
def write(name,value):
    p=OUT/name; tmp=p.with_suffix('.tmp'); tmp.write_text(json.dumps(value,indent=2,ensure_ascii=False));tmp.replace(p)
def cost(usage):
    if not isinstance(usage,dict) or 'output_tokens' not in usage: raise ValueError('Missing usage; halt further requests')
    detail=usage.get('input_tokens_details') or {}
    # Ignore cached discounts: conservatively bill all input at the uncached rate.
    image=detail.get('image_tokens',0)
    text=detail.get('text_tokens',max(0,usage.get('input_tokens',0)-image))
    return (text*5+image*8+usage['output_tokens']*30)/1_000_000

def request(job):
    id=job['id']; parent=job['parent']; rawref=None
    if parent:
        path=Path('existing-4k')/(parent.split(':',1)[1]+'.png') if parent.startswith('existing:') else OUT/(parent+'.png')
        rawref=path.read_bytes(); im=Image.open(io.BytesIO(rawref)); assert im.size==(3840,2160)
    client='trapstudio-max-'+id+'-'+str(uuid.uuid4()); started=now()
    fields={'model':PLAN['model'],'prompt':job['prompt'],'size':PLAN['size'],'quality':PLAN['quality'],'output_format':'png','n':1}
    headers={'Authorization':'Bearer '+KEY,'X-Client-Request-Id':client}
    endpoint='edits' if rawref else 'generations'
    with LOCK:
        LEDGER['attempted']+=1
        assert LEDGER['attempted']<=PLAN['maxPaidRequests']
        LEDGER['entries'].append({'id':id,'clientRequestId':client,'startedAt':started,'state':'submitted'})
        write('cost-ledger.json',LEDGER)
    print('START '+id,flush=True)
    try:
        if rawref:
            response=requests.post('https://api.openai.com/v1/images/'+endpoint,headers=headers,data=fields,files={'image':('reference.png',rawref,'image/png')},timeout=(30,780))
        else:
            response=requests.post('https://api.openai.com/v1/images/'+endpoint,headers=headers,json=fields,timeout=(30,780))
        rid=response.headers.get('x-request-id') or response.headers.get('openai-request-id')
        if not response.ok:
            try:
                err=response.json().get('error',{})
            except Exception: err={}
            write(id+'-api-error.json',dict(status=response.status_code,requestId=rid,code=err.get('code'),type=err.get('type'),message=str(err.get('message',''))[:700]))
            raise RuntimeError('HTTP '+str(response.status_code)+'; request '+str(rid)+'; code '+str(err.get('code')))
        payload=response.json(); usd=cost(payload.get('usage'))
        with LOCK:
            LEDGER['estimatedUSD']+=usd
            entry=next(x for x in LEDGER['entries'] if x['id']==id)
            entry.update(state='received',estimatedUSD=usd,requestId=rid)
            write('cost-ledger.json',LEDGER)
        raw=base64.b64decode(payload['data'][0]['b64_json'],validate=True)
        (OUT/(id+'.png')).write_bytes(raw)
        im=Image.open(io.BytesIO(raw));im.load()
        meta=dict(ok=im.size==(3840,2160) and im.format=='PNG' and bool(rid),asset=id,source='OpenAI Images API',endpoint='/v1/images/'+endpoint,requestedModel=PLAN['model'],responseModel=payload.get('model'),requestedSize=PLAN['size'],actualWidth=im.width,actualHeight=im.height,requestedQuality=PLAN['quality'],responseQuality=payload.get('quality'),format=im.format,openaiRequestId=rid,clientRequestId=client,sha256=digest(raw),bytes=len(raw),parentSha256=digest(rawref) if rawref else None,parentAsset=parent,upscaled=False,usage=payload.get('usage'),estimatedUSD=usd,prompt=job['prompt'],startedAt=started,completedAt=now())
        write(id+'.json',meta)
        if not meta['ok']: raise RuntimeError('4K source verification failed')
        if usd>PLAN['reserveUSDPerInFlightRequest']: raise RuntimeError('Request exceeded conservative cost reservation; stopping batch')
        with LOCK:
            MANIFEST[id]=meta;write('manifest.json',MANIFEST)
        print('SAVED '+id+' estimatedUSD='+str(round(usd,5)),flush=True)
        return id
    except Exception as exc:
        # Never print response bodies or credentials. An uncertain paid request is not retried.
        write(id+'-error.json',dict(asset=id,errorType=type(exc).__name__,message=str(exc)[:160] if isinstance(exc,(RuntimeError,ValueError)) else 'Network or decoding failure; no retry',clientRequestId=client,paidRequestMayHaveCompleted=True))
        raise RuntimeError(id+': '+type(exc).__name__+'; no retry') from None

def main():
    if not KEY: raise RuntimeError('Existing repository credential is unavailable')
    if os.environ.get('GITHUB_RUN_ATTEMPT','1')!='1': raise RuntimeError('Automatic reruns disabled to prevent duplicate paid requests')
    pre=requests.get('https://api.openai.com/v1/models/'+PLAN['model'],headers={'Authorization':'Bearer '+KEY},timeout=45)
    write('preflight.json',dict(model=PLAN['model'],status=pre.status_code,time=now()))
    if not pre.ok: raise RuntimeError('Model access check failed before paid requests')
    write('plan.json',PLAN)
    phase=sys.argv[1] if len(sys.argv)>1 else 'all'
    pending=[j for j in PLAN['jobs'] if j['id'] not in MANIFEST and (phase=='all' or (phase=='masters' and not j['parent']) or (phase=='variants' and j['parent']))]
    failure=[]; reserved=0
    workers=int(os.environ.get('TRAPSTUDIO_CONCURRENCY','4'))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        running={}
        while pending or running:
            for j in list(pending):
                parent=j['parent'];ready=not parent or parent.startswith('existing:') or parent in MANIFEST
                if failure or len(running)>=workers: break
                if not ready: continue
                if LEDGER['estimatedUSD']+reserved+PLAN['reserveUSDPerInFlightRequest']>PLAN['usdSpendCeiling']: continue
                pending.remove(j);reserved+=PLAN['reserveUSDPerInFlightRequest'];running[pool.submit(request,j)]=j['id']
            if not running:
                if pending: failure.append('Budget ceiling or unavailable reference; remaining requests were not submitted')
                break
            completed,_=wait(running,return_when=FIRST_COMPLETED)
            for f in completed:
                id=running.pop(f);reserved-=PLAN['reserveUSDPerInFlightRequest']
                try:f.result()
                except Exception as exc:failure.append(str(exc))
            if failure and not running:break
    write('completion-'+phase+'.json',dict(ok=not failure,phase=phase,completed=len(MANIFEST),pending=[x['id'] for x in pending],failures=failure,estimatedUSD=LEDGER['estimatedUSD'],conservativeEURAllowance=LEDGER['estimatedUSD']*PLAN['conservativeEURPerUSD'],userBudgetEUR=50,paidRequestsAttempted=LEDGER['attempted'],completedAt=now()))
    if failure:raise RuntimeError('; '.join(failure))
if __name__=='__main__':
    try:main()
    except Exception as exc:print('STOPPED: '+str(exc),flush=True);sys.exit(1)
