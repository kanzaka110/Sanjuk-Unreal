import unreal,traceback,math
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\f525ae6b-fccb-4356-b678-43eef9ec8640\scratchpad\diag_space.txt"
L=[];w=lambda s:L.append(str(s))
def U(x,y,z): return unreal.Vector(x,y,z)
def nrm(v):
    m=(v.x*v.x+v.y*v.y+v.z*v.z)**0.5
    return U(v.x/m,v.y/m,v.z/m) if m>1e-6 else U(0,0,0)
def cross(a,b): return U(a.y*b.z-a.z*b.y, a.z*b.x-a.x*b.z, a.x*b.y-a.y*b.x)
try:
    world=unreal.UnrealEditorSubsystem().get_game_world()
    pawn=unreal.GameplayStatics.get_player_pawn(world,0)
    mesh=pawn.get_component_by_class(unreal.SkeletalMeshComponent)
    ai=mesh.get_anim_instance()
    cT=mesh.get_world_transform(); cR=cT.rotation
    invR=cR.inverse() if hasattr(cR,'inverse') else None
    w("mesh comp world rot (euler)=%s"%cR.euler())
    tR=ai.get_editor_property("WallHandTargetWorld");tL=ai.get_editor_property("WallHandTargetL")
    n=ai.get_editor_property("WallHandNormal")
    wDelta=tR-tL
    wCross=nrm(cross(nrm(wDelta),U(0,0,1)))
    w("world: rightT-leftT=%s"%wDelta)
    w("world wall dir (-normal)=%s"%(n*-1.0))
    w("world cross(unit(delta),up)=%s   (벽향과 일치해야)"%wCross)
    # component-space delta (what ToRig.Global delta would be if ToRig=component)
    cDelta=cR.unrotate_vector(wDelta) if hasattr(cR,'unrotate_vector') else None
    if cDelta is not None:
        cCross=nrm(cross(nrm(cDelta),U(0,0,1)))
        cCross_w=cR.rotate_vector(cCross)
        w("comp: invRot(delta)=%s"%cDelta)
        w("comp cross(unit(compDelta),up)=%s  (CR가 만든 값 추정)"%cCross)
        w("  -> 이 comp방향을 world로 = %s  (palm이 실제 향한 곳; ±Z면 이게 범인)"%cCross_w)
    # also: world wall dir expressed in component (what I SHOULD feed to Primary.Target if space=component)
    wd=n*-1.0
    wd_c=cR.unrotate_vector(wd)
    w("FIX단서: world벽향(-normal)을 comp로 변환=%s  (이걸 Primary.Target에 줘야 palm이 벽 향함)"%wd_c)
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
