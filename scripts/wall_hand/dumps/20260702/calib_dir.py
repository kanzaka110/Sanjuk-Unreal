# -*- coding: utf-8 -*-
"""벽yaw-프레임 캘리브레이션 v2 — 런타임과 동일 수식(액터상대 yaw × 컴포넌트공간 손quat) + flush 보정."""
import unreal, math, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/calib_dir.txt"
L=[]
try:
    w = unreal.UnrealEditorSubsystem().get_game_world()
    p = unreal.GameplayStatics.get_player_pawn(w, 0)
    mesh = p.get_component_by_class(unreal.SkeletalMeshComponent)
    ai = mesh.get_anim_instance()
    g = ai.get_editor_property
    al = float(g('WallHandAlpha')); br = bool(g('bWallHandRight')); bf = bool(g('bWallHandFront'))
    L.append(f"alpha={al:.2f} bR={br} bF={bf}")
    if al < 0.9 or bf: raise RuntimeError("측면 attach 아님")
    hand = "hand_r" if br else "hand_l"
    nm = g("WallHandNormal")
    qh_w = mesh.get_socket_quaternion(hand)
    qc = mesh.get_world_transform().rotation          # 메시 컴포넌트 월드 회전
    aq = p.get_actor_rotation().quaternion()          # 액터 월드 회전
    def conj(q): return unreal.Quat(-q.x,-q.y,-q.z,q.w)
    # 1) flush 보정 (월드 최소회전)
    palm_local = unreal.Vector(0,1,0) if br else unreal.Vector(0,-1,0)
    palm = qh_w.rotate_vector(palm_local)
    tdir = unreal.Vector(-nm.x,-nm.y,-nm.z)
    def dot(a,b): return a.x*b.x+a.y*b.y+a.z*b.z
    def cross(a,b): return unreal.Vector(a.y*b.z-a.z*b.y, a.z*b.x-a.x*b.z, a.x*b.y-a.y*b.x)
    d = max(-1.0,min(1.0,dot(palm,tdir)))
    L.append(f"palmDot={d:.3f} (보정 {math.degrees(math.acos(d)):.1f}도)")
    if d < 0.999:
        ax = cross(palm,tdir); axl = math.sqrt(dot(ax,ax))
        if axl > 1e-4:
            ax = unreal.Vector(ax.x/axl,ax.y/axl,ax.z/axl)
            ang = math.acos(d); s=math.sin(ang/2); c=math.cos(ang/2)
            qh_w = unreal.Quat(ax.x*s,ax.y*s,ax.z*s,c).multiply(qh_w)
    # 2) 런타임 수식 재현: yawRel = 액터상대 −normal yaw / off = conj(quatZ(yawRel)) × qh_comp
    dloc = conj(aq).rotate_vector(tdir)               # ABP InverseTransformDirection(CharacterTransform)
    yawRel = math.atan2(dloc.y, dloc.x)
    s=math.sin(yawRel/2); c=math.cos(yawRel/2)
    qyaw = unreal.Quat(0,0,s,c)
    qh_comp = conj(qc).multiply(qh_w)
    off = conj(qyaw).multiply(qh_comp)
    side = "R" if br else "L"
    L.append(f"yawRel={math.degrees(yawRel):.1f}도  off{side}=(X={off.x:.6f},Y={off.y:.6f},Z={off.z:.6f},W={off.w:.6f})")
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    ctrl.set_pin_default_value(f"QMul{side}.B", f"(X={off.x:.6f},Y={off.y:.6f},Z={off.z:.6f},W={off.w:.6f})")
    bp.recompile_vm(); bp.recompile_vm_if_required()
    ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
    L.append(f"QMul{side}.B 적용, save={ok}")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
