# PIE 화면 버스트 캡처 — PIE 감지되면 0.3s 간격 40장 (약 12초) 촬영 후 자동 해제
import unreal, sys, types

for name in ("__cap__",):
    m = sys.modules.get(name)
    if m is not None and getattr(m, "handle", None) is not None:
        try:
            unreal.unregister_slate_post_tick_callback(m.handle)
        except Exception:
            pass
        m.handle = None

mod = types.ModuleType("__cap__")
sys.modules["__cap__"] = mod
OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/piecap"
import os
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    try:
        os.remove(os.path.join(OUT, f))
    except Exception:
        pass


def _tick(dt, _st={"t": 0.0, "n": 0, "started": False}):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None:
            return
        _st["t"] += dt
        if _st["t"] < 0.3:
            return
        _st["t"] = 0.0
        _st["n"] += 1
        if _st["n"] > 40:
            unreal.unregister_slate_post_tick_callback(mod.handle)
            mod.handle = None
            print("capture done")
            return
        path = "%s/f%03d.png" % (OUT, _st["n"])
        unreal.AutomationLibrary.take_high_res_screenshot(1280, 720, path)
    except Exception as e:
        print("cap err", e)


mod.handle = unreal.register_slate_post_tick_callback(_tick)
print("capture burst armed -> " + OUT)
