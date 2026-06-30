import unreal,sys
# kill prior handles
for attr in ("_wallhand_rel_h","_wallhand_axis_h"):
    h=getattr(sys,attr,None)
    if h:
        try: unreal.unregister_slate_post_tick_callback(h)
        except: pass
def U(x,y,z): return unreal.Vector(x,y,z)
def C(r,g,b): return unreal.LinearColor(r,g,b,1.0)
def draw(dt):
    try:
        world=unreal.UnrealEditorSubsystem().get_game_world()
        if not world: return
        pawn=unreal.GameplayStatics.get_player_pawn(world,0)
        if not pawn: return
        mesh=pawn.get_component_by_class(unreal.SkeletalMeshComponent)
        ai=mesh.get_anim_instance()
        n=ai.get_editor_property("WallHandNormal")
        toWall=n*-1.0
        for nm in ("hand_r","hand_l"):
            xf=mesh.get_socket_transform(nm,unreal.RelativeTransformSpace.RTS_WORLD)
            p=xf.translation; q=xf.rotation
            X=q.rotate_vector(U(1,0,0));Y=q.rotate_vector(U(0,1,0));Z=q.rotate_vector(U(0,0,1))
            unreal.SystemLibrary.draw_debug_line(world,p,p+X*25,C(1,0,0),0,1.0)   # X red
            unreal.SystemLibrary.draw_debug_line(world,p,p+Y*25,C(0,1,0),0,1.0)   # Y green
            unreal.SystemLibrary.draw_debug_line(world,p,p+Z*25,C(0,0.4,1),0,1.0) # Z blue
            unreal.SystemLibrary.draw_debug_line(world,p,p+toWall*35,C(1,1,1),0,2.5) # wall dir white thick
    except: pass
sys._wallhand_axis_h=unreal.register_slate_post_tick_callback(draw)
unreal.log("palm_axisdraw armed")
