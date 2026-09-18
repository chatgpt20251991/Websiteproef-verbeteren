#!/usr/bin/env python3
"""Generate one native Avenzo 4K image using the existing Actions AVIN2 secret.

One request only: no retry, resizing, alternative model, or deployment.
Public reference bytes and exact dimensions are pinned before any paid request.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import struct
import sys
import time
import warnings
import zlib

import requests
from PIL import Image

MODEL = "gpt-image-2.5-sunburst"
ENDPOINT = "https://api.openai.com/v1/images/edits"
REFERENCE_ROOT = "https://avenzodigital.nl/assets/qhd/"
QUALITY = "max"
USER_AGENT = "Avenzo-Owner-Asset-Verification/1.0"
MAX_REFERENCE_BYTES = 26_000_000
MAX_RESPONSE_BYTES = 100 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 20_000_000
warnings.simplefilter("error", Image.DecompressionBombWarning)

# Reference images were fetched and fully decoded on 18 September 2026.
ASSETS = {'hero-desktop-apps': ('hero-desktop-apps-2560.webp',
                       (3840, 2160),
                       'Preserve the exact wide architectural photograph: very dark sweeping cantilever '
                       'of board-formed concrete on the left; glossy black stone floor with warm '
                       'uplights; the large bordeaux-red curving bridge across the upper half; glass '
                       'windows and restrained trees. The polished metal 3D Configurator display, AI '
                       'Studio phone, code enclosure and AI enclosure remain grouped on the RIGHT in '
                       'precisely the same relative scale and perspective. The left 44 percent stays '
                       'empty architecture for separate HTML copy. Do not shift the hardware to the '
                       'center. Keep the building shown INSIDE the configurator screen, readable title '
                       '3D Configurator, readable title AI Studio on the phone, original detailed UI '
                       'and cables.'),
 'hero-mobile-apps': ('hero-mobile-apps-1440.webp',
                      (2160, 3840),
                      'Match this portrait version of the original architecture and hardware group. The '
                      'same 3D Configurator display and phone must remain prominent, centered in the '
                      'upper-middle of the portrait, fully visible. Preserve the curved bordeaux bridge '
                      'above, concrete walls, trees and reflective black floor below. Extend the '
                      'existing architecture vertically only as necessary for 9:16, never add objects '
                      'or change the product design. This is only a portrait visual, not a mobile '
                      'webpage.'),
 'service-web': ('service-web-2560.webp',
                 (3840, 2160),
                 'Recreate exactly this brushed-metal desktop browser display, smaller upright phone in '
                 'front at right, flat metal plinth and layered panels behind. The screens show the '
                 'original red architectural bridge website. Preserve the neutral pale stone room, '
                 'sunlight from upper left, polished reflections, burgundy accents and exact device '
                 'composition. Extend the existing pale room subtly at the sides for 16:9, do not '
                 'change the subjects.'),
 'service-ai': ('service-ai-2560.webp',
                (3840, 2160),
                'Recreate exactly the low brushed-metal AI compute block on a square base on the left, '
                'three burgundy pipes extending right to a thin upright silver workflow panel. The '
                'panel has three original steps Analyse, Verbind, Actie and fine outline icons. Same '
                'clean pale stone room, daylight upper left, subtle reflections, same exact relative '
                'positions and scale. No extra devices. Extend only the plain room at the sides for '
                '16:9.'),
 'service-software': ('service-software-2560.webp',
                      (3840, 2160),
                      'Recreate the exact stack of layered silver software panels: front short wide '
                      'project and code panel, middle browser panel, taller dashboard behind, and low '
                      'code enclosure on the right connected with parallel burgundy pipes. Same pale '
                      'stone studio, sunlight, reflections, brushed aluminium and burgundy details. '
                      'Preserve front-to-back arrangement, perspective, and product proportions. Extend '
                      'only plain side background for 16:9.'),
 'service-data': ('service-data-2560.webp',
                  (3840, 2160),
                  'Recreate the exact silver-framed dashboard with burgundy line chart and small lower '
                  'charts, rear layered metal module and the four physical bar-chart columns on a small '
                  'metal plinth at front-right. Preserve the pale stone floor and wall, diagonal soft '
                  'daylight, precise brush-metal surfaces, muted burgundy bars and original '
                  'arrangement. Extend only neutral side margins for 16:9.'),
 'service-search': ('service-search-2560.webp',
                    (3840, 2160),
                    'Recreate the precise thick upright brushed-metal search ring on the left with a '
                    'horizontal search field through its center reading Zoeken. On the right keep the '
                    'two layered silver-framed results panels linked by three parallel burgundy pipes. '
                    'Same neutral stone room, diagonal sunlight and reflections, exact metal thickness, '
                    'camera view and scale. Extend only plain side room for 16:9.'),
 'service-testing': ('service-testing-2560.webp',
                     (3840, 2160),
                     'Recreate the exact silver desktop quality-testing UI panel on its stepped metal '
                     'base, upright phone foreground at right, silver code enclosure and AI/module at '
                     'right, burgundy connecting pipes. Preserve original monitor/phone placement and '
                     'testing checklist interface, muted palette, pale stone studio, soft daylight and '
                     'precise reflections. Extend only neutral margins for 16:9.'),
 'software-closeup': ('software-closeup-2560.webp',
                      (3840, 2160),
                      'Recreate precisely this close elevated macro view of the layered metal '
                      'application panels, the brushed AI cube behind, and multiple fine burgundy '
                      'cables connecting modules. Keep the very close diagonal crop of the foreground '
                      'project interface, metal thicknesses, frame spacing, exact camera angle, tonal '
                      'contrast and cinematic material details. No zooming out and no rearrangement.')}
REFERENCE_HASHES = {'hero-desktop-apps': '17a507d95c16f3416740c6a6e7a2c9883d7db86a9cb9e14276991ee5079a92d5',
 'hero-mobile-apps': '94c0c235a95f846035e616e0908a2e145fb124d3f1da5b194b7e3f789bd91ec3',
 'service-web': 'c4864f04097f4a1720531ce84f15af0d0f28d7a0e7aafb871f452ebf74164e8b',
 'service-ai': '4a0dcc7c4f65cc79d10862746320ceeb33697ae47391a62bbac6528bc43cd0ae',
 'service-software': 'd2ff576913edbe83ad657ed1dfd555de3a6dfc0d7d2c93c78c5a8ed4c1c1205f',
 'service-data': 'f0d37044adf65a206139de9acfd1444ab9d2366a72b0d17dbc59a3a48710342c',
 'service-search': 'f4db837a9b451cb5038895ca9a85b3a76655635ef486c0162bf10fe992617201',
 'service-testing': '0e52130bafbded8bf8894a833fc5a245ea06b927d4a93b618255e5c568de2e3f',
 'software-closeup': 'ba1140227bae21b3d290ba568c3e80d8eb20f4a5dbebc3520a51db0e5e8eb72d'}
BASE_PROMPT = 'Create a NEW, high-detail photorealistic reconstruction of the attached original Avenzo visual at the requested native output dimensions. The reference is the strict composition and art-direction master, NOT loose inspiration. Keep the original visual recognizably one-to-one: same camera viewpoint, same objects, same positions, same background, same lighting direction, same materials and same bordeaux/metal color scheme. Reconstruct fine surface texture, light reflections, polished bevels and legible device interface details directly in the new image. Do not simplify into primitive 3D boxes. Do not invent a different design. No blur, painted styling, exaggerated bloom or cartoon materials.\nCRITICAL: Output only the photographic scene. DO NOT add webpage headings, navigation bars, buttons, an Avenzo logo floating over the scene, footer, white page sections, borders or browser chrome outside the physical displays. The actual website text, logo, links and buttons will be separate HTML and SVG. Preserve text and UI that is physically INSIDE the pictured device screens. No watermark or advertising claims.\n'


class SafeFailure(Exception):
    """Only fixed, locally authored error codes may cross this boundary."""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_bounded(response, limit: int, code: str) -> bytes:
    chunks = []
    total = 0
    for chunk in response.iter_content(65536):
        total += len(chunk)
        if total > limit:
            raise SafeFailure(code)
        chunks.append(chunk)
    return b"".join(chunks)


def numeric_usage(value):
    """Allow known usage names and finite numbers; exclude API strings entirely."""
    fields = {"input_tokens", "output_tokens", "total_tokens", "image_tokens",
              "text_tokens", "cached_tokens", "input_tokens_details",
              "output_tokens_details", "cached_tokens_details"}
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value if math.isfinite(value) and 0 <= value < 10**15 else None
    if isinstance(value, dict):
        return {name: numeric_usage(item) for name, item in value.items() if name in fields}
    return None


def validate_reference(asset: str, raw: bytes) -> tuple[bytes, tuple[int, int]]:
    if sha(raw) != REFERENCE_HASHES[asset]:
        raise SafeFailure("reference_hash_mismatch")
    expected = (1440, 2560) if asset == "hero-mobile-apps" else (2560, 1440)
    try:
        with Image.open(io.BytesIO(raw)) as im:
            if im.format != "WEBP" or im.size != expected or getattr(im, "n_frames", 1) != 1:
                raise SafeFailure("reference_format_or_dimensions_invalid")
            im.verify()
        with Image.open(io.BytesIO(raw)) as im:
            im.load()
            output = io.BytesIO()
            # A lossless format conversion only. No pixel dimensions are changed.
            im.convert("RGB").save(output, "PNG")
            return output.getvalue(), im.size
    except SafeFailure:
        raise
    except Exception:
        raise SafeFailure("reference_decode_failed") from None


def fetch_reference(asset: str) -> tuple[bytes, bytes, tuple[int, int]]:
    filename = ASSETS[asset][0]
    try:
        with requests.Session() as session:
            # Do not inherit .netrc credentials, auth headers or proxy credentials.
            session.trust_env = False
            with session.get(REFERENCE_ROOT + filename,
                             headers={"User-Agent": USER_AGENT},
                             timeout=(30, 90), allow_redirects=False, stream=True) as response:
                if response.status_code != 200:
                    raise SafeFailure("reference_http_error")
                if response.headers.get("Content-Type", "").split(";")[0].strip() != "image/webp":
                    raise SafeFailure("reference_content_type_invalid")
                raw = read_bounded(response, MAX_REFERENCE_BYTES, "reference_too_large")
        png, dimensions = validate_reference(asset, raw)
        return raw, png, dimensions
    except requests.RequestException:
        raise SafeFailure("reference_transport_failed") from None


def png_dimensions(raw: bytes) -> tuple[int, int]:
    """Check complete PNG structure, CRCs, a single frame, and decoded pixels."""
    if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        raise SafeFailure("output_not_png")
    offset = 8
    dimensions = None
    seen_data = False
    ended = False
    while offset + 12 <= len(raw):
        length = struct.unpack_from(">I", raw, offset)[0]
        kind = raw[offset + 4:offset + 8]
        end = offset + 12 + length
        if end > len(raw):
            raise SafeFailure("output_png_truncated")
        data = raw[offset + 8:offset + 8 + length]
        expected_crc = struct.unpack_from(">I", raw, offset + 8 + length)[0]
        if zlib.crc32(kind + data) & 0xffffffff != expected_crc:
            raise SafeFailure("output_png_crc_invalid")
        if offset == 8:
            if kind != b"IHDR" or length != 13:
                raise SafeFailure("output_png_header_invalid")
            dimensions = struct.unpack_from(">II", data)
            if min(dimensions) < 1 or max(dimensions) > 7680 or dimensions[0] * dimensions[1] > 20_000_000:
                raise SafeFailure("output_dimensions_out_of_bounds")
        elif kind == b"IHDR":
            raise SafeFailure("output_png_duplicate_header")
        if kind in (b"acTL", b"fcTL", b"fdAT"):
            raise SafeFailure("output_animation_not_allowed")
        if kind == b"IDAT":
            seen_data = True
        if kind == b"IEND":
            if length or not seen_data or end != len(raw):
                raise SafeFailure("output_png_end_invalid")
            ended = True
            break
        offset = end
    if not ended or dimensions is None:
        raise SafeFailure("output_png_incomplete")
    try:
        with Image.open(io.BytesIO(raw)) as im:
            if im.format != "PNG" or im.size != dimensions:
                raise SafeFailure("output_png_decode_mismatch")
            im.verify()
        with Image.open(io.BytesIO(raw)) as im:
            im.load()
    except SafeFailure:
        raise
    except Exception:
        raise SafeFailure("output_png_decode_failed") from None
    return dimensions


def request_image(key: str, prompt: str, size: tuple[int, int], reference: bytes, report: dict):
    fields = {"model": MODEL, "prompt": prompt, "size": f"{size[0]}x{size[1]}",
              "quality": QUALITY, "n": "1", "output_format": "png", "background": "opaque"}
    try:
        with requests.Session() as session:
            session.trust_env = False
            # requests uses zero automatic retries by default. Never retry this POST.
            with session.post(ENDPOINT,
                              headers={"Authorization": "Bearer " + key, "User-Agent": USER_AGENT},
                              data=fields, files={"image[]": ("avenzo-reference.png", reference, "image/png")},
                              timeout=(30, 1200), allow_redirects=False, stream=True) as response:
                report["http_status"] = response.status_code
                if response.status_code != 200:
                    codes = {400: "api_request_rejected", 401: "api_authentication_failed",
                             403: "api_access_denied", 404: "api_model_or_endpoint_unavailable",
                             429: "api_rate_limit_or_quota", 500: "api_server_error",
                             502: "api_server_error", 503: "api_server_error"}
                    raise SafeFailure(codes.get(response.status_code, "api_http_error"))
                raw = read_bounded(response, MAX_RESPONSE_BYTES, "api_response_too_large")
                request_id = response.headers.get("x-request-id", "")
                if re.fullmatch(r"req_[0-9a-f]{16,64}", request_id) and key not in request_id:
                    report["request_id"] = request_id
        try:
            payload = json.loads(raw)
            entries = payload.get("data") if isinstance(payload, dict) else None
            if not isinstance(entries, list) or len(entries) != 1 or not isinstance(entries[0], dict):
                raise SafeFailure("api_single_image_missing")
            encoded = entries[0].get("b64_json")
            if not isinstance(encoded, str):
                raise SafeFailure("api_base64_missing")
            image = base64.b64decode(encoded, validate=True)
            report["usage"] = numeric_usage(payload.get("usage"))
            return image
        except SafeFailure:
            raise
        except Exception:
            raise SafeFailure("api_response_invalid") from None
    except requests.RequestException:
        # A timeout may already have incurred cost. Never resubmit automatically.
        raise SafeFailure("api_transport_uncertain_no_retry") from None


def run(asset: str, output: Path, validate_only: bool = False) -> int:
    started = time.monotonic()
    name, size, extra = ASSETS[asset]
    report = {"asset": asset, "model_requested": MODEL, "quality_requested": QUALITY,
              "endpoint": ENDPOINT, "requested_dimensions": list(size),
              "reference_url": REFERENCE_ROOT + name, "reference_sha256": REFERENCE_HASHES[asset],
              "requests_submitted": 0, "image_generated": False, "usage": None,
              "resizing_performed": False, "upscaling_performed_by_build": False,
              "deployment_performed": False, "automatic_retries": 0, "status": "checking"}
    reportfile = output / (asset + ".json")
    target = output / (asset + ".png")
    acquired = False
    code = 1
    try:
        attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "1")
        if not re.fullmatch(r"[0-9]{1,6}", attempt) or int(attempt) != 1:
            raise SafeFailure("github_rerun_blocked")
        report["github_run_attempt"] = 1
        for variable, field, pattern in (("GITHUB_SHA", "commit_sha", r"[0-9a-f]{40}"),
                                          ("GITHUB_RUN_ID", "github_run_id", r"[0-9]{1,30}")):
            value = os.environ.get(variable, "")
            if re.fullmatch(pattern, value):
                report[field] = value
        key = os.environ.get("OPENAI_API_KEY", "").strip()
        report["api_key_configured"] = bool(key)
        if not validate_only and not key:
            raise SafeFailure("api_key_missing")
        output.mkdir(parents=True, exist_ok=True)
        if target.exists() or reportfile.exists():
            raise SafeFailure("existing_output_or_attempt_blocked")
        # Exclusive creation guards duplicate invocations sharing this output directory.
        with reportfile.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
        acquired = True
        raw, reference, reference_size = fetch_reference(asset)
        report.update(reference_dimensions=list(reference_size), reference_bytes=len(raw),
                      reference_png_sha256=sha(reference), reference_png_dimensions=list(reference_size))
        prompt = BASE_PROMPT + extra + f"\nFinal native output: {size[0]} x {size[1]} pixels."
        report["prompt"] = prompt
        if validate_only:
            report["status"] = "reference_verified_no_api_request"
            code = 0
        else:
            report["requests_submitted"] = 1
            report["status"] = "request_submitted"
            reportfile.write_text(json.dumps(report, indent=2), encoding="utf-8")
            image = request_image(key, prompt, size, reference, report)
            actual = png_dimensions(image)
            report.update(image_generated=True, actual_dimensions=list(actual),
                          output_sha256=sha(image), output_bytes=len(image))
            # Preserve the exact API response image bytes, including metadata.
            filename = target if actual == size else output / (asset + "-dimension-mismatch.png")
            with filename.open("xb") as handle:
                handle.write(image)
            report["output_filename"] = filename.name
            if actual != size:
                raise SafeFailure("native_output_dimensions_mismatch")
            report["status"] = "native_image_received_pending_visual_review"
            code = 0
    except SafeFailure as exc:
        report.update(status="stopped", error=str(exc))
    except Exception:
        report.update(status="stopped", error="unexpected_internal_error_no_retry")
    finally:
        report["seconds"] = round(time.monotonic() - started, 2)
        if acquired:
            try:
                reportfile.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
            except Exception:
                report.update(status="stopped", error="report_write_failed_no_retry")
                code = 1
        print(json.dumps({k: v for k, v in report.items() if k != "prompt"}, allow_nan=False), flush=True)
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", choices=ASSETS, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--validate-only", action="store_true",
                        help="Verify the pinned public reference without submitting an image request.")
    args = parser.parse_args()
    return run(args.asset, args.output, args.validate_only)


if __name__ == "__main__":
    sys.exit(main())
