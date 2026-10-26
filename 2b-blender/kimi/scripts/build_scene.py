"""Rebuild the editable Blender scene from the original browser diorama export.

Run from the diorama folder:
  blender -b --factory-startup --python blender/scripts/build_scene.py
"""
import bpy
import math
import json
import random
from pathlib import Path
from collections import defaultdict
from mathutils import Vector, Matrix, Quaternion

ROOT = Path(__file__).resolve().parents[2]
BLENDER = ROOT / "blender"
DATA = json.loads((BLENDER / "source" / "market.json").read_text(encoding="utf-8"))
OUT = BLENDER / "night_market.blend"
TAU = math.tau

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for collection in list(bpy.data.collections):
    bpy.data.collections.remove(collection)
for material in list(bpy.data.materials):
    bpy.data.materials.remove(material)
scene = bpy.context.scene
scene.name = "SHENZHEN | After the Rain"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.fps = 24
scene.render.fps_base = 1.0
scene.frame_start = 1
scene.frame_end = 240
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.image_settings.color_depth = "8"
scene.render.image_settings.compression = 15
scene.render.filepath = "//render/frames/market_"
scene.render.film_transparent = False
scene.render.use_file_extension = True
scene.render.use_motion_blur = False
scene.render.motion_blur_shutter = 0.3
scene.render.threads_mode = "AUTO"
scene.unit_settings.system = "METRIC"
scene.sync_mode = "FRAME_DROP"
scene.eevee.taa_render_samples = 24
scene.eevee.taa_samples = 24
scene.eevee.use_raytracing = True
scene.eevee.ray_tracing_method = "SCREEN"
scene.eevee.ray_tracing_options.resolution_scale = "2"
scene.eevee.ray_tracing_options.trace_max_roughness = 0.65
scene.eevee.ray_tracing_options.screen_trace_quality = 0.5
scene.eevee.ray_tracing_options.use_denoise = True
scene.eevee.use_fast_gi = True
scene.eevee.fast_gi_method = "AMBIENT_OCCLUSION_ONLY"
scene.eevee.fast_gi_distance = 3.0
scene.eevee.fast_gi_quality = 0.5
scene.eevee.fast_gi_ray_count = 2
scene.eevee.fast_gi_step_count = 8
scene.eevee.fast_gi_resolution = "2"
scene.eevee.shadow_pool_size = "1024"
scene.eevee.shadow_ray_count = 1
scene.eevee.shadow_step_count = 6
scene.eevee.use_volumetric_shadows = True
scene.eevee.volumetric_samples = 32
scene.eevee.volumetric_tile_size = "8"
scene.eevee.volumetric_shadow_samples = 12
scene.eevee.use_volume_custom_range = True
scene.eevee.volumetric_start = 0.2
scene.eevee.volumetric_end = 95
scene.view_settings.view_transform = "AgX"
try:
    scene.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
scene.view_settings.exposure = 0.6

world = bpy.data.worlds.new("Night | indigo ambient sky")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.025, 0.045, 0.085, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.32
scene.world = world


def collection(name, parent=None):
    result = bpy.data.collections.new(name)
    (parent.children if parent else scene.collection.children).link(result)
    return result


collections = {
    "01 | Foundation & wet streets": collection("01 | Foundation & wet streets"),
    "02 | Towers & shophouses": collection("02 | Towers & shophouses"),
    "03 | Market & street details": collection("03 | Market & street details"),
    "04 | Pixel neon & wayfinding": collection("04 | Pixel neon & wayfinding"),
    "05 | Lanterns & overhead wires": collection("05 | Lanterns & overhead wires"),
}
life = collection("06 | Market life - animated rigs")
people = collection("People | original articulated voxel actors", life)
vendors = collection("Vendors & diners", people)
walkers = collection("Walkers & customers", people)
scooters = collection("Scooters | moving & parked", life)
weather = collection("07 | Rain, steam & atmosphere")
lights = collection("08 | Motivated lighting")
lantern_lights = collection("Lanterns | warm practical light", lights)
neon_lights = collection("Neon | rose, cyan & amber bounce", lights)
film_lights = collection("Moon & soft cinematic fill", lights)
camera_collection = collection("09 | FlyCam")


def p3(value):
    return Vector((value[0], -value[2], value[1]))


def s3(value):
    return Vector((value[0], value[2], value[1]))


def color3(value):
    return tuple(min(1.0, max(0.0, channel)) for channel in value[:3])


def three_rotation(rotation):
    x, y, z = rotation
    a, b, c, d, e, f = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    source = Matrix(((c * e, -c * f, d),
                     (a * f + b * e * d, a * e - b * f * d, -b * c),
                     (b * f - a * e * d, b * e + a * f * d, a * c)))
    convert = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
    return convert @ source @ convert.transposed()


def three_matrix(item):
    rotation = three_rotation(item.get("r", (0, 0, 0))).to_4x4()
    scale = Matrix.Diagonal((*s3(item["s"]), 1))
    return Matrix.Translation(p3(item["p"])) @ rotation @ scale


VERTICES = [(-0.5, -0.5, -0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5),
            (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5), (-0.5, 0.5, 0.5)]
