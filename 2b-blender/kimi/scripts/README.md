# Night market — Blender rebuild

The scene is a direct transfer of the Part 1 `index.html`, not a redesign. The browser generator is instrumented in memory only; the original HTML is never edited. No models, image textures, HDRIs, fonts, or add-ons are downloaded for the Blender scene.

## Rebuild

Run these commands from the folder containing `index.html` and `blender/`.

```bash
python blender/scripts/rebuild.py
```

This exports the original scene, builds `night_market.blend`, validates it, renders 240 full-resolution frames, renders the hero and comparison, and encodes `flythrough.mp4`.

Useful variations:

```bash
# Reuse the included source export; no browser export is needed.
python blender/scripts/rebuild.py --skip-export

# Build and validate the scene and comparison only.
python blender/scripts/rebuild.py --skip-export --prepare-only

# Render the existing .blend without rebuilding it.
python blender/scripts/rebuild.py --render-only

# Resume an interrupted render of the SAME scene; completed PNGs are kept.
python blender/scripts/rebuild.py --render-only --resume
```

`BLENDER_BIN` can override the Blender executable. `CHROME` can override Chrome for a fresh export. The installed Blender path is used by default. Node.js is needed only for a fresh browser export. The system Python needs Pillow for the comparison and delivery checks. FFmpeg and ffprobe must be on `PATH`.

## Settings

- Eevee, using the machine's AMD GPU; no Cycles GPU dependency.
- 1920 × 1080, 24 fps, frames 1–240 inclusive.
- 24 render samples for the film; 64 for the hero still.
- `FlyCam` is the only camera. The timeline and camera view are ready on opening the file.
- The hero is frame 97. The comparison uses the original browser camera at source time 3 seconds.
- Rendering produces a numbered PNG sequence first, then H.264 / yuv420p with fast-start playback.

## Files

- `source/market.json`: exact source voxel transforms, linear colors, light positions, actor rigs and 240 sampled animation poses. Includes the original file's SHA-256.
- `source/scene_spec.json`: global spatial contract, source constraints, camera path, and render settings.
- `export_scene.mjs`: source transfer and original-camera browser capture.
- `build_scene.py`: editable Blender construction, materials, lighting, camera, baked actor motion, and Geometry Nodes weather.
- `render_scene.py`: test, sequence, hero, and matched-camera rendering. Sequence rendering skips completed frames unless `--overwrite` is supplied.
- `validate_scene.py`: delivery settings, actor transforms and ground contact, weather motion, camera clearance, and unchanged-source checks.
- `package_render.py`: comparison layout, H.264 encoding, frame-count/duration checks, and full video decode validation.
- `rebuild.py`: end-to-end orchestration.
- `probe_blender.py`, `probe_nodes.py`: local Blender capability checks used during the build; not required for normal rebuilding.

The `.blend` is self-contained. Its numbered collections separate the city block, architecture, market stalls, signs, lantern canopy, animated life, weather, lighting, and camera. A `START HERE` text block is included in the file.
