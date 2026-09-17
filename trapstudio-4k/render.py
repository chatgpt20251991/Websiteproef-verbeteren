"""Generate six native-size API outputs; no image upscaling and no deployment.
Run only with an owner-authorized OPENAI_API_KEY in the job environment.
Every output is saved before the next request. No automatic retry of paid requests.
"""
import base64, hashlib, io, json, os, sys, time, uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import requests
from PIL import Image

OUT = Path('trapstudio-4k-output')
OUT.mkdir(exist_ok=True)
MODEL = 'gpt-image-2.5-sunburst'
SIZE = '3840x2160'
QUALITY = 'max'
KEY = os.environ.get('OPENAI_API_KEY', '').strip()
API = 'https://api.openai.com/v1/images/'

def now():
    return datetime.now(timezone.utc).isoformat()

def digest(data):
    return hashlib.sha256(data).hexdigest()

def save_json(name, data):
    p = OUT / name
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    tmp.replace(p)

def fail(message):
    save_json('error.json', {'ok': False, 'message': message, 'time': now()})
    raise RuntimeError(message)

if not KEY:
    fail('OPENAI_API_KEY is not configured in this GitHub repository. No paid request was made.')

# Read-only access check. The key and complete error responses are never logged.
try:
    pre = requests.get('https://api.openai.com/v1/models/' + MODEL,
        headers={'Authorization': 'Bearer ' + KEY}, timeout=45)
    report = {'keyPresent': True, 'model': MODEL, 'status': pre.status_code,
              'accessible': pre.ok, 'checkedAt': now()}
    save_json('preflight.json', report)
    if not pre.ok:
        fail('Model access check failed: HTTP ' + str(pre.status_code) + '. No images requested.')
except requests.RequestException as exc:
    fail('Preflight connection failed: ' + type(exc).__name__)

MASTER = '''Create a premium Dutch staircase product visualization. Render the actual output directly at 3840 x 2160 pixels with crisp fine material detail, not a resized small image.
ONE SINGLE STRAIGHT FLIGHT of closed stairs, no zigzag, no turn, no L shape, no U shape, no floating disconnected steps. The bottom of the stairs is near x=0.26 to 0.51 of the frame and y=0.77 to 0.86. The top is near x=0.51 to 0.66 and y=0.09 to 0.16. The entire stair fits in frame. Exactly fourteen evenly spaced steps where possible, natural pale European oak treads and matching risers with physically plausible horizontal grain, matte oil finish, refined edge bevels. Black steel stringers with straight smooth sides, slim straight black handrail and clear frameless glass on the right. Warm 2700K recessed LED below every tread, soft warm light on risers and a plausible reflection near the foot of the stairs, never blown out.
Scene and composition: same luxurious modern European entrance hall as the reference when supplied. Eye-level architectural photo, natural 35mm perspective. Stair dominates center-left. On the far left a tall black-framed window and a large dark textured stone planter with an olive tree. Between the stairs and left window a tall off-white plaster wall with one slim abstract neutral artwork and a black up/down sconce. Behind and to the right of the stairs, a black console, vase, warm wall lights. At rear right a dining table with beige upholstered chairs and warm glass pendant lights; black-framed glazing onto a lush evening garden. At extreme right a partial cream sofa and round dark coffee table, with textured rug. Pale stone large-format tile floor, subtle glossy reflections. Dusk outside, warm welcoming light inside. Keep natural tonal range: readable oak pores, authentic grain, crisp steel edges, physically credible glass reflections and accurate contact shadows. Highly refined architectural photography, subtle material imperfections, no excessive bloom, no waxy smoothing. No text, people, watermark, UI or labels.'''

VARIANTS = {
 'oak-off': 'ONLY switch OFF all staircase LED strips. Remove their emitted light and local glow on the risers, glass and the floor near the foot of the stairs. Keep oak color, all normal wall lights, pendants, dusk sky and overall room exposure unchanged.',
 'walnut-on': 'ONLY change the oak treads and risers to natural walnut with authentic fine flowing walnut grain and a refined medium-brown matte-oiled tone. Keep warm LEDs ON. Do not change any steel, glass, stair structure, artwork, room lighting or furniture.',
 'smoked-on': 'ONLY change the oak treads and risers to smoked oak, a sophisticated deep brown with slight cool undertone and visible fine oak grain. Keep warm LEDs ON. Preserve the black steel, glass, room and exposure.',
 'black-off': 'ONLY change the treads and risers to black-stained oak with visible subtle fine oak grain, and switch OFF all staircase LED strips, removing their local light spill. Keep the normal room lights, dusk sky, exposure, black steel, glass and all furniture unchanged.',
 'whitewash-on': 'ONLY change the treads and risers to premium white-washed oak, a pale natural oak texture with subtle white pigment and visible fine grain, not plain paint. Keep warm LEDs ON, room lights and exposure unchanged. Preserve all black steel, glass and surroundings.'
}

# Recover a previous full-resolution reference if it still exists. A failed GET
# never creates a new render. Otherwise the clearly labelled layout reference is used.
reference = None
reference_name = None
old = 'https://oke-1-rhfe.onrender.com/v1/renders/master-1789254242550-5ea0e6343b5e.png'
try:
    r = requests.get(old, timeout=65)
    if r.ok and len(r.content) < 25_000_000:
        im = Image.open(io.BytesIO(r.content))
        if im.format == 'PNG' and im.width >= 2000:
            reference, reference_name = r.content, 'previous-api-master.png'
except Exception:
    pass
if reference is None:
    p = Path('trapstudio-4k/layout-reference.webp.b64')
    if p.exists():
        raw = base64.b64decode(p.read_text().strip(), validate=True)
        Image.open(io.BytesIO(raw)).verify()
        reference, reference_name = raw, 'layout-reference.webp'

