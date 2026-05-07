"""PC_01 Sanjuk 활성 헤어 + Component SimulationSetup 통합 덤프 (2026-05-06).

목적:
  - 활성본 GroomAsset (`PC_01_Hair_01`) 5그룹 풀 파라미터
  - PC_01_BP_Sanjuk GroomComponent 측 SimulationSettings (override / setup / forces / constraints)
  - UE 5.7 공식 기본값 비교 위한 raw export
  - 6일 전 (HairDump_Original_20260429.txt) 와 diff 가능한 형태

실행:
  UE 에디터 > Window > Developer Tools > Output Log > Cmd: Python
    exec(open(r'C:/Dev/Sanjuk-Unreal/scripts/dump_pc01_hair_active_full.py').read())

결과:
  Saved/Logs/HairDump_Active_20260506.txt
"""

from __future__ import annotations

import logging
import os
from typing import Any, Iterable

import unreal

# ---------------------------------------------------------------------------
# 대상 에셋
# ---------------------------------------------------------------------------

ACTIVE_GROOM: str = (
    "/Game/Art/Character/PC/PC_01/Equipment/Hair/PC_01_Hair_01/PC_01_Hair_01"
)
REFERENCE_GROOMS: tuple[str, ...] = (
    "/Game/Art/Character/PC/PC_01/Equipment/Hair/PC_01_Hair_01/PC_01_Hair_Original",
    "/Game/Art/Character/PC/PC_01/Equipment/Hair/PC_01_Hair_01/PC_01_Hair_Sanjuk",
)
BINDING_PATH: str = (
    "/Game/Art/Character/PC/PC_01/Equipment/Hair/PC_01_Hair_01/Binding/"
    "PC_01_Hair_01_Binding"
)
BLUEPRINT_PATH: str = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP_Sanjuk"

OUT_FILENAME: str = "HairDump_Active_20260506.txt"

logger = logging.getLogger("hair_dump")
_LINES: list[str] = []


def emit(msg: str = "") -> None:
    _LINES.append(msg)
    unreal.log(msg)


def section(title: str) -> None:
    emit("")
    emit("=" * 78)
    emit(title)
    emit("=" * 78)


# ---------------------------------------------------------------------------
# Groom asset side dumper (5그룹)
# ---------------------------------------------------------------------------

ASSET_GROUP_FIELD_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("strands_parameters", (
        "strands_size", "strands_density", "strands_smoothing",
        "strands_thickness", "thickness_scale",
    )),
    ("solver_settings", (
        "b_enable_deformation", "enable_simulation", "niagara_solver",
        "custom_system", "gravity_preloading",
        "sub_steps", "iteration_count", "b_force_visible",
    )),
    ("external_forces", (
        "gravity_vector", "air_drag", "air_velocity",
    )),
)

# MaterialConstraints는 sub-struct (bend / stretch / collision) 분해 필요.
ASSET_MATERIAL_FIELDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("bend_constraint", (
        "solve_bend", "project_bend", "bend_damping", "bend_stiffness",
        "bend_scale",
    )),
    ("stretch_constraint", (
        "solve_stretch", "project_stretch",
        "stretch_damping", "stretch_stiffness", "stretch_scale",
    )),
    ("collision_constraint", (
        "solve_collision", "project_collision",
        "static_friction", "kinetic_friction",
        "strands_viscosity", "grid_dimension",
        "collision_radius", "radius_scale",
    )),
)


def fmt_value(value: Any) -> str:
    """Curve, Vector 등 보기 어려운 객체를 안전하게 문자열로 변환."""
    if value is None:
        return "None"
    try:
        cls_name = value.__class__.__name__
    except Exception:
        cls_name = ""
    if cls_name == "RuntimeFloatCurve":
        try:
            curve = value.get_editor_property("editor_curve_data")
            keys = curve.get_editor_property("keys") if curve else []
            if not keys:
                return "Curve(empty)"
            kv = ["({:.3f}->{:.3f})".format(
                k.get_editor_property("time"),
                k.get_editor_property("value"),
            ) for k in keys]
            return "Curve[" + ", ".join(kv) + "]"
        except Exception as exc:
            return f"Curve(<read err: {exc}>)"
    return str(value)


