"""Retrieve the identical earlier artifact backing the user-uploaded reference."""
import hashlib, io, os, zipfile
from pathlib import Path
import requests
root = Path(__file__).resolve().parent
url = "https://api.github.com/repos/chatgpt20251991/Websiteproef-verbeteren/actions/artifacts/10563954735/zip"
with requests.Session() as session:
    session.trust_env = False
    response = session.get(url,headers={"Authorization":"Bearer "+os.environ["GH_ARTIFACT_TOKEN"],"Accept":"application/vnd.github+json"},allow_redirects=False,timeout=60)
    if response.status_code != 302:
        raise SystemExit("Reference artifact lookup failed")
    location = response.headers.get("Location","")
    if not location.startswith("https://"):
        raise SystemExit("Reference redirect invalid")
    archive = session.get(location,timeout=90).content
if hashlib.sha256(archive).hexdigest() != "4b6b3c6aea7702c7092b3206f4ac23358ef69cfd662b5f2a9303e3de2aee0847":
    raise SystemExit("Reference artifact checksum mismatch")
with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
    image = bundle.read("startjouwautobedrijf-sunburst-max.png")
if hashlib.sha256(image).hexdigest() != "e15dcf419f8a936f7b275e6351b29c5ab811cba7e4f46f80c10ec9bd179a06c9":
    raise SystemExit("Uploaded reference checksum mismatch")
(root/"user-copy-reference.png").write_bytes(image)
print("User's attached copy-reference verified.")
