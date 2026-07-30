# wind_debug_overlay_build v2 후속 패치: WindComponent(베이스) -> 파생 컴포넌트 프로퍼티 직결 불가 해결
# GetComponentByClass(파생클래스)로 extD/falD/strD, radR/falR/strR 의 self 를 공급.
# 임퓨어면 LoopBody exec 스플라이스. 컴파일 0 에러 확인까지.
import json, urllib.request

URL = "http://localhost:9316/mcp"
BP = "/Game/Developers/SHIFTUP/CSH/SBWind_Weight_TEST01_Map"
FN = "CalcWindAt"
LOG = {"steps": [], "errors": []}


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:400])
    return json.loads(txt)


g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})
nodes = {n["id"]: n for n in g["nodes"]}


def pins(n):
    return {p["name"]: p for p in n.get("pins", [])}


def find_vget(pin_name, self_type):
    """출력핀 이름 + self 핀 타입으로 외부 VariableGet 특정 (위치는 자동 재배치로 신뢰 불가)"""
    for nid, n in nodes.items():
        if "VariableGet" not in n.get("class", ""):
            continue
        P = pins(n)
        if pin_name in P and P.get("self", {}).get("type") == "object:" + self_type:
            return nid
    raise SystemExit("VariableGet %s (self=%s) 미발견" % (pin_name, self_type))


def find_loop(elem_type):
    for nid, n in nodes.items():
        if "MacroInstance" not in n.get("class", ""):
            continue
        P = pins(n)
        if P.get("Array Element", {}).get("type") == "object:" + elem_type:
            return nid
    raise SystemExit("ForEachLoop (elem=%s) 미발견" % elem_type)


def find_branch_after(loop_id):
    """execute 가 해당 루프 LoopBody 에서 오는 Branch"""
    for nid, n in nodes.items():
        if "IfThenElse" not in n.get("class", ""):
            continue
        srcs = pins(n).get("execute", {}).get("connected_to") or []
        if any(s.split(".")[0] == loop_id for s in srcs):
            return nid
    raise SystemExit("Branch (after %s) 미발견" % loop_id)


extD = find_vget("BoxExtent", "SBDirectionalWindComponent")
falD = find_vget("FalloffExponent", "SBDirectionalWindComponent")
strD = find_vget("WindStrength", "SBDirectionalWindComponent")
radR = find_vget("Radius", "SBRadialWindComponent")
falR = find_vget("FalloffExponent", "SBRadialWindComponent")
strR = find_vget("WindStrength", "SBRadialWindComponent")
loopD = find_loop("SBDirectionalWindActor")
loopR = find_loop("SBRadialWindActor")
brInD = find_branch_after(loopD)
brInR = find_branch_after(loopR)
LOG["steps"].append("targets: extD=%s falD=%s strD=%s radR=%s falR=%s strR=%s loopD=%s loopR=%s brInD=%s brInR=%s"
                    % (extD, falD, strD, radR, falR, strR, loopD, loopR, brInD, brInR))

# GetComponentByClass 스폰 x2
made = {}
for tid, ycls, y in (("gcD", "/Script/SB2.SBDirectionalWindComponent", 1250), ("gcR", "/Script/SB2.SBRadialWindComponent", 2650)):
    r = call("blueprint_query", "add_node",
             {"asset_path": BP, "graph_name": FN, "node_type": "CallFunction",
              "function_name": "GetComponentByClass", "target_class": "Actor", "position": [950, y]})
    nid = r.get("node_id") or r.get("id")
    if not nid:
        raise SystemExit("GetComponentByClass 스폰 실패: %s" % json.dumps(r)[:300])
    call("blueprint_query", "set_pin_default", {"asset_path": BP, "graph_name": FN, "node_id": nid,
                                                "pin_name": "ComponentClass", "value": ycls})
    made[tid] = nid
    LOG["steps"].append("%s = %s (%s)" % (tid, nid, ycls))

# 스폰 후 핀 확인 (임퓨어 여부 + ReturnValue 타입)
det = call("blueprint_query", "get_node_details", {"asset_path": BP, "graph_name": FN, "node_id": made["gcD"]})
dpins = [p.get("name") for p in (det.get("pins") or det.get("node", {}).get("pins") or [])]
impure = "execute" in dpins
LOG["steps"].append("gcD pins=%s impure=%s" % (dpins, impure))

conns = []


def C(sn, sp, tn, tp):
    conns.append({"source_node": sn, "source_pin": sp, "target_node": tn, "target_pin": tp})


# self 공급: 루프 element -> gc, gc -> 파생 게터들
C(loopD, "Array Element", made["gcD"], "self")
C(loopR, "Array Element", made["gcR"], "self")
for t in (extD, falD, strD):
    C(made["gcD"], "ReturnValue", t, "self")
for t in (radR, falR, strR):
    C(made["gcR"], "ReturnValue", t, "self")

if impure:
    for loop, gc, br in ((loopD, made["gcD"], brInD), (loopR, made["gcR"], brInR)):
        call("blueprint_query", "disconnect_pins",
             {"asset_path": BP, "graph_name": FN,
              "source_node": loop, "source_pin": "LoopBody", "target_node": br, "target_pin": "execute"})
        C(loop, "LoopBody", gc, "execute")
        C(gc, "then", br, "execute")

rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": FN, "connections": conns})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if fails:
    LOG["errors"].append({"conns": fails})
LOG["steps"].append("links: %d req %d fail" % (len(conns), len(fails)))

cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:600])

print(json.dumps(LOG, ensure_ascii=False, indent=1))
