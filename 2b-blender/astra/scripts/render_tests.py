"""Render representative frames, including the closest pass, before the full sequence."""
import bpy,time,json
from pathlib import Path
root=Path(__file__).resolve().parent.parent
s=bpy.context.scene
s.render.image_settings.file_format='PNG'
records=[]
for frame in (1,120,200,240):
    s.frame_set(frame);s.render.filepath=str(root/f'render/tests/frame_{frame:03d}.png')
    start=time.monotonic();bpy.ops.render.render(write_still=True)
    records.append({'frame':frame,'seconds':round(time.monotonic()-start,3)})
    print('TIMING',records[-1],flush=True)
(root/'render/tests/timing.json').write_text(json.dumps(records,indent=2))
