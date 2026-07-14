import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/ratescale_result.json"
BASE = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing/"
TARGETS = ["P_Player_Ledge_Move_ShortL", "P_Player_Ledge_Move_ShortR",
           "P_Player_Ledge_Move_ShortL_01", "P_Player_Ledge_Move_ShortL_02",
           "P_Player_Ledge_Move_ShortR_01", "P_Player_Ledge_Move_ShortR_02",
           "P_Player_Ledge_Move_ShortL_Wallless", "P_Player_Ledge_Move_ShortR_Wallless"]
RATE = 1.0
result = {}
try:
    for name in TARGETS:
        seq = unreal.load_asset(BASE + name)
        if seq is None:
            result[name] = "LOAD_FAIL"
            continue
        old = float(seq.get_editor_property("rate_scale"))
        seq.set_editor_property("rate_scale", RATE)
        saved = unreal.EditorAssetLibrary.save_asset(BASE + name, only_if_is_dirty=False)
        result[name] = {"old": old, "new": RATE, "saved": bool(saved)}
except Exception:
    import traceback
    result["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(result, fp, indent=1)
print("RATESCALE_DONE")

