"""Fix axis mapping in PC_01_CtrlRig_FootClamp Control Rig.

UE 5.7 AnimationCore::EulerFromQuat(ZYX) returns FVector where:
    .X = Roll  (X-axis rotation)
    .Y = Pitch (Y-axis rotation)
    .Z = Yaw   (Z-axis rotation)

Current Clamp_1 wiring maps:
    Minimum/Maximum.X <- Angle_Clamp_Pitch (VariableNode_4)  -- WRONG, X is Roll
    Minimum/Maximum.Y <- Angle_Clamp_Roll  (VariableNode_2)  -- WRONG, Y is Pitch
    Minimum/Maximum.Z <- Angle_Clamp_Yaw   (VariableNode_1)  -- OK

Fix: swap X <-> Y wiring on Clamp_1 Min/Max so Pitch var clamps Pitch axis.

Run inside Unreal Editor:
    exec(open("C:/Dev/Sanjuk-Unreal/scripts/fix_footclamp_rig.py").read())

Flow:
    DRY_RUN = True  -> print current state + intended edits only
    DRY_RUN = False -> backup, checkout, break/add 4 links, compile, save
"""
from __future__ import annotations

import datetime
from pathlib import Path

import unreal

CR_PATH: str = "/Game/ART/Character/PC/PC_01/Rig/PC_01_CtrlRig_FootClamp"
DRY_RUN: bool = False
BACKUP_DIR: Path = Path("C:/Dev/Sanjuk-Unreal/scripts")

# (target_pin_on_Clamp, expected_current_source, new_source)
LINK_SWAPS: tuple[tuple[str, str, str], ...] = (
    ("Clamp_1.Minimum.X", "VariableNode_4.Value.X", "VariableNode_2.Value.X"),
    ("Clamp_1.Maximum.X", "VariableNode_4.Value.Y", "VariableNode_2.Value.Y"),
    ("Clamp_1.Minimum.Y", "VariableNode_2.Value.X", "VariableNode_4.Value.X"),
    ("Clamp_1.Maximum.Y", "VariableNode_2.Value.Y", "VariableNode_4.Value.Y"),
)


def line(t: str = "") -> None:
    print(t)


def section(t: str) -> None:
    line("\n" + "=" * 70)
    line(t)
    line("=" * 70)


def get_controller(bp):
    for getter in ("get_default_model", "get_focused_model", "get_model"):
        try:
            fn = getattr(bp, getter, None)
            if callable(fn):
                m = fn()
                if m:
                    c = bp.get_or_create_controller(m)
                    if c:
                        return c
        except Exception:
            continue
    try:
        for m in bp.get_all_models():
            c = bp.get_or_create_controller(m)
            if c:
                return c
    except Exception:
        pass
    return None


def pin_path(pin) -> str:
    try:
        return str(pin.get_pin_path())
    except Exception:
        try:
            return str(pin.get_name())
        except Exception:
            return "?"


def find_pin_in_graph(graph, full_path: str):
    """full_path like 'Clamp_1.Minimum.X' — split node/rest."""
    parts = full_path.split(".", 1)
    if len(parts) != 2:
        return None
    node_name, rest = parts
    node = graph.find_node_by_name(node_name)
    if not node:
        return None
    try:
        return node.find_pin(rest)
    except Exception:
        return None


def current_source_of(graph, target_full_path: str) -> str | None:
    pin = find_pin_in_graph(graph, target_full_path)
    if not pin:
        return None
    try:
        srcs = list(pin.get_linked_source_pins())
    except Exception:
        return None
    if not srcs:
        return None
    return pin_path(srcs[0])


def verify_current(graph) -> bool:
    line("\n[verify] current sources of Clamp_1 Min/Max pins:")
    all_ok = True
    for tgt, expected_src, _ in LINK_SWAPS:
        actual = current_source_of(graph, tgt)
        match = (actual == expected_src)
        mark = "OK " if match else "MISS"
        line(f"  [{mark}] {tgt}")
        line(f"         expected: {expected_src}")
        line(f"         actual  : {actual}")
        if not match:
            all_ok = False
    return all_ok


