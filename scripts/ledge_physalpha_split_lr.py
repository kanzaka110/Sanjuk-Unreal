# -*- coding: utf-8 -*-
"""LedgePhysAnimAlpha 좌/우 다리 분리 (2026-08-11)

배경: 렛지 피직스 컨트롤은 이미 ParentSpace_LegLeft / ParentSpace_LegRight 로 좌우 분리돼
  있으나, Strength 산출이 하나뿐이라 두 다리가 같은 값을 받는다.
    GetCurveValueWithDefault("LedgePhysAnimAlpha", 1.0)
      -> Set LedgePhysAnimAlpha -> Lerp(0..4) -> LegLeft.Strength + (Knot_7) LegRight.Strength

설계(기존 커브 폴백 = 승호 선택):
  베이스 커브는 그대로 두고, L/R 커브를 각각 읽되 DefaultValue 에 베이스 값을 물린다.
  -> L/R 커브가 없는 애님은 베이스 값 그대로 = 기존 동작 100% 불변
  -> L/R 커브를 깐 애님만 좌우 따로 먹는다
    base = GetCurveValueWithDefault("LedgePhysAnimAlpha", 1.0)  (유지)
    L    = GetCurveValueWithDefault("LedgePhysAnimAlphaL", Default=base) -> Set LedgePhysAnimAlphaL
    R    = GetCurveValueWithDefault("LedgePhysAnimAlphaR", Default=base) -> Set LedgePhysAnimAlphaR
    Lerp(0,4,L) -> LegLeft.Strength   /   Lerp(0,4,R) -> LegRight.Strength (신규)

페이즈: pre | all | verify | compile | save
"""
import json
import sys
import urllib.request

MCP = "http://localhost:9316/mcp"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge"
G = "EventGraph"

BASE_CURVE = "K2Node_CallFunction_13"   # GetCurveValueWithDefault("LedgePhysAnimAlpha")
SET_BASE = "K2Node_VariableSet_41"      # Set LedgePhysAnimAlpha
LERP_L = "K2Node_CallFunction_22"       # Lerp(0,4) -> 현재 좌우 공유
KNOT_ALPHA = "K2Node_Knot_11"           # SET_BASE.Output_Get -> LERP_L.Alpha
KNOT_R = "K2Node_Knot_7"                # LERP_L.ReturnValue -> LegRight.Strength
CTRL_L = "K2Node_CallFunction_19"       # SetControlAngularData ParentSpace_LegLeft
CTRL_R = "K2Node_CallFunction_21"       # SetControlAngularData ParentSpace_LegRight
SEQ_NEXT = "K2Node_ExecutionSequence_1"  # SET_BASE.then 의 기존 목적지

VAR_L = "LedgePhysAnimAlphaL"
VAR_R = "LedgePhysAnimAlphaR"
CURVE_L = "LedgePhysAnimAlphaL"
CURVE_R = "LedgePhysAnimAlphaR"
CATEGORY = "Custom Move Ledge"

LOG = {"steps": [], "errors": []}


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(MCP, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:500])
    try:
        return json.loads(txt)
    except Exception:
        return {"raw": txt}


def node_id_of(r):
    nid = r.get("node_id") or r.get("id")
    if nid:
        return nid

    def hv(o):
        if isinstance(o, dict):
            if o.get("node_id") or o.get("id"):
                return o.get("node_id") or o.get("id")
            for v in o.values():
                x = hv(v)
                if x:
                    return x
        elif isinstance(o, list):
            for e in o:
                x = hv(e)
                if x:
                    return x
    return hv(r)


def add(ntype, x, y, **kw):
    p = {"asset_path": BP, "graph_name": G, "node_type": ntype, "position": [x, y]}
    p.update(kw)
    nid = node_id_of(call("blueprint_query", "add_node", p))
    print("  + %s(%s) -> %s" % (ntype, kw.get("function_name") or kw.get("variable_name") or "", nid))
    return nid


def pindef(nid, pin, val):
    call("blueprint_query", "set_pin_default",
         {"asset_path": BP, "graph_name": G, "node_id": nid, "pin_name": pin, "value": val})


def disconnect(sn, sp, tn, tp):
    call("blueprint_query", "disconnect_pins",
         {"asset_path": BP, "graph_name": G,
          "source_node": sn, "source_pin": sp, "target_node": tn, "target_pin": tp})
    print("  - %s.%s -/-> %s.%s" % (sn, sp, tn, tp))


