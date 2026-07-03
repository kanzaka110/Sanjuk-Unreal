import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/wallframe_result.txt"
L=[]
try:
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    g = ctrl.get_graph()
    nodes = {n.get_name(): n for n in g.get_nodes()}
    sub_s  = nodes["ReachSub"].get_script_struct().get_path_name()
    unit_s = nodes["PalmDirUnit"].get_script_struct().get_path_name()
    faa_s  = nodes["Quat_spine_02"].get_script_struct().get_path_name()
    L.append(f"structs: sub={sub_s.split('.')[-1]} unit={unit_s.split('.')[-1]} faa={faa_s.split('.')[-1]}")
    # 벽 수평 방향 = R타겟 − L타겟
    ctrl.add_unit_node_from_struct_path(sub_s,  "Execute", unreal.Vector2D(200, 1250), "WallD")
    ctrl.add_unit_node_from_struct_path(unit_s, "Execute", unreal.Vector2D(360, 1250), "WallDir")
    atan_ok=None
    for sp in ("/Script/RigVM.RigVMFunction_MathFloatAtan2",):
        try:
            ctrl.add_unit_node_from_struct_path(sp, "Execute", unreal.Vector2D(520, 1250), "WallYaw")
            atan_ok=sp; break
        except Exception as e: L.append(f"{sp} 실패 {str(e)[:60]}")
    if not atan_ok: raise RuntimeError("Atan2 없음")
    ctrl.add_unit_node_from_struct_path(faa_s, "Execute", unreal.Vector2D(680, 1250), "WallQ")
    L.append("spawn ok")
    ctrl.add_link("ToRig.Global", "WallD.A")
    ctrl.add_link("ToRigL.Global", "WallD.B")
    ctrl.add_link("WallD.Result", "WallDir.Value")
    ctrl.add_link("WallDir.Result.Y", "WallYaw.A")
    ctrl.add_link("WallDir.Result.X", "WallYaw.B")
    ctrl.set_pin_default_value("WallQ.Axis", "(X=0.000000,Y=0.000000,Z=1.000000)")
    ctrl.add_link("WallYaw.Result", "WallQ.Angle")
    L.append("wall frame wired")
    # QMulR/L 재배선: A ← WallQ (GetRootTf 대체), B = 정면오프셋 상수(QSel 링크 절단)
    for side, off in (("R","(X=-0.017212,Y=-0.706897,Z=0.017212,W=-0.706897)"),
                      ("L","(X=0.707019,Y=0.011136,Z=0.707019,W=-0.011136)")):
        try: ctrl.break_link("GetRootTf.Transform.Rotation", f"QMul{side}.A")
        except Exception: pass
        try: ctrl.break_link(f"QSel{side}.Result", f"QMul{side}.B")
        except Exception: pass
        ctrl.add_link("WallQ.Result", f"QMul{side}.A")
        ctrl.set_pin_default_value(f"QMul{side}.B", off)
        # QSel IfTrue(정면) ← 벽프레임×오프셋
        ctrl.add_link(f"QMul{side}.Result", f"QSel{side}.IfTrue")
        L.append(f"{side} ok")
    bp.recompile_vm(); bp.recompile_vm_if_required()
    ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
    L.append(f"save={ok}")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
