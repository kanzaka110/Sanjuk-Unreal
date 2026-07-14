import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/pelvis_clamp.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
log = {"steps": []}


def step(m):
    log["steps"].append(str(m))


try:
    bp = unreal.load_asset(CR)
    c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()

    def add_unit(path, name, pos):
        n = c.add_unit_node_from_struct_path(path, "Execute", unreal.Vector2D(pos[0], pos[1]), name)
        if n is None:
            raise RuntimeError("add fail " + name)
        step("created " + name)
        return str(n.get_node_path())

    def setdef(pin, val):
        try:
            c.set_pin_default_value(pin, val, False)
            step("DEF " + pin + " = " + val)
        except Exception as e:
            step("DEF ERR " + pin + " : " + repr(e)[:100])

    def link(a, b):
        try:
            ok = c.add_link(a, b)
            step(("LINK OK " if ok else "LINK FAIL ") + a + " -> " + b)
        except Exception as e:
            step("LINK ERR " + a + " -> " + b + " : " + repr(e)[:100])

    # 노드: minZ, sub(MaxDrop), clampMax, alphaMax, lerpZ, makeVec
    nMin = add_unit("/Script/RigVM.RigVMFunction_MathFloatMin", "PvClampMinHandZ", (300, 1700))
    nSub = add_unit("/Script/RigVM.RigVMFunction_MathFloatSub", "PvClampLimit", (450, 1700))
    nMax = add_unit("/Script/RigVM.RigVMFunction_MathFloatMax", "PvClampApply", (600, 1700))
    nAM = add_unit("/Script/RigVM.RigVMFunction_MathFloatMax", "PvClampAlpha", (450, 1850))
    nLp = add_unit("/Script/RigVM.RigVMFunction_MathFloatLerp", "PvClampLerp", (750, 1700))
    nMk = add_unit("/Script/RigVM.RigVMFunction_MathVectorMake", "PvClampMake", (900, 1700))

    # minZ = min(compHandL.Z, compHandR.Z)  — LatchToComp 결과 재활용
    link("LatchToCompL.Result.Z", nMin + ".A")
    link("LatchToCompR.Result.Z", nMin + ".B")
    # limit = minZ - MaxDrop (초기 100, 캘리브레이션 예정)
    link(nMin + ".Result", nSub + ".A")
    setdef(nSub + ".B", "100.0")
    # clampZ = max(원래Z, limit)
    link("RigVMFunction_MathVectorAdd.Result.Z", nMax + ".A")
    link(nSub + ".Result", nMax + ".B")
    # alpha = max(pinL, pinR)
    link("VariableNode_4.Value", nAM + ".A")
    link("VariableNode_3.Value", nAM + ".B")
    # lerpZ = Lerp(원래Z, clampZ, alpha)
    link("RigVMFunction_MathVectorAdd.Result.Z", nLp + ".A")
    link(nMax + ".Result", nLp + ".B")
    link(nAM + ".Result", nLp + ".T")
    # makeVec(XY=원래, Z=lerpZ) -> SetTranslation.Value 재배선
    link("RigVMFunction_MathVectorAdd.Result.X", nMk + ".X")
    link("RigVMFunction_MathVectorAdd.Result.Y", nMk + ".Y")
    link(nLp + ".Result", nMk + ".Z")
    try:
        c.break_link("RigVMFunction_MathVectorAdd.Result", "RigUnit_SetTranslation.Value")
        step("broke Add -> SetTranslation")
    except Exception as e:
        step("break err: " + repr(e)[:80])
    link(nMk + ".Result", "RigUnit_SetTranslation.Value")

    bp.recompile_vm()
    step("recompiled")
    saved = unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False)
    log["saved"] = bool(saved)
except Exception:
    import traceback
    log["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1)
print("PVCLAMP_DONE")
