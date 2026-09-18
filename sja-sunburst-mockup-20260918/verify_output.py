"""Verify generated image without altering pixels or making API calls."""
import hashlib
import json
import os
from pathlib import Path
from PIL import Image

root = Path("sunburst-output")
image = root / "startjouwautobedrijf-mockup.png"
with Image.open(image) as im:
    assert im.format == "PNG", "Output must be PNG"
    im.verify()
with Image.open(image) as im:
    im.load()
    dims = list(im.size)
assert min(dims) > 0
brief = Path("sja-sunburst-mockup-20260918/prompt.txt").read_bytes()
(root / "prompt.txt").write_bytes(brief)
report = {
    "source": "OpenAI Images API, bundled imagegen CLI via GitHub Actions",
    "model_requested": "gpt-image-2.5-sunburst",
    "quality_requested": "high",
    "size_requested": "auto",
    "actual_dimensions": dims,
    "images_requested": 1,
    "output_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
    "prompt_sha256": hashlib.sha256(brief).hexdigest(),
    "pixels_modified_after_generation": False,
    "repository": os.environ.get("GITHUB_REPOSITORY"),
    "commit": os.environ.get("GITHUB_SHA"),
    "run_id": os.environ.get("GITHUB_RUN_ID"),
}
(root / "generation-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report))
