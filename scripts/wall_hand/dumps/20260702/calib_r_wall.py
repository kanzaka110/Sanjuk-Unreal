import unreal, math, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/calib_r_wall.txt"
L=[]
try:
    w = unreal.UnrealEditorSubsystem().get_game_world()
    p = unreal.GameplayStatics.get_player_pawn(w, 0)
    mesh = p.get_component_by_class(unreal.SkeletalMeshComponent)
    ai = mesh.get_anim_instance()
    g = ai.get_editor_property
    al = float(g('WallHandAlpha')); br = bool(g('bWallHandRight')); bf = bool(g('bWallHandFront'))
    nm = g("WallHandNormal")
    L.append(f"alpha={al:.2f} bR={br} bF={bf} n=({nm.x:.3f},{nm.y:.3f},{nm.z:.3f})")
    if al > 0.9 and br and not bf:
        qh = mesh.get_socket_quaternion("hand_r")
        # 벽프레임 yaw: X_wall = Cross(n, up)
        wx, wy = nm.y*1.0, -nm.x*1.0   # Cross((nx,ny,0),(0,0,1)) = (ny, -nx, 0)
        yaw = math.atan2(wy, wx)
        s=math.sin(yaw/2); c=math.cos(yaw/2)
        wq = unreal.Quat(0,0,s,c)
        def conj(q): return unreal.Quat(-q.x,-q.y,-q.z,q.w)
        off = conj(wq).multiply(qh)
        rec = wq.multiply(off)
        d = abs(rec.x*qh.x+rec.y*qh.y+rec.z*qh.z+rec.w*qh.w)
        L.append(f"offR_wall=(X={off.x:.6f},Y={off.y:.6f},Z={off.z:.6f},W={off.w:.6f}) 오차={(1-min(d,1.0))*2:.6f}")
        # 적용
        bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
        ctrl = bp.get_controller_by_name("RigVMModel")
        ctrl.set_pin_default_value("QMulR.B", f"(X={off.x:.6f},Y={off.y:.6f},Z={off.z:.6f},W={off.w:.6f})")
        bp.recompile_vm(); bp.recompile_vm_if_required()
        ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
        L.append(f"QMulR.B 적용, save={ok}")
    else:
        L.append("조건 불충족 — 우벽(bR=True, bF=False, alpha>0.9) 아님")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
