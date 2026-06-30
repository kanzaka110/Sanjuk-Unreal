import unreal,sys
CSV=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\f525ae6b-fccb-4356-b678-43eef9ec8640\scratchpad\rel.csv"
for a in ("_wallhand_axis_h","_wallhand_rel_h","_wallhand_trans_h"):
    h=getattr(sys,a,None)
    if h:
        try: unreal.unregister_slate_post_tick_callback(h)
        except: pass
rows=["t,bR,bF,spd,alpha,hR_x,hR_y,hR_z,hL_x,hL_y,hL_z (root-rel)"]; st={"t":0.0}
def gp(ai,n,d=None):
    try: return ai.get_editor_property(n)
    except: return d
def tick(dt):
    try:
        st["t"]+=dt
        w=unreal.UnrealEditorSubsystem().get_game_world()
        if not w: return
        p=unreal.GameplayStatics.get_player_pawn(w,0)
        if not p: return
        m=p.get_component_by_class(unreal.SkeletalMeshComponent);ai=m.get_anim_instance()
        loc=p.get_actor_location();v=p.get_velocity();spd=(v.x*v.x+v.y*v.y)**0.5
        hr=m.get_socket_location("hand_r")-loc; hl=m.get_socket_location("hand_l")-loc
        al=gp(ai,"WallHandAlpha",-1)
        rows.append("%.2f,%d,%d,%.0f,%.2f,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f"%(st["t"],1 if gp(ai,"bWallHandRight") else 0,1 if gp(ai,"bWallHandFront") else 0,spd,al,hr.x,hr.y,hr.z,hl.x,hl.y,hl.z))
        if len(rows)%5==0: open(CSV,"w").write("\n".join(rows[-220:]))
    except: pass
sys._wallhand_trans_h=unreal.register_slate_post_tick_callback(tick)
open(CSV,"w").write("armed-rel\n")
