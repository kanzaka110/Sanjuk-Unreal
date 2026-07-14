import unreal, sys, types

# 핸드IK v2 디버그 — 알파(커브 스무딩) + 손 위치. 재실행 시 토글.
m = sys.modules.get("__hdv2__")
if m is not None and getattr(m, "handle", None) is not None:
    try:
        unreal.unregister_slate_post_tick_callback(m.handle)
    except Exception:
        pass
    m.handle = None
    unreal.log("[HandIKv2] debug OFF")
else:
    mod = types.ModuleType("__hdv2__")
    sys.modules["__hdv2__"] = mod

    def _tick(dt):
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
            aL = float(anim.get_editor_property("LedgeHandIKAlphaL"))
            aR = float(anim.get_editor_property("LedgeHandIKAlphaR"))
            hl = mesh.get_socket_location("hand_l")
            hr = mesh.get_socket_location("hand_r")
            for pos, a in ((hl, aL), (hr, aR)):
                col = unreal.LinearColor(1.0 - a, a, 0.0, 1.0)
                unreal.SystemLibrary.draw_debug_sphere(w, pos, 5.0, 8, col, 0.0, 0.6)
            head = pawn.get_actor_location() + unreal.Vector(0, 0, 120)
            txt = "IKv2  aL %.2f  aR %.2f" % (aL, aR)
            unreal.SystemLibrary.draw_debug_string(w, head, txt, None,
                                                   unreal.LinearColor(0, 1, 1, 1), 0.0)
        except Exception:
            pass

    mod.handle = unreal.register_slate_post_tick_callback(_tick)
    unreal.log("[HandIKv2] debug ON")
