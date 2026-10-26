"""Rebuild and render the complete night-market deliverable with local tools.

Full rebuild:
  python blender/scripts/rebuild.py
Reuse the exported source data:
  python blender/scripts/rebuild.py --skip-export
Prepare only the scene and comparison:
  python blender/scripts/rebuild.py --skip-export --prepare-only
Render the existing scene and package the film:
  python blender/scripts/rebuild.py --render-only
Resume an interrupted sequence without overwriting completed frames:
  python blender/scripts/rebuild.py --render-only --resume

BLENDER_BIN and CHROME may override the installed executable paths.
"""
from pathlib import Path
import argparse
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "blender" / "scripts"
parser = argparse.ArgumentParser()
parser.add_argument("--skip-export", action="store_true")
parser.add_argument("--prepare-only", action="store_true")
parser.add_argument("--render-only", action="store_true")
parser.add_argument("--resume", action="store_true")
args = parser.parse_args()


def run(command):
    print("\nRUN", " ".join(str(part) for part in command), flush=True)
    subprocess.run([str(part) for part in command], cwd=ROOT, check=True)


installed = Path(os.environ.get("BLENDER_BIN", "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"))
blender = installed if installed.exists() else shutil.which("blender")
assert blender, "Set BLENDER_BIN to the installed Blender executable"


def blender_python(script, arguments=()):
    run([blender, "-b", ROOT / "blender" / "night_market.blend", "--python-exit-code", "1", "--python", SCRIPTS / script, "--", *arguments])


if not args.render_only:
    if not args.skip_export:
        node = shutil.which("node")
        assert node, "Node.js is required only for a fresh browser export"
        run([node, SCRIPTS / "export_scene.mjs"])
    run([blender, "-b", "--factory-startup", "--python-exit-code", "1", "--python", SCRIPTS / "build_scene.py"])

blender_python("validate_scene.py")
if args.prepare_only:
    blender_python("render_scene.py", ("--mode", "compare", "--samples", "24"))
    run([sys.executable, SCRIPTS / "package_render.py", "--compare-only"])
else:
    frame_args = ["--mode", "frames", "--samples", "24"]
    if not args.resume:
        frame_args.append("--overwrite")
    blender_python("render_scene.py", frame_args)
    blender_python("render_scene.py", ("--mode", "hero", "--hero-frame", "97", "--samples", "64"))
    blender_python("render_scene.py", ("--mode", "compare", "--samples", "24"))
    run([sys.executable, SCRIPTS / "package_render.py"])
