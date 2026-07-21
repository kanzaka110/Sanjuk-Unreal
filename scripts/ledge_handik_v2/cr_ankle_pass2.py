# 발목 보존 2패스 (2026-07-21) — 발목 꺾임과 ball 접지를 동시에 해결
#
# A/B 실측으로 확정된 트레이드오프 (같은 뿌리의 앞뒷면):
#   ToeConv = FootTarget - (ball_애님 - foot_애님)   ← ToeOff 가 '애님 회전' 기준으로 고정
#   보존 ON  : 발목 0.9도(정상)  / ball 오차 4.6~5.7cm  (발 글로벌 회전이 애님과 달라 ToeOff 불일치)
#   보존 OFF : 발목 2.4~65도(꺾임) / ball 오차 0.68cm
#
# 패스2: 패스1 종료 시점의 '실제' ball 위치를 재서 그 오차만큼 이펙터를 밀어 재IK.
#   err     = FootTarget - ball_실제(패스1 후)
#   eff2    = Clamp76(패스1 이펙터 + err)
#   재IK 후 발목 회전을 다시 보존(AnkleRel 재적용)
#   오차 5cm -> 0.2cm 수준이라 1회 반복으로 수렴.
#
# 선행: cr_ankle_preserve.py (패스1) 적용 완료 / 변수 AnkleRelL,R
# 백업: cr_snapshot_pre_ankle.BACKUP.json (개조 전 92노드)
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/cr_ankle_pass2.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
REACH_MAX = "76.000000"
# 패스1 실측 (cr_snapshot) — 좌우 축 부호가 다르므로 그대로 복사한다
AXIS = {"L": ("(X=-1.000000,Y=0.0,Z=0.0)", "(X=0.0,Y=1.000000,Z=0.0)"),
        "R": ("(X=1.000000,Y=0.0,Z=0.0)", "(X=0.0,Y=-1.000000,Z=0.0)")}
TGT_GET = {"L": "VariableNode_6", "R": "VariableNode_5"}    # Get FootTarget
REL_GET = {"L": "VariableNode_7", "R": "VariableNode_8"}    # Get AnkleRel (Transform)
log = {"steps": [], "created": [], "links": []}


def step(m):
    log["steps"].append(str(m))