def connect(pairs):
    rc = call("blueprint_query", "connect_pins_bulk",
              {"asset_path": BP, "graph_name": G, "connections": [
                  {"source_node": a, "source_pin": b, "target_node": c, "target_pin": d}
                  for a, b, c, d in pairs]})
    fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
    for fl in fails:
        print("  !! conn fail:", json.dumps(fl, ensure_ascii=False)[:250])
    if not fails:
        for a, b, c, d in pairs:
            print("  + %s.%s --> %s.%s" % (a, b, c, d))
    return len(fails)


def links(node_id):
    d = call("blueprint_query", "get_node_details",
             {"asset_path": BP, "graph_name": G, "node_id": node_id})
    return {p["name"]: (p.get("connected_to") or []) for p in d["pins"]}


def defaults(node_id):
    d = call("blueprint_query", "get_node_details",
             {"asset_path": BP, "graph_name": G, "node_id": node_id})
    return {p["name"]: p.get("default_value") for p in d["pins"]}


def preflight():
    """현재 배선이 '좌우 공유' 원형인지 확인. 다르면 중단."""
    base = links(BASE_CURVE)
    sb = links(SET_BASE)
    lp = links(LERP_L)
    cl = links(CTRL_L)
    cr = links(CTRL_R)
    assert base["OutValue"] == ["%s.LedgePhysAnimAlpha" % SET_BASE], "베이스 커브 배선 상이: %s" % base["OutValue"]
    assert defaults(BASE_CURVE)["CurveName"] == "LedgePhysAnimAlpha", "베이스 커브명 상이"
    assert sb["then"] == ["%s.execute" % SEQ_NEXT], "SET_BASE.then 상이: %s" % sb["then"]
    assert sb["Output_Get"] == ["%s.InputPin" % KNOT_ALPHA], "SET_BASE.Output_Get 상이: %s" % sb["Output_Get"]
    assert lp["Alpha"] == ["%s.OutputPin" % KNOT_ALPHA], "Lerp.Alpha 상이: %s" % lp["Alpha"]
    assert set(lp["ReturnValue"]) == {"%s.Strength" % CTRL_L, "%s.InputPin" % KNOT_R}, \
        "Lerp 출력 상이(좌우 공유 아님): %s" % lp["ReturnValue"]
    assert cl["Strength"] == ["%s.ReturnValue" % LERP_L], "LegLeft.Strength 상이"
    assert cr["Strength"] == ["%s.OutputPin" % KNOT_R], "LegRight.Strength 상이"
    dl, dr = defaults(CTRL_L), defaults(CTRL_R)
    assert dl["Name"] == "ParentSpace_LegLeft" and dr["Name"] == "ParentSpace_LegRight", "컨트롤 이름 상이"
    lerp_def = defaults(LERP_L)
    print("[PRE] Lerp A=%s B=%s / Damping L=%s R=%s / ExtraDamp L=%s R=%s" % (
        lerp_def["A"], lerp_def["B"], dl["DampingRatio"], dr["DampingRatio"],
        dl["ExtraDamping"], dr["ExtraDamping"]))
    print("[PRE] ok — 커브1개 -> Lerp1개 -> 좌우 공유")
    return lerp_def


