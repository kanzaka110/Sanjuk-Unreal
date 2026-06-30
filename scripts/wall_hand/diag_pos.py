import unreal,traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\f525ae6b-fccb-4356-b678-43eef9ec8640\scratchpad\diag_pos.txt"
L=[];w=lambda s:L.append(str(s))
def U(x,y,z): return unreal.Vector(x,y,z)
try:
    world=unreal.UnrealEditorSubsystem().get_game_world()
    pawn=unreal.GameplayStatics.get_player_pawn(world,0)
    if not pawn: w("PIE 아님(pawn None) — 재생 필요"); raise SystemExit
    mesh=pawn.get_component_by_class(unreal.SkeletalMeshComponent)
    ai=mesh.get_anim_instance()
    bf=ai.get_editor_property("bWallHandFront");br=ai.get_editor_property("bWallHandRight");a=ai.get_editor_property("WallHandAlpha")
    tR=ai.get_editor_property("WallHandTargetWorld");tL=ai.get_editor_property("WallHandTargetL")
    aloc=pawn.get_actor_location();aq=pawn.get_actor_transform().rotation
    fwd=aq.get_forward_vector() if hasattr(aq,'get_forward_vector') else aq.rotate_vector(U(1,0,0))
    rgt=aq.rotate_vector(U(0,1,0)); up=U(0,0,1)
    pelvis=mesh.get_socket_location("pelvis")
    def rel(p,nm):
        d=p-aloc
        w("  %s: fwd=%.1f right=%.1f up(vs actor base)=%.1f | height vs pelvis=%.1f"%(nm,d.dot(fwd),d.dot(rgt),d.dot(up),(p-pelvis).z))
    w("bFront=%s bRight=%s alpha=%.2f"%(bf,br,a))
    w("actor loc=%s"%aloc)
    rel(tR,"rightT"); rel(tL,"leftT")
    hr=mesh.get_socket_location("hand_r");hl=mesh.get_socket_location("hand_l")
    rel(hr,"hand_r"); rel(hl,"hand_l")
    w("spread(rightT-leftT)=%.1fcm"%((tR-tL).length()))
    w("head height vs pelvis=%.1f, hand_r height vs pelvis=%.1f"%((mesh.get_socket_location('head')-pelvis).z,(hr-pelvis).z))
except SystemExit: pass
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
