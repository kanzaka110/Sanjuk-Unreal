import unreal,traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\f525ae6b-fccb-4356-b678-43eef9ec8640\scratchpad\diag_reach.txt"
L=[];w=lambda s:L.append(str(s))
def vl(v): return (v.x*v.x+v.y*v.y+v.z*v.z)**0.5
try:
    world=unreal.UnrealEditorSubsystem().get_game_world()
    pawn=unreal.GameplayStatics.get_player_pawn(world,0)
    mesh=pawn.get_component_by_class(unreal.SkeletalMeshComponent)
    ai=mesh.get_anim_instance()
    bf=ai.get_editor_property("bWallHandFront");br=ai.get_editor_property("bWallHandRight");a=ai.get_editor_property("WallHandAlpha")
    tR=ai.get_editor_property("WallHandTargetWorld");tL=ai.get_editor_property("WallHandTargetL")
    hr=mesh.get_socket_location("hand_r");hl=mesh.get_socket_location("hand_l")
    w("bFront=%s bRight=%s alpha=%.2f"%(bf,br,a))
    w("RIGHT target=%s  hand_r=%s  gap=%.1fcm"%(tR,hr,vl(hr-tR)))
    w("LEFT  target=%s  hand_l=%s  gap=%.1fcm"%(tL,hl,vl(hl-tL)))
    w("hand_r<->hand_l spread=%.1fcm"%vl(hr-hl))
    # palm facing: hand_r right-vector (palm normal approx). socket transform
    xr=mesh.get_socket_transform("hand_r",unreal.RelativeTransformSpace.RTS_WORLD).rotation
    xl=mesh.get_socket_transform("hand_l",unreal.RelativeTransformSpace.RTS_WORLD).rotation
    # report palm axis guesses (X/Y/Z of hand bone in world)
    for nm,q in (("R",xr),("L",xl)):
        w("  hand_%s axes X=%s Y=%s Z=%s"%(nm,q.get_forward_vector(),q.get_right_vector(),q.get_up_vector()))
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
