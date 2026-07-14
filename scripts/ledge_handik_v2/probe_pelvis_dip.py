import unreal, json, sys, time, types

for name in ("__pvdip__",):
    m = sys.modules.get(name)
    if m is not None and getattr(m, "handle", None) is not None:
        try:
            unreal.unregister_slate_post_tick_callback(m.handle)
        except Exception:
            pass
        m.handle = None

mod = types.ModuleType("__pvdip__")
sys.modules["__pvdip__"] = mod
LOG = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/pelvis_dip.log"
open(LOG, "w").close()
NL = chr(10)


def _tick(dt, _st={"t0": time.time(), "n": 0}):
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
        pv = mesh.get_socket_location("pelvis")
        actor_z = pawn.get_actor_location().z
        mesh_z = mesh.get_world_transform().translation.z
        rec = {"t": round(time.time() - _st["t0"], 3),
               "pvZ": round(pv.z, 1),                    # 펠비스 월드 Z
               "acZ": round(actor_z, 1),                 # 캡슐(액터) Z
               "msZ": round(mesh_z, 1),                  # 메시 컴포넌트 Z
               "rel": round(pv.z - mesh_z, 1)}           # 펠비스-메시 상대 Z (애님/리그 성분)
        try:
            rec["cP"] = round(float(anim.get_curve_value("ledge_pelvis_spring")), 2)
            rec["aL"] = round(float(anim.get_editor_property("LedgeHandIKAlphaL")), 2)
            rec["dg"] = round(float(anim.get_editor_property("LedgeDangleAlpha")), 2)
        except Exception:
            pass
        with open(LOG, "a") as f:
            f.write(json.dumps(rec) + NL)
    except Exception:
        pass


mod.handle = unreal.register_slate_post_tick_callback(_tick)
print("PVDIP_ON")