FACES = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def mesh_object(name, vertices, faces, target_collection, materials=(), colors=None):
    mesh = bpy.data.meshes.new(name + " | geometry")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    for material in materials:
        mesh.materials.append(material)
    if colors is not None:
        attribute = mesh.color_attributes.new(name="VoxelColor", type="FLOAT_COLOR", domain="POINT")
        attribute.data.foreach_set("color", [component for color in colors for component in (*color[:3], 1.0)])
    obj = bpy.data.objects.new(name, mesh)
    target_collection.objects.link(obj)
    if colors:
        obj.color = (*color3(colors[0]), 1)
    return obj


def boxes_object(name, items, target_collection, material):
    vertices, faces, colors = [], [], []
    for item in items:
        transform = three_matrix(item)
        start = len(vertices)
        vertices.extend(tuple(transform @ Vector(vertex)) for vertex in VERTICES)
        faces.extend(tuple(start + index for index in face) for face in FACES)
        colors.extend([item["c"]] * 8)
    return mesh_object(name, vertices, faces, target_collection, [material], colors)


def base_material(name, color=(0.2, 0.2, 0.2, 1)):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = color
    material.node_tree.nodes.clear()
    nodes, links = material.node_tree.nodes, material.node_tree.links
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (620, 60)
    return material, nodes, links, output


def voxel_material(name, roughness, metallic=0.0, coat=0.0, emission=0.0, wet=False):
    material, nodes, links, output = base_material(name)
    attribute = nodes.new("ShaderNodeVertexColor")
    attribute.layer_name = "VoxelColor"
    attribute.label = "Exact source voxel tint"
    attribute.location = (-600, 100)
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.location = (300, 60)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Coat Weight"].default_value = coat
    shader.inputs["Coat Roughness"].default_value = 0.09 if wet else 0.22
    links.new(attribute.outputs["Color"], shader.inputs["Base Color"])
    if emission:
        links.new(attribute.outputs["Color"], shader.inputs["Emission Color"])
        shader.inputs["Emission Strength"].default_value = emission
    if wet:
        geometry = nodes.new("ShaderNodeNewGeometry")
        geometry.location = (-850, -230)
        noise = nodes.new("ShaderNodeTexNoise")
        noise.location = (-610, -230)
        noise.inputs["Scale"].default_value = 28
        noise.inputs["Detail"].default_value = 2
        links.new(geometry.outputs["Position"], noise.inputs["Vector"])
        bump = nodes.new("ShaderNodeBump")
        bump.location = (30, -180)
        bump.inputs["Strength"].default_value = 0.13
        bump.inputs["Distance"].default_value = 0.022
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def glow_material(name, strength=1.0, alpha=1.0, flicker_index=None):
    material, nodes, links, output = base_material(name)
    attribute = nodes.new("ShaderNodeVertexColor")
    attribute.layer_name = "VoxelColor"
    attribute.location = (-550, 70)
    emission = nodes.new("ShaderNodeEmission")
    emission.location = (130, 80)
    emission.inputs["Strength"].default_value = strength
    links.new(attribute.outputs["Color"], emission.inputs["Color"])
    if flicker_index is not None:
        hex_color = ("ff3f65", "40f5de", "ffaf51")[flicker_index]
        channels = [int(hex_color[index:index + 2], 16) / 255 for index in (0, 2, 4)]
        tint = tuple(channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels)
        multiply = nodes.new("ShaderNodeMixRGB")
        multiply.blend_type = "MULTIPLY"
        multiply.label = "Original neon tint"
        multiply.location = (-280, 90)
        multiply.inputs[0].default_value = 1.0
        multiply.inputs[2].default_value = (*tint, 1.0)
        links.new(attribute.outputs["Color"], multiply.inputs[1])
        links.new(multiply.outputs[0], emission.inputs["Color"])
        base_strength = (3.3, 2.6, 3.0)[flicker_index]
        flicker = nodes.new("ShaderNodeValue")
        flicker.name = "Original sign flicker"
        flicker.label = "Sampled from Part 1"
        flicker.location = (-290, -170)
        for frame, values in enumerate(DATA["flickerFrames"], 1):
            flicker.outputs[0].default_value = strength * base_strength * values[flicker_index]
            flicker.outputs[0].keyframe_insert(data_path="default_value", frame=frame)
        links.new(flicker.outputs[0], emission.inputs["Strength"])
    if alpha < 1.0:
        transparent = nodes.new("ShaderNodeBsdfTransparent")
        transparent.location = (100, -140)
        mix = nodes.new("ShaderNodeMixShader")
        mix.location = (410, 70)
        mix.inputs[0].default_value = alpha
        links.new(transparent.outputs[0], mix.inputs[1])
        links.new(emission.outputs[0], mix.inputs[2])
        links.new(mix.outputs[0], output.inputs["Surface"])
        material.surface_render_method = "DITHERED"
        material.use_transparent_shadow = False
    else:
        links.new(emission.outputs[0], output.inputs["Surface"])
    return material


materials = {
    "matte": voxel_material("Voxel | painted plaster & cloth", 0.79),
    "metal": voxel_material("Voxel | aged metal & rooftop equipment", 0.36, 0.66, 0.2),
    "road": voxel_material("Street | wet basalt, procedural micro-ripples", 0.19, 0.47, 0.9, wet=True),
    "lantern": voxel_material("Lantern | warm ribbed paper", 0.65, emission=0.42),
    "emit": glow_material("Light | practical bulbs & gold lettering", 1.0),
    "windows": glow_material("Windows | occupied apartments", 0.88),
    "neonRose": glow_material("Neon | rose - animated flicker", 1.0, flicker_index=0),
    "neonCyan": glow_material("Neon | cyan - animated flicker", 1.0, flicker_index=1),
    "neonAmber": glow_material("Neon | amber - animated flicker", 1.0, flicker_index=2),
    "reflection": glow_material("Water | broken neon reflection accents", 0.55, alpha=0.30),
    "wet": voxel_material("Puddles | transparent rainwater glaze", 0.075, 0.72, 1.0, wet=True),
}
lantern_shader = next(node for node in materials["lantern"].node_tree.nodes if node.type == "BSDF_PRINCIPLED")
for link in list(lantern_shader.inputs["Emission Color"].links):
    materials["lantern"].node_tree.links.remove(link)
