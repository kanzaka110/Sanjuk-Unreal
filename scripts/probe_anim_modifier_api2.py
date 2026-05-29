"""
Probe 2: AnimationModifiersAssetUserData 경유 모디파이어 접근.

가설:
  SB2 Python 에 AnimationModifierLibrary 미노출.
  대신 AnimSequence -> AssetUserData (AnimationModifiersAssetUserData) ->
       animation_modifier_instances 리스트 -> 각 인스턴스의 .on_apply/.on_revert 직접 호출.

실행:
  exec(open(r"C:\\Dev\\Sanjuk-Unreal\\scripts\\probe_anim_modifier_api2.py",
            encoding="utf-8").read(), {"__name__": "__main__"})

read-only. apply 직접 호출은 안 함 (백업 후 메인 스크립트에서).
"""
from __future__ import annotations

import unreal

PROBE_SEQ = "/Game/Art/Character/PC/PC_01/Animation/Body/Run/P_Player_Run_Stop_F_Lfoot"


def section(title: str) -> None:
    unreal.log("=" * 70)
    unreal.log(f"[PROBE2] {title}")
    unreal.log("=" * 70)


def main() -> None:
    seq = unreal.load_asset(PROBE_SEQ)
    if not seq:
        unreal.log_error(f"[PROBE2] load fail: {PROBE_SEQ}")
        return

    # A. AnimationModifiersAssetUserData 클래스 멤버
    section("A. AnimationModifiersAssetUserData class members")
    aud_cls = unreal.AnimationModifiersAssetUserData
    for m in sorted(dir(aud_cls)):
        if not m.startswith("_"):
            unreal.log(f"[PROBE2]   .{m}")

    # B. AnimSequence 의 AssetUserData getter probe
    section("B. AnimSequence AssetUserData getter probe")
    for name in [
        "get_asset_user_data_of_class",
        "get_asset_user_data",
        "get_all_asset_user_data",
        "add_asset_user_data_of_class",
    ]:
        fn = getattr(seq, name, None)
        unreal.log(f"[PROBE2]   seq.{name}: {'OK' if fn else 'NOT FOUND'}")

    # C. 실제 AssetUserData 가져오기
    section("C. Fetch AssetUserData on probe seq")
    aud = None
    try:
        aud = seq.get_asset_user_data_of_class(unreal.AnimationModifiersAssetUserData)
        unreal.log(f"[PROBE2]   get_asset_user_data_of_class -> {aud}")
    except Exception as e:
        unreal.log(f"[PROBE2]   FAIL: {type(e).__name__}: {e}")

    # D. 모디파이어 인스턴스 리스트 접근
    if aud is not None:
        section("D. Modifier instances on AUD")
        for prop in [
            "animation_modifier_instances",
            "modifier_instances",
            "modifiers",
            "instances",
        ]:
            try:
                v = aud.get_editor_property(prop)
                unreal.log(f"[PROBE2]   {prop}: len={len(v) if hasattr(v, '__len__') else 'n/a'}")
                if hasattr(v, "__iter__"):
                    for i, inst in enumerate(v):
                        if inst is None:
                            unreal.log(f"[PROBE2]     [{i}] <None>")
                            continue
                        cls_name = inst.get_class().get_name()
                        path = inst.get_class().get_path_name()
                        unreal.log(f"[PROBE2]     [{i}] class={cls_name}  path={path}")
                        # 메소드 노출 확인
                        for mname in ["on_apply", "on_revert", "execute_apply"]:
                            fn = getattr(inst, mname, None)
                            unreal.log(f"[PROBE2]         .{mname}: {'OK' if fn else 'NO'}")
            except Exception as e:
                unreal.log(f"[PROBE2]   {prop}: FAIL ({type(e).__name__}: {e})")
    else:
        unreal.log("[PROBE2]   skip D (no AUD)")

    # E. 어제 검증된 anim 에서 AM_SBFootIKWeight 확인
    section("E. Check AM_SBFootIKWeight_C presence on probe seq")
    if aud is not None:
        try:
            instances = aud.get_editor_property("animation_modifier_instances")
            target = None
            for inst in instances:
                if inst and inst.get_class().get_name() == "AM_SBFootIKWeight_C":
                    target = inst
                    break
            if target:
                unreal.log(f"[PROBE2]   FOUND AM_SBFootIKWeight_C instance: {target}")
                unreal.log("[PROBE2]   READY for apply via on_revert+on_apply chain.")
            else:
                names = [i.get_class().get_name() for i in instances if i]
                unreal.log(f"[PROBE2]   AM_SBFootIKWeight_C NOT in {names}")
        except Exception as e:
            unreal.log(f"[PROBE2]   probe E fail: {e}")

    section("DONE")


if __name__ == "__main__":
    main()
