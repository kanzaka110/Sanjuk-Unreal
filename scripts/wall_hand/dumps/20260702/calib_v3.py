# -*- coding: utf-8 -*-
"""v3: 현재 자세 무관 — 런타임 WHWallYaw + 저장된 '좋았던' comp공간 손자세 조합."""
import unreal, math, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/calib_v3.txt"
L=[]
GOOD = {
    "R": unreal.Quat(0.487681,-0.512023,-0.487681,-0.512023),  # 우벽 좋았던 comp 자세
    "L": unreal.Quat(0.418297,-0.570112,0.418297,0.570112),    # 좌벽 flush 보정본
}
try:
    w = unreal.UnrealEditorSubsystem().get_game_world()
    p = unreal.GameplayStatics.get_player_pawn(w, 0)
    mesh = p.get_component_by_class(unreal.SkeletalMeshComponent)
    ai = mesh.get_anim_instance()
    g = ai.get_editor_property
    al = float(g('WallHandAlpha')); br = bool(g('bWallHandRight')); bf = bool(g('bWallHandFront'))
    yawDeg = float(g('WHWallYaw'))
    L.append(f"alpha={al:.2f} bR={br} bF={bf} WHWallYaw={yawDeg:.1f}도")
    if al < 0.9 or bf: raise RuntimeError("측면 attach 아님")
    side = "R" if br else "L"
    yr = math.radians(yawDeg)
    s=math.sin(yr/2); c=math.cos(yr/2)
    def conj(q): return unreal.Quat(-q.x,-q.y,-q.z,q.w)
    off = conj(unreal.Quat(0,0,s,c)).multiply(GOOD[side])
    L.append(f"off{side}=(X={off.x:.6f},Y={off.y:.6f},Z={off.z:.6f},W={off.w:.6f})")
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    ctrl.set_pin_default_value(f"QMul{side}.B", f"(X={off.x:.6f},Y={off.y:.6f},Z={off.z:.6f},W={off.w:.6f})")
    bp.recompile_vm(); bp.recompile_vm_if_required()
    ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
    L.append(f"QMul{side}.B 적용, save={ok}")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
