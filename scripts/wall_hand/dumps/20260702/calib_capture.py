import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/calib.txt"
L=[]
try:
    w = unreal.UnrealEditorSubsystem().get_game_world()
    p = unreal.GameplayStatics.get_player_pawn(w, 0)
    mesh = p.get_component_by_class(unreal.SkeletalMeshComponent)
    ai = mesh.get_anim_instance()
    g = ai.get_editor_property
    L.append(f"alpha={float(g('WallHandAlpha')):.2f} bR={bool(g('bWallHandRight'))} bF={bool(g('bWallHandFront'))}")
    nm = g("WallHandNormal"); L.append(f"normal=({nm.x:.3f},{nm.y:.3f},{nm.z:.3f})")
    # 30프레임 평균 대신 단발 3회 샘플 (정지라 안정)
    for name in ("root","pelvis","hand_r","hand_l"):
        q = mesh.get_socket_quaternion(name)
        L.append(f"{name} quat=({q.x:.6f},{q.y:.6f},{q.z:.6f},{q.w:.6f})")
    # q_off 후보 (양 방향 합성) — 검증용 재구성 오차 포함
    qr = mesh.get_socket_quaternion("root")
    qh = mesh.get_socket_quaternion("hand_r")
    def conj(q): return unreal.Quat(-q.x,-q.y,-q.z,q.w)
    def mul(a,b): return a.multiply(b) if hasattr(a,"multiply") else a*b
    for label, off in (("A(=inv(root)*hand)", mul(conj(qr), qh)), ("B(=hand*inv(root))", mul(qh, conj(qr)))):
        # 재구성: candA: root*off / candB: off*root
        ra = mul(qr, off); rb = mul(off, qr)
        def err(a,b):
            d = abs(a.x*b.x+a.y*b.y+a.z*b.z+a.w*b.w)
            return round((1-min(d,1.0))*2, 6)
        L.append(f"off{label}=({off.x:.6f},{off.y:.6f},{off.z:.6f},{off.w:.6f}) errA(root*off)={err(ra,qh)} errB(off*root)={err(rb,qh)}")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
