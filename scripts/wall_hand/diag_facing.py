import unreal,traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\f525ae6b-fccb-4356-b678-43eef9ec8640\scratchpad\diag_facing.txt"
L=[];w=lambda s:L.append(str(s))
def U(x,y,z): return unreal.Vector(x,y,z)
try:
    world=unreal.UnrealEditorSubsystem().get_game_world()
    pawn=unreal.GameplayStatics.get_player_pawn(world,0)
    mesh=pawn.get_component_by_class(unreal.SkeletalMeshComponent)
    ai=mesh.get_anim_instance()
    bf=ai.get_editor_property("bWallHandFront");br=ai.get_editor_property("bWallHandRight")
    n=ai.get_editor_property("WallHandNormal");toWall=n*-1.0
    aq=pawn.get_actor_transform().rotation
    fwd=aq.rotate_vector(U(1,0,0));rgt=aq.rotate_vector(U(0,1,0))
    w("bFront=%s bRight=%s"%(bf,br))
    w("toWall=%s"%toWall)
    w("actorForward=%s  dot(toWall)=%+.2f  <- 1이면 정면, 0이면 측면"%(fwd,fwd.dot(toWall)))
    w("actorRight  =%s  dot(toWall)=%+.2f  <- 1이면 벽이 오른쪽(측면)"%(rgt,rgt.dot(toWall)))
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
