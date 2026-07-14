import unreal, json, sys, time, types

for name in ("__ikv2__", "__ikdrift__", "__ikiso__"):
    m = sys.modules.get(name)
    if m is not None and getattr(m, "handle", None) is not None:
        try:
            unreal.unregister_slate_post_tick_callback(m.handle)
        except Exception:
            pass
        m.handle = None

mod = types.ModuleType("__ikiso__")
sys.modules["__ikiso__"] = mod
LOG = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/ikiso.log"
open(LOG, "w").close()
NL = chr(10)

# (phase명, 진입 시 콘솔 명령 목록, 지속 초)
PHASES = [
    ("base", [], 5.0),
    ("rigidbody_off", ["p.RigidBodyNode 0"], 5.0),
    ("footplacement_off", ["p.RigidBodyNode 1", "a.AnimNode.FootPlacement.Enable 0"], 5.0),
    ("legik_off", ["a.AnimNode.FootPlacement.Enable 1", "a.AnimNode.LegIK.Enable 0"], 5.0),
    ("all_restore", ["a.AnimNode.LegIK.Enable 1"], 5.0),
]


def _tick(dt, _st={"n": 0, "t0": None, "pi": -1}):
    _st["n"] += 1
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None:
            _st["t0"] = None
            _st["pi"] = -1
            return
        pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
        if pawn is None:
            return
        mesh = pawn.get_components_by_class(unreal.SkeletalMeshComponent)[0]
        anim = mesh.get_anim_instance()
        if anim is None:
            return
        aL = float(anim.get_editor_property("LedgeHandIKAlphaL"))
        # 렛지 IK가 켜진 뒤부터 타임라인 시작 (렛지 잡을 때까지 대기)
        if _st["t0"] is None:
            if aL < 0.9:
                return
            _st["t0"] = time.time()
        el = time.time() - _st["t0"]
        # 현재 phase 결정 + 진입 명령 실행
        acc = 0.0
        idx = None
        for i, (pname, cmds, dur) in enumerate(PHASES):
            if el < acc + dur:
                idx = i
                break
            acc += dur
        if idx is None:
            for c in ("p.RigidBodyNode 1", "a.AnimNode.FootPlacement.Enable 1",
                      "a.AnimNode.LegIK.Enable 1"):
                unreal.SystemLibrary.execute_console_command(w, c)
            with open(LOG, "a") as f:
                f.write(json.dumps({"phase": "DONE"}) + NL)
            unreal.unregister_slate_post_tick_callback(mod.handle)
            mod.handle = None
            return
        if idx != _st["pi"]:
            _st["pi"] = idx
            for c in PHASES[idx][1]:
                unreal.SystemLibrary.execute_console_command(w, c)
        if _st["n"] % 2 != 0:
            return
        if hasattr(mesh, "get_world_transform"):
            m2w = mesh.get_world_transform()
        else:
            m2w = mesh.get_socket_transform("", unreal.RelativeTransformSpace.RTS_WORLD)
        cl = anim.get_editor_property("LedgeHandIdleCompL")
        cr = anim.get_editor_property("LedgeHandIdleCompR")
        tL = m2w.transform_location(cl)
        tR = m2w.transform_location(cr)
        hl = mesh.get_socket_location("hand_l")
        hr = mesh.get_socket_location("hand_r")
        rec = {
            "ph": PHASES[idx][0],
            "t": round(el, 2),
            "aL": round(aL, 2),
            "gapL": round((hl - tL).length(), 2),
            "gapR": round((hr - tR).length(), 2),
        }
        with open(LOG, "a") as f:
            f.write(json.dumps(rec) + NL)
    except Exception as e:
        if _st["n"] % 120 == 0:
            try:
                with open(LOG, "a") as f:
                    f.write(json.dumps({"err": repr(e)[:150]}) + NL)
            except Exception:
                pass


mod.handle = unreal.register_slate_post_tick_callback(_tick)
print("IKISO_PROBE_ON")