def save_backup_t3d(ctrl) -> Path | None:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = BACKUP_DIR / f"_footclamp_backup_{ts}.txt"
    try:
        graph = ctrl.get_graph()
        node_names = []
        for n in graph.get_nodes():
            try:
                node_names.append(n.get_node_path())
            except Exception:
                pass
        if not node_names:
            return None
        # prefer export_nodes_to_text if it accepts names
        try:
            txt = ctrl.export_nodes_to_text(node_names)
        except Exception:
            # fallback: select all then export
            try:
                for nm in node_names:
                    ctrl.select_node_by_name(nm, True)
                txt = ctrl.export_selected_nodes_to_text()
            except Exception:
                txt = None
        if txt:
            out.write_text(txt, encoding="utf-8")
            return out
    except Exception as e:
        line(f"  backup err: {e}")
    return None


def checkout_asset(bp) -> bool:
    try:
        return bool(unreal.EditorAssetLibrary.checkout_loaded_asset(bp))
    except Exception as e:
        line(f"  checkout attempt failed: {e}")
        return False


def apply_swaps(ctrl) -> bool:
    line("\n[apply] break + re-add 4 links")
    try:
        ctrl.open_undo_bracket("FootClamp axis swap")
    except Exception:
        pass

    ok = True
    for tgt, old_src, new_src in LINK_SWAPS:
        try:
            br = ctrl.break_link(old_src, tgt)
            line(f"  break  {old_src} -> {tgt}   ->  "
                 f"{'OK' if br else 'FAIL'}")
            if not br:
                ok = False
                continue
        except Exception as e:
            line(f"  break err: {e}")
            ok = False
            continue
        try:
            ad = ctrl.add_link(new_src, tgt)
            line(f"  add    {new_src} -> {tgt}   ->  "
                 f"{'OK' if ad else 'FAIL'}")
            if not ad:
                ok = False
        except Exception as e:
            line(f"  add err: {e}")
            ok = False

    try:
        if ok:
            ctrl.close_undo_bracket()
        else:
            ctrl.cancel_undo_bracket()
    except Exception:
        pass
    return ok


def compile_and_save(bp) -> bool:
    try:
        bp.recompile_vm()
    except Exception:
        try:
            unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        except Exception as e:
            line(f"  compile err: {e}")
            return False
    try:
        unreal.EditorAssetLibrary.save_loaded_asset(bp)
        return True
    except Exception as e:
        line(f"  save err: {e}")
        return False


def main() -> None:
    section(f"FootClamp Rig axis-swap fix  (DRY_RUN={DRY_RUN})")

    bp = unreal.load_asset(CR_PATH)
    if not bp:
        line("[ERR] load fail")
        return
    ctrl = get_controller(bp)
    if not ctrl:
        line("[ERR] no controller")
        return
    graph = ctrl.get_graph()
    line(f"loaded: {bp.get_name()}  links={len(graph.get_links())}")

    if not verify_current(graph):
        line("\n[ABORT] current wiring does not match expected. "
             "Rig may already be fixed or structure differs.")
        return

    if DRY_RUN:
        section("DRY_RUN — intended swaps")
        for tgt, old_src, new_src in LINK_SWAPS:
            line(f"  {tgt}")
            line(f"    -  {old_src}")
            line(f"    +  {new_src}")
        line("\nFlip DRY_RUN = False and rerun to apply.")
        return

    section("backup")
    bk = save_backup_t3d(ctrl)
    if bk:
        line(f"  backup written: {bk}")
    else:
        line("  WARN: no backup written (continuing)")

    section("p4 checkout")
    line(f"  checkout attempt -> {checkout_asset(bp)}")

    section("apply swaps")
    if not apply_swaps(ctrl):
        line("[ABORT] edits failed; state may be partial. "
             "Undo in editor or restore from backup.")
        return

    section("verify new wiring")
    ok = True
    for tgt, _, new_src in LINK_SWAPS:
        actual = current_source_of(graph, tgt)
        match = (actual == new_src)
        mark = "OK " if match else "MISS"
        line(f"  [{mark}] {tgt}  <-  {actual}  "
             f"(want {new_src})")
        if not match:
            ok = False
    if not ok:
        line("[ABORT] post-edit verify failed.")
        return

    section("compile + save")
    if compile_and_save(bp):
        line("  compile + save OK")
    else:
        line("  FAIL — compile or save manually.")


main()
