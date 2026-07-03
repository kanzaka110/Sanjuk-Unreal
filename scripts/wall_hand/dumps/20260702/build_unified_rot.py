import unreal, math, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/unified_result.txt"
L=[]
try:
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    g = ctrl.get_graph()
    nodes = {n.get_name(): n for n in g.get_nodes()}
    atan_s = nodes["WallYaw"].get_script_struct().get_path_name()
    faa_s  = nodes["WallQ"].get_script_struct().get_path_name()
    # 초기 오프셋 환산: off_dir = yaw(+90°) × off_tangent  (탄젠트프레임→방향프레임)
    s=math.sin(math.radians(45)); c=math.cos(math.radians(45))
    qz90 = unreal.Quat(0,0,s,c)
    offR_t = unreal.Quat(-0.705990,0.039720,0.705990,0.039720)   # calib_r_wall
    offL_t = unreal.Quat(-0.010149,-0.707034,-0.010149,0.707034) # walloff_l
    offR = qz90.multiply(offR_t); offL = qz90.multiply(offL_t)
    def qs(q): return f"(X={q.x:.6f},Y={q.y:.6f},Z={q.z:.6f},W={q.w:.6f})"
    L.append(f"offR_dir={qs(offR)}"); L.append(f"offL_dir={qs(offL)}")
    # 손별 타겟방향 yaw → 쿼트
    for side, tgt in (("R","ToRig"),("L","ToRigL")):
        ctrl.add_unit_node_from_struct_path(atan_s, "Execute", unreal.Vector2D(300, 1400 if side=="R" else 1520), f"DirYaw{side}")
        ctrl.add_link(f"{tgt}.Global.Y", f"DirYaw{side}.A")
        ctrl.add_link(f"{tgt}.Global.X", f"DirYaw{side}.B")
        ctrl.add_unit_node_from_struct_path(faa_s, "Execute", unreal.Vector2D(460, 1400 if side=="R" else 1520), f"DirQ{side}")
        ctrl.set_pin_default_value(f"DirQ{side}.Axis", "(X=0.000000,Y=0.000000,Z=1.000000)")
        ctrl.add_link(f"DirYaw{side}.Result", f"DirQ{side}.Angle")
        # QMul 재사용: A ← DirQ (WallQ 링크 절단), B = off_dir
        try: ctrl.break_link("WallQ.Result", f"QMul{side}.A")
        except Exception: pass
        ctrl.add_link(f"DirQ{side}.Result", f"QMul{side}.A")
        ctrl.set_pin_default_value(f"QMul{side}.B", qs(offR if side=="R" else offL))
        # Effector ← QMul 직결 (QLerp 우회)
        try: ctrl.break_link(f"QLerp{side}.Result", f"TwoBoneIK_{side}.Effector.Rotation")
        except Exception: pass
        ctrl.add_link(f"QMul{side}.Result", f"TwoBoneIK_{side}.Effector.Rotation")
        L.append(f"{side} 연속회전 배선 ok")
    # 구 벽프레임/슬러프 체인 제거
    for nm in ("QLerpR","QLerpL","TMulR","TMulL","TGate","WallLen","WallQ","WallYaw","WallDir","WallDBias","WallD"):
        try:
            ctrl.remove_node_by_name(nm); L.append(f"remove {nm}")
        except Exception as e: L.append(f"remove {nm} 실패 {str(e)[:50]}")
    bp.recompile_vm(); bp.recompile_vm_if_required()
    ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
    L.append(f"save={ok}")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
