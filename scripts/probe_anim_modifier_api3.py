"""
Probe 3: AM_SBFootIKWeight_C 인스턴스의 *모든* 멤버 dump.
on_apply 직접 호출이 silent fail. BlueprintCallable wrapper 메소드 탐색.

후보:
  - ApplyToAnimationSequence (UE 5.7 표준)
  - call_method("Name", args) 우회

실행:
  exec(open(r"C:\\Dev\\Sanjuk-Unreal\\scripts\\probe_anim_modifier_api3.py",
            encoding="utf-8").read(), {"__name__": "__main__"})
"""
from __future__ import annotations

import unreal

PROBE_SEQ = "/Game/Art/Character/PC/PC_01/Animation/Body/Run/P_Player_Run_Stop_F_Lfoot"


def section(t: str) -> None:
    unreal.log("=" * 70)
    unreal.log(f"[PROBE3] {t}")
    unreal.log("=" * 70)


def main() -> None:
    seq = unreal.load_asset(PROBE_SEQ)
    aud = seq.get_asset_user_data_of_class(unreal.AnimationModifiersAssetUserData)
    instances = aud.get_editor_property("animation_modifier_instances")

    target = None
    for inst in instances:
        if inst and inst.get_class().get_name() == "AM_SBFootIKWeight_C":
            target = inst
            break

    if target is None:
        unreal.log_error("[PROBE3] AM_SBFootIKWeight_C 미발견")
        return

    section("A. instance class chain")
    cls = target.get_class()
    while cls is not None:
        unreal.log(f"[PROBE3]   class: {cls.get_name()}  path: {cls.get_path_name()}")
        try:
            cls = cls.get_super_class()
        except Exception:
            break

    section("B. ALL non-underscore members (instance)")
    all_members = sorted(m for m in dir(target) if not m.startswith("_"))
    for m in all_members:
        unreal.log(f"[PROBE3]   .{m}")

    section("C. members matching apply/execute/run/process/modify")
    keywords = ("apply", "execute", "run", "process", "modify", "reapply", "trigger")
    hits = [m for m in all_members if any(k in m.lower() for k in keywords)]
    for m in hits or ["<none>"]:
        unreal.log(f"[PROBE3]   .{m}")

    section("D. call_method probes (BlueprintCallable wrapper)")
    candidates = [
        "ApplyToAnimationSequence",
        "ApplyModifier",
        "ReapplyModifier",
        "Apply",
        "ExecuteApply",
    ]
    for name in candidates:
        try:
            r = target.call_method(name, (seq,))
            unreal.log(f"[PROBE3]   call_method({name!r}, (seq,)) OK -> {r}")
        except Exception as e:
            unreal.log(f"[PROBE3]   call_method({name!r}) FAIL: {type(e).__name__}: {e}")

    section("E. AnimSequence class methods for modifier reapply")
    seq_methods = sorted(m for m in dir(seq) if not m.startswith("_"))
    seq_hits = [m for m in seq_methods if any(k in m.lower() for k in ("modifier", "reapply", "rebuild"))]
    for m in seq_hits or ["<none>"]:
        unreal.log(f"[PROBE3]   seq.{m}")

    section("F. unreal.* helpers with 'reapply' or 'modifier_lib'")
    syms = sorted(s for s in dir(unreal) if "eapply" in s.lower() or "modifierlib" in s.lower())
    for s in syms or ["<none>"]:
        unreal.log(f"[PROBE3]   unreal.{s}")

    section("DONE")


if __name__ == "__main__":
    main()
