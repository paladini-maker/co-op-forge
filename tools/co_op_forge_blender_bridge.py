"""Co-Op Forge: Rig JSON -> Blender armature bridge.

Run this file in Blender's Text Editor, or install it as an add-on.
The operator reads the JSON exported by Co-Op Forge and builds a simple,
editable humanoid armature. Optional nearest-segment weights are RIGID
(one vertex belongs to exactly one deform group), as a GoldSrc-oriented
blockout. Inspect and correct the result before SMD/QC export or compilation.

This does not import binary GoldSrc MDL files, retarget existing animations,
export SMD, or compile MDL. It generates a Blender scene rig from 2D guide
markers, not a reconstruction of an existing model's native skeleton.

Complexity: rigid weighting is O(V * B), where V is mesh vertices and B is
created bones. Temporary world-vertex positions require O(V) memory.
"""

from __future__ import annotations

bl_info = {
    "name": "Co-Op Forge Rig JSON Bridge",
    "author": "OpenAI",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > Co-Op Forge",
    "description": "Create a Blender armature from a Co-Op Forge rig setup JSON",
    "category": "Rigging",
}


import json
import math
import os
from typing import Any

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector


JOINT_KEYS = {
    "chin", "shoulder_l", "shoulder_r", "elbow_l", "elbow_r",
    "wrist_l", "wrist_r", "pelvis", "knee_l", "knee_r", "ankle_l", "ankle_r",
}

# Segment tuples: (Blender bone name, head marker, tail marker, parent bone).
BONE_DEFINITIONS = (
    ("spine", "pelvis", "chin", None),
    ("head", "chin", "head_top", "spine"),
    ("clavicle.L", "chin", "shoulder_l", "spine"),
    ("upperarm.L", "shoulder_l", "elbow_l", "clavicle.L"),
    ("forearm.L", "elbow_l", "wrist_l", "upperarm.L"),
    ("clavicle.R", "chin", "shoulder_r", "spine"),
    ("upperarm.R", "shoulder_r", "elbow_r", "clavicle.R"),
    ("forearm.R", "elbow_r", "wrist_r", "upperarm.R"),
    ("thigh.L", "pelvis", "knee_l", "spine"),
    ("calf.L", "knee_l", "ankle_l", "thigh.L"),
    ("thigh.R", "pelvis", "knee_r", "spine"),
    ("calf.R", "knee_r", "ankle_r", "thigh.R"),
)


class RigBridgeError(RuntimeError):
    """Raised when the supplied setup or target object is not usable."""