def build():
    lerp_def = preflight()

    # 1) 변수 2개
    existing = {v["name"] for v in call("blueprint_query", "get_variables",
                                        {"asset_path": BP}).get("variables", [])}
    for nm in (VAR_L, VAR_R):
        if nm in existing:
            print("  = var %s 이미 존재 (스킵)" % nm)
            continue
        call("blueprint_query", "add_variable",
             {"asset_path": BP, "name": nm, "type": "double",
              "default_value": "1.0", "category": CATEGORY})
        print("  + var %s" % nm)

    # 2) L/R 커브 리드 (DefaultValue <- 베이스 값 = 폴백)
    curveL = add("CallFunction", -480, 1020, function_name="GetCurveValueWithDefault",
                 target_class="AnimInstance")
    pindef(curveL, "CurveName", CURVE_L)
    curveR = add("CallFunction", -480, 1200, function_name="GetCurveValueWithDefault",
                 target_class="AnimInstance")
    pindef(curveR, "CurveName", CURVE_R)

    # 3) Set 노드 2개 (exec 체인: SET_BASE -> setL -> setR -> SEQ_NEXT)
    setL = add("VariableSet", -140, 1020, variable_name=VAR_L)
    setR = add("VariableSet", 120, 1020, variable_name=VAR_R)

    # 4) 오른다리 전용 Lerp (좌측 Lerp 의 A/B 를 그대로 복제)
    lerpR = add("CallFunction", 928, 1360, function_name="Lerp",
                target_class="KismetMathLibrary")
    pindef(lerpR, "A", str(lerp_def["A"]))
    pindef(lerpR, "B", str(lerp_def["B"]))

    # 5) 기존 공유 배선 절단
    disconnect(SET_BASE, "then", SEQ_NEXT, "execute")
    disconnect(SET_BASE, "Output_Get", KNOT_ALPHA, "InputPin")
    disconnect(KNOT_ALPHA, "OutputPin", LERP_L, "Alpha")
    disconnect(LERP_L, "ReturnValue", KNOT_R, "InputPin")
    disconnect(KNOT_R, "OutputPin", CTRL_R, "Strength")
    for k in (KNOT_ALPHA, KNOT_R):
        call("blueprint_query", "remove_node", {"asset_path": BP, "graph_name": G, "node_id": k})
        print("  - 고아 크노트 제거 %s" % k)

    # 6) 신규 배선
    f = connect([
        # exec 체인 스플라이스
        (SET_BASE, "then", setL, "execute"),
        (setL, "then", setR, "execute"),
        (setR, "then", SEQ_NEXT, "execute"),
        # 폴백: 베이스 값 -> 각 커브 리드의 DefaultValue
        (BASE_CURVE, "OutValue", curveL, "DefaultValue"),
        (BASE_CURVE, "OutValue", curveR, "DefaultValue"),
        # 커브 -> 변수
        (curveL, "OutValue", setL, VAR_L),
        (curveR, "OutValue", setR, VAR_R),
        # 변수 -> 각 다리 Lerp -> Strength
        (setL, "Output_Get", LERP_L, "Alpha"),
        (setR, "Output_Get", lerpR, "Alpha"),
        (lerpR, "ReturnValue", CTRL_R, "Strength"),
    ])
    assert f == 0, "배선 실패 %d건" % f
    LOG["steps"].append({"curveL": curveL, "curveR": curveR, "setL": setL,
                         "setR": setR, "lerpR": lerpR})
    print("[BUILD] nodes:", json.dumps(LOG["steps"][-1], ensure_ascii=False))


def verify():
    lp = links(LERP_L)
    cl = links(CTRL_L)
    cr = links(CTRL_R)
    assert lp["ReturnValue"] == ["%s.Strength" % CTRL_L], \
        "좌 Lerp 가 아직 우측에도 물림: %s" % lp["ReturnValue"]
    assert cl["Strength"] == ["%s.ReturnValue" % LERP_L], "LegLeft.Strength = %s" % cl["Strength"]
    assert cr["Strength"] and cr["Strength"][0] != "%s.ReturnValue" % LERP_L, \
        "LegRight.Strength 가 좌측과 동일 소스: %s" % cr["Strength"]
    lerpR_node = cr["Strength"][0].rsplit(".", 1)[0]
    lr = links(lerpR_node)
    assert lr["Alpha"], "우 Lerp.Alpha 미연결"
    print("[POST] LegLeft.Strength  <- %s" % cl["Strength"])
    print("[POST] LegRight.Strength <- %s (Alpha <- %s)" % (cr["Strength"], lr["Alpha"]))
    dl, dr = defaults(CTRL_L), defaults(CTRL_R)
    print("[POST] Name L=%s R=%s / Damping %s,%s / ExtraDamp %s,%s / MaxTorque %s,%s" % (
        dl["Name"], dr["Name"], dl["DampingRatio"], dr["DampingRatio"],
        dl["ExtraDamping"], dr["ExtraDamping"], dl["MaxTorque"], dr["MaxTorque"]))
    print("[POST] ok — 좌우 독립")


def compile_bp():
    r = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
    print("[COMPILE] errors=%s %s" % (
        r.get("error_count"),
        json.dumps(r.get("errors"), ensure_ascii=False)[:500] if r.get("error_count") else ""))
    return r


def save():
    r = call("blueprint_query", "save_asset", {"asset_path": BP})
    print("[SAVE]", json.dumps(r, ensure_ascii=False)[:400])


def phase_all():
    build()
    verify()
    compile_bp()


if __name__ == "__main__":
    ph = sys.argv[1] if len(sys.argv) > 1 else "all"
    {"pre": preflight, "all": phase_all, "verify": verify,
     "compile": compile_bp, "save": save}[ph]()
    print(json.dumps(LOG, ensure_ascii=False))
