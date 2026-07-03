# 라이브 PIE에서 프레임별 캡슐(액터) vs 메시/펠비스 월드 위치 샘플링 (10초)
# 몬스터 밀착 덜덜거림: 캡슐 진동(CMC) vs 메시 전용 진동(ABP/OffsetRootBone/IK) 판별용
import unreal

OUT = r"C:/Dev/Sanjuk-Unreal/Saved/jitter_samples.csv"
DURATION = 10.0

state = {"t": 0.0, "rows": [], "handle": None, "done": False}


def find_pawn():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not world:
        return None, None
    actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Character)
    pc = None
    monster = None
    for a in actors:
        n = a.get_name()
        if n.startswith("PC_01"):
            pc = a
        elif n.startswith("M_001"):
            monster = a
    return pc, monster


def tick(dt):
    if state["done"]:
        return
    state["t"] += dt
    try:
        pc, monster = find_pawn()
        if pc:
            al = pc.get_actor_location()
            ar = pc.get_actor_rotation()
            mesh = pc.get_editor_property("mesh")
            ml = mesh.get_world_location() if mesh else unreal.Vector()
            try:
                pel = mesh.get_socket_location("pelvis")
            except Exception:
                pel = unreal.Vector()
            try:
                root = mesh.get_socket_location("root")
            except Exception:
                root = unreal.Vector()
            mloc = monster.get_actor_location() if monster else unreal.Vector()
            vel = pc.get_velocity()
            state["rows"].append(
                f"{state['t']:.4f},{dt:.4f},"
                f"{al.x:.3f},{al.y:.3f},{al.z:.3f},{ar.yaw:.3f},"
                f"{ml.x:.3f},{ml.y:.3f},{ml.z:.3f},"
                f"{pel.x:.3f},{pel.y:.3f},{pel.z:.3f},"
                f"{root.x:.3f},{root.y:.3f},{root.z:.3f},"
                f"{vel.x:.2f},{vel.y:.2f},{vel.z:.2f},"
                f"{mloc.x:.2f},{mloc.y:.2f},{mloc.z:.2f}"
            )
    except Exception as e:
        state["rows"].append(f"ERR,{state['t']:.4f},{e}")
    if state["t"] >= DURATION:
        state["done"] = True
        try:
            unreal.unregister_slate_post_tick_callback(state["handle"])
        except Exception:
            pass
        header = ("t,dt,ax,ay,az,ayaw,mx,my,mz,px,py,pz,rx,ry,rz,vx,vy,vz,monx,mony,monz")
        with open(OUT, "w", encoding="utf-8") as f:
            f.write(header + "\n" + "\n".join(state["rows"]))
        unreal.log("[JITTER_SAMPLER] done rows=%d -> %s" % (len(state["rows"]), OUT))


state["handle"] = unreal.register_slate_post_tick_callback(tick)
unreal.log("[JITTER_SAMPLER] started, %.1fs" % DURATION)
