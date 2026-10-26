"""Create the side-by-side comparison, encode H.264, and verify all deliverables.

Run with the system Python after Blender's numbered-frame render finishes.
Use --compare-only to rebuild just render/compare.png.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
BLENDER = ROOT / "blender"
RENDER = BLENDER / "render"
WORK = BLENDER / "work"
RENDER.mkdir(exist_ok=True)
WORK.mkdir(exist_ok=True)
parser = argparse.ArgumentParser()
parser.add_argument("--compare-only", action="store_true")
args = parser.parse_args()


def font(size, bold=False):
    candidates = [Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / ("segoeuib.ttf" if bold else "segoeui.ttf"),
                  Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / ("arialbd.ttf" if bold else "arial.ttf")]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default(size=size)


def compose_comparison():
    source = Image.open(WORK / "browser_compare.png").convert("RGB")
    blender = Image.open(WORK / "blender_compare.png").convert("RGB")
    assert source.size == (1920, 1080) and blender.size == (1920, 1080)
    canvas = Image.new("RGB", (1920, 1080), (5, 12, 20))
    draw = ImageDraw.Draw(canvas)
    draw.text((48, 54), "PART 1 / PART 2   ·   THE SAME LITTLE WORLD", font=font(16), fill=(118, 160, 168))
    draw.text((48, 90), "Shenzhen, after the rain", font=font(40, True), fill=(232, 231, 213))
    draw.text((1872, 68), "VOXEL NIGHT MARKET", font=font(16), fill=(118, 160, 168), anchor="ra")
    draw.text((1872, 99), "22:48  /  10 seconds", font=font(20), fill=(216, 184, 143), anchor="ra")
    draw.text((48, 238), "01   BROWSER / THREE.JS", font=font(18, True), fill=(120, 224, 209))
    draw.text((1008, 238), "02   BLENDER / EEVEE", font=font(18, True), fill=(255, 166, 132))
    canvas.paste(source.resize((960, 540), Image.Resampling.LANCZOS), (0, 278))
    canvas.paste(blender.resize((960, 540), Image.Resampling.LANCZOS), (960, 278))
    draw.line((0, 277, 1920, 277), fill=(38, 61, 71), width=1)
    draw.line((959, 278, 959, 818), fill=(38, 61, 71), width=1)
    draw.line((0, 818, 1920, 818), fill=(38, 61, 71), width=1)
    draw.text((48, 856), "index.html", font=font(21, True), fill=(224, 228, 216))
    draw.text((1008, 856), "night_market.blend", font=font(21, True), fill=(224, 228, 216))
    draw.text((48, 891), "Original procedural geometry and palette", font=font(16), fill=(129, 156, 166))
    draw.text((1008, 891), "Source geometry, practical lighting, weather and life", font=font(16), fill=(129, 156, 166))
    draw.line((48, 950, 1872, 950), fill=(30, 48, 59), width=1)
    draw.text((960, 986), "MATCHED CAMERA   /   (13.0, 10.5, 21.0)   /   47° VERTICAL FOV",
              font=font(16), fill=(142, 174, 183), anchor="mm")
    canvas.save(RENDER / "compare.png")
    print("COMPARE", RENDER / "compare.png", flush=True)


compose_comparison()
if args.compare_only:
    raise SystemExit(0)

frames = [RENDER / "frames" / f"market_{frame:04d}.png" for frame in range(1, 241)]
missing = [frame.name for frame in frames if not frame.exists()]
assert not missing, f"Missing frames: {missing}"
for path in frames:
    with Image.open(path) as image:
        assert image.size == (1920, 1080), f"Wrong frame size: {path}"
        image.verify()
with Image.open(RENDER / "hero.png") as image:
    assert image.size == (1920, 1080), "Hero image is not 1920 x 1080"

ffmpeg = shutil.which("ffmpeg")
ffprobe = shutil.which("ffprobe")
assert ffmpeg and ffprobe, "FFmpeg and ffprobe must be available on PATH"
video = RENDER / "flythrough.mp4"
command = [ffmpeg, "-y", "-hide_banner", "-framerate", "24", "-start_number", "1",
           "-i", str(RENDER / "frames" / "market_%04d.png"), "-frames:v", "240",
           "-vf", "scale=iw:ih:in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p",
           "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-level", "4.1",
           "-pix_fmt", "yuv420p", "-color_range", "tv", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
           "-movflags", "+faststart", "-an", "-metadata", "title=Shenzhen - After the Rain", str(video)]
encoded = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
(WORK / "ffmpeg_encode.log").write_text(encoded.stdout + encoded.stderr, encoding="utf-8")
assert encoded.returncode == 0, f"FFmpeg failed: {encoded.stderr[-4000:]}"

probe = subprocess.run([ffprobe, "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", str(video)],
                       check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
media = json.loads(probe.stdout)
stream = next(item for item in media["streams"] if item["codec_type"] == "video")
assert stream["codec_name"] == "h264"
assert (stream["width"], stream["height"]) == (1920, 1080)
assert stream["r_frame_rate"] == "24/1" and stream["avg_frame_rate"] == "24/1"
assert int(stream["nb_read_frames"]) == 240
assert abs(float(media["format"]["duration"]) - 10.0) < 0.001
assert stream["pix_fmt"] == "yuv420p"
decoded = subprocess.run([ffmpeg, "-v", "error", "-i", str(video), "-f", "null", "-"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
assert decoded.returncode == 0 and not decoded.stderr.strip(), decoded.stderr
subprocess.run([ffmpeg, "-y", "-v", "error", "-i", str(video), "-vf",
                "fps=1,scale=384:216:flags=lanczos,tile=5x2", "-frames:v", "1", str(WORK / "video_contact_sheet.png")], check=True)
subprocess.run([ffmpeg, "-y", "-v", "error", "-ss", "4", "-i", str(video), "-frames:v", "1",
                str(WORK / "video_frame_0097.png")], check=True)
from PIL import ImageChops, ImageStat
with Image.open(WORK / "video_frame_0097.png") as decoded_frame, Image.open(RENDER / "frames" / "market_0097.png") as source_frame:
    color_error = sum(ImageStat.Stat(ImageChops.difference(decoded_frame.convert("RGB"), source_frame.convert("RGB"))).mean) / 3
assert color_error < 12, f"Video color differs too much from the source frame: {color_error}"

source = json.loads((BLENDER / "source" / "market.json").read_text(encoding="utf-8"))
validation = json.loads((WORK / "scene_validation.json").read_text(encoding="utf-8"))
timing_path = WORK / "render_timing.json"
timing = json.loads(timing_path.read_text(encoding="utf-8")) if timing_path.exists() else None
verification = {
    "passed": True,
    "source_unchanged": hashlib.sha256((ROOT / "index.html").read_bytes()).hexdigest() == source["metadata"]["sourceSha256"],
    "scene_validation_passed": validation["passed"],
    "png_frames": len(frames), "resolution": [1920, 1080], "fps": 24, "duration_seconds": 10.0,
    "video_codec": stream["codec_name"], "pixel_format": stream["pix_fmt"], "decoded_video_frames": int(stream["nb_read_frames"]),
    "full_decode_passed": True, "hero_frame_mean_abs_error": round(color_error, 3), "render_timing": timing,
    "files": {name: (BLENDER / name).stat().st_size for name in ("night_market.blend", "render/flythrough.mp4", "render/hero.png", "render/compare.png")}
}
assert verification["source_unchanged"] and verification["scene_validation_passed"]
if timing:
    total_render_seconds = timing.get("cumulative_frame_seconds", timing["elapsed_seconds"])
    verification["total_frame_render_seconds"] = total_render_seconds
    assert total_render_seconds < 1500, "The full render exceeded 25 minutes"
(RENDER / "verification.json").write_text(json.dumps(verification, indent=2), encoding="utf-8")
print(json.dumps(verification, indent=2), flush=True)
print("DELIVERABLES_VERIFIED", flush=True)
