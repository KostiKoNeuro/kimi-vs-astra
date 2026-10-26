# Part 2 - Bring your diorama into Blender

Now take **the voxel night market diorama you just built in Part 1** (`index.html` in this folder) and bring it into **Blender** as a cinematic 3D scene. The Blender scene must be built from your diorama, not invented from scratch.

## Tools

- **Blender** is installed on this computer at:
  `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`
- Work through Blender's Python API (`bpy`) and run Blender in background mode, for example `blender -b --python build_scene.py`. Modifiers, Geometry Nodes, shader nodes, the compositor and all built-in Blender features are allowed.
- Choose how to transfer the diorama yourself: port your generator to Python, export the scene from the browser (for example with Three.js `GLTFExporter`) and import it, or any other approach. **No downloaded models, images, textures, HDRIs or add-ons.**
- Hardware: AMD Radeon RX 590 (8 GB), Ryzen 7 3700X, 32 GB RAM. Cycles has no GPU support on this card, so plan the render engine and settings for this machine. The final render must take **no more than 25 minutes**.

## Requirements

- **It must be recognisably the same diorama:** the same layout, buildings, stalls, signs, colours and voxel style. Viewers will compare the two side by side.
- Then make it look like a frame from an animated film: real lighting from lanterns and neon, glow, reflections on the wet ground, depth, atmosphere, rain, steam.
- **It must be alive:** people walking, scooters moving, steam rising, signs flickering. Real animation, not a static scene with a moving camera.
- One camera named `FlyCam` with a smooth cinematic camera move through the market.
- Render: **1920x1080, 24 fps, exactly 240 frames (10 seconds)**.
- The scene file must be clean, because it will be shown in the Blender UI: objects grouped into clearly named collections, readable object and material names, no leftover junk.

## Deliver (in a new folder `blender/` next to your diorama)

- `blender/night_market.blend`: the scene, opens in Blender with the animation and camera ready to play.
- `blender/render/flythrough.mp4`: the final 10-second render (H.264).
- `blender/render/hero.png`: the single most beautiful frame, 1920x1080.
- `blender/render/compare.png`: the browser diorama and the Blender scene **from the same viewpoint**, side by side, 1920x1080.
- `blender/scripts/`: all scripts you used, so the scene can be rebuilt from scratch.

Do not change the browser diorama itself. Do not ask questions. Build it, render test frames, look at them yourself, and fix anything that looks broken or ugly before the final render. Watch the final video before finishing.
