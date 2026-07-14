# 폴벡터 바이어스 삽입 — 역꺾임 수정 (v5.7)
# 문제: 폴 = 애님 lowerarm 위치인데 렛지 애님 팔이 거의 일직선 → 폴이 어깨-손 축 위 → 굽힘평면 퇴화
# 수정: 폴' = lowerarm + 자연굽힘방향 바이어스 (실측 perp ×10: L=(35,17,-7) R=(-36,14,-5), 컴포넌트공간)
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/ik_pole_bias.json"
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

    addL = add_unit("/Script/RigVM.RigVMFunction_MathVectorAdd", "PoleBiasL", (300, 1700))
    addR = add_unit("/Script/RigVM.RigVMFunction_MathVectorAdd", "PoleBiasR", (300, 1850))

    def setdef(pin, val):
        try:
            c.set_pin_default_value(pin, val, False)
            step("DEF " + pin)
        except Exception as e:
            step("DEF ERR " + pin + " : " + repr(e)[:100])

    def relink(a, b):
        try:
            c.break_all_links(b, True)
            step("BREAK " + b)
        except Exception as e:
            step("BREAK ERR " + b + " : " + repr(e)[:80])
        try:
            ok = c.add_link(a, b)
            step(("LINK OK " if ok else "LINK FAIL ") + a + " -> " + b)
        except Exception as e:
            step("LINK ERR " + a + " -> " + b + " : " + repr(e)[:100])

    setdef(addL + ".B", "(X=35.0,Y=17.0,Z=-7.0)")
    setdef(addR + ".B", "(X=-36.0,Y=14.0,Z=-5.0)")

    # 게터 → Add.A
    relink("PoleElbowL.Transform.Translation", addL + ".A")
    relink("PoleElbowR.Transform.Translation", addR + ".A")
    # Add.Result → PoleVector (기존 직결 대체)
    relink(addL + ".Result", "RigUnit_TwoBoneIKSimplePerItem.PoleVector")
    relink(addR + ".Result", "RigUnit_TwoBoneIKSimplePerItem_1.PoleVector")

    bp.recompile_vm()
    step("recompiled")
    saved = unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False)
    log["saved"] = bool(saved)
except Exception:
    import traceback
    log["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1)
print("POLE_BIAS_DONE")
