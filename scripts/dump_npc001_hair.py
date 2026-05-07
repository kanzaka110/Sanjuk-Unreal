"""NPC_001_Hair_01 Groom 파라미터 덤프.

실행:
  UE 에디터 > Window > Developer Tools > Output Log
  Cmd 드롭다운을 'Python'으로 변경 후 입력:
    exec(open(r'C:/Dev/Sanjuk-Unreal/scripts/dump_npc001_hair.py').read())

저장: E:/Perforce/SB2/Workspace/Internal/SB2/Saved/Logs/HairDump_NPC001.txt
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import unreal

GROOM_PATH: str = (
    "/Game/Art/Character/NPC/NPC_001/Equipment/Hair/NPC_001_Hair_01/NPC_001_Hair_01"
)

_LINES: list[str] = []


def log(msg: str = "") -> None:
    _LINES.append(msg)
    unreal.log(msg)


def section(title: str) -> None:
    log("")
    log("=" * 78)
    log(title)
    log("=" * 78)


def dump_props(label: str, obj: Any, depth: int = 0) -> None:
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
    for name in sorted(dir(obj)):
        if name.startswith("_"):
            continue
        try:
            val = obj.get_editor_property(name)
        except Exception:
            continue
        if callable(val):
            continue
        log(f"{indent}  {name} = {val}")


def dump_groom(path: str) -> None:
    section(f"GroomAsset: {path}")
    asset = unreal.load_asset(path)
    if asset is None:
        log("  [ERROR] load failed")
        return

    log(f"  class     = {asset.get_class().get_name()}")
    log(f"  dump_time = {datetime.now().isoformat()}")

    try:
        groups_physics = asset.get_editor_property("hair_groups_physics")
    except Exception as exc:
        log(f"  hair_groups_physics 접근 실패: {exc}")
        return

    if not groups_physics:
        log("  hair_groups_physics = (empty)")
        return

    log(f"  그룹 수 = {len(groups_physics)}")

    for idx, grp in enumerate(groups_physics):
        section(f"  [Group {idx}]")
        for field in (
            "strands_parameters",
            "solver_settings",
            "external_forces",
            "material_constraints",
            "collision_constraints",
        ):
            try:
                sub = grp.get_editor_property(field)
                dump_props(field, sub, depth=2)
            except Exception:
                pass

    # 그룹 정보 (Curve 수, 가이드 수)
    try:
        groups_info = asset.get_editor_property("hair_groups_info")
        if groups_info:
            section("  HairGroupsInfo (Curves/Guides/MaxLen)")
            for idx, info in enumerate(groups_info):
                dump_props(f"Group {idx}", info, depth=2)
    except Exception:
        pass


def main() -> None:
    dump_groom(GROOM_PATH)

    out_dir = unreal.Paths.project_saved_dir() + "Logs"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "HairDump_NPC001.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(_LINES))
    log("")
    log(f"=> 저장됨: {out_path}")


main()
