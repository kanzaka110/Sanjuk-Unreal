# 발목 로컬 회전 보존 개조 (2026-07-21) — 렛지 발 IK 발목 꺾임 근본수정
#
# 문제: FootMake.Rotation <- AnimFoot 글로벌 회전 고정 → TwoBoneIK 가 calf 를 돌리면
#       그 차이가 전부 발목 로컬 각도로 흡수됨. 실측: 알파 1 구간에서 원본 애님 대비 최대 65°
#       (probe_ankle.py + measure_ankle_range.py 최근접 대조, 알파 0 구간은 오차 1~2°)
#
# 처방: IK 전에 애님 발목 로컬(calf 기준) 회전을 변수에 담고, IK 후 calf 에 다시 얹는다.
#   [IK 전]  Rel = Inv(calf_glob) * foot_glob   -> Set AnkleRel{L,R}.Value.Rotation
#   [IK 후]  foot_rot = calf_glob_now * Rel     -> SetRotation(foot, Global, propagate)
#   알파 0 이면 calf_now == calf_anim 이므로 항등 = 애님 그대로 (안전)
#
# 선행(유저 수동): CR 변수 AnkleRelL/R (Transform) + Get 노드 2개 + Set 노드 2개
# 백업: dump_cr_snapshot.py -> cr_snapshot_pre_ankle.json (92노드)
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/cr_ankle_preserve.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
HAND_IK_LAST = "RigUnit_TwoBoneIKSimplePerItem_1"  # 손 IK 마지막 노드 (현 exec: -> FootIKL -> FootIKR)
SETROT_CANDIDATES = ["/Script/ControlRig.RigUnit_SetRotation"]
log = {"steps": [], "created": [], "links": []}


def step(m):
    log["steps"].append(str(m))


