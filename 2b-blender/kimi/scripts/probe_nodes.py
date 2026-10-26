import bpy
import gpu

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
tree = bpy.data.node_groups.new('Probe', 'CompositorNodeTree')
glow = tree.nodes.new('CompositorNodeGlare')
for name in ('Type', 'Quality', 'Size', 'Strength', 'Threshold'):
    socket = glow.inputs[name]
    print('GLARE', name, socket.bl_idname, repr(socket.default_value))
    try:
        print('ENUM', [(e.identifier, e.name) for e in socket.bl_rna.properties['default_value'].enum_items])
    except Exception as exc:
        print('NO_STATIC_ENUM', exc)
for prop in ('fast_gi_method', 'fast_gi_resolution'):
    print(prop, [(e.identifier, e.name) for e in scene.eevee.bl_rna.properties[prop].enum_items])
for prop in ('view_transform', 'look'):
    print(prop, getattr(scene.view_settings, prop))
print('MOTION_BLUR', hasattr(scene.render, 'use_motion_blur'))
probe = bpy.data.lightprobes.new('Probe reflection', 'PLANE')
print('PLANE', [p.identifier for p in probe.bl_rna.properties])
print('LIGHT', [p.identifier for p in bpy.data.lights.new('Probe', 'POINT').bl_rna.properties if 'shadow' in p.identifier])
print('NODE_TREE', [p.identifier for p in tree.bl_rna.properties])
print('RENDER_IMAGE', [p.identifier for p in scene.render.image_settings.bl_rna.properties])
try:
    print('GPU', gpu.platform.vendor_get(), gpu.platform.renderer_get(), gpu.platform.version_get())
except Exception as exc:
    print('GPU_CONTEXT', exc)