def _number(value: Any, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise RigBridgeError(f"Invalid numeric value for {label}.") from exc
    if not math.isfinite(number):
        raise RigBridgeError(f"Non-finite numeric value for {label}.")
    return number


def _load_rig_json(filepath: str) -> dict[str, Any]:
    if not filepath or not os.path.isfile(filepath):
        raise RigBridgeError("Select a valid Co-Op Forge rig setup JSON file.")
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RigBridgeError(f"Could not read JSON: {exc}") from exc

    if not isinstance(data, dict) or not isinstance(data.get("joints"), dict):
        raise RigBridgeError("JSON does not contain a 'joints' object. Export a rig setup from Co-Op Forge.")
    joints = data["joints"]
    missing = sorted(JOINT_KEYS - set(joints.keys()))
    if missing:
        raise RigBridgeError("Rig JSON is missing required markers: " + ", ".join(missing))

    clean: dict[str, tuple[float, float]] = {}
    for key in JOINT_KEYS:
        point = joints.get(key)
        if not isinstance(point, dict):
            raise RigBridgeError(f"Joint '{key}' must contain x and y values.")
        clean[key] = (_number(point.get("x"), f"{key}.x"), _number(point.get("y"), f"{key}.y"))
    return {"source": data, "joints": clean}


def _target_bounds(mesh_obj: bpy.types.Object | None, requested_height: float) -> tuple[Vector, float, float, float]:
    """Return world-space model center and size; fallback dimensions for an unbound rig."""
    if mesh_obj is None:
        height = max(0.1, min(5.0, requested_height))
        width = height * 0.6
        return Vector((0.0, 0.0, 0.0)), width, height, height * 0.12

    corners = [mesh_obj.matrix_world @ Vector(corner) for corner in mesh_obj.bound_box]
    min_x, max_x = min(p.x for p in corners), max(p.x for p in corners)
    min_y, max_y = min(p.y for p in corners), max(p.y for p in corners)
    min_z, max_z = min(p.z for p in corners), max(p.z for p in corners)
    width, depth, height = max_x - min_x, max_y - min_y, max_z - min_z
    if height < 1e-5:
        height = max(0.1, min(5.0, requested_height))
        min_z = mesh_obj.matrix_world.translation.z
    if width < 1e-5:
        width = height * 0.6
    center = Vector(((min_x + max_x) * 0.5, (min_y + max_y) * 0.5, min_z))
    return center, width, height, depth


def _map_joints_to_world(joints: dict[str, tuple[float, float]], center: Vector,
                         width: float, height: float) -> dict[str, Vector]:
    wrist_l_x, wrist_r_x = joints["wrist_l"][0], joints["wrist_r"][0]
    span = abs(wrist_r_x - wrist_l_x)
    if span < 1.0:
        span = 284.0
    mid_x = (wrist_l_x + wrist_r_x) * 0.5
    x_scale = width / span

    ankle_y = (joints["ankle_l"][1] + joints["ankle_r"][1]) * 0.5
    chin_y = joints["chin"][1]
    top_y = min(chin_y - max(30.0, (ankle_y - chin_y) * 0.14), ankle_y - 1.0)
    vertical_span = max(1.0, ankle_y - top_y)
    z_scale = height / vertical_span

    result: dict[str, Vector] = {}
    for key, (x, y) in joints.items():
        world_x = center.x + (x - mid_x) * x_scale
        world_z = center.z + (ankle_y - y) * z_scale
        result[key] = Vector((world_x, center.y, world_z))

    # The browser marker is the chin, not the top of the head. Estimate a short head tail.
    result["head_top"] = result["chin"] + Vector((0.0, 0.0, max(height * 0.1, 0.06)))
    return result


def _point_segment_distance_sq(point: Vector, head: Vector, tail: Vector) -> float:
    segment = tail - head
    length_sq = segment.length_squared
    if length_sq <= 1e-12:
        return (point - head).length_squared
    t = max(0.0, min(1.0, (point - head).dot(segment) / length_sq))
    closest = head + t * segment
    return (point - closest).length_squared


def _rigid_bind(mesh_obj: bpy.types.Object, arm_obj: bpy.types.Object,
                segments: list[tuple[str, Vector, Vector]], replace_groups: bool) -> int:
    if mesh_obj.type != "MESH":
        raise RigBridgeError("The target object must be a mesh.")
    if len(mesh_obj.data.vertices) == 0:
        raise RigBridgeError("The selected mesh contains no vertices.")
    if mesh_obj.vertex_groups and not replace_groups:
        raise RigBridgeError(
            "The mesh already has vertex groups. Enable 'Replace existing vertex groups' only if you intend to overwrite them, "
            "or run without rigid weighting to create the armature only."
        )

    # Cache original world-space positions before changing the parent/modifier stack.
    world_positions = [mesh_obj.matrix_world @ vertex.co for vertex in mesh_obj.data.vertices]
    if replace_groups:
        for group in list(mesh_obj.vertex_groups):
            mesh_obj.vertex_groups.remove(group)

    groups = {name: mesh_obj.vertex_groups.new(name=name) for name, _, _ in segments}
    assigned = 0
    for vertex_index, point in enumerate(world_positions):
        bone_name = min(segments, key=lambda seg: _point_segment_distance_sq(point, seg[1], seg[2]))[0]
        groups[bone_name].add([vertex_index], 1.0, "REPLACE")
        assigned += 1

    modifier = mesh_obj.modifiers.new(name="Co-Op Forge Armature", type="ARMATURE")
    modifier.object = arm_obj
    modifier.use_vertex_groups = True

    old_world = mesh_obj.matrix_world.copy()
    mesh_obj.parent = arm_obj
    mesh_obj.matrix_world = old_world
    return assigned


def _build_armature(context: bpy.types.Context, rig: dict[str, Any], filepath: str,
                    bind_rigid_weights: bool, replace_groups: bool) -> tuple[bpy.types.Object, int]:
    active = context.view_layer.objects.active
    mesh_obj = active if active and active.type == "MESH" else None
    if bind_rigid_weights and mesh_obj is None:
        raise RigBridgeError("Select the target mesh object before importing the rig JSON, or disable 'Assign rigid weights'.")
    if bind_rigid_weights and mesh_obj and mesh_obj.vertex_groups and not replace_groups:
        raise RigBridgeError("Selected mesh already has vertex groups. Tick 'Replace existing vertex groups' only if overwrite is intended.")

    source = rig["source"]
    requested_height = _number(source.get("height_meters", 1.8), "height_meters")
    center, width, height, _depth = _target_bounds(mesh_obj, requested_height)
    points = _map_joints_to_world(rig["joints"], center, width, height)

    arm_name = "CoOpForge_Rig"
    if arm_name in bpy.data.objects:
        raise RigBridgeError(f"An object named '{arm_name}' already exists. Rename it or remove the previous generated rig first.")

    arm_data = bpy.data.armatures.new(arm_name)
    arm_obj = bpy.data.objects.new(arm_name, arm_data)
    context.scene.collection.objects.link(arm_obj)
    arm_obj.show_in_front = True
    arm_data.display_type = "STICK"

    created_segments: list[tuple[str, Vector, Vector]] = []
    try:
        # Switch to Object Mode before editing armature data.
        if context.object and context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        arm_obj.select_set(True)
        context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode="EDIT")
        edit_bones: dict[str, bpy.types.EditBone] = {}

        for bone_name, head_key, tail_key, parent_name in BONE_DEFINITIONS:
            head, tail = points[head_key].copy(), points[tail_key].copy()
            if (tail - head).length < 0.005:
                tail.z += 0.02
            bone = arm_data.edit_bones.new(bone_name)
            bone.head, bone.tail = head, tail
            edit_bones[bone_name] = bone
            created_segments.append((bone_name, head.copy(), tail.copy()))

        for bone_name, _head_key, _tail_key, parent_name in BONE_DEFINITIONS:
            if parent_name:
                bone = edit_bones[bone_name]
                parent = edit_bones[parent_name]
                bone.parent = parent
                bone.use_connect = (bone.head - parent.tail).length < 1e-4

        bpy.ops.object.mode_set(mode="OBJECT")
        assigned = 0
        if bind_rigid_weights and mesh_obj:
            assigned = _rigid_bind(mesh_obj, arm_obj, created_segments, replace_groups)
        else:
            assigned = 0

        # Keep the source mesh and generated rig selected for inspection.
        bpy.ops.object.select_all(action="DESELECT")
        arm_obj.select_set(True)
        if mesh_obj:
            mesh_obj.select_set(True)
        context.view_layer.objects.active = arm_obj

        report = {
            "bridge": "Co-Op Forge Rig JSON Bridge",
            "source_json": os.path.abspath(filepath),
            "target_mesh": mesh_obj.name if mesh_obj else None,
            "armature_object": arm_obj.name,
            "bone_names": [name for name, _, _, _ in BONE_DEFINITIONS],
            "rigid_vertex_assignments": assigned,
            "height_meters_from_setup": requested_height,
            "target_mesh_dimensions_world": {"width": width, "height": height, "depth": _depth},
            "warnings": [
                "Bone positions are mapped from 2D browser markers; inspect scale, depth and joint alignment.",
                "Nearest-segment weights are a rigid blockout and are not quality-assured animation weights.",
                "Bone names differ from an existing game's native skeleton unless manually renamed; animation compatibility is not guaranteed.",
                "Export SMD/QC with a compatible Blender toolchain and compile with a suitable GoldSrc/Sven Co-op StudioMDL.",
            ],
        }
        report_path = os.path.splitext(os.path.abspath(filepath))[0] + "_blender_bridge_report.json"
        with open(report_path, "w", encoding="utf-8") as report_file:
            json.dump(report, report_file, indent=2)
        return arm_obj, assigned
    except Exception:
        # Remove the partial generated armature if creation failed. The source mesh is not deleted.
        if arm_obj.name in bpy.data.objects:
            bpy.data.objects.remove(arm_obj, do_unlink=True)
        if arm_data.users == 0:
            bpy.data.armatures.remove(arm_data)
        raise


