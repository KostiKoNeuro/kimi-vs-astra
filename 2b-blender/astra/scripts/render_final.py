"""Render the exact 240-frame, 24-fps H.264 movie using Blender's built-in encoder."""
import bpy,time,json,sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent
scene=bpy.context.scene
assert scene.frame_start==1 and scene.frame_end==240 and scene.render.fps==24
assert scene.render.resolution_x==1920 and scene.render.resolution_y==1080
assert scene.camera.name=='FlyCam'
scene.render.image_settings.file_format='FFMPEG'
scene.render.ffmpeg.format='MPEG4';scene.render.ffmpeg.codec='H264'
scene.render.ffmpeg.constant_rate_factor='HIGH';scene.render.ffmpeg.ffmpeg_preset='GOOD'
scene.render.ffmpeg.audio_codec='NONE'
scene.render.filepath=str(root/'render/flythrough.mp4')
start=time.monotonic();completed=[]
def record(scene,*unused):
    completed.append(scene.frame_current)
    elapsed=time.monotonic()-start
    (root/'render/render_progress.json').write_text(json.dumps({'frame':scene.frame_current,'of':240,'elapsed_seconds':round(elapsed,2)},indent=2))
    if scene.frame_current%24==0:print('MOVIE_PROGRESS',scene.frame_current,'/ 240',round(elapsed,1),'seconds',flush=True)
bpy.app.handlers.render_post.append(record)
try:bpy.ops.render.render(animation=True)
finally:bpy.app.handlers.render_post.remove(record)
elapsed=time.monotonic()-start
report={'frames':len(completed),'resolution':[1920,1080],'fps':24,'duration_seconds':10,'render_seconds':round(elapsed,3),'under_25_minutes':elapsed<1500,'blender':bpy.app.version_string,'engine':scene.render.engine,'samples':scene.eevee.taa_render_samples}
if not (root/'render/flythrough.mp4').exists():
    candidates=sorted((root/'render').glob('flythrough*.mp4'),key=lambda p:p.stat().st_mtime)
    if candidates:candidates[-1].replace(root/'render/flythrough.mp4')
(root/'render/render_report.json').write_text(json.dumps(report,indent=2))
print('FINAL_RENDER',json.dumps(report),flush=True)
assert len(completed)==240
