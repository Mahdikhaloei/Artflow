import os
import sys

import bpy

blend_file = sys.argv[-3]
image_path = sys.argv[-2]
output_path = sys.argv[-1]

bpy.ops.wm.open_mainfile(filepath=blend_file)

obj = bpy.data.objects["BIS Template Area"]
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

bpy.ops.object.mode_set(mode="OBJECT")

mat = bpy.data.materials.new(name="ImageMaterial")
mat.use_nodes = True

bsdf = mat.node_tree.nodes.get("Principled BSDF")
tex_image = mat.node_tree.nodes.new("ShaderNodeTexImage")

if os.path.exists(image_path):
    img = bpy.data.images.load(image_path)
    tex_image.image = img
else:
    raise FileNotFoundError(f"Image not found: {image_path}")

mat.node_tree.links.new(bsdf.inputs["Base Color"], tex_image.outputs["Color"])
mat.node_tree.links.new(bsdf.inputs["Alpha"], tex_image.outputs["Alpha"])

mat.blend_method = "BLEND"
mat.use_backface_culling = False

if obj.data.materials:
    obj.data.materials[0] = mat
else:
    obj.data.materials.append(mat)

bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.uv.smart_project()
bpy.ops.object.mode_set(mode="OBJECT")

camera = bpy.data.objects.get("Camera")

bpy.context.scene.camera = camera
bpy.context.scene.render.filepath = output_path

bpy.context.scene.view_settings.exposure = 1.5

bpy.context.scene.world.use_nodes = True
bg = bpy.context.scene.world.node_tree.nodes["Background"]
bg.inputs[1].default_value = 1.5

bpy.context.scene.render.engine = "CYCLES"
bpy.context.scene.cycles.samples = 512
bpy.context.scene.cycles.use_denoising = False
bpy.context.scene.cycles.use_adaptive_sampling = True
bpy.context.scene.render.image_settings.color_depth = "16"
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1920
bpy.context.scene.render.resolution_percentage = 100
bpy.context.scene.render.image_settings.file_format = "PNG"
bpy.context.scene.render.image_settings.color_depth = "16"
bpy.context.scene.render.image_settings.compression = 0
camera.data.lens = 50
camera.location.y += 1.0

bpy.ops.render.render(write_still=True)
