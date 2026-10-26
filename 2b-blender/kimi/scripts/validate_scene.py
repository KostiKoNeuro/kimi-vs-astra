"""Validate the delivered scene and its source-animation transfer in Blender."""
import bpy
import json
import math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT = Path(__file__).resolve().parents[2]
BLENDER = ROOT / "blender"
source = json.loads((BLENDER / "source" / "market.json").read_text(encoding="utf-8"))
scene = bpy.context.scene
report = {
    "camera_count": len([obj for obj in scene.objects if obj.type == "CAMERA"]),
    "camera_name": scene.camera.name if scene.camera else None,
    "resolution": [scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage],
    "fps": scene.render.fps / scene.render.fps_base,
    "frame_start": scene.frame_start,
    "frame_end": scene.frame_end,
    "engine": scene.render.engine,
    "objects": len(scene.objects),
    "mesh_objects": len([obj for obj in scene.objects if obj.type == "MESH"]),
    "collections": [collection.name for collection in scene.collection.children],
    "external_images": [image.filepath for image in bpy.data.images if image.source == "FILE" and not image.packed_file],
    "compositor_enabled": scene.use_nodes and scene.render.use_compositing,
    "camera_collision_frames": list(scene.get("camera_clearance_violations", [])),
    "saved_frame": scene.frame_current,
    "source_rigs": len(source["rigs"]),
    "camera_view_ready": all(area.spaces.active.region_3d.view_perspective == "CAMERA"
                             for screen in bpy.data.screens for area in screen.areas if area.type == "VIEW_3D"),
    "orphan_meshes": len([mesh for mesh in bpy.data.meshes if mesh.users == 0]),
    "temporary_node_groups": [tree.name for tree in bpy.data.node_groups if tree.name.startswith("TEMP")],
    "default_startup_objects": [obj.name for obj in scene.objects if obj.name in ("Cube", "Camera", "Light")],
}
assert report["camera_count"] == 1 and report["camera_name"] == "FlyCam"
assert report["saved_frame"] == 49 and report["camera_view_ready"]
assert report["source_rigs"] == 40 and scene.camera.data.animation_data
assert report["orphan_meshes"] == 0 and not report["temporary_node_groups"] and not report["default_startup_objects"]
assert report["resolution"] == [1920, 1080, 100]
assert report["fps"] == 24 and report["frame_start"] == 1 and report["frame_end"] == 240
assert report["engine"] == "BLENDER_EEVEE"
assert not report["external_images"]
assert report["compositor_enabled"]
assert not report["camera_collision_frames"]


def p3(value):
    return Vector((value[0], -value[2], value[1]))