def get_prop(obj: Any, *names: str) -> Any:
    for name in names:
        try:
            return obj.get_editor_property(name)
        except Exception:
            continue
    return "<not found>"


def dump_struct_fields(label: str, struct: Any, fields: Iterable[str], indent: str = "    ") -> None:
    emit(f"{indent}[{label}]")
    if struct is None:
        emit(f"{indent}  (None)")
        return
    for field in fields:
        val = get_prop(struct, field)
        emit(f"{indent}  {field:<24}= {fmt_value(val)}")


def dump_groom_asset(path: str) -> None:
    section(f"GroomAsset: {path}")
    asset = unreal.load_asset(path)
    if asset is None:
        emit("  (load failed)")
        return

    emit(f"  class = {asset.get_class().get_name()}")

    try:
        groups = asset.get_editor_property("hair_groups_physics")
    except Exception as exc:
        emit(f"  hair_groups_physics 접근 실패: {exc}")
        return

    if not groups:
        emit("  (no physics groups)")
        return

    for idx, grp in enumerate(groups):
        emit("")
        emit(f"  --- Group {idx} ---")
        # GroupName 가능하면 출력
        try:
            gn = grp.get_editor_property("group_name")
            emit(f"    group_name              = {gn}")
        except Exception:
            pass

        for sub_name, fields in ASSET_GROUP_FIELD_GROUPS:
            sub = get_prop(grp, sub_name)
            dump_struct_fields(sub_name, sub, fields)

        # MaterialConstraints
        material = get_prop(grp, "material_constraints")
        emit("    [material_constraints]")
        if material is None or material == "<not found>":
            emit("      (None)")
        else:
            for sub_name, fields in ASSET_MATERIAL_FIELDS:
                sub_struct = get_prop(material, sub_name)
                dump_struct_fields(sub_name, sub_struct, fields, indent="      ")


# ---------------------------------------------------------------------------
# GroomBindingAsset
# ---------------------------------------------------------------------------


def dump_binding(path: str) -> None:
    section(f"GroomBindingAsset: {path}")
    asset = unreal.load_asset(path)
    if asset is None:
        emit("  (load failed)")
        return
    for name in (
        "groom",
        "target_skeletal_mesh",
        "source_skeletal_mesh",
        "num_interpolation_points",
        "matching_section",
    ):
        emit(f"  {name:<26}= {fmt_value(get_prop(asset, name))}")


# ---------------------------------------------------------------------------
# GroomComponent SimulationSettings (PC_01_BP_Sanjuk)
# ---------------------------------------------------------------------------

SETUP_FIELDS: tuple[str, ...] = (
    "b_reset_simulation",
    "b_debug_simulation",
    "b_local_simulation",
    "linear_velocity_scale",
    "angular_velocity_scale",
    "local_bone",
    "teleport_distance",
)
COMP_FORCES_FIELDS: tuple[str, ...] = ("gravity_vector", "air_drag", "air_velocity")
COMP_CONSTRAINTS_FIELDS: tuple[str, ...] = (
    "bend_damping", "bend_stiffness",
    "stretch_damping", "stretch_stiffness",
    "static_friction", "kinetic_friction",
    "strands_viscosity", "collision_radius",
)
COMP_SOLVER_FIELDS: tuple[str, ...] = ("b_enable_simulation",)


