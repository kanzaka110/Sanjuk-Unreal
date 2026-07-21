# 발목 보존 배선 검증 (read-only) — knot 경유 오결선 탐지용 역추적
# README v11 교훈: connect_pins 가 "성공"을 반환하고 컴파일도 통과했는데 knot 때문에
# 엉뚱한 소스에 붙은 사례 있음 → 실제 소스 노드까지 deknot 으로 역추적해서 확인한다.
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/ankle_wiring_verify.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"

# 기대 배선: 입력핀 -> 실제 소스핀 (knot 통과 후)
EXPECT = {}
for sfx in ("L", "R"):
    rel_get = "VariableNode_7" if sfx == "L" else "VariableNode_8"
    rel_set = "VariableNode_9" if sfx == "L" else "VariableNode_10"
    EXPECT.update({
        "AnkInvCalf%s.Value" % sfx: "AnkAnimCalf%s.Transform.Rotation" % sfx,
        "AnkRelMul%s.A" % sfx: "AnkInvCalf%s.Result" % sfx,
        "AnkRelMul%s.B" % sfx: "AnkAnimFoot%s.Transform.Rotation" % sfx,
        "%s.Value.Rotation" % rel_set: "AnkRelMul%s.Result" % sfx,
        "AnkNewRot%s.A" % sfx: "AnkCalfNow%s.Transform.Rotation" % sfx,
        "AnkNewRot%s.B" % sfx: "%s.Value.Rotation" % rel_get,
        # ⚠ RigUnit_SetRotation 의 회전 입력 핀은 Rotation 이 아니라 Value (FQuat).
        #    add_link 에 "Rotation" 을 줘도 레거시 리다이렉트로 Value 에 붙고 "성공"을 반환한다.
        "AnkSetRot%s.Value" % sfx: "AnkNewRot%s.Result" % sfx,
    })

res = {"checks": [], "bones": {}, "exec": [], "mismatch": 0}
try:
    bp = unreal.load_asset(CR)
    c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()
    g = c.get_graph()

    def pin_by_path(path):
        node = g.find_node_by_name(path.split(".")[0])
        if node is None:
            return None
        for p in node.get_pins():
            if str(p.get_name()) == path.split(".")[1]:
                if len(path.split(".")) == 2:
                    return p
                for s in p.get_sub_pins():
                    if str(s.get_name()) == path.split(".")[2]:
                        return s
        return None

    def deknot(pin, depth=0):
        """입력핀의 실제 소스핀을 knot(Reroute)을 건너뛰며 역추적"""
        if depth > 12:
            return "DEPTH"
        links = pin.get_links()
        if not links:
            return None
        src = links[0].get_source_pin()
        spath = str(src.get_pin_path())
        node = src.get_node()
        # Reroute/knot 이면 그 입력으로 계속 거슬러 올라간다
        if isinstance(node, unreal.RigVMRerouteNode):
            for p in node.get_pins():
                if str(p.get_direction()).endswith("INPUT") or str(p.get_direction()).endswith("IO"):
                    up = deknot(p, depth + 1)
                    if up:
                        return up
        return spath.split(":")[-1]

    for dst, want in EXPECT.items():
        p = pin_by_path(dst)
        got = deknot(p) if p is not None else "PIN_NOT_FOUND"
        ok = (got == want)
        if not ok:
            res["mismatch"] += 1
        res["checks"].append({"pin": dst, "want": want, "got": got, "ok": ok})

    # 본 지정 확인 (좌우 바꿔 물린 사고 방지)
    for nm in ("AnkAnimCalfL", "AnkAnimFootL", "AnkCalfNowL", "AnkSetRotL",
               "AnkAnimCalfR", "AnkAnimFootR", "AnkCalfNowR", "AnkSetRotR"):
        n = g.find_node_by_name(nm)
        if n is None:
            res["bones"][nm] = "NODE_NOT_FOUND"
            continue
        d = {}
        for p in n.get_pins():
            pn = str(p.get_name())
            if pn in ("Item", "Space", "bPropagateToChildren", "Weight", "bInitial"):
                d[pn] = str(p.get_default_value())
        res["bones"][nm] = d

    # exec 체인 순서
    for nm in ("RigUnit_TwoBoneIKSimplePerItem_1", "VariableNode_9", "VariableNode_10",
               "FootIKL", "FootIKR", "AnkSetRotL", "AnkSetRotR"):
        n = g.find_node_by_name(nm)
        if n is None:
            res["exec"].append({nm: "NOT_FOUND"})
            continue
        outs = []
        for p in n.get_pins():
            if "ExecuteContext" not in str(p.get_cpp_type()):
                continue
            for l in p.get_links():
                tgt = str(l.get_target_pin().get_pin_path()).split(":")[-1]
                src = str(l.get_source_pin().get_pin_path()).split(":")[-1]
                if src.startswith(nm + "."):
                    outs.append(tgt)
        res["exec"].append({nm: outs})
except Exception:
    import traceback
    res["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(res, fp, indent=1)
print("ANKLE_WIRING_VERIFY_DONE mismatch=%s" % res.get("mismatch"))
