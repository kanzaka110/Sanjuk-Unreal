import unreal, json, sys, time, types

for name in ("__ikv2__",):
    m = sys.modules.get(name)
    if m is not None and getattr(m, "handle", None) is not None:
        try:
            unreal.unregister_slate_post_tick_callback(m.handle)
        except Exception:
            pass
        m.handle = None

mod = types.ModuleType("__ikv2__")
sys.modules["__ikv2__"] = mod
LOG = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/ikv2.log"
open(LOG, "w").close()
NL = chr(10)


def _tick(dt, _st={"t0": time.time(), "n": 0, "pl": None, "pr": None}):
    _st["n"] += 1
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None:
            return
        pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
        if pawn is None:
            return
        mesh = pawn.get_components_by_class(unreal.SkeletalMeshComponent)[0]
        anim = mesh.get_anim_instance()
        if anim is None:
            return
        if _st["n"] % 2 != 0:
            return
        rec = {"t": round(time.time() - _st["t0"], 3)}
        # raw 커브
        try:
            rec["cL"] = round(float(anim.get_curve_value("ledge_hand_ik_l")), 2)
            rec["cR"] = round(float(anim.get_curve_value("ledge_hand_ik_r")), 2)
        except Exception as e:
            rec["cerr"] = repr(e)[:60]
        # 스무딩+게이트 후 알파
        rec["aL"] = round(float(anim.get_editor_property("LedgeHandIKAlphaL")), 2)
        rec["aR"] = round(float(anim.get_editor_property("LedgeHandIKAlphaR")), 2)
        # 손 틱변위 (정착게이트 판정용)
        hl = mesh.get_socket_location("hand_l")
        hr = mesh.get_socket_location("hand_r")
        if _st["pl"] is not None:
            rec["dL"] = round((hl - _st["pl"]).length(), 2)
            rec["dR"] = round((hr - _st["pr"]).length(), 2)
        _st["pl"] = hl
        _st["pr"] = hr
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
print("IKV2_PROBE_ON")
