import unreal, math, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/flush_fix_l.txt"
L=[]
try:
    w = unreal.UnrealEditorSubsystem().get_game_world()
    p = unreal.GameplayStatics.get_player_pawn(w, 0)
    mesh = p.get_component_by_class(unreal.SkeletalMeshComponent)
    ai = mesh.get_anim_instance()
    nm = ai.get_editor_property("WallHandNormal")
    qh = mesh.get_socket_quaternion("hand_l")
    qc = mesh.get_world_transform().rotation
    # 현재 손바닥-바깥 축(왼손 로컬 -Y) world
    palm = qh.rotate_vector(unreal.Vector(0,-1,0))
    target = unreal.Vector(-nm.x,-nm.y,-nm.z)  # 벽을 향하는 방향
    def dot(a,b): return a.x*b.x+a.y*b.y+a.z*b.z
    def cross(a,b): return unreal.Vector(a.y*b.z-a.z*b.y, a.z*b.x-a.x*b.z, a.x*b.y-a.y*b.x)
    d = max(-1.0, min(1.0, dot(palm,target)))
    L.append(f"현재 palmDot(벽방향)={d:.3f} (1=완전 flush)")
    ax = cross(palm, target)
    axlen = math.sqrt(dot(ax,ax))
    if axlen < 1e-4:
        L.append("이미 정렬됨 — 보정 불필요")
    else:
        ax = unreal.Vector(ax.x/axlen, ax.y/axlen, ax.z/axlen)
        ang = math.acos(d)
        s=math.sin(ang/2); c=math.cos(ang/2)
        qcorr = unreal.Quat(ax.x*s, ax.y*s, ax.z*s, c)  # world 최소회전
        qh_new_world = qcorr.multiply(qh)
        def conj(q): return unreal.Quat(-q.x,-q.y,-q.z,q.w)
        off_new = conj(qc).multiply(qh_new_world)
        L.append(f"보정각={math.degrees(ang):.1f}도, offL_new=(X={off_new.x:.6f},Y={off_new.y:.6f},Z={off_new.z:.6f},W={off_new.w:.6f})")
        bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
        ctrl = bp.get_controller_by_name("RigVMModel")
        ctrl.set_pin_default_value("QSelL.IfFalse", f"(X={off_new.x:.6f},Y={off_new.y:.6f},Z={off_new.z:.6f},W={off_new.w:.6f})")
        bp.recompile_vm(); bp.recompile_vm_if_required()
        ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
        L.append(f"QSelL.IfFalse 적용, save={ok}")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
