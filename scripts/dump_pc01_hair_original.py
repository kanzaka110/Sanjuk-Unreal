"""PC_01 Hair Original/01 신규 덤프 (2026-04-29 작성).

목적: 6일 전 stale HairDump.txt 대신 신규 덤프.
사용자가 "PC_01_Hair_01 (Original)"이라 표현했지만 실제로는 별개 에셋:
  - PC_01_Hair_Original: 2026-04-23 변경 (보존 baseline)
  - PC_01_Hair_01      : 2026-04-29 변경 (오늘, 활성 워킹 카피일 가능성)
둘 다 덤프해야 어느 쪽이 사용자가 본 "Original"인지 확정 가능.

실행:
  UE 에디터 > Window > Developer Tools > Output Log
  Cmd 드롭다운을 'Python'으로 변경 후 아래 입력:
    exec(open(r'C:/Dev/Sanjuk-Unreal/scripts/dump_pc01_hair_original.py').read())

저장: E:/Perforce/SB2/Workspace/Internal/SB2/Saved/Logs/HairDump_Original_20260429.txt
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import unreal

GROOM_PATHS: list[str] = [
    "/Game/Art/Character/PC/PC_01/Equipment/Hair/PC_01_Hair_01/PC_01_Hair_Original",
    "/Game/Art/Character/PC/PC_01/Equipment/Hair/PC_01_Hair_01/PC_01_Hair_01",
]
BINDING_PATH: str = (
    "/Game/Art/Character/PC/PC_01/Equipment/Hair/PC_01_Hair_01/Binding/PC_01_Hair_01_Binding"
)

_PRINT_LINES: list[str] = []


def log(msg: str = "") -> None:
    _PRINT_LINES.append(msg)
    unreal.log(msg)


def section(title: str) -> None:
    log("")
    log("=" * 78)
    log(title)
    log("=" * 78)


def dump_editor_properties(label: str, obj: Any, depth: int = 0) -> None:
    indent = "  " * depth
    log(f"{indent}[{label}]")
    if obj is None:
        log(f"{indent}  (None)")
        return

    try:
        text = obj.export_text()
        if text and text != "()":
            for chunk in text.replace("),", ")\n").split("\n"):
                log(f"{indent}  {chunk}")
            return
    except Exception:
        pass

    seen: set[str] = set()
    for name in sorted(dir(obj)):
        if name.startswith("_") or name in seen:
            continue
        seen.add(name)
        try:
            value = obj.get_editor_property(name)
        except Exception:
            continue
        if callable(value):
            continue
        log(f"{indent}  {name} = {value}")


def dump_groom(path: str) -> None:
    section(f"GroomAsset: {path}")
    asset = unreal.load_asset(path)
    if asset is None:
        log("  (load failed)")
        return

    log(f"  class      = {asset.get_class().get_name()}")
    log(f"  dump_time  = {datetime.now().isoformat()}")

    try:
        groups_physics = asset.get_editor_property("hair_groups_physics")
    except Exception as exc:
        log(f"  hair_groups_physics 접근 실패: {exc}")
        groups_physics = None

    if groups_physics:
        for idx, grp in enumerate(groups_physics):
            section(f"  [Group {idx}] HairGroupsPhysics")
            for field in (
                "strands_parameters",
                "solver_settings",
                "external_forces",
                "material_constraints",
                "collision_constraints",
            ):
                try:
                    sub = grp.get_editor_property(field)
                    dump_editor_properties(field, sub, depth=2)
                except Exception:
                    pass
            dump_editor_properties("(full group)", grp, depth=2)

    for name in (
        "hair_groups_rendering",
        "hair_groups_lod",
        "hair_groups_interpolation",
        "hair_groups_cards",
        "hair_groups_meshes",
        "hair_groups_info",
        "enable_global_interpolation",
        "enable_simulation_cache",
    ):
        try:
            val = asset.get_editor_property(name)
            log(f"  {name} = {val}")
        except Exception:
            pass


def dump_binding() -> None:
    section(f"GroomBindingAsset: {BINDING_PATH}")
    asset = unreal.load_asset(BINDING_PATH)
    if asset is None:
        log("  (load failed)")
        return
    for name in (
        "groom",
        "target_skeletal_mesh",
        "source_skeletal_mesh",
        "num_interpolation_points",
        "matching_section",
    ):
        try:
            val = asset.get_editor_property(name)
            log(f"  {name} = {val}")
        except Exception:
            pass


def main() -> None:
    for path in GROOM_PATHS:
        dump_groom(path)
    dump_binding()

    out_dir = unreal.Paths.project_saved_dir() + "Logs"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "HairDump_Original_20260429.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(_PRINT_LINES))
    log("")
    log(f"=> 저장됨: {out_path}")


main()
