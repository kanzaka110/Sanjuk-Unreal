import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/calib_r.txt"
L=[]
try:
    w = unreal.UnrealEditorSubsystem().get_game_world()
    p = unreal.GameplayStatics.get_player_pawn(w, 0)
    mesh = p.get_component_by_class(unreal.SkeletalMeshComponent)
    ai = mesh.get_anim_instance()
    g = ai.get_editor_property
    al = float(g('WallHandAlpha')); br = bool(g('bWallHandRight')); bf = bool(g('bWallHandFront'))
    L.append(f"alpha={al:.2f} bR={br} bF={bf}")
    if al > 0.9 and br and not bf:
        qr = mesh.get_socket_quaternion("root")
        qh = mesh.get_socket_quaternion("hand_r")
        def conj(q): return unreal.Quat(-q.x,-q.y,-q.z,q.w)
        off = conj(qr).multiply(qh)
        rec = qr.multiply(off)
        d = abs(rec.x*qh.x+rec.y*qh.y+rec.z*qh.z+rec.w*qh.w)
        L.append(f"offR=({off.x:.6f},{off.y:.6f},{off.z:.6f},{off.w:.6f}) 재구성오차={(1-min(d,1.0))*2:.6f}")
    else:
        L.append("조건 불충족 — 우벽에 alpha 1로 붙어있지 않음")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