lantern_shader.inputs["Emission Color"].default_value = (1.0, 0.177888, 0.011137, 1)
lantern_shader.inputs["Emission Strength"].default_value = 1.2

wet_nodes = materials["wet"].node_tree
wet_shader = next(node for node in wet_nodes.nodes if node.type == "BSDF_PRINCIPLED")
wet_output = next(node for node in wet_nodes.nodes if node.type == "OUTPUT_MATERIAL")
wet_transparent = wet_nodes.nodes.new("ShaderNodeBsdfTransparent")
wet_mix = wet_nodes.nodes.new("ShaderNodeMixShader")
wet_mix.inputs[0].default_value = 0.74
wet_nodes.links.new(wet_transparent.outputs[0], wet_mix.inputs[1])
wet_nodes.links.new(wet_shader.outputs[0], wet_mix.inputs[2])
wet_nodes.links.new(wet_mix.outputs[0], wet_output.inputs["Surface"])
materials["wet"].surface_render_method = "DITHERED"
materials["wet"].use_transparent_shadow = False

batches = defaultdict(list)
for batch in DATA["staticBatches"]:
    for item in batch["items"]:
        section = "01 | Foundation & wet streets" if batch["kind"] == "reflection" else item["section"]
        kind = batch["kind"]
        batches[(section, item["assembly"], kind)].append(item)
for (section, assembly, kind), items in sorted(batches.items()):
    boxes_object(f"{assembly} | {kind}", items, collections[section], materials[kind])
print(f"STATIC: {sum(len(batch['items']) for batch in DATA['staticBatches'])} source voxels, {len(batches)} readable batches", flush=True)


def linear_keys(obj):
    if not obj.animation_data or not obj.animation_data.action:
        return
    action = obj.animation_data.action
    if hasattr(action, "fcurves"):
        curves = action.fcurves
    else:
        curves = [curve for layer in action.layers for strip in layer.strips
                  for bag in strip.channelbags for curve in bag.fcurves]
    for curve in curves:
        for key in curve.keyframe_points:
            key.interpolation = "LINEAR"


def pretty_name(name):
    return " ".join(part.capitalize() for part in name.split("-"))


def moving_part(part, frames, index):
    return any(any(abs(value - reference) > 0.00002 for value, reference in zip(frame["parts"][index][field], part[field]))
               for frame in frames for field in ("p", "r"))


for rig_index, rig in enumerate(DATA["rigs"]):
    name = pretty_name(rig["name"])
    target = scooters if "scooter" in rig["name"] else vendors if rig["name"].startswith(("vendor", "diner")) else walkers
    root = bpy.data.objects.new(name + " | rig", None)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 0.22
    target.objects.link(root)
    frames = [frame[rig_index] for frame in DATA["frames"]]
    root.rotation_mode = "QUATERNION"
    root["source_actor"] = rig["name"]
    for frame_number, pose in enumerate(frames, 1):
        root.location = p3(pose["root"]["p"])
        root.rotation_quaternion = three_rotation(pose["root"]["r"]).to_quaternion()
        root.scale = s3(pose["root"]["s"])
        root.keyframe_insert(data_path="location", frame=frame_number, group="Original root motion")
        root.keyframe_insert(data_path="rotation_quaternion", frame=frame_number, group="Original root motion")
    linear_keys(root)
    grouped = defaultdict(list)
    for index, part in enumerate(rig["parts"]):
        if not moving_part(part, frames, index):
            grouped[part["kind"]].append(part)
            continue
        material = materials[{"glow": "emit"}.get(part["kind"], part["kind"])]
        centered_part = {**part, "p": (0, 0, 0), "r": (0, 0, 0)}
        dimensions = tuple(round(value, 2) for value in part["s"])
        role = {(0.13, 0.37, 0.16): "sleeve", (0.13, 0.15, 0.14): "hand",
                (0.16, 0.58, 0.18): "leg", (0.18, 0.13, 0.29): "shoe"}.get(dimensions)
        if role:
            part_name = ("Left " if part["p"][0] < 0 else "Right ") + role
        elif dimensions == (0.18, 0.45, 0.43):
            part_name = "Front wheel" if part["p"][2] > 0 else "Rear wheel"
        else:
            part_name = f"Animated detail {index:02d}"
        obj = boxes_object(f"{name} | {part_name}", [centered_part], target, material)
        obj["source_part_index"] = index
        obj.parent = root
        obj.rotation_mode = "QUATERNION"
        for frame_number, pose in enumerate(frames, 1):
            obj.location = p3(pose["parts"][index]["p"])
            obj.rotation_quaternion = three_rotation(pose["parts"][index]["r"]).to_quaternion()
            obj.keyframe_insert(data_path="location", frame=frame_number, group="Original limb pose")
            obj.keyframe_insert(data_path="rotation_quaternion", frame=frame_number, group="Original limb pose")
        linear_keys(obj)
    for kind, parts in grouped.items():
        material = materials[{"glow": "emit"}.get(kind, kind)]
        obj = boxes_object(f"{name} | {kind} body", parts, target, material)
        obj.parent = root
