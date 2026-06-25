"""A안 확정: SpineAim 제거 + orphan VariableNode 정리 + Begin->TwoBoneIK exec 복원.
최종 안정 CR = Begin -> TwoBoneIK_R(위치) -> PalmAim(손바닥 +Y).
"""
import unreal, traceback
OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\finalize_cr.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
lines = []
def w(s): lines.append(str(s));
def flush():
    with open(OUT,"w",encoding="utf-8") as f: f.write("\n".join(lines))
try:
    bp = unreal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")
    g = ctrl.get_graph()
    w("before=" + str([n.get_node_path() for n in g.get_nodes()]))
    # 1) SpineAim 제거
    for nm in ("SpineAim_02","SpineAim_03"):
        if any(n.get_node_path()==nm for n in g.get_nodes()):
            try: ctrl.remove_node_by_name(nm); w(f"removed {nm}")
            except Exception as e: w(f"rm {nm} err {str(e)[:40]}")
    # 2) orphan VariableNode 제거 (출력 미연결)
    for n in list(g.get_nodes()):
        if n.get_class().get_name()=="RigVMVariableNode":
            np = n.get_node_path()
            out_linked = False
            try:
                for p in n.get_pins():
                    if p.get_direction()==unreal.RigVMPinDirection.OUTPUT:
                        if len(p.get_linked_target_pins())>0: out_linked=True
            except Exception as e:
                w(f"check {np} err {str(e)[:40]}"); out_linked=True
            if not out_linked:
                try: ctrl.remove_node_by_name(np); w(f"removed orphan {np}")
                except Exception as e: w(f"rm orphan {np} err {str(e)[:40]}")
    # 3) Begin -> TwoBoneIK exec 복원 (없으면)
    begin="RigUnit_BeginExecution"
    has=False
    for lk in g.get_links():
        if lk.get_source_pin().get_pin_path()==f"{begin}.ExecutePin" and lk.get_target_pin().get_pin_path()=="TwoBoneIK_R.ExecutePin":
            has=True
    if not has:
        try: ok=ctrl.add_link(f"{begin}.ExecutePin","TwoBoneIK_R.ExecutePin"); w(f"restored Begin->TwoBoneIK ({ok})")
        except Exception as e: w(f"restore err {str(e)[:40]}")
    # 4) 최종 덤프
    w("after=" + str([n.get_node_path() for n in g.get_nodes()]))
    w("-- links --")
    for lk in g.get_links():
        w(f"  {lk.get_source_pin().get_pin_path()} -> {lk.get_target_pin().get_pin_path()}")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); w("compiled")
    unreal.EditorAssetLibrary.save_asset(DST); w("saved")
    w("DONE")
except Exception:
    w("\n!!! EXC:\n"+traceback.format_exc())
flush()
unreal.log("[finalize_cr] done")