class IMPORT_SCENE_OT_coop_forge_rig_json(Operator, ImportHelper):
    """Import a Co-Op Forge rig setup JSON and generate a Blender armature."""

    bl_idname = "import_scene.coop_forge_rig_json"
    bl_label = "Import Co-Op Forge Rig JSON"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})
    bind_rigid_weights: BoolProperty(
        name="Assign rigid weights",
        description="Assign every mesh vertex to its nearest rig bone segment (blockout only)",
        default=True,
    )
    replace_existing_vertex_groups: BoolProperty(
        name="Replace existing vertex groups",
        description="Destructively remove the selected mesh's existing vertex groups before generating rigid weights",
        default=False,
    )

    def execute(self, context):
        try:
            rig = _load_rig_json(self.filepath)
            arm_obj, assigned = _build_armature(
                context,
                rig,
                self.filepath,
                bool(self.bind_rigid_weights),
                bool(self.replace_existing_vertex_groups),
            )
        except (RigBridgeError, OSError, RuntimeError, ValueError) as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        if self.bind_rigid_weights:
            self.report({"WARNING"}, f"Created {arm_obj.name}; assigned {assigned} rigid vertex weights. Inspect deformations before export.")
        else:
            self.report({"INFO"}, f"Created {arm_obj.name}. No vertex weights were assigned.")
        return {"FINISHED"}


class VIEW3D_PT_coop_forge_rig_bridge(Panel):
    bl_label = "Co-Op Forge"
    bl_idname = "VIEW3D_PT_coop_forge_rig_bridge"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Co-Op Forge"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Rig JSON → Blender Armature", icon="ARMATURE_DATA")
        layout.label(text="Select the target mesh first.", icon="INFO")
        layout.operator(IMPORT_SCENE_OT_coop_forge_rig_json.bl_idname, icon="IMPORT")
        box = layout.box()
        box.label(text="Rigid nearest-bone weights are approximate.")
        box.label(text="Inspect bones, groups, and animation before SMD export.")


CLASSES = (
    IMPORT_SCENE_OT_coop_forge_rig_json,
    VIEW3D_PT_coop_forge_rig_bridge,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