def actor_snapshot(frame):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    rows = []
    errors = []
    for index, rig in enumerate(source["rigs"]):
        name = " ".join(part.capitalize() for part in rig["name"].split("-"))
        root = bpy.data.objects.get(name + " | rig")
        if not root:
            errors.append(f"Missing root {name}")
            continue
        root_error = (root.location - p3(source["frames"][frame - 1][index]["root"]["p"])).length
        if root_error > 0.0001:
            errors.append(f"Root mismatch {name}: {root_error}")
        uprightness = (root.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized().z
        if uprightness < 0.98:
            errors.append(f"Actor is tipped over {name}: {uprightness}")
        for child in root.children:
            if child.type != "MESH":
                continue
            minimum_z = min((child.matrix_world @ Vector(corner)).z for corner in child.bound_box)
            if minimum_z < -0.2:
                errors.append(f"Actor below ground {name} / {child.name}: {minimum_z}")
            if "source_part_index" not in child:
                continue
            part_index = child["source_part_index"]
            error = (child.location - p3(source["frames"][frame - 1][index]["parts"][part_index]["p"])).length
            if error > 0.0001:
                errors.append(f"Part mismatch {name} {part_index}: {error}")
        if rig["name"] in ("walker-8", "vendor-5", "scooter-1"):
            row = {"actor": rig["name"], "root": list(root.location), "scale": list(root.scale), "parts": []}
            for child in root.children:
                if child.type != "MESH":
                    continue
                bounds = [child.matrix_world @ Vector(corner) for corner in child.bound_box]
                center = sum(bounds, Vector()) / 8
                projection = world_to_camera_view(scene, scene.camera, center)
                row["parts"].append({"name": child.name, "hide_render": child.hide_render,
                                     "world_bounds": [[min(v[i] for v in bounds) for i in range(3)], [max(v[i] for v in bounds) for i in range(3)]],
                                     "screen": list(projection), "material": child.active_material.name})
            rows.append(row)
    return rows, errors


report["actor_samples"] = {}
all_errors = []
for frame in (1, 145, 240):
    rows, errors = actor_snapshot(frame)
    report["actor_samples"][str(frame)] = rows
    all_errors.extend(errors)
report["animation_transfer_errors"] = all_errors

report["weather"] = {}
for name, minimum_vertices in (("Steam | noodle pots, tea, wok & roof vent", 1000),
                               ("Rain | awning drips & sparse night rainfall", 2000),
                               ("Embers | wok sparks", 150)):
    obj = bpy.data.objects.get(name)
    if obj is None:
        all_errors.append(f"Missing weather system {name}")
        continue
    snapshots = []
    for frame in (1, 13):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        snapshot = {"frame": frame, "vertices": len(mesh.vertices), "attributes": list(mesh.attributes.keys()),
                    "first_vertex": list(mesh.vertices[0].co) if mesh.vertices else None}
        if len(mesh.vertices) < minimum_vertices:
            all_errors.append(f"Empty or incomplete weather mesh {name} at frame {frame}")
        attribute = mesh.attributes.get("vapour_alpha")
        if attribute:
            values = [item.value for item in attribute.data]
            snapshot["alpha_range"] = [min(values), max(values)]
        evaluated.to_mesh_clear()
        snapshots.append(snapshot)
    report["weather"][name] = snapshots
    if snapshots[0]["first_vertex"] and snapshots[1]["first_vertex"]:
        movement = (Vector(snapshots[0]["first_vertex"]) - Vector(snapshots[1]["first_vertex"])).length
        report["weather"][name].append({"motion_between_frames": movement})
        if movement < 0.001:
            all_errors.append(f"Weather is static {name}")

previous_position, previous_rotation = None, None
max_step, max_angle = 0.0, 0.0
for frame in range(1, 241):
    scene.frame_set(frame)
    position = scene.camera.matrix_world.translation.copy()
    rotation = scene.camera.matrix_world.to_quaternion()
    if previous_position is not None:
        max_step = max(max_step, (position - previous_position).length)
        max_angle = max(max_angle, math.degrees(previous_rotation.rotation_difference(rotation).angle))
    previous_position, previous_rotation = position, rotation
report["camera_motion"] = {"maximum_step_per_frame": max_step, "maximum_degrees_per_frame": max_angle}
if max_step > 1.5 or max_angle > 15:
    all_errors.append("Camera path contains a discontinuity")

report["actor_travel"] = {}
for name in ("walker-0", "front-walker-0", "scooter-0", "scooter-1", "scooter-2"):
    root = next(obj for obj in scene.objects if obj.get("source_actor") == name)
    scene.frame_set(1)
    start = root.location.copy()
    scene.frame_set(240)
    distance = (root.location - start).length
    report["actor_travel"][name] = distance
    if distance < 0.5:
        all_errors.append(f"Actor does not travel {name}")

report["flicker_variation"] = {}
for name in ("Neon | rose - animated flicker", "Neon | cyan - animated flicker", "Neon | amber - animated flicker"):
    socket = bpy.data.materials[name].node_tree.nodes["Original sign flicker"].outputs[0]
    scene.frame_set(1)
    start = socket.default_value
    scene.frame_set(13)
    difference = abs(socket.default_value - start)
    report["flicker_variation"][name] = difference
    if difference < 0.00001:
        all_errors.append(f"Sign does not flicker {name}")

import hashlib
report["source_unchanged"] = hashlib.sha256((ROOT / "index.html").read_bytes()).hexdigest() == source["metadata"]["sourceSha256"]
if not report["source_unchanged"]:
    all_errors.append("The original browser diorama was modified")
report["glare"] = {name: scene.compositing_node_group.nodes["Lantern & neon halation"].inputs[name].default_value
                   for name in ("Type", "Strength", "Size", "Threshold")}
report["passed"] = not all_errors
(BLENDER / "work" / "scene_validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
summary = {key: value for key, value in report.items() if key != "actor_samples"}
print(json.dumps(summary, indent=2), flush=True)
assert not all_errors, "Scene validation failed"
print("SCENE_VALIDATION_PASSED", flush=True)
