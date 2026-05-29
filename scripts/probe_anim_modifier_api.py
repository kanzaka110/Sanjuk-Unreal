"""
SB2 빌드 unreal 모듈에서 AnimationModifier 접근 API 탐색.

실행:
  exec(open(r"C:\\Dev\\Sanjuk-Unreal\\scripts\\probe_anim_modifier_api.py",
            encoding="utf-8").read(), {"__name__": "__main__"})

결과: Output Log 에서 "[PROBE]" prefix 줄만 보면 됨.
"""
from __future__ import annotations

import unreal

PROBE_SEQ = "/Game/Art/Character/PC/PC_01/Animation/Body/Run/P_Player_Run_Stop_F_Lfoot"


def section(title: str) -> None:
    unreal.log("=" * 70)
    unreal.log(f"[PROBE] {title}")
    unreal.log("=" * 70)


def main() -> None:
    # 1) unreal 모듈에 Modifier 포함 심볼 전수 출력
    section("1. unreal.* symbols containing 'Modifier'")
    syms = sorted(s for s in dir(unreal) if "odifier" in s)
    for s in syms:
        unreal.log(f"[PROBE]   {s}")
    if not syms:
        unreal.log("[PROBE]   <none>")

    # 2) 후보 클래스 존재 여부 + 멤버 출력
    section("2. Candidate class probe")
    candidates = [
        "AnimationModifier",
        "AnimationModifierLibrary",
        "AnimationModifiersSubsystem",
        "AnimationModifierSubsystem",
        "AnimationBlueprintLibrary",
    ]
    for name in candidates:
        cls = getattr(unreal, name, None)
        if cls is None:
            unreal.log(f"[PROBE]   {name}: NOT FOUND")
            continue
        members = [m for m in dir(cls) if not m.startswith("_")]
        unreal.log(f"[PROBE]   {name}: OK ({len(members)} members)")
        for m in members:
            unreal.log(f"[PROBE]       .{m}")

    # 3) AnimSequence editor_property 후보
    section("3. AnimSequence editor_property probe")
    seq = unreal.load_asset(PROBE_SEQ)
    if not seq:
        unreal.log_error(f"[PROBE] load fail: {PROBE_SEQ}")
        return
    unreal.log(f"[PROBE]   target: {PROBE_SEQ}")
    unreal.log(f"[PROBE]   class: {seq.get_class().get_name()}")

    prop_names = [
        "animation_modifier_instances",
        "anim_modifier_instances",
        "modifier_instances",
        "applied_modifier_instances",
        "animation_modifiers",
        "modifiers",
    ]
    for p in prop_names:
        try:
            v = seq.get_editor_property(p)
            unreal.log(f"[PROBE]   {p}: OK -> {type(v).__name__} len={len(v) if hasattr(v, '__len__') else 'n/a'}")
            if hasattr(v, "__iter__"):
                for i, inst in enumerate(v):
                    cls_name = inst.get_class().get_name() if inst else "<None>"
                    unreal.log(f"[PROBE]       [{i}] {cls_name}")
        except Exception as e:
            unreal.log(f"[PROBE]   {p}: FAIL ({type(e).__name__}: {e})")

    # 4) Subsystem 인스턴스화 시도
    section("4. Subsystem getter probe")
    for ss_name in ["AnimationModifiersSubsystem", "AnimationModifierSubsystem"]:
        cls = getattr(unreal, ss_name, None)
        if cls is None:
            continue
        try:
            ss = unreal.get_editor_subsystem(cls)
            unreal.log(f"[PROBE]   get_editor_subsystem({ss_name}) -> {ss}")
            if ss:
                members = [m for m in dir(ss) if not m.startswith("_")]
                for m in members:
                    unreal.log(f"[PROBE]       .{m}")
        except Exception as e:
            unreal.log(f"[PROBE]   get_editor_subsystem({ss_name}) FAIL: {e}")

    # 5) AnimationBlueprintLibrary 가 모디파이어 메서드 가지는지
    section("5. AnimationBlueprintLibrary modifier-related methods")
    abl = getattr(unreal, "AnimationBlueprintLibrary", None)
    if abl:
        mods = [m for m in dir(abl) if "odifier" in m]
        for m in mods or ["<none>"]:
            unreal.log(f"[PROBE]   .{m}")

    section("DONE")


if __name__ == "__main__":
    main()
