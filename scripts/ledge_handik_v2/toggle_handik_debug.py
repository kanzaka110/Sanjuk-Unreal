import unreal, sys

# 디버그 드로잉 토글 — 실행할 때마다 on<->off
m = sys.modules.get("__hddbg__")
if m is not None and getattr(m, "handle", None) is not None:
    try:
        unreal.unregister_slate_post_tick_callback(m.handle)
    except Exception:
        pass
    m.handle = None
    unreal.log("[HandIK] debug draw OFF")
else:
    import importlib.util
    path = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/C--Dev-Sanjuk-Unreal/3046997f-cc6c-41e4-9b62-36ad8e3fb125/scratchpad/handik_debug_draw.py"
    spec = importlib.util.spec_from_file_location("__hddbg_loader__", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    unreal.log("[HandIK] debug draw ON")
