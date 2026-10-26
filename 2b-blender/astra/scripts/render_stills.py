"""Render the selected hero and the camera-matched browser comparison frame."""
import bpy
from pathlib import Path
root=Path(__file__).resolve().parent.parent
scene=bpy.context.scene
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGB'
scene.eevee.taa_render_samples=64
for frame,path in [(120,root/'render/hero.png'),(1,root/'scripts/blender_reference.png')]:
    scene.frame_set(frame);scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True)

