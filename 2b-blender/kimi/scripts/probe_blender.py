import bpy
import json
from pathlib import Path

out = Path(__file__).resolve().parents[1] / "work"
out.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.render.engine = "BLENDER_EEVEE"
info = {
    "version": bpy.app.version_string,
    "gpu_backend": bpy.context.preferences.system.gpu_backend,
    "scene_eevee": [p.identifier for p in scene.eevee.bl_rna.properties],
    "eevee_ray_options": [p.identifier for p in scene.eevee.ray_tracing_options.bl_rna.properties],
    "scene_compositor": [p.identifier for p in scene.bl_rna.properties if "composit" in p.identifier or "node" in p.identifier],
    "material": [p.identifier for p in bpy.types.Material.bl_rna.properties if any(s in p.identifier for s in ("render", "shadow", "transparen"))],
    "lightprobe_types": [e.identifier for e in bpy.types.LightProbe.bl_rna.properties["type"].enum_items],
    "view_transforms": [e.identifier for e in scene.view_settings.bl_rna.properties["view_transform"].enum_items],
}
try:
    info["looks"] = [e.identifier for e in scene.view_settings.bl_rna.properties["look"].enum_items]
except Exception:
    pass
(out / "blender_capabilities.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
print(json.dumps(info, indent=2))

scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.eevee.taa_render_samples = 16
bpy.ops.object.camera_add(location=(5, -7, 4))
cam = bpy.context.object
from mathutils import Vector
cam.rotation_euler = (Vector((0, 0, 0.6)) - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0.5))
cube = bpy.context.object
mat = bpy.data.materials.new("Probe | teal")
mat.diffuse_color = (0.04, 0.5, 0.45, 1)
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.04, 0.5, 0.45, 1)
bsdf.inputs["Metallic"].default_value = 0.4
bsdf.inputs["Roughness"].default_value = 0.2
cube.data.materials.append(mat)
bpy.ops.mesh.primitive_plane_add(size=200)
plane = bpy.context.object
plane.data.materials.append(mat)
bpy.ops.object.light_add(type="AREA", location=(2, -3, 5))
light = bpy.context.object
light.data.energy = 800
light.data.shape = "DISK"
light.data.size = 5
scene.world.color = (0.04, 0.04, 0.04)
scene.render.filepath = str(out / "probe.png")
if hasattr(scene, "use_nodes"):
    scene.use_nodes = True
if hasattr(scene, "compositing_node_group") and scene.compositing_node_group is None:
    tree = bpy.data.node_groups.new("Probe compositor", "CompositorNodeTree")
    scene.compositing_node_group = tree
    tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    output = tree.nodes.new("NodeGroupOutput")
else:
    tree = scene.node_tree
    tree.nodes.clear()
    output = tree.nodes.new("CompositorNodeComposite")
rl = tree.nodes.new("CompositorNodeRLayers")
glow = tree.nodes.new("CompositorNodeGlare")
print("GLARE INPUTS", [(s.name, s.identifier) for s in glow.inputs])
print("GLARE PROPS", [p.identifier for p in glow.bl_rna.properties])
tree.links.new(rl.outputs["Image"], glow.inputs["Image"])
tree.links.new(glow.outputs["Image"], output.inputs["Image"])
bpy.ops.render.render(write_still=True)
print("PROBE_RENDER_OK")
