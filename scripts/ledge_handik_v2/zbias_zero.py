import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/zbias_zero.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
log = {}
try:
    bp = unreal.load_asset(CR)
    c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()
    c.set_pin_default_value("HandZBiasL.B", "(X=0.0,Y=0.0,Z=0.0)", False)
    c.set_pin_default_value("HandZBiasR.B", "(X=0.0,Y=0.0,Z=0.0)", False)
    log["zbias"] = "0"
    bp.recompile_vm()
    saved = unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False)
    log["saved"] = bool(saved)
except Exception:
    import traceback
    log["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1)
print("ZBIAS_ZERO_DONE")
