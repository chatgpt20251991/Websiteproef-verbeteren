import hashlib, io, os, zipfile
from pathlib import Path
import requests
out=Path("sunburst-suite-editorial-output")
out.mkdir(exist_ok=True)
with requests.Session() as session:
    session.trust_env=False
    r=session.get("https://api.github.com/repos/chatgpt20251991/Websiteproef-verbeteren/actions/artifacts/10566831005/zip",headers={"Authorization":"Bearer "+os.environ["GH_ARTIFACT_TOKEN"],"Accept":"application/vnd.github+json"},allow_redirects=False,timeout=60)
    if r.status_code !=302 or not r.headers.get("Location","").startswith("https://"):
        raise SystemExit("Reference lookup failed")
    raw=session.get(r.headers["Location"],timeout=90).content
if hashlib.sha256(raw).hexdigest()!="77d72006b5051748abc46c0227029b0c46382c5d2b3c2baf720cac24194528be":
    raise SystemExit("Reference checksum mismatch")
with zipfile.ZipFile(io.BytesIO(raw)) as z:
    im=z.read("01-dashboard-desktop.png")
if hashlib.sha256(im).hexdigest()!="49bdc0dca6b8d0a3fb26b0695a452a9316d0cfc083e33a164807b517ce4e1805":
    raise SystemExit("Image checksum mismatch")
(out/"01-dashboard-desktop.png").write_bytes(im)
print("Design master verified.")
