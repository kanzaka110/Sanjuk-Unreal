import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/latch_thresh.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
log = {}
try:
    bp = unreal.load_asset(CR)
    c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()
    c.set_pin_default_value("LatchLessL.B", "0.9", False)
    c.set_pin_default_value("LatchLessR.B", "0.9", False)
    log["latch_threshold"] = "0.9"
    bp.recompile_vm()
    saved = unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False)
    log["saved"] = bool(saved)
except Exception:
    import traceback
    log["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1)
print("LATCH_THRESH_DONE")
