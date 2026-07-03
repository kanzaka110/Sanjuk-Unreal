import unreal, math, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/walloff_l.txt"
L=[]
try:
    # 좌벽 캘리브레이션 (calib.txt 저장값): normal=(-1,0,0), hand_l 좋은 자세
    qh = unreal.Quat(0.492772,-0.507125,0.492772,0.507125)
    # 벽프레임: X_wall = Cross(n, up) = (0,1,0) → yaw 90°
    yaw = math.atan2(1.0, 0.0)
    s=math.sin(yaw/2); c=math.cos(yaw/2)
    wq = unreal.Quat(0,0,s,c)
    def conj(q): return unreal.Quat(-q.x,-q.y,-q.z,q.w)
    off = conj(wq).multiply(qh)
    # 검증: wq×off == qh
    rec = wq.multiply(off)
    d = abs(rec.x*qh.x+rec.y*qh.y+rec.z*qh.z+rec.w*qh.w)
    L.append(f"offL_wall=(X={off.x:.6f},Y={off.y:.6f},Z={off.z:.6f},W={off.w:.6f}) 오차={(1-min(d,1.0))*2:.6f}")
    # CR QMulL.B에 적용
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    ctrl.set_pin_default_value("QMulL.B", f"(X={off.x:.6f},Y={off.y:.6f},Z={off.z:.6f},W={off.w:.6f})")
    bp.recompile_vm(); bp.recompile_vm_if_required()
    ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
    L.append(f"QMulL.B 적용, save={ok}")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
