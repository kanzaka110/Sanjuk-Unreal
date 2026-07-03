# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260703_opt/cr_release_compile.txt"
L = []
try:
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    L.append("compiled OK")
    # 검증: fSelRel 링크
    ctrl = bp.get_controller_by_name("RigVMModel")
    g = ctrl.get_graph()
    for n in g.get_nodes():
        nm = n.get_name()
        if nm.startswith("fSelRel") or "bWallHandLeft" in nm:
            for p in n.get_pins():
                for src in p.get_linked_source_pins():
                    L.append("  %s.%s <- %s" % (nm, p.get_name(), src.get_pin_path()))
                for tgt in p.get_linked_target_pins():
                    L.append("  %s.%s -> %s" % (nm, p.get_name(), tgt.get_pin_path()))
    L.append("DONE")
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(L))
