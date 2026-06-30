import unreal,traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\f525ae6b-fccb-4356-b678-43eef9ec8640\scratchpad\diag_axes.txt"
L=[];w=lambda s:L.append(str(s))
def U(x,y,z): return unreal.Vector(x,y,z)
try:
    world=unreal.UnrealEditorSubsystem().get_game_world()
    pawn=unreal.GameplayStatics.get_player_pawn(world,0)
    if not pawn: w("PIE 아님"); raise SystemExit
    mesh=pawn.get_component_by_class(unreal.SkeletalMeshComponent)
    ai=mesh.get_anim_instance()
    n=ai.get_editor_property("WallHandNormal"); toWall=n*-1.0; up=U(0,0,1)
    w("toWall(=-normal)=%s  up=(0,0,1)"%toWall)
    for nm in ("hand_r","hand_l"):
        q=mesh.get_socket_transform(nm,unreal.RelativeTransformSpace.RTS_WORLD).rotation
        ax={"+X":q.rotate_vector(U(1,0,0)),"+Y":q.rotate_vector(U(0,1,0)),"+Z":q.rotate_vector(U(0,0,1))}
        w("== %s =="%nm)
        best=None
        for k,v in ax.items():
            dW=v.dot(toWall); dU=v.dot(up)
            w("  %s world=%s  dot(toWall)=%+.2f  dot(up)=%+.2f"%(k,v,dW,dU))
        # best palm-normal candidate (max |dot toWall|), best finger (max dot up)
        allc=[]
        for k,v in ax.items():
            allc.append((k,v.dot(toWall))); allc.append(("-"+k[1],-v.dot(toWall)))
        allc.sort(key=lambda t:-t[1])
        w("  => 벽 가장 향하는 축: %s (dot %+.2f)"%(allc[0][0],allc[0][1]))
except SystemExit: pass
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
