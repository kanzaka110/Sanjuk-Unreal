# CR 발 IK 빌드 (FrontBlocked 벽 짚기, 핸드IK 미러) — v9 Stage 2
# TwoBoneIK(thigh->calf->foot) x2 + 이펙터 Lerp(애님발, FootTarget, 알파) + 폴 바이어스 + 신전클램프 76
# ⚠ CR 변수(FootTargetL/R, FootAlphaL/R)는 크래시 함정으로 미생성 — Lerp B/T 디폴트(0)=패스스루.
#    유저 수동 변수 생성 후 wire_foot_vars 단계에서 연결.
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/cr_foot_ik.json"
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
            step("DEF " + pin)
        except Exception as e:
            step("DEF ERR " + pin + " : " + repr(e)[:100])

    def link(a, b, brk=False):
        if brk:
            try:
                c.break_all_links(b, True)
            except Exception:
                pass
        try:
            ok = c.add_link(a, b)
            step(("LINK OK " if ok else "LINK FAIL ") + a + " -> " + b)
        except Exception as e:
            step("LINK ERR " + a + " -> " + b + " : " + repr(e)[:100])

    POLE_BIAS = {"L": "(X=16.0,Y=20.0,Z=52.0)", "R": "(X=-18.0,Y=23.0,Z=49.0)"}
    prev_exec = "RigUnit_TwoBoneIKSimplePerItem_1.ExecutePin"
    for side, sfx in (("l", "L"), ("r", "R")):
        y = 2200 if sfx == "L" else 2500
        # 애님 발 트랜스폼 / 폴(무릎) / 힙(클램프 기준)
        gf = add_unit("/Script/ControlRig.RigUnit_GetTransform", "AnimFoot" + sfx, (100, y))
        setdef(gf + ".Item", '(Type=Bone,Name="foot_%s")' % side)
        setdef(gf + ".Space", "GlobalSpace"); setdef(gf + ".bInitial", "False")
        gk = add_unit("/Script/ControlRig.RigUnit_GetTransform", "PoleKnee" + sfx, (100, y + 90))
        setdef(gk + ".Item", '(Type=Bone,Name="calf_%s")' % side)
        setdef(gk + ".Space", "GlobalSpace"); setdef(gk + ".bInitial", "False")
        gt = add_unit("/Script/ControlRig.RigUnit_GetTransform", "FootHip" + sfx, (100, y + 180))
        setdef(gt + ".Item", '(Type=Bone,Name="thigh_%s")' % side)
        setdef(gt + ".Space", "GlobalSpace"); setdef(gt + ".bInitial", "False")
        # 폴 = 무릎 + 바이어스
        pb = add_unit("/Script/RigVM.RigVMFunction_MathVectorAdd", "FootPoleBias" + sfx, (300, y + 90))
        setdef(pb + ".B", POLE_BIAS[sfx])
        link(gk + ".Transform.Translation", pb + ".A")
        # 이펙터: Lerp(애님발, FootTarget[미연결=0 → 알파0 패스스루], 알파)
        lp = add_unit("/Script/RigVM.RigVMFunction_MathVectorLerp", "FootLerp" + sfx, (300, y))
        link(gf + ".Transform.Translation", lp + ".A")
        setdef(lp + ".T", "0.000000")  # FootAlpha 변수 연결 전 = IK 투명
        # 신전 클램프 (다리 79.1의 96% = 76)
        sb = add_unit("/Script/RigVM.RigVMFunction_MathVectorSub", "FootReachSub" + sfx, (450, y))
        cl = add_unit("/Script/RigVM.RigVMFunction_MathVectorClampLength", "FootReachClamp" + sfx, (600, y))
        ad = add_unit("/Script/RigVM.RigVMFunction_MathVectorAdd", "FootReachAdd" + sfx, (750, y))
        setdef(cl + ".MinimumLength", "0.000000")
        setdef(cl + ".MaximumLength", "76.000000")
        link(lp + ".Result", sb + ".A")
        link(gt + ".Transform.Translation", sb + ".B")
        link(sb + ".Result", cl + ".Value")
        link(gt + ".Transform.Translation", ad + ".A")
        link(cl + ".Result", ad + ".B")
        # 이펙터 트랜스폼 (회전=애님 발 회전)
        mk = add_unit("/Script/RigVM.RigVMFunction_MathTransformMake", "FootMake" + sfx, (900, y))
        link(ad + ".Result", mk + ".Translation")
        link(gf + ".Transform.Rotation", mk + ".Rotation")
        # TwoBoneIK
        ik = add_unit("/Script/ControlRig.RigUnit_TwoBoneIKSimplePerItem", "FootIK" + sfx, (1100, y))
        setdef(ik + ".ItemA", '(Type=Bone,Name="thigh_%s")' % side)
        setdef(ik + ".ItemB", '(Type=Bone,Name="calf_%s")' % side)
        setdef(ik + ".EffectorItem", '(Type=Bone,Name="foot_%s")' % side)
        setdef(ik + ".PrimaryAxis", "(X=1.0,Y=0.0,Z=0.0)")
        setdef(ik + ".SecondaryAxis", "(X=0.0,Y=-1.0,Z=0.0)")
        setdef(ik + ".PoleVectorKind", "Location")
        setdef(ik + ".bPropagateToChildren", "True")
        link(mk + ".Result", ik + ".Effector")
        link(pb + ".Result", ik + ".PoleVector")
        link(prev_exec, ik + ".ExecutePin")
        prev_exec = ik + ".ExecutePin"

    bp.recompile_vm()
    step("recompiled")
    saved = unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False)
    log["saved"] = bool(saved)
except Exception:
    import traceback
    log["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1)
print("CR_FOOT_IK_DONE")
