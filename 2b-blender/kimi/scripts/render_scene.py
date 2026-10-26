"""Render stills, a comparison, or a resumable full-resolution PNG sequence.

Examples (run with Blender's --python-exit-code 1):
  blender -b blender/night_market.blend --python blender/scripts/render_scene.py -- --mode test --frames 49,145,193
  blender -b blender/night_market.blend --python blender/scripts/render_scene.py -- --mode frames
  blender -b blender/night_market.blend --python blender/scripts/render_scene.py -- --mode hero --hero-frame 49 --samples 64
  blender -b blender/night_market.blend --python blender/scripts/render_scene.py -- --mode compare
"""
import bpy
import sys
import json
import math
import time
import argparse
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
BLENDER = ROOT / "blender"
parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=("test", "frames", "hero", "compare"), default="frames")
parser.add_argument("--frames", default="49,145,193")
parser.add_argument("--start", type=int, default=1)
parser.add_argument("--end", type=int, default=240)
parser.add_argument("--samples", type=int, default=24)
parser.add_argument("--scale", type=int, default=100)
parser.add_argument("--hero-frame", type=int, default=97)
parser.add_argument("--motion-blur", action="store_true")
parser.add_argument("--bloom-strength", type=float)
parser.add_argument("--bloom-size", type=float)
parser.add_argument("--overwrite", action="store_true")
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = args.scale
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.image_settings.color_depth = "8"
scene.eevee.taa_render_samples = args.samples
scene.render.use_motion_blur = args.motion_blur
scene.render.motion_blur_shutter = 0.3
if args.bloom_strength is not None:
    scene.compositing_node_group.nodes["Lantern & neon halation"].inputs["Strength"].default_value = args.bloom_strength
if args.bloom_size is not None:
    scene.compositing_node_group.nodes["Lantern & neon halation"].inputs["Size"].default_value = args.bloom_size
source = json.loads((BLENDER / "source" / "market.json").read_text(encoding="utf-8"))
try:
    import gpu
    gpu.init()
    device = {"vendor": gpu.platform.vendor_get(), "renderer": gpu.platform.renderer_get(), "version": gpu.platform.version_get()}
except Exception as exc:
    device = {"probe": str(exc)}
print("RENDER_DEVICE", device, flush=True)
(BLENDER / "work").mkdir(exist_ok=True)
(BLENDER / "work" / "render_device.json").write_text(json.dumps(device, indent=2), encoding="utf-8")


def p3(value):
    if isinstance(value, dict):
        return Vector((value["x"], -value["z"], value["y"]))
    return Vector((value[0], -value[2], value[1]))


def complete_png(path):
    if not path.is_file() or path.stat().st_size < 20:
        return False
    with path.open("rb") as file:
        file.seek(-12, 2)
        return file.read() == b"\x00\x00\x00\x00IEND\xaeB\x60\x82"


def render(frame, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if complete_png(path) and not args.overwrite and args.mode == "frames":
        print(f"SKIP {frame:04d} | already rendered", flush=True)
        return {"frame": frame, "seconds": 0, "skipped": True, "path": str(path)}
    scene.frame_set(frame)
    scene.render.filepath = str(path)
    start = time.perf_counter()
    bpy.ops.render.render(write_still=True)
    elapsed = time.perf_counter() - start
    result = {"frame": frame, "seconds": round(elapsed, 3), "samples": args.samples,
              "width": int(1920 * args.scale / 100), "height": int(1080 * args.scale / 100),
              "skipped": False, "path": str(path)}
    print(f"FRAME {frame:04d} | {elapsed:.2f}s | {args.samples} samples | {path.name}", flush=True)
    (BLENDER / "work" / f"timing_{args.mode}_{frame:04d}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if args.mode == "compare":
    camera = scene.camera
    scene.frame_set(73)
    camera.animation_data_clear()
    camera.data.animation_data_clear()
    pose = source["metadata"]["compareCamera"]
    position, target = p3(pose["position"]), p3(pose["target"])
    camera.location = position
    camera.rotation_mode = "QUATERNION"
    camera.rotation_quaternion = (target - position).to_track_quat("-Z", "Y")
    camera.data.sensor_fit = "VERTICAL"
    camera.data.sensor_height = 24
    camera.data.lens = 12 / math.tan(math.radians(pose["fov"]) / 2)
    camera.data.dof.use_dof = False
    render(73, BLENDER / "work" / "blender_compare.png")
elif args.mode == "hero":
    scene.eevee.taa_render_samples = args.samples
    render(args.hero_frame, BLENDER / "render" / "hero.png")
elif args.mode == "test":
    for frame in (int(value) for value in args.frames.split(",")):
        render(frame, BLENDER / "work" / f"test_{frame:04d}.png")
else:
    results = []
    total_start = time.perf_counter()
    for frame in range(args.start, args.end + 1):
        results.append(render(frame, BLENDER / "render" / "frames" / f"market_{frame:04d}.png"))
    elapsed = time.perf_counter() - total_start
    completed_timings = []
    for frame in range(args.start, args.end + 1):
        timing_file = BLENDER / "work" / f"timing_frames_{frame:04d}.json"
        if timing_file.exists():
            completed_timings.append(json.loads(timing_file.read_text(encoding="utf-8"))["seconds"])
    cumulative_seconds = sum(completed_timings)
    summary = {"engine": scene.render.engine, "frames_requested": len(results), "elapsed_seconds": round(elapsed, 3),
               "under_25_minutes": elapsed < 1500, "cumulative_frame_seconds": round(cumulative_seconds, 3),
               "cumulative_under_25_minutes": cumulative_seconds < 1500, "resolution": [1920, 1080], "fps": 24, "samples": args.samples,
               "rendered": sum(not result["skipped"] for result in results), "results": results}
    (BLENDER / "work" / "render_timing.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"SEQUENCE COMPLETE | {elapsed:.1f}s | all {len(completed_timings)} frames: {cumulative_seconds:.1f}s | under 25 minutes: {cumulative_seconds < 1500}", flush=True)
