import unreal, traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\probe_offset.txt"
L=[]
def w(s): L.append(str(s))
def world():
    try:
        ws=unreal.EditorLevelLibrary.get_game_world()
        if ws: return ws
    except Exception: pass
    try:
        return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    except Exception: return None
try:
    w_=world()
    w(f"world={w_.get_name() if w_ else None} type={w_.get_world_type() if w_ and hasattr(w_,'get_world_type') else '?'}")
    pawn=None
    if w_:
        try: pawn=unreal.GameplayStatics.get_player_pawn(w_,0)
        except Exception: pawn=None
        if pawn is None:
            for a in unreal.GameplayStatics.get_all_actors_of_class(w_,unreal.Pawn):
                if "PC_01_BP" in a.get_class().get_name(): pawn=a; break
    w(f"pawn={pawn.get_name() if pawn else None}")
    if pawn:
        mesh=None
        try: mesh=pawn.get_editor_property("Mesh")
        except Exception: pass
        if mesh is None: mesh=pawn.get_component_by_class(unreal.SkeletalMeshComponent)
        actorZ=pawn.get_actor_location().z
        spineZ=mesh.get_socket_location("spine_05").z
        try: rootZ=mesh.get_socket_location("root").z
        except Exception: rootZ=None
        w(f"actorZ={actorZ:.2f} spine_05Z={spineZ:.2f} rootZ={rootZ}")
        w(f"offset(spine_05 - actor)={spineZ-actorZ:.2f}")
        if rootZ is not None: w(f"offset(spine_05 - root)={spineZ-rootZ:.2f}")
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