save_json('plan.json', {
    'model': MODEL, 'requestedSize': SIZE, 'requestedQuality': QUALITY,
    'maxPaidRequests': 6, 'scope': ['oak-on'] + list(VARIANTS),
    'reference': reference_name, 'referenceSha256': digest(reference) if reference else None,
    'referenceIsLayoutOnly': reference_name == 'layout-reference.webp',
    'publication': 'GitHub artifact only; existing websites and Render are not modified',
    'upscalePerformed': False, 'createdAt': now()
})


def request_image(name, prompt, ref=None, ref_name='master.png', parent=None):
    started = now()
    client_id = 'trapstudio-4k-' + name + '-' + str(uuid.uuid4())
    headers = {'Authorization': 'Bearer ' + KEY, 'X-Client-Request-Id': client_id}
    fields = {'model': MODEL, 'prompt': prompt, 'size': SIZE,
              'quality': QUALITY, 'output_format': 'png', 'n': 1}
    endpoint = 'edits' if ref else 'generations'
    print('START ' + name + ' ' + endpoint + ' ' + SIZE, flush=True)
    try:
        if ref:
            mime = 'image/webp' if ref_name.endswith('.webp') else 'image/png'
            response = requests.post(API + endpoint, headers=headers, data=fields,
               files={'image': (ref_name, ref, mime)}, timeout=(30, 780))
        else:
            response = requests.post(API + endpoint, headers=headers,
               json=fields, timeout=(30, 780))
    except requests.RequestException as exc:
        # A timed out API call might still be billed: no blind retry.
        save_json(name + '-error.json', {'ok': False, 'phase': 'request', 'type': type(exc).__name__,
              'clientRequestId': client_id, 'mayStillHaveBeenProcessed': True})
        raise RuntimeError(name + ': connection failure; not retried') from None
    rid = response.headers.get('x-request-id') or response.headers.get('openai-request-id')
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    if not response.ok:
        err = payload.get('error', {})
        safe_error = {'ok': False, 'status': response.status_code, 'requestId': rid,
                      'code': err.get('code') if isinstance(err, dict) else None}
        save_json(name + '-error.json', safe_error)
        raise RuntimeError(name + ': API rejected request, HTTP ' + str(response.status_code))
    items = payload.get('data') or []
    if not items or not items[0].get('b64_json'):
        raise RuntimeError(name + ': no image in successful response')
    raw = base64.b64decode(items[0]['b64_json'], validate=True)
    im = Image.open(io.BytesIO(raw)); im.load()
    # SAVE ORIGINAL BYTES before doing anything else, never resize the source.
    (OUT / (name + '.png')).write_bytes(raw)
    meta = {'ok': im.size == (3840, 2160), 'asset': name,
        'source': 'OpenAI Images API', 'endpoint': '/v1/images/' + endpoint,
        'requestedModel': MODEL, 'responseModel': payload.get('model'),
        'requestedSize': SIZE, 'actualWidth': im.width, 'actualHeight': im.height,
        'requestedQuality': QUALITY, 'responseQuality': payload.get('quality'),
        'responseSize': payload.get('size'), 'format': im.format,
        'openaiRequestId': rid, 'clientRequestId': client_id,
        'sha256': digest(raw), 'bytes': len(raw), 'parentSha256': digest(ref) if ref else None,
        'parentAsset': parent or reference_name, 'upscaled': False,
        'usage': payload.get('usage'), 'startedAt': started, 'completedAt': now()}
    save_json(name + '.json', meta)
    if im.size != (3840, 2160) or im.format != 'PNG':
        raise RuntimeError(name + ': source dimensions/format mismatch; no upscaling fallback')
    if not rid:
        raise RuntimeError(name + ': missing API request ID')
    print('SAVED ' + name + ' ' + str(im.size) + ' bytes=' + str(len(raw)) + ' request=' + rid, flush=True)
    return raw, meta

try:
    master_prompt = MASTER
    if reference:
        master_prompt += '\nUse the supplied image as the composition and architecture reference. Reconstruct material microdetails at the requested 4K resolution. Do not move the camera, windows, walls, sofa, artwork, stair flight or furniture. Keep the staircase closed and straight. This is not a website screenshot; produce only the clean scene.'
    master, master_meta = request_image('oak-on', master_prompt, reference,
        reference_name or 'master.png')
    save_json('manifest.json', {'oak-on': master_meta})
    manifest = {'oak-on': master_meta}
    failures = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        tasks = {}
        for name, edit in VARIANTS.items():
            prompt = ('Edit this exact 4K master image with minimal local changes. Preserve identical camera, perspective, framing, stair position and geometry, all room objects, windows, art, plant, sofa, rug and fine details. ' + edit + '\nNo new scene, no camera movement, no step count change, no text or UI. Return the entire clean scene at 3840 x 2160, retaining sharp micro-detail. Small lighting changes only where physically required by the requested material or LED change.')
            tasks[executor.submit(request_image, name, prompt, master, 'master.png', 'oak-on')] = name
        for task in as_completed(tasks):
            name = tasks[task]
            try:
                _, meta = task.result(); manifest[name] = meta
                save_json('manifest.json', manifest)
            except Exception as exc:
                failures.append({'asset': name, 'message': str(exc)})
    save_json('completion.json', {'ok': not failures, 'completed': sorted(manifest),
             'failures': failures, 'actualSourceSize': SIZE, 'paidRequestsAttempted': 6})
    if failures:
        raise RuntimeError('One or more variants failed; originals and errors are preserved in the artifact.')
except Exception as exc:
    print('FAILED: ' + str(exc), flush=True)
    sys.exit(1)
