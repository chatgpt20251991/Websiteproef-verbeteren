"""Use the existing owner's image transport with this new set of design briefs."""
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sja-logos-20261005"))
import generate_logos as runner
parser = argparse.ArgumentParser()
parser.add_argument("--asset", required=True)
parser.add_argument("--validate-only", action="store_true")
args = parser.parse_args()
names = ["01-noir-aeroline","02-editorial-oxblood","03-argent-motion","04-velvet-signature","05-monolith","06-copper-aperture","07-mist-line","08-nightfall","09-maison-sage","10-carbon-pulse"]
if args.asset not in names:
    raise SystemExit("unknown concept")
runner.ROOT = Path(__file__).resolve().parent
runner.OUT = Path("premium-reset-output")
runner.ASSETS = {name: ((2560, 1600), []) for name in names}
raise SystemExit(runner.generate(args.asset, args.validate_only))