print(f"LIFE: {len(DATA['rigs'])} original actor rigs, baked over 240 frames", flush=True)


def light(name, kind, location, color, energy, target_collection, radius=0.3, shadow=False, target=None, size=3.0):
    data = bpy.data.lights.new(name, kind)
    data.color = color3(color)
    data.energy = energy
    data.use_shadow = shadow
    if kind == "POINT":
        data.shadow_soft_size = radius
        data.use_shadow_jitter = True
        data.shadow_filter_radius = 1.5
    if kind == "AREA":
        data.shape = "DISK"
        data.size = size
    obj = bpy.data.objects.new(name, data)
    target_collection.objects.link(obj)
    obj.location = location
    if target is not None:
        obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj


for index, source in enumerate(DATA["lights"]):
    target = neon_lights if index < 3 else lantern_lights
    light(f"Source practical {index + 1:02d} | {['rose neon', 'cyan neon', 'amber neon'][index] if index < 3 else 'stall & lantern glow'}",
          "POINT", p3(source["p"]), source["c"], source["intensity"] * 4.5,
          target, radius=0.35, shadow=index in (3, 5, 7, 9))
for index, lantern in enumerate(DATA["lanternPlacements"]):
    light(f"Paper lantern {index + 1:02d} | warm emitter", "POINT", p3([lantern["x"], lantern["y"] - 0.06, lantern["z"]]),
          (1.0, 0.30, 0.055), 24 * lantern["scale"] ** 2, lantern_lights, radius=0.28 * lantern["scale"])
light("Moon | blue night key", "SUN", p3([-15, 28, 15]), (0.43, 0.60, 0.86), 0.75,
      film_lights, shadow=True, target=p3([0, 0, -1])).data.angle = math.radians(7)
light("Sky | broad soft overhead", "AREA", (0, 0, 27), (0.28, 0.46, 0.72), 1550,
      film_lights, target=(0, 0, 0), size=21)
light("Street | cool reflected sky", "AREA", (1, -16, 10), (0.20, 0.48, 0.63), 850,
      film_lights, target=(0, 0, 3), size=14)
light("Night market sign | rose spill", "AREA", (-7.35, -1.35, 7.2), (1.0, 0.055, 0.15), 95,
      neon_lights, target=(-2.7, -0.2, 2.3), size=3)
light("Street food sign | cyan spill", "AREA", (7.45, 3.1, 6.4), (0.035, 1.0, 0.65), 85,
      neon_lights, target=(2.7, 0, 2.0), size=2.7)

reflection_data = bpy.data.lightprobes.new("Street | wet reflection plane", "PLANE")
reflection_data.influence_distance = 38
reflection_data.clip_start = 0.06
reflection = bpy.data.objects.new("Street | planar neon reflections", reflection_data)
film_lights.objects.link(reflection)
reflection.location = (0, 0, 0.09)


def transparent_emission(name, color, strength, opacity):
    material, nodes, links, output = base_material(name, (*color, opacity))
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (*color, 1)
    emission.inputs["Strength"].default_value = strength
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = opacity
    links.new(transparent.outputs[0], mix.inputs[1])
    links.new(emission.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], output.inputs["Surface"])
    material.surface_render_method = "DITHERED"
    material.use_transparent_shadow = False
    return material


steam_material, nodes, links, output = base_material("Steam | soft translucent voxel vapour", (0.52, 0.66, 0.68, 0.18))
attribute = nodes.new("ShaderNodeAttribute")
attribute.attribute_name = "vapour_alpha"
attribute.location = (-500, 100)
multiply = nodes.new("ShaderNodeMath")
multiply.operation = "MULTIPLY"
multiply.inputs[1].default_value = 0.22
links.new(attribute.outputs["Fac"], multiply.inputs[0])
shader = nodes.new("ShaderNodeBsdfPrincipled")
shader.inputs["Base Color"].default_value = (0.72, 0.82, 0.80, 1)
shader.inputs["Roughness"].default_value = 1.0
shader.inputs["Emission Color"].default_value = (0.36, 0.48, 0.47, 1)
shader.inputs["Emission Strength"].default_value = 0.28
transparent = nodes.new("ShaderNodeBsdfTransparent")
mix = nodes.new("ShaderNodeMixShader")
links.new(multiply.outputs[0], mix.inputs[0])
links.new(transparent.outputs[0], mix.inputs[1])
links.new(shader.outputs[0], mix.inputs[2])
links.new(mix.outputs[0], output.inputs["Surface"])
steam_material.surface_render_method = "DITHERED"
steam_material.use_transparent_shadow = False
rain_material = transparent_emission("Rain | fine blue-silver streaks", (0.28, 0.50, 0.68), 0.8, 0.24)
ember_material, nodes, links, output = base_material("Fire | floating wok embers", (1.0, 0.36, 0.04, 1))
emission = nodes.new("ShaderNodeEmission")
emission.inputs["Color"].default_value = (1.0, 0.27, 0.022, 1)
emission.inputs["Strength"].default_value = 3.0
links.new(emission.outputs[0], output.inputs["Surface"])


