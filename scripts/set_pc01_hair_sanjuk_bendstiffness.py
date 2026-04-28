"""PC_01_Hair_Sanjuk Group 0 BendStiffness 단일 변경 (0.01 -> 0.1).

배경:
  - Monolith HTTP set_cdo_property 가 nested struct path 를 거부하고
    HairGroupsPhysics 배열 전체 set 도 timeout/recv-error 로 실패.
  - UE Python API (Editor) 로 직접 in-memory CDO 변경 후 mark_package_dirty + save_asset.

실행 (UE 5.7 Output Log > Cmd: Python):
  exec(open(r'C:/Dev/Sanjuk-Unreal/scripts/set_pc01_hair_sanjuk_bendstiffness.py').read())

변경 대상:
  /Game/Art/Character/PC/PC_01/Equipment/Hair/PC_01_Hair_01/PC_01_Hair_Sanjuk
  HairGroupsPhysics[0].MaterialConstraints.BendConstraint.BendStiffness
  0.01 -> 0.1
"""

from __future__ import annotations

import unreal

ASSET_PATH: str = (
    "/Game/Art/Character/PC/PC_01/Equipment/Hair/PC_01_Hair_01/PC_01_Hair_Sanjuk"
)
TARGET_GROUP: int = 0
NEW_BEND_STIFFNESS: float = 0.1


def main() -> None:
    asset = unreal.load_asset(ASSET_PATH)
    if asset is None:
        unreal.log_error(f"Load failed: {ASSET_PATH}")
        return

    groups = asset.get_editor_property("hair_groups_physics")
    if groups is None or len(groups) <= TARGET_GROUP:
        unreal.log_error(f"hair_groups_physics missing or short. len={len(groups) if groups else 'None'}")
        return

    grp = groups[TARGET_GROUP]
    mc = grp.get_editor_property("material_constraints")
    bc = mc.get_editor_property("bend_constraint")

    before = bc.get_editor_property("bend_stiffness")
    unreal.log(f"[BendStiffness] Group {TARGET_GROUP} BEFORE = {before}")

    # struct 는 value type — 수정 후 다시 set 해줘야 함
    bc.set_editor_property("bend_stiffness", NEW_BEND_STIFFNESS)
    mc.set_editor_property("bend_constraint", bc)
    grp.set_editor_property("material_constraints", mc)

    # TArray 도 마찬가지: 변경한 element 를 다시 array 슬롯에 대입
    groups[TARGET_GROUP] = grp
    asset.set_editor_property("hair_groups_physics", groups)

    # 재조회로 검증
    groups2 = asset.get_editor_property("hair_groups_physics")
    after = (
        groups2[TARGET_GROUP]
        .get_editor_property("material_constraints")
        .get_editor_property("bend_constraint")
        .get_editor_property("bend_stiffness")
    )
    unreal.log(f"[BendStiffness] Group {TARGET_GROUP} AFTER  = {after}")

    if abs(after - NEW_BEND_STIFFNESS) > 1e-6:
        unreal.log_error(
            f"Set verification failed: expected {NEW_BEND_STIFFNESS}, got {after}"
        )
        return

    asset.modify()
    unreal.EditorAssetLibrary.save_loaded_asset(asset)
    unreal.log(f"Saved asset: {ASSET_PATH}")


main()
