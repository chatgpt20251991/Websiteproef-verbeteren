"""Generate the owner's Sunburst MAX responsive concept suite; one request per asset."""
import argparse, base64, io, json, os, re, time
from pathlib import Path
import requests
from PIL import Image
from transport import MODEL, ENDPOINT, QUALITY, SafeFailure, sha, read_bounded, numeric_usage, png_dimensions
ROOT = Path(__file__).resolve().parent
OUT = Path("sunburst-suite-output")
ASSETS = {
"01-dashboard-desktop": ((3840,2160), ["user-copy-reference.png","original-platform-reference.jpg"]),
"02-landing-desktop": ((2160,3840), ["@01-dashboard-desktop","user-copy-reference.png"]),
"03-lesson-desktop": ((3840,2160), ["@01-dashboard-desktop"]),
"04-landing-mobile-top": ((1280,3840), ["@02-landing-desktop","@01-dashboard-desktop"]),
"05-landing-mobile-bottom": ((1280,3840), ["@04-landing-mobile-top","@02-landing-desktop"]),
"06-dashboard-mobile": ((1776,3840), ["@01-dashboard-desktop"]),
"07-lesson-mobile": ((1776,3840), ["@03-lesson-desktop"]),
}
STAGES = {"master":["01-dashboard-desktop"],
          "desktop":["02-landing-desktop","03-lesson-desktop"],
          "mobile":["04-landing-mobile-top","05-landing-mobile-bottom","06-dashboard-mobile","07-lesson-mobile"]}

def generate(asset, validate_only=False):
    size, refs = ASSETS[asset]
    OUT.mkdir(exist_ok=True)
    reportpath = OUT / (asset + ".json")
    report = {"asset":asset, "model_requested":MODEL, "quality_requested":QUALITY,
              "requested_dimensions":list(size), "endpoint":ENDPOINT, "requests_submitted":0,
              "image_generated":False, "automatic_retries":0, "resizing_performed":False,
              "deployment_performed":False, "references":[]}
    started = time.monotonic()
    acquired = False
    code = 1
    try:
        if os.environ.get("GITHUB_RUN_ATTEMPT", "1") != "1":
            raise SafeFailure("rerun_blocked")
        if reportpath.exists() or (OUT / (asset + ".png")).exists():
            raise SafeFailure("existing_attempt_blocked")
        prompt = (ROOT / "prompts" / (asset + ".txt")).read_text(encoding="utf-8")
        files = []
        for ref in refs:
            path = OUT / (ref[1:] + ".png") if ref.startswith("@") else ROOT / ref
            raw = path.read_bytes()
            with Image.open(io.BytesIO(raw)) as im:
                dimensions = im.size
                im.verify()
            if len(raw) > 26000000:
                raise SafeFailure("reference_too_large")
            mime = "image/jpeg" if path.suffix.lower() == ".jpg" else "image/png"
            files.append(("image[]",(path.name,raw,mime)))
            report["references"].append({"name":path.name,"sha256":sha(raw),"dimensions":list(dimensions)})
        report["prompt_sha256"] = sha(prompt.encode("utf-8"))
        if validate_only:
            report["status"] = "validated_without_api_request"
            print(json.dumps(report),flush=True)
            return 0
        key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not key:
            raise SafeFailure("api_key_missing")
        with reportpath.open("x",encoding="utf-8") as handle:
            json.dump(report,handle)
        acquired = True
        report.update(requests_submitted=1,status="request_submitted")
        reportpath.write_text(json.dumps(report,indent=2),encoding="utf-8")
        print(json.dumps({"asset":asset,"status":"request_submitted","quality":QUALITY,"size":size}),flush=True)
        fields = {"model":MODEL,"prompt":prompt,"size":f"{size[0]}x{size[1]}","quality":QUALITY,
                  "n":"1","output_format":"png","background":"opaque"}
        with requests.Session() as session:
            session.trust_env = False
            with session.post(ENDPOINT,headers={"Authorization":"Bearer "+key},
                              data=fields,files=files,timeout=(30,1200),allow_redirects=False,stream=True) as response:
                report["http_status"] = response.status_code
                if response.status_code != 200:
                    raise SafeFailure("api_request_failed_"+str(response.status_code))
                request_id = response.headers.get("x-request-id","")
                if re.fullmatch(r"req_[0-9a-f]{16,64}",request_id) and key not in request_id:
                    report["request_id"] = request_id
                raw = read_bounded(response,100*1024*1024,"response_too_large")
        payload = json.loads(raw)
        entries = payload.get("data",[])
        if len(entries) != 1 or not isinstance(entries[0].get("b64_json"),str):
            raise SafeFailure("single_image_missing")
        image = base64.b64decode(entries[0]["b64_json"],validate=True)
        actual = png_dimensions(image)
        target = OUT / (asset+".png")
        target.write_bytes(image)
        (OUT / (asset+"-prompt.txt")).write_text(prompt,encoding="utf-8")
        report.update(image_generated=True,actual_dimensions=list(actual),output_sha256=sha(image),
                      output_bytes=len(image),output_filename=target.name,usage=numeric_usage(payload.get("usage")))
        if actual != size:
            raise SafeFailure("native_dimensions_mismatch")
        report["status"] = "native_image_received_pending_visual_review"
        code = 0
    except SafeFailure as exc:
        report.update(status="stopped",error=str(exc))
    except requests.RequestException:
        report.update(status="stopped",error="transport_uncertain_no_retry")
    except Exception:
        report.update(status="stopped",error="internal_error_no_retry")
    finally:
        report["seconds"] = round(time.monotonic()-started,2)
        if acquired:
            reportpath.write_text(json.dumps(report,indent=2,allow_nan=False),encoding="utf-8")
    print(json.dumps(report,allow_nan=False),flush=True)
    return code

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage",choices=STAGES,required=True)
    parser.add_argument("--validate-only",action="store_true")
    args = parser.parse_args()
    for name in STAGES[args.stage]:
        result = generate(name,args.validate_only)
        if result:
            raise SystemExit(result)
