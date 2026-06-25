"""orphan 노드 제거(ToRig_1, VariableNode_3) + PalmAim.Primary 확인 + compile/save."""
import unreal, traceback
OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\cr_cleanup.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
lines = []
def w(s): lines.append(str(s))
try:
    bp = unreal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")
    g = ctrl.get_graph()
    existing = [n.get_node_path() for n in g.get_nodes()]
    w(f"before={existing}")
    for orphan in ("ToRig_1", "VariableNode_3"):
        if orphan in existing:
            try:
                ctrl.remove_node_by_name(orphan); w(f"removed {orphan}")
            except Exception as e: w(f"rm {orphan} err {str(e)[:50]}")
    # PalmAim.Primary 확인
    for n in g.get_nodes():
        if n.get_node_path() == "PalmAim":
            for p in n.get_pins():
                if p.get_name() in ("Primary","Secondary","Bone","Weight"):
                    w(f"PalmAim.{p.get_name()} = {p.get_default_value()!r}")
    w(f"after={[n.get_node_path() for n in g.get_nodes()]}")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); w("compiled")
    unreal.EditorAssetLibrary.save_asset(DST); w("saved")
except Exception:
    w("\n!!! EXC:\n"+traceback.format_exc())
with open(OUT,"w",encoding="utf-8") as f: f.write("\n".join(lines))
unreal.log("[cleanup] done")