def dump_groom_component(label: str, comp: Any) -> None:
    emit("")
    emit(f"  --- GroomComponent: {label} ---")
    emit(f"    groom_asset    = {fmt_value(get_prop(comp, 'groom_asset'))}")
    emit(f"    binding_asset  = {fmt_value(get_prop(comp, 'binding_asset'))}")
    emit(f"    physics_asset  = {fmt_value(get_prop(comp, 'physics_asset'))}")
    emit(f"    attachment     = {fmt_value(get_prop(comp, 'attachment_name'))}")

    sim = get_prop(comp, "simulation_settings")
    if sim is None or sim == "<not found>":
        emit("    simulation_settings = None")
        return

    override = get_prop(sim, "b_override_settings")
    emit(f"    b_override_settings    = {override}")

    setup = get_prop(sim, "simulation_setup")
    dump_struct_fields("simulation_setup", setup, SETUP_FIELDS, indent="    ")

    solver = get_prop(sim, "solver_settings")
    dump_struct_fields("solver_settings (component-side)", solver, COMP_SOLVER_FIELDS, indent="    ")

    forces = get_prop(sim, "external_forces")
    dump_struct_fields("external_forces (component-side)", forces, COMP_FORCES_FIELDS, indent="    ")

    constr = get_prop(sim, "material_constraints")
    dump_struct_fields("material_constraints (component-side)", constr, COMP_CONSTRAINTS_FIELDS, indent="    ")


def dump_blueprint_groom_components(bp_path: str) -> None:
    section(f"Blueprint: {bp_path}")
    bp = unreal.load_asset(bp_path)
    if bp is None:
        emit("  (load failed)")
        return

    gen_class = bp.generated_class() if hasattr(bp, "generated_class") else None
    if gen_class is None:
        emit("  generated_class None")
        return
    emit(f"  generated_class = {gen_class.get_name()}")

    found = 0

    # SimpleConstructionScript 우선
    try:
        scs = bp.get_editor_property("simple_construction_script")
        if scs:
            nodes = scs.get_editor_property("all_nodes") or []
            for node in nodes:
                try:
                    var_name = node.get_editor_property("variable_name")
                    template = node.get_editor_property("component_template")
                    if template is None:
                        continue
                    cls_name = template.get_class().get_name()
                    if "GroomComponent" in cls_name:
                        dump_groom_component(str(var_name), template)
                        found += 1
                except Exception as exc:
                    emit(f"  [SCS] node iter error: {exc}")
    except Exception as exc:
        emit(f"  [WARN] SCS 접근 실패: {exc}")

    if found == 0:
        emit("  (GroomComponent 없음 — Subobject 폴백 시도)")
        try:
            subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
            handles = subsys.k2_gather_subobject_data_for_blueprint(bp)
            for h in handles:
                data = subsys.k2_find_subobject_data_from_handle(h)
                if data is None:
                    continue
                try:
                    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data)
                except Exception:
                    obj = None
                if obj is None:
                    continue
                cls_name = obj.get_class().get_name()
                if "GroomComponent" in cls_name:
                    dump_groom_component(obj.get_name(), obj)
                    found += 1
        except Exception as exc:
            emit(f"  [WARN] SDS 폴백 실패: {exc}")

    emit("")
    emit(f"  [요약] GroomComponent 발견 = {found}개")


# ---------------------------------------------------------------------------
# 진입점
# ---------------------------------------------------------------------------


def main() -> None:
    emit("PC_01 Active Hair Full Dump (2026-05-06)")
    emit(f"  active asset    : {ACTIVE_GROOM}")
    emit(f"  reference assets: {REFERENCE_GROOMS}")
    emit(f"  binding         : {BINDING_PATH}")
    emit(f"  blueprint       : {BLUEPRINT_PATH}")

    dump_groom_asset(ACTIVE_GROOM)
    for ref in REFERENCE_GROOMS:
        dump_groom_asset(ref)

    dump_binding(BINDING_PATH)
    dump_blueprint_groom_components(BLUEPRINT_PATH)

    out_dir = os.path.join(unreal.SystemLibrary.get_project_directory(), "Saved", "Logs")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, OUT_FILENAME)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(_LINES))
    emit("")
    emit(f"=> 저장: {out_path}")


main()
