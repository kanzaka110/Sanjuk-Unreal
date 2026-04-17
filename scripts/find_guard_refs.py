"""Find who references P_Player_Fist_Normal_Guard01 / _Start / _End / _Move.

Run inside Unreal Editor:
    exec(open("C:/Dev/Sanjuk-Unreal/scripts/find_guard_refs.py").read())
"""
from __future__ import annotations

import unreal

BASE = "/Game/ART/Character/PC/PC_01/Animation/Body/Attack/"
TARGETS = (
    "P_Player_Fist_Normal_Guard01",
    "P_Player_Fist_Normal_Guard01_Start",
    "P_Player_Fist_Normal_Guard01_End",
    "P_Player_Fist_Normal_Guard01_Move",
)


def main() -> None:
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    opts = unreal.AssetRegistryDependencyOptions(
        include_soft_package_references=True,
        include_hard_package_references=True,
        include_searchable_names=False,
        include_soft_management_references=False,
        include_hard_management_references=False,
    )

    for name in TARGETS:
        full = BASE + name
        print("\n" + "=" * 70)
        print(f"[target] {full}")
        print("=" * 70)

        asset = unreal.load_asset(full)
        if asset:
            print(f"  class  : {asset.get_class().get_name()}")
            try:
                add = asset.get_editor_property("additive_anim_type")
                print(f"  additive_anim_type : {add}")
            except Exception:
                pass
            try:
                ln = asset.get_editor_property("sequence_length")
                print(f"  sequence_length    : {ln}")
            except Exception:
                pass
        else:
            print("  (load fail)")
            continue

        try:
            refs = ar.get_referencers(unreal.Name(full), opts)
        except Exception as e:
            print(f"  referencers err: {e}")
            continue

        if not refs:
            print("  Referencers: 없음")
            continue

        print(f"  Referencers: {len(list(refs))}")
        for r in list(refs):
            print(f"    ← {r}")


main()