try:
    bp = unreal.load_asset(CR)
    c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()
    g = c.get_graph()

    for nm in ("AnkSetRotL", "AnkSetRotR", "FootIKL", "FootIKR", "FootReachAddL", "FootReachAddR",
               "FootHipL", "FootHipR", "GetFootAlphaL", "GetFootAlphaR", "AnimFootL", "AnimFootR",
               "FootPoleBiasL", "FootPoleBiasR"):
        if g.find_node_by_name(nm) is None:
            raise RuntimeError("선행 노드 없음: " + nm)
    for nm in list(TGT_GET.values()) + list(REL_GET.values()):
        if g.find_node_by_name(nm) is None:
            raise RuntimeError("변수 Get 노드 없음: " + nm)
    step("anchors verified")

    def add_unit(path, name, pos):
        n = c.add_unit_node_from_struct_path(path, "Execute", unreal.Vector2D(pos[0], pos[1]), name)
        if n is None:
            raise RuntimeError("add fail " + name)
        log["created"].append(name)
        return str(n.get_node_path())

    def setdef(pin, val):
        try:
            c.set_pin_default_value(pin, val, False)
        except Exception as e:
            step("DEF ERR " + pin + " : " + repr(e)[:100])

    def link(a, b):
        try:
            ok = c.add_link(a, b)
            log["links"].append(("OK " if ok else "FAIL ") + a + " -> " + b)
        except Exception as e:
            log["links"].append("ERR " + a + " -> " + b + " : " + repr(e)[:100])

    def exec_pin(node_path):
        n = g.find_node_by_name(node_path.split(".")[-1])
        for p in n.get_pins():
            if "ExecuteContext" in str(p.get_cpp_type()):
                return node_path + "." + str(p.get_name())
        raise RuntimeError("exec pin not found: " + node_path)

    post = []
    for side, sfx in (("l", "L"), ("r", "R")):
        y = 4200 if sfx == "L" else 4700

        # 1) 패스1 종료 시점의 실제 ball (pure — P2IK 실행 시점에 평가되므로 AnkSetRot 반영본)
        pb = add_unit("/Script/ControlRig.RigUnit_GetTransform", "P2Ball" + sfx, (100, y))
        setdef(pb + ".Item", '(Type=Bone,Name="ball_%s")' % side)
        setdef(pb + ".Space", "GlobalSpace"); setdef(pb + ".bInitial", "False")

        # 2) err = FootTarget - ball_실제
        er = add_unit("/Script/RigVM.RigVMFunction_MathVectorSub", "P2Err" + sfx, (350, y))
        link(TGT_GET[sfx] + ".Value", er + ".A")
        link(pb + ".Transform.Translation", er + ".B")

        # 3) eff2 = 패스1 이펙터 + err
        ef = add_unit("/Script/RigVM.RigVMFunction_MathVectorAdd", "P2Eff" + sfx, (550, y))
        link("FootReachAdd%s.Result" % sfx, ef + ".A")
        link(er + ".Result", ef + ".B")

        # 4) 신전 클램프 재적용 (패스1과 동일 기준)
        sb = add_unit("/Script/RigVM.RigVMFunction_MathVectorSub", "P2ReachSub" + sfx, (750, y))
        link(ef + ".Result", sb + ".A")
        link("FootHip%s.Transform.Translation" % sfx, sb + ".B")
        cl = add_unit("/Script/RigVM.RigVMFunction_MathVectorClampLength", "P2ReachClamp" + sfx, (900, y))
        setdef(cl + ".MinimumLength", "0.000000"); setdef(cl + ".MaximumLength", REACH_MAX)
        link(sb + ".Result", cl + ".Value")
        ad = add_unit("/Script/RigVM.RigVMFunction_MathVectorAdd", "P2ReachAdd" + sfx, (1050, y))
        link("FootHip%s.Transform.Translation" % sfx, ad + ".A")
        link(cl + ".Result", ad + ".B")

        # 5) 이펙터 트랜스폼 (회전은 P2SetRot 이 덮으므로 현재 회전 그대로)
        mk = add_unit("/Script/RigVM.RigVMFunction_MathTransformMake", "P2Make" + sfx, (1250, y))
        link(ad + ".Result", mk + ".Translation")
        link("AnimFoot%s.Transform.Rotation" % sfx, mk + ".Rotation")

        # 6) 재IK (패스1과 동일 파라미터 — 좌우 축 부호 유지)
        ik = add_unit("/Script/ControlRig.RigUnit_TwoBoneIKSimplePerItem", "P2IK" + sfx, (1450, y))
        setdef(ik + ".ItemA", '(Type=Bone,Name="thigh_%s")' % side)
        setdef(ik + ".ItemB", '(Type=Bone,Name="calf_%s")' % side)
        setdef(ik + ".EffectorItem", '(Type=Bone,Name="foot_%s")' % side)
        setdef(ik + ".PrimaryAxis", AXIS[sfx][0]); setdef(ik + ".SecondaryAxis", AXIS[sfx][1])
        setdef(ik + ".PoleVectorKind", "Location")
        setdef(ik + ".bPropagateToChildren", "True")
        link(mk + ".Result", ik + ".Effector")
        link("FootPoleBias%s.Result" % sfx, ik + ".PoleVector")
        link("GetFootAlpha%s.Value" % sfx, ik + ".Weight")

        # 7) 발목 회전 재보존 (재IK 로 calf 가 또 돌았으므로)
        cn = add_unit("/Script/ControlRig.RigUnit_GetTransform", "P2CalfNow" + sfx, (1650, y))
        setdef(cn + ".Item", '(Type=Bone,Name="calf_%s")' % side)
        setdef(cn + ".Space", "GlobalSpace"); setdef(cn + ".bInitial", "False")
        nr = add_unit("/Script/RigVM.RigVMFunction_MathQuaternionMul", "P2NewRot" + sfx, (1850, y))
        link(cn + ".Transform.Rotation", nr + ".A")
        link(REL_GET[sfx] + ".Value.Rotation", nr + ".B")
        sr = add_unit("/Script/ControlRig.RigUnit_SetRotation", "P2SetRot" + sfx, (2050, y))
        setdef(sr + ".Item", '(Type=Bone,Name="foot_%s")' % side)
        setdef(sr + ".Space", "GlobalSpace"); setdef(sr + ".bInitial", "False")
        setdef(sr + ".Weight", "1.000000"); setdef(sr + ".bPropagateToChildren", "True")
        link(nr + ".Result", sr + ".Value")
        post.append((ik, sr))

    # ── exec: AnkSetRotR -> P2IKL -> P2IKR -> P2SetRotL -> P2SetRotR ──
    order = ["AnkSetRotR", post[0][0], post[1][0], post[0][1], post[1][1]]
    for i in range(len(order) - 1):
        a, b = exec_pin(order[i]), exec_pin(order[i + 1])
        try:
            c.break_all_links(b, True)
        except Exception:
            pass
        link(a, b)
    log["exec_order"] = order

    # ── 패스1 회전 보존 ON 복구 (A/B 측정 때 0 으로 꺼둔 상태) ──
    for nm in ("AnkSetRotL", "AnkSetRotR"):
        setdef(nm + ".Weight", "1.000000")
    step("pass1 weight restored to 1.0")

    bp.recompile_vm()
    step("recompiled")
    log["saved"] = bool(unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False))
except Exception:
    import traceback
    log["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1)
print("CR_ANKLE_PASS2_DONE err=%s" % ("error" in log))
