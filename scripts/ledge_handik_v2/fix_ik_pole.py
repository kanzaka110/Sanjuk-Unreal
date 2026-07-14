import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/ik_pole_fix.json"
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

    gtL = add_unit("/Script/ControlRig.RigUnit_GetTransform", "PoleElbowL", (100, 1700))
    gtR = add_unit("/Script/ControlRig.RigUnit_GetTransform", "PoleElbowR", (100, 1850))

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

    setdef(gtL + ".Item", '(Type=Bone,Name="lowerarm_l")')
    setdef(gtR + ".Item", '(Type=Bone,Name="lowerarm_r")')
    setdef(gtL + ".Space", "GlobalSpace")
    setdef(gtR + ".Space", "GlobalSpace")
    setdef(gtL + ".bInitial", "False")
    setdef(gtR + ".bInitial", "False")

    # 폴 = 애님 팔꿈치 위치 (Location)
    link(gtL + ".Transform.Translation", "RigUnit_TwoBoneIKSimplePerItem.PoleVector")
    link(gtR + ".Transform.Translation", "RigUnit_TwoBoneIKSimplePerItem_1.PoleVector")
    setdef("RigUnit_TwoBoneIKSimplePerItem.PoleVectorKind", "Location")
    setdef("RigUnit_TwoBoneIKSimplePerItem_1.PoleVectorKind", "Location")

    bp.recompile_vm()
    step("recompiled")
    saved = unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False)
    log["saved"] = bool(saved)
except Exception:
    import traceback
    log["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1)
print("POLE_FIX_DONE")