try:
    bp = unreal.load_asset(CR)
    c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()
    g = c.get_graph()

    # --- 유저 수동 생성 변수 노드 탐색 (Get / Set) ---
    getter, setter = {}, {}
    for n in g.get_nodes():
        if not isinstance(n, unreal.RigVMVariableNode):
            continue
        vn = str(n.get_variable_name())
        if vn not in ("AnkleRelL", "AnkleRelR"):
            continue
        side = vn[-1]
        (getter if n.is_getter() else setter)[side] = str(n.get_node_path())
    step("getter=%s setter=%s" % (getter, setter))
    miss = [s for s in ("L", "R") if s not in getter or s not in setter]
    if miss:
        raise RuntimeError("AnkleRel Get/Set 노드 부족: %s (에디터에서 생성 필요)" % miss)

    # exec 핀 이름은 노드 종류마다 다르다 (RigUnit=ExecutePin, 변수 Set=ExecuteContext) → 실측으로 찾는다
    def exec_pin(node_path):
        n = g.find_node_by_name(node_path.split(".")[-1])
        if n is None:
            raise RuntimeError("node not found: " + node_path)
        for p in n.get_pins():
            if "ExecuteContext" in str(p.get_cpp_type()):
                return node_path + "." + str(p.get_name())
        raise RuntimeError("exec pin not found on " + node_path)

    def add_unit(path, name, pos):
        n = c.add_unit_node_from_struct_path(path, "Execute", unreal.Vector2D(pos[0], pos[1]), name)
        if n is None:
            raise RuntimeError("add fail " + name + " (" + path + ")")
        log["created"].append(name)
        return str(n.get_node_path())

    def setdef(pin, val):
        try:
            c.set_pin_default_value(pin, val, False)
        except Exception as e:
            step("DEF ERR " + pin + " : " + repr(e)[:120])

    def link(a, b, brk=False):
        if brk:
            try:
                c.break_all_links(b, True)
            except Exception:
                pass
        try:
            ok = c.add_link(a, b)
            log["links"].append(("OK " if ok else "FAIL ") + a + " -> " + b)
        except Exception as e:
            log["links"].append("ERR " + a + " -> " + b + " : " + repr(e)[:120])

    # SetRotation 유닛 경로 확정 (첫 시도 노드는 프로브용으로 만들고 실패 시 예외)
    setrot_path = None
    for cand in SETROT_CANDIDATES:
        try:
            probe = c.add_unit_node_from_struct_path(cand, "Execute", unreal.Vector2D(-9999, -9999), "AnkProbe")
            if probe is not None:
                setrot_path = cand
                pname = str(probe.get_node_path()).split(".")[-1]
                try:
                    c.remove_node(probe)
                except Exception:
                    c.remove_node_by_name(pname)
                step("probe removed: " + pname)
                break
        except Exception as e:
            step("setrot cand fail " + cand + " : " + repr(e)[:80])
    if setrot_path is None:
        raise RuntimeError("SetRotation 유닛 경로 확인 실패 — 대안 배선 필요")
    step("setrot_path=" + setrot_path)

    pre_chain, post_chain = [], []
    for side, sfx in (("l", "L"), ("r", "R")):
        y = 3200 if sfx == "L" else 3600

        # [IK 전] 애님 글로벌 calf / foot
        ac = add_unit("/Script/ControlRig.RigUnit_GetTransform", "AnkAnimCalf" + sfx, (100, y))
        setdef(ac + ".Item", '(Type=Bone,Name="calf_%s")' % side)
        setdef(ac + ".Space", "GlobalSpace"); setdef(ac + ".bInitial", "False")
        af = add_unit("/Script/ControlRig.RigUnit_GetTransform", "AnkAnimFoot" + sfx, (100, y + 90))
        setdef(af + ".Item", '(Type=Bone,Name="foot_%s")' % side)
        setdef(af + ".Space", "GlobalSpace"); setdef(af + ".bInitial", "False")

        # Rel = Inv(calf) * foot
        iv = add_unit("/Script/RigVM.RigVMFunction_MathQuaternionInverse", "AnkInvCalf" + sfx, (350, y))
        link(ac + ".Transform.Rotation", iv + ".Value")
        rm = add_unit("/Script/RigVM.RigVMFunction_MathQuaternionMul", "AnkRelMul" + sfx, (550, y))
        link(iv + ".Result", rm + ".A")
        link(af + ".Transform.Rotation", rm + ".B")
        link(rm + ".Result", setter[sfx] + ".Value.Rotation", brk=True)
        pre_chain.append(setter[sfx])

        # [IK 후] foot_rot = calf_now * Rel
        cn = add_unit("/Script/ControlRig.RigUnit_GetTransform", "AnkCalfNow" + sfx, (800, y))
        setdef(cn + ".Item", '(Type=Bone,Name="calf_%s")' % side)
        setdef(cn + ".Space", "GlobalSpace"); setdef(cn + ".bInitial", "False")
        nr = add_unit("/Script/RigVM.RigVMFunction_MathQuaternionMul", "AnkNewRot" + sfx, (1000, y))
        link(cn + ".Transform.Rotation", nr + ".A")
        link(getter[sfx] + ".Value.Rotation", nr + ".B")

        sr = add_unit(setrot_path, "AnkSetRot" + sfx, (1250, y))
        setdef(sr + ".Item", '(Type=Bone,Name="foot_%s")' % side)
        setdef(sr + ".Space", "GlobalSpace")
        setdef(sr + ".bInitial", "False")
        setdef(sr + ".Weight", "1.000000")
        setdef(sr + ".bPropagateToChildren", "True")
        link(nr + ".Result", sr + ".Rotation")
        post_chain.append(sr)

    # --- exec 재배선: 손IK -> SetRelL -> SetRelR -> FootIKL -> FootIKR -> SetRotL -> SetRotR ---
    order = [HAND_IK_LAST] + pre_chain + ["FootIKL", "FootIKR"] + post_chain
    for i in range(len(order) - 1):
        ap = exec_pin(order[i])
        bp_ = exec_pin(order[i + 1])
        try:
            c.break_all_links(bp_, True)
        except Exception:
            pass
        link(ap, bp_)
    log["exec_order"] = order

    bp.recompile_vm()
    step("recompiled")
    log["saved"] = bool(unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False))
except Exception:
    import traceback
    log["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1)
print("CR_ANKLE_PRESERVE_DONE err=%s" % ("error" in log))
