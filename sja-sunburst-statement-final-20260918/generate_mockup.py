"""One Sunburst MAX mockup using the owner's existing API integration."""
import argparse
import base64
import io
import json
import os
from pathlib import Path
import re
import time
import requests
from PIL import Image
from transport import MODEL, ENDPOINT, QUALITY, SafeFailure, sha, read_bounded, numeric_usage, png_dimensions

ROOT = Path(__file__).resolve().parent
SIZE = (2160, 3840)
REFERENCES = (
    ("statement-reference.png", "image/png"),
)

def run(validate_only=False):
    output = Path("sunburst-statement-final-output")
    output.mkdir(exist_ok=True)
    reportpath = output / "generation-report.json"
    report = {"model_requested": MODEL, "quality_requested": QUALITY,
              "requested_dimensions": list(SIZE), "endpoint": ENDPOINT,
              "image_generated": False, "requests_submitted": 0,
              "automatic_retries": 0, "resizing_performed": False,
              "deployment_performed": False, "references": []}
    started = time.monotonic()
    code = 1
    try:
        if os.environ.get("GITHUB_RUN_ATTEMPT", "1") != "1":
            raise SafeFailure("rerun_blocked")
        if reportpath.exists():
            raise SafeFailure("existing_attempt_blocked")
        prompt = (ROOT / "prompt.txt").read_text(encoding="utf-8")
        files = []
        for name, mime in REFERENCES:
            raw = (ROOT / name).read_bytes()
            with Image.open(io.BytesIO(raw)) as im:
                dimensions = im.size
                im.verify()
            if len(raw) > 26000000:
                raise SafeFailure("reference_too_large")
            files.append(("image[]", (name, raw, mime)))
            report["references"].append({"name": name, "sha256": sha(raw), "dimensions": list(dimensions)})
        report["prompt_sha256"] = sha(prompt.encode("utf-8"))
        if validate_only:
            print(json.dumps({"status": "validated_without_api_request", **report}))
            return 0
        key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not key:
            raise SafeFailure("api_key_missing")
        report["requests_submitted"] = 1
        report["status"] = "request_submitted"
        reportpath.write_text(json.dumps(report, indent=2), encoding="utf-8")
        fields = {"model": MODEL, "prompt": prompt, "size": "2160x3840",
                  "quality": QUALITY, "n": "1", "output_format": "png", "background": "opaque"}
        with requests.Session() as session:
            session.trust_env = False
            with session.post(ENDPOINT, headers={"Authorization": "Bearer " + key},
                              data=fields, files=files, timeout=(30,1200),
                              allow_redirects=False, stream=True) as response:
                report["http_status"] = response.status_code
                if response.status_code != 200:
                    raise SafeFailure("api_request_failed_" + str(response.status_code))
                request_id = response.headers.get("x-request-id", "")
                if re.fullmatch(r"req_[0-9a-f]{16,64}", request_id) and key not in request_id:
                    report["request_id"] = request_id
                raw = read_bounded(response, 100*1024*1024, "api_response_too_large")
        payload = json.loads(raw)
        entries = payload.get("data", [])
        if len(entries) != 1 or not isinstance(entries[0].get("b64_json"), str):
            raise SafeFailure("single_image_missing")
        image = base64.b64decode(entries[0]["b64_json"], validate=True)
        actual = png_dimensions(image)
        target = output / "startjouwautobedrijf-statement-2026.png"
        target.write_bytes(image)
        report.update(image_generated=True, actual_dimensions=list(actual),
                      output_sha256=sha(image), output_bytes=len(image),
                      output_filename=target.name, usage=numeric_usage(payload.get("usage")))
        (output / "prompt.txt").write_text(prompt, encoding="utf-8")
        if actual != SIZE:
            raise SafeFailure("native_dimensions_mismatch")
        report["status"] = "native_image_received_pending_visual_review"
        code = 0
    except SafeFailure as exc:
        report.update(status="stopped", error=str(exc))
    except requests.RequestException:
        report.update(status="stopped", error="transport_uncertain_no_retry")
    except Exception:
        report.update(status="stopped", error="internal_error_no_retry")
    finally:
        report["seconds"] = round(time.monotonic() - started, 2)
        if not validate_only:
            reportpath.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps(report, allow_nan=False), flush=True)
    return code

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    raise SystemExit(run(parser.parse_args().validate_only))

