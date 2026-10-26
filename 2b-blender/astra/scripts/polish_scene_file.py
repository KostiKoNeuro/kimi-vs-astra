"""Organize editor node layouts and embed a short guide; does not change the rendered scene."""
import bpy
from pathlib import Path
root=Path(__file__).resolve().parent.parent
locations={'ShaderNodeOutputMaterial':(460,160),'ShaderNodeBsdfPrincipled':(80,160),'ShaderNodeVertexColor':(-240,160),'ShaderNodeTexCoord':(-1050,80),'ShaderNodeTexBrick':(-800,220),'ShaderNodeTexNoise':(-800,-240),'ShaderNodeValToRGB':(-510,-220),'ShaderNodeBump':(-230,70),'ShaderNodeVolumePrincipled':(40,160)}
for material in bpy.data.materials:
    if material.use_nodes:
        for node in material.node_tree.nodes:
            if node.bl_idname in locations:node.location=locations[node.bl_idname]
            node.width=200
scene=bpy.context.scene
children=sorted(list(scene.collection.children),key=lambda c:c.name)
for c in children:scene.collection.children.unlink(c)
for c in children:scene.collection.children.link(c)
guide=bpy.data.texts.get('START HERE • scene guide') or bpy.data.texts.new('START HERE • scene guide')
guide.clear();guide.write('SHENZHEN — AFTER RAIN\n\nPart 1 diorama transferred from the original procedural generator.\n28,238 original static cubes; 48 residents; 3 scooters.\n\nFlyCam is active. Frames 1–240, 24 fps, 1920×1080.\nSpace: play animation. Numpad 0: camera view.\n\nAll animation is baked into ordinary F-curves.\nNo script execution, add-ons, linked libraries or external textures required.\n\nCollections 01–07: original city geometry.\n08–10: articulated residents, scooters, steam and rain.\n11–12: practical lights, atmosphere and wet pavement reflection.\n13: the single FlyCam and its focus target.\n\nRead README.txt next to this file for rebuild and render instructions.\n')
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(root/'night_market.blend'),compress=True)