def node(tree, node_type, name, x=0, y=0):
    result = tree.nodes.new(node_type)
    result.name = name
    result.label = name
    result.location = (x, y)
    return result


class Graph:
    def __init__(self, tree):
        self.tree = tree
        self.links = tree.links
        self.count = 0

    def connect(self, value, socket):
        if isinstance(value, bpy.types.NodeSocket):
            self.links.new(value, socket)
        else:
            socket.default_value = value

    def math(self, operation, a, b=None, label=None):
        result = node(self.tree, "ShaderNodeMath", label or operation.title(), (self.count % 8) * 170 - 1200, -(self.count // 8) * 170)
        self.count += 1
        result.operation = operation
        self.connect(a, result.inputs[0])
        if b is not None:
            self.connect(b, result.inputs[1])
        return result.outputs[0]

    def vector(self, x, y, z, label="Position"):
        result = node(self.tree, "ShaderNodeCombineXYZ", label, 900, 100)
        for value, socket in zip((x, y, z), result.inputs):
            self.connect(value, socket)
        return result.outputs[0]

    def attribute(self, name):
        result = node(self.tree, "GeometryNodeInputNamedAttribute", name, -1500, -200 * (self.count % 5))
        result.data_type = "FLOAT"
        result.inputs["Name"].default_value = name
        self.count += 1
        return result.outputs["Attribute"]

    def instance_cloud(self, name, positions, attributes, position, scale, material, rotation=None, alpha=None, tree=None):
        mesh = bpy.data.meshes.new(name + " | emitter points")
        mesh.from_pydata(positions, [], [])
        for attribute_name, values in attributes.items():
            attr = mesh.attributes.new(attribute_name, "FLOAT", "POINT")
            attr.data.foreach_set("value", values)
        obj = bpy.data.objects.new(name, mesh)
        weather.objects.link(obj)
        if tree is None:
            tree = bpy.data.node_groups.new(name + " | deterministic motion", "GeometryNodeTree")
        tree.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        tree.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
        group_in = node(tree, "NodeGroupInput", "Emitter positions", -1700, 400)
        group_out = node(tree, "NodeGroupOutput", "Visible voxels", 1900, 400)
        set_position = node(tree, "GeometryNodeSetPosition", "Advect particles", 1100, 400)
        self.links.new(group_in.outputs["Geometry"], set_position.inputs["Geometry"])
        self.links.new(position, set_position.inputs["Position"])
        geometry = set_position.outputs["Geometry"]
        if alpha is not None:
            store = node(tree, "GeometryNodeStoreNamedAttribute", "Fade over particle lifetime", 1300, 400)
            store.data_type = "FLOAT"
            store.domain = "POINT"
            store.inputs["Name"].default_value = "vapour_alpha"
            self.links.new(geometry, store.inputs["Geometry"])
            self.links.new(alpha, store.inputs["Value"])
            geometry = store.outputs["Geometry"]
        cube = node(tree, "GeometryNodeMeshCube", "One voxel", 1100, 50)
        cube.inputs["Size"].default_value = (1, 1, 1)
        assign = node(tree, "GeometryNodeSetMaterial", "Particle material", 1300, 50)
        assign.inputs["Material"].default_value = material
        self.links.new(cube.outputs["Mesh"], assign.inputs["Geometry"])
        instances = node(tree, "GeometryNodeInstanceOnPoints", "Instanced weather", 1550, 400)
        self.links.new(geometry, instances.inputs["Points"])
        self.links.new(assign.outputs["Geometry"], instances.inputs["Instance"])
        self.connect(scale, instances.inputs["Scale"])
        if rotation is not None:
            self.links.new(rotation, instances.inputs["Rotation"])
        realize = node(tree, "GeometryNodeRealizeInstances", "Readable shader attributes", 1750, 400)
        self.links.new(instances.outputs["Instances"], realize.inputs["Geometry"])
        self.links.new(realize.outputs["Geometry"], group_out.inputs["Geometry"])
        modifier = obj.modifiers.new(name + " | time-driven", "NODES")
        modifier.node_group = tree
        obj["animation"] = "Geometry Nodes / Scene Time; no wall-clock dependencies"
        return obj


particles = DATA["steamParticles"]
g = Graph.__new__(Graph)
steam_tree = bpy.data.node_groups.new("TEMP", "GeometryNodeTree")
g.tree, g.links, g.count = steam_tree, steam_tree.links, 0
seconds = node(steam_tree, "GeometryNodeInputSceneTime", "Seconds", -1900, 650).outputs["Seconds"]
phase = g.attribute("source_phase")
speed = g.attribute("source_speed")
seed = g.attribute("source_seed")
sway = g.attribute("source_sway")
smoke = g.attribute("is_smoke")
age = g.math("FRACT", g.math("ADD", phase, g.math("MULTIPLY", seconds, speed)))
sine = g.math("SINE", g.math("MULTIPLY", age, math.pi))
visibility = g.math("POWER", sine, 1.4)
size = g.math("MULTIPLY", g.math("ADD", 0.10, g.math("MULTIPLY", age, 0.47)), g.math("MAXIMUM", 0.08, visibility))
drift = g.math("ADD", 0.4, g.math("MULTIPLY", smoke, 0.45))
lift = g.math("ADD", 2.05, g.math("MULTIPLY", smoke, 0.60))
x = g.math("ADD", g.math("MULTIPLY", g.math("SINE", g.math("ADD", g.math("MULTIPLY", age, 4.5), g.math("MULTIPLY", seed, TAU))), g.math("MULTIPLY", age, 0.3)), g.math("MULTIPLY", age, drift))
y = g.math("MULTIPLY", g.math("COSINE", g.math("ADD", g.math("MULTIPLY", age, sway), g.math("MULTIPLY", seed, 3))), g.math("MULTIPLY", age, -0.24))
z = g.math("MULTIPLY", age, lift)
offset = g.vector(x, y, z, "Rising steam & drifting smoke")
position_node = node(steam_tree, "GeometryNodeInputPosition", "Original cooking source", 500, 650)
add = node(steam_tree, "ShaderNodeVectorMath", "Source + animated offset", 850, 400)
add.operation = "ADD"
g.links.new(position_node.outputs["Position"], add.inputs[0])
g.links.new(offset, add.inputs[1])
scale = g.vector(g.math("MULTIPLY", size, 1.15), size, g.math("MULTIPLY", size, 0.83), "Vapour expansion")
rotation = g.vector(g.math("MULTIPLY", age, 0.7), g.math("MULTIPLY", age, -0.35), g.math("ADD", g.math("MULTIPLY", seed, 3), age), "Slow tumble")
g.instance_cloud("Steam | noodle pots, tea, wok & roof vent", [p3(p["source"]) for p in particles],
                 {"source_phase": [p["phase"] for p in particles], "source_speed": [p["speed"] for p in particles],
                  "source_seed": [p["seed"] for p in particles], "source_sway": [p["sway"] for p in particles],
                  "is_smoke": [float(p["smoke"]) for p in particles]},
                 add.outputs["Vector"], scale, steam_material, rotation, g.math("MULTIPLY", visibility, g.math("ADD", 1.0, g.math("MULTIPLY", smoke, -0.55))), tree=steam_tree)
steam_tree.name = "Steam | persistent source-driven motion"

random.seed(48271)
rain_positions, phases, heights = [], [], []
for drip in DATA["drips"]:
    rain_positions.append((drip["x"], -drip["z"], 0))
    phases.append(drip["phase"])
    heights.append(drip["height"])
for index in range(200):
    if index < 115:
        x, y = random.uniform(-2.6, 2.6), random.uniform(-7, 10.5)
    else:
        x, y = random.uniform(-13.5, 13.5), random.uniform(-11, -7.4)
    rain_positions.append((x, y, 0))
    phases.append(random.random())
    heights.append(random.uniform(6, 14))
tree = bpy.data.node_groups.new("Rain motion", "GeometryNodeTree")
g = Graph(tree)
time = node(tree, "GeometryNodeInputSceneTime", "Seconds", -1600, 700).outputs["Seconds"]
phase, height = g.attribute("rain_phase"), g.attribute("fall_height")
age = g.math("FRACT", g.math("ADD", phase, g.math("MULTIPLY", time, 0.8)))
z = g.math("ADD", 0.10, g.math("MULTIPLY", g.math("SUBTRACT", 1.0, age), height))
position = node(tree, "GeometryNodeInputPosition", "Rain column", 300, 600)
separate = node(tree, "ShaderNodeSeparateXYZ", "Preserve column X / Y", 500, 600)
g.links.new(position.outputs["Position"], separate.inputs[0])
location = g.vector(separate.outputs["X"], separate.outputs["Y"], z, "Falling rain")
g.instance_cloud("Rain | awning drips & sparse night rainfall", rain_positions,
                 {"rain_phase": phases, "fall_height": heights}, location,
                 (0.011, 0.011, 0.14), rain_material, tree=tree)
tree.name = "Rain | persistent gravity-driven motion"

tree = bpy.data.node_groups.new("Embers | source-driven motion", "GeometryNodeTree")
g = Graph(tree)
time = node(tree, "GeometryNodeInputSceneTime", "Seconds", -1600, 650).outputs["Seconds"]
phase, ember_index = g.attribute("ember_phase"), g.attribute("ember_index")
age = g.math("FRACT", g.math("ADD", phase, g.math("MULTIPLY", time, 0.5)))
x = g.math("MULTIPLY", g.math("SINE", g.math("ADD", g.math("MULTIPLY", ember_index, 5.3), g.math("MULTIPLY", age, 3))), g.math("MULTIPLY", age, 0.33))
y = g.math("MULTIPLY", g.math("COSINE", g.math("ADD", g.math("MULTIPLY", ember_index, 3.5), g.math("MULTIPLY", age, 2))), g.math("MULTIPLY", age, -0.33))
z = g.math("MULTIPLY", age, 1.45)
position = node(tree, "GeometryNodeInputPosition", "Wok fire source", 400, 500)
add = node(tree, "ShaderNodeVectorMath", "Rising ember position", 800, 400)
add.operation = "ADD"
g.links.new(position.outputs["Position"], add.inputs[0])
g.links.new(g.vector(x, y, z, "Heat drift"), add.inputs[1])
size = g.math("MAXIMUM", 0.001, g.math("MULTIPLY", g.math("SINE", g.math("MULTIPLY", age, math.pi)), 0.033))
g.instance_cloud("Embers | wok sparks", [(4.23, 4.0, 1.7)] * 20,
                 {"ember_phase": [index / 20 for index in range(20)], "ember_index": list(range(20))},
                 add.outputs["Vector"], g.vector(size, size, size, "Spark size"), ember_material, tree=tree)

for index in range(14):
    items = []
    for side in range(4):
        x = (1 if side == 1 else -1) if side < 2 else 0
        y = (1 if side == 3 else -1) if side >= 2 else 0
        sx, sy = (0.012, 2.0) if side < 2 else (2.0, 0.012)
        items.append({"p": (x, y, 0), "s": (sx, sy, 0.006), "r": (0, 0, 0), "c": (0.23, 0.38, 0.42)})
    material = glow_material(f"Ripple {index + 1:02d} | fading rain ring", 0.65, alpha=0.16)
    obj = boxes_object(f"Rain ripple {index + 1:02d} | expanding square", items, weather, material)
    obj.location = (math.sin(index * 12.37) * 2.1, -(index * 3.71 % 14 - 5.4), 0.066)
    mix = next(node for node in material.node_tree.nodes if node.type == "MIX_SHADER")
    for frame in range(1, 241):
        age = (index / 14 + (frame - 1) / 24 / 3) % 1
        radius = 0.06 + age * 0.53
        obj.scale = (radius, radius, 1)
        obj.keyframe_insert(data_path="scale", frame=frame)
        mix.inputs[0].default_value = 0.16 * max(0.001, 1 - age)
        mix.inputs[0].keyframe_insert(data_path="default_value", frame=frame)

fog_material, nodes, links, output = base_material("Atmosphere | thin blue night mist")
volume = nodes.new("ShaderNodeVolumePrincipled")
volume.inputs["Density"].default_value = 0.004
volume.inputs["Color"].default_value = (0.38, 0.52, 0.65, 1)
volume.inputs["Anisotropy"].default_value = 0.25
links.new(volume.outputs["Volume"], output.inputs["Volume"])
fog = mesh_object("Atmosphere | local humid-night haze",
                  [(x * 17, y * 14, z * 16 + 12) for x, y, z in VERTICES], FACES, weather, [fog_material])
fog.display_type = "WIRE"

camera_keys = [
    (0.0, [25, 19, 32], [0, 6.0, -1], 49),
    (2.0, [13, 10.5, 21], [0, 3.0, 1], 47),
    (4.0, [2.0, 3.25, 10.3], [0, 2.0, 0], 55),
    (6.0, [0.3, 2.6, 4.3], [0.5, 1.9, -2.8], 55),
    (8.0, [-0.65, 2.4, 0.9], [-3.8, 1.9, -3.0], 54),
    (10.0, [0.15, 2.65, -0.6], [-4.2, 2.1, -3.8], 52),
]


def spline(points, t):
    scaled = min(0.999999999, max(0, t)) * (len(points) - 1)
    index = int(scaled)
    u = scaled - index
    p1, p2 = points[index], points[index + 1]
    p0 = points[max(0, index - 1)]
    p3_ = points[min(len(points) - 1, index + 2)]
    d0 = max(0.0001, (p1 - p0).length ** 0.5)
    d1 = max(0.0001, (p2 - p1).length ** 0.5)
    d2 = max(0.0001, (p3_ - p2).length ** 0.5)
    tangent1 = ((p1 - p0) / d0 - (p2 - p0) / (d0 + d1) + (p2 - p1) / d1) * d1
    tangent2 = ((p2 - p1) / d1 - (p3_ - p1) / (d1 + d2) + (p3_ - p2) / d2) * d1
    return (2 * u ** 3 - 3 * u ** 2 + 1) * p1 + (u ** 3 - 2 * u ** 2 + u) * tangent1 + (-2 * u ** 3 + 3 * u ** 2) * p2 + (u ** 3 - u ** 2) * tangent2


camera_data = bpy.data.cameras.new("FlyCam | 24mm sensor, animated cinema lens")
camera = bpy.data.objects.new("FlyCam", camera_data)
camera_collection.objects.link(camera)
scene.camera = camera
camera.rotation_mode = "QUATERNION"
camera_data.sensor_fit = "VERTICAL"
camera_data.sensor_height = 24
camera_data.clip_start = 0.08
camera_data.clip_end = 180
camera_data.dof.use_dof = True
camera_data.dof.aperture_fstop = 7.1
camera_data.dof.aperture_blades = 7
camera_data.passepartout_alpha = 1
previous_rotation = None
positions = [p3(key[1]) for key in camera_keys]
targets = [p3(key[2]) for key in camera_keys]
for frame in range(1, 241):
    time = (frame - 1) / 24
    u = time / 10
    position, target = spline(positions, u), spline(targets, u)
    rotation = (target - position).to_track_quat("-Z", "Y")
    if previous_rotation and rotation.dot(previous_rotation) < 0:
        rotation.negate()
    previous_rotation = rotation.copy()
    camera.location = position
    camera.rotation_quaternion = rotation
    camera.keyframe_insert(data_path="location", frame=frame, group="Cinematic dolly")
    camera.keyframe_insert(data_path="rotation_quaternion", frame=frame, group="Look target")
    segment = min(len(camera_keys) - 2, int(u * (len(camera_keys) - 1)))
    blend = u * (len(camera_keys) - 1) - segment
    blend = blend * blend * (3 - 2 * blend)
    fov = camera_keys[segment][3] * (1 - blend) + camera_keys[segment + 1][3] * blend
    camera_data.lens = 12 / math.tan(math.radians(fov) / 2)
    camera_data.dof.focus_distance = (target - position).length
    camera_data.keyframe_insert(data_path="lens", frame=frame)
    camera_data.dof.keyframe_insert(data_path="focus_distance", frame=frame)
linear_keys(camera)
linear_keys(camera_data)

compositor = bpy.data.node_groups.new("Film | gentle neon halation", "CompositorNodeTree")
scene.compositing_node_group = compositor
scene.use_nodes = True
scene.render.use_compositing = True
compositor.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
render_layer = compositor.nodes.new("CompositorNodeRLayers")
render_layer.location = (-350, 50)
glow = compositor.nodes.new("CompositorNodeGlare")
glow.name = "Lantern & neon halation"
glow.label = "Restrained cinematic bloom"
glow.location = (-50, 50)
glow.inputs["Type"].default_value = "Fog Glow"
glow.inputs["Quality"].default_value = "High"
glow.inputs["Threshold"].default_value = 0.65
glow.inputs["Smoothness"].default_value = 0.18
glow.inputs["Strength"].default_value = 2.6
glow.inputs["Size"].default_value = 0.65
output = compositor.nodes.new("NodeGroupOutput")
output.location = (250, 50)
compositor.links.new(render_layer.outputs["Image"], glow.inputs["Image"])
compositor.links.new(glow.outputs["Image"], output.inputs["Image"])

for frame, label in [(1, "01 - The city after rain"), (49, "02 - Lantern gate"), (97, "03 - Enter the market"),
                     (145, "04 - Dinner & steam"), (193, "05 - Neon aisle"), (240, "06 - Deep market")]:
    scene.timeline_markers.new(label, frame=frame)

clearance = []
for frame in range(1, 241):
    scene.frame_set(frame)
    point = camera.location
    for obstacle in DATA["obstacles"]:
        lower, upper = obstacle["min"], obstacle["max"]
        if lower[0] < point.x < upper[0] and -upper[2] < point.y < -lower[2] and lower[1] < point.z < upper[1]:
            clearance.append(frame)
scene.frame_set(49)
scene["source_file"] = "index.html"
scene["source_sha256"] = DATA["metadata"]["sourceSha256"]
scene["source_voxels"] = DATA["metadata"]["staticVoxels"]
scene["animated_rigs"] = len(DATA["rigs"])
scene["camera_clearance_violations"] = clearance
scene["render_budget"] = "Eevee / AMD Radeon RX 590 / 240 frames / under 25 minutes"
scene["delivery"] = "1920 x 1080 / 24 fps / exactly 240 frames"
scene["animation_notes"] = "Original actor poses are baked every frame. Weather is deterministic Geometry Nodes using Scene Time. No downloaded assets."
notes = bpy.data.texts.new("START HERE | Night Market")
notes.write("SHENZHEN - AFTER THE RAIN\n\n"
            "The exact voxel transforms, colors, signs, building layout, actor rigs and motion were exported from the unmodified Part 1 index.html.\n"
            "Collections 01-05 contain the source diorama. Collection 06 contains the original animated actors.\n"
            "Collection 07 contains procedural rain, rising steam, ripples and atmosphere. Collection 08 contains motivated lighting.\n"
            "FlyCam is the only camera. The timeline is 1-240, 24 fps, 1920 x 1080.\n"
            "The scene is self-contained: no external models, image textures, HDRIs, fonts or add-ons.\n"
            "Use the scripts folder to rebuild from source or resume the numbered-frame render.\n")
notes.use_fake_user = True

for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == "VIEW_3D":
            space = area.spaces.active
            space.region_3d.view_perspective = "CAMERA"
            space.region_3d.view_camera_zoom = 0
            space.clip_end = 180
            space.shading.type = "MATERIAL"
            space.shading.use_scene_world = True
            space.shading.use_scene_lights = True
            if hasattr(space.shading, "use_compositor"):
                space.shading.use_compositor = "CAMERA"
            space.overlay.show_overlays = False
        elif area.type == "DOPESHEET_EDITOR":
            area.spaces.active.show_region_ui = False

spec = {
    "title": DATA["metadata"]["title"],
    "source_sha256": DATA["metadata"]["sourceSha256"],
    "quality_tier": "authored procedural voxel diorama - source-faithful production",
    "explicit_constraints": DATA["metadata"]["explicitConstraints"],
    "inferred_details": DATA["metadata"]["inferredDetails"],
    "world": {"width": 28.2, "depth": 23, "foundation": "flat city block", "seed": DATA["metadata"]["seed"]},
    "regions": ["Foundation & wet paving", "Nine towers & shophouses", "Six food stalls & outdoor dining", "Pixel neon", "Lantern canopy", "Animated market life"],
    "landmarks": {"gate": [0, 5.78, 7.35], "tallest_tower": [2.1, 22, -9], "stall_rows_x": [-5, 5]},
    "camera_path": [{"time": key[0], "position": key[1], "target": key[2], "vertical_fov": key[3]} for key in camera_keys],
    "camera_collision_frames": clearance,
    "render": {"engine": "BLENDER_EEVEE", "width": 1920, "height": 1080, "fps": 24, "frames": 240, "samples": 24},
    "assets": {"downloaded": 0, "textures": 0, "models": 0, "hdris": 0, "addons": 0}
}
(BLENDER / "source" / "scene_spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
print("CAMERA COLLISION FRAMES", clearance, flush=True)
bpy.ops.object.select_all(action="DESELECT")
camera.select_set(True)
bpy.context.view_layer.objects.active = camera
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), compress=True)
print("SAVED", OUT, flush=True)
