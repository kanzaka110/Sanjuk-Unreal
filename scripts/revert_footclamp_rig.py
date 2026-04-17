"""Revert FootClamp axis swap — undo the fix_footclamp_rig.py changes.

Run inside Unreal Editor:
    exec(open("C:/Dev/Sanjuk-Unreal/scripts/revert_footclamp_rig.py").read())
"""
from __future__ import annotations

import unreal

CR_PATH: str = "/Game/ART/Character/PC/PC_01/Rig/PC_01_CtrlRig_FootClamp"
DRY_RUN: bool = False

# Reverse of LINK_SWAPS: now current has swapped sources, revert to original
LINK_REVERTS: tuple[tuple[str, str, str], ...] = (
    ("Clamp_1.Minimum.X", "VariableNode_2.Value.X", "VariableNode_4.Value.X"),
    ("Clamp_1.Maximum.X", "VariableNode_2.Value.Y", "VariableNode_4.Value.Y"),
    ("Clamp_1.Minimum.Y", "VariableNode_4.Value.X", "VariableNode_2.Value.X"),
    ("Clamp_1.Maximum.Y", "VariableNode_4.Value.Y", "VariableNode_2.Value.Y"),
)


def line(t: str = "") -> None:
    print(t)


def get_controller(bp):
    for g in ("get_default_model", "get_focused_model", "get_model"):
        try:
            fn = getattr(bp, g, None)
            if callable(fn):
                m = fn()
                if m:
                    c = bp.get_or_create_controller(m)
                    if c:
                        return c
        except Exception:
            pass
    return None


def source_of(graph, target_path: str) -> str | None:
    parts = target_path.split(".", 1)
    node = graph.find_node_by_name(parts[0])
    if not node:
        return None
    pin = node.find_pin(parts[1])
    if not pin:
        return None
    srcs = list(pin.get_linked_source_pins())
    return str(srcs[0].get_pin_path()) if srcs else None


def main() -> None:
    bp = unreal.load_asset(CR_PATH)
    ctrl = get_controller(bp)
    graph = ctrl.get_graph()

    line(f"[revert]  DRY_RUN={DRY_RUN}")
    line("current sources:")
    for tgt, expected_cur, _ in LINK_REVERTS:
        actual = source_of(graph, tgt)
        mark = "OK " if actual == expected_cur else "MISS"
        line(f"  [{mark}] {tgt}  <- {actual}   (expect {expected_cur})")

    if DRY_RUN:
        line("\nDRY_RUN — no edits.  Intended:")
        for tgt, old, new in LINK_REVERTS:
            line(f"  {tgt}:  -{old}  +{new}")
        return

    try:
        unreal.EditorAssetLibrary.checkout_loaded_asset(bp)
    except Exception:
        pass

    try:
        ctrl.open_undo_bracket("FootClamp revert swap")
    except Exception:
        pass

    ok = True
    for tgt, old, new in LINK_REVERTS:
        try:
            br = ctrl.break_link(old, tgt)
            line(f"  break {old} -> {tgt}: {'OK' if br else 'FAIL'}")
            ad = ctrl.add_link(new, tgt)
            line(f"  add   {new} -> {tgt}: {'OK' if ad else 'FAIL'}")
            if not (br and ad):
                ok = False
        except Exception as e:
            line(f"  err: {e}")
            ok = False

    try:
        if ok:
            ctrl.close_undo_bracket()
        else:
            ctrl.cancel_undo_bracket()
    except Exception:
        pass

    if ok:
        try:
            bp.recompile_vm()
        except Exception:
            unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        unreal.EditorAssetLibrary.save_loaded_asset(bp)
        line("\nreverted + compiled + saved")
    else:
        line("\nrevert FAILED, check state manually")


main()
