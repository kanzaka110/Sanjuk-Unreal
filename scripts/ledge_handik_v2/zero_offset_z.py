import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/offset_z.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
result = {}
try:
    bp = unreal.load_asset(CR)
    c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()
    # 오프셋 게인 = RigVMFunction_MathVectorMul (A <- Sub.Result, Result -> ClampLength)
    ok = c.set_pin_default_value("RigVMFunction_MathVectorMul.B.Z", "0.0", False)
    result["set_offset_gain_Z0"] = bool(ok)
    # 확인
    g = c.get_graph()
    for n in g.get_nodes():
        if str(n.get_node_path()) == "RigVMFunction_MathVectorMul":
            for p in n.get_pins():
                if str(p.get_name()) == "B":
                    result["offset_gain_B"] = str(p.get_default_value())
    bp.recompile_vm()
    saved = unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False)
    result["saved"] = bool(saved)
except Exception:
    import traceback
    result["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(result, fp, indent=1)
print("OFFSET_Z_DONE")
