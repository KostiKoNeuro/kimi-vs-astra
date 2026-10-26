"""Read-only audit of the saved Blender deliverable and its baked animation."""
import bpy,json,math
from pathlib import Path
root=Path(__file__).resolve().parent.parent
s=bpy.context.scene
data=json.loads((root/'scripts/diorama.json').read_text(encoding='utf-8'))
assert s.camera.name=='FlyCam'
assert len([o for o in bpy.data.objects if o.type=='CAMERA'])==1
assert (s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage)==(1920,1080,100)
assert (s.frame_start,s.frame_end,s.render.fps,s.render.fps_base)==(1,240,24,1)
assert s.frame_current==1
assert sum(o.get('Original voxel count',0) for o in bpy.data.objects)==sum(len(a) for a in data['static'].values())
assert not [i for i in bpy.data.images if i.source=='FILE' and i.filepath and not i.packed_file]
assert not list(bpy.data.libraries)
assert not [o for o in bpy.data.objects if not o.users_collection]
walk=next(o for o in bpy.data.objects if o.name.startswith('Walk ') and o.type=='EMPTY')
scooter=next(o for o in bpy.data.objects if o.name=='Scooter 1 • moving rider')
steam=next(o for o in bpy.data.objects if o.name.startswith('Steam 01 • puff'))
points=[]
for f in (1,120,240):
    s.frame_set(f)
    points.append({o.name:list(o.location) for o in (s.camera,walk,scooter,steam)})
for name in points[0]:assert points[0][name]!=points[-1][name],name+' is static'
s.frame_set(1)
report={'status':'PASS','blender':bpy.app.version_string,'engine':s.render.engine,'cameras':['FlyCam'],'collections':[c.name for c in s.collection.children],'objects':len(bpy.data.objects),'original_static_voxels':sum(len(a) for a in data['static'].values()),'residents':len(data['actors']),'scooters':len(data['scooters']),'steam_puffs':len(data['steamSeeds']),'rain_streaks':len(data['rainSeeds']),'animation_samples':points,'external_libraries':0,'external_image_textures':0,'handlers_required':False}
(root/'render/scene_audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print('SCENE_AUDIT_PASS',report['objects'],'objects',report['original_static_voxels'],'source voxels')

