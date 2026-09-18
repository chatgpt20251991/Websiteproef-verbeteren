import hashlib, io, os, zipfile
from pathlib import Path
import requests
root = Path(__file__).resolve().parent
url = "https://api.github.com/repos/chatgpt20251991/Websiteproef-verbeteren/actions/artifacts/10566250627/zip"
with requests.Session() as session:
    session.trust_env = False
    response = session.get(url, headers={"Authorization": "Bearer " + os.environ["GH_ARTIFACT_TOKEN"], "Accept": "application/vnd.github+json"}, allow_redirects=False, timeout=60)
    if response.status_code != 302:
        raise SystemExit("Artifact lookup failed")
    location = response.headers.get("Location", "")
    if not location.startswith("https://"):
        raise SystemExit("Artifact redirect invalid")
    archive = session.get(location, timeout=90).content
if hashlib.sha256(archive).hexdigest() != "4c44dc35ed419c96913038028761a96b9f2a8fef8d576db1753cb35ea20699c3":
    raise SystemExit("Artifact checksum mismatch")
with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
    image = bundle.read("startjouwautobedrijf-statement-2026.png")
if hashlib.sha256(image).hexdigest() != "727d94c8e95a03b46f0584b8e9200b6e36e52431c47742aafc1221b0af676076":
    raise SystemExit("Image checksum mismatch")
(root / "statement-reference.png").write_bytes(image)
print("Previously generated image verified for targeted cleanup.")
