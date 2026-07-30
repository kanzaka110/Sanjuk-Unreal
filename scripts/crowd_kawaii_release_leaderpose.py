# CrowdWoman_Kawaii / CrowdMan_Kawaii 에 헤어 LeaderPose 해제 배선 (테스트 BP 한정)
#   BeginPlay -> Delay(1.0) -> Hair.SetLeaderPoseComponent(None)
#   공용 부모 CH_Mutable_Baked 는 건드리지 않음 (Tier 2 회피)
# 근거: SetLeaderPoseHair 의 실제 게이트는 IsAnimNext (UseHairLeaderPose 는 死변수)
import json, urllib.request, atexit

URL = "http://localhost:9316/mcp"
TARGETS = ["/Game/Developers/SHIFTUP/CSH/CrowdWoman_Kawaii",
           "/Game/Developers/SHIFTUP/CSH/CrowdMan_Kawaii"]
EG = "EventGraph"
LOG = {"steps": [], "errors": []}
atexit.register(lambda: print(json.dumps(LOG, ensure_ascii=False, indent=1)))


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


def nid_of(r):
    return r.get("node_id") or r.get("id")


for BP in TARGETS:
    name = BP.split("/")[-1]
    def add(ntype, x, y, **kw):
        p = {"asset_path": BP, "graph_name": EG, "node_type": ntype, "position": [x, y]}
        p.update(kw)
        return nid_of(call("blueprint_query", "add_node", p))

    def pins_of(nid):
        det = call("blueprint_query", "get_node_details", {"asset_path": BP, "graph_name": EG, "node_id": nid})
        return [p.get("name") for p in (det.get("pins") or det.get("node", {}).get("pins") or [])]

    # 중복 실행 가드: 이미 SetLeaderPoseComponent 있으면 skip
    g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": EG})
    if any("Set Leader Pose" in (n.get("title") or "") for n in g["nodes"]):
        LOG["steps"].append("%s: 이미 배선됨 — skip" % name)
        continue

    # BeginPlay 확보
    begin = None
    for n in g["nodes"]:
        if "K2Node_Event" in n.get("class", "") and ("Begin Play" in (n.get("title") or "") or "BeginPlay" in (n.get("title") or "")):
            begin = n["id"]
    if not begin:
        r = call("blueprint_query", "add_node",
                 {"asset_path": BP, "graph_name": EG, "node_type": "Event",
                  "event_name": "ReceiveBeginPlay", "position": [0, 900]})
        begin = nid_of(r)
        LOG["steps"].append("%s: BeginPlay 추가 %s" % (name, begin))
    else:
        LOG["steps"].append("%s: BeginPlay 기존 %s" % (name, begin))

    # 기존 BeginPlay 체인 꼬리 보존
    g2 = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": EG})
    bn = [n for n in g2["nodes"] if n["id"] == begin][0]
    first = None
    for p in bn.get("pins", []):
        if p.get("name") == "then":
            ct = p.get("connected_to") or []
            first = ct[0] if ct else None

    dl = add("CallFunction", 300, 900, function_name="Delay", target_class="KismetSystemLibrary")
    call("blueprint_query", "set_pin_default", {"asset_path": BP, "graph_name": EG, "node_id": dl,
                                               "pin_name": "Duration", "value": "1.0"})
    # 부모 변수 Hair 게터 (self context)
    r = call("blueprint_query", "add_node",
             {"asset_path": BP, "graph_name": EG, "node_type": "VariableGet",
              "variable_name": "Hair", "position": [520, 1030]})
    hg = nid_of(r)
    if "Hair" not in pins_of(hg):
        call("blueprint_query", "set_node_property",
             {"asset_path": BP, "graph_name": EG, "node_id": hg,
              "property_name": "VariableReference",
              "value": '(MemberName="Hair",bSelfContext=True)'})
        call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": EG, "node_id": hg})
    assert "Hair" in pins_of(hg), "%s: Hair 게터 실패 (%s)" % (name, pins_of(hg))

    slp = add("CallFunction", 760, 900, function_name="SetLeaderPoseComponent", target_class="SkinnedMeshComponent")
    sp = pins_of(slp)
    LOG["steps"].append("%s: SetLeaderPose 핀 %s" % (name, sp))

    conns = [
        {"source_node": hg, "source_pin": "Hair", "target_node": slp, "target_pin": "self"},
        {"source_node": begin, "source_pin": "then", "target_node": dl, "target_pin": "execute"},
        {"source_node": dl, "source_pin": "then", "target_node": slp, "target_pin": "execute"},
    ]
    if first:
        fn, fp = first.split(".")
        call("blueprint_query", "disconnect_pins",
             {"asset_path": BP, "graph_name": EG,
              "source_node": begin, "source_pin": "then", "target_node": fn, "target_pin": fp})
        # 기존 로직 먼저 실행 → 그 뒤 Delay 체인
        conns = [c for c in conns if not (c["target_node"] == dl and c["source_node"] == begin)]
        conns.append({"source_node": begin, "source_pin": "then", "target_node": fn, "target_pin": fp})
        LOG["steps"].append("%s: 기존 체인 %s 보존, Delay는 병행 Sequence 필요" % (name, first))
        # Sequence 삽입해 병행 실행
        seq = add("Sequence", 120, 900)
        call("blueprint_query", "disconnect_pins",
             {"asset_path": BP, "graph_name": EG,
              "source_node": begin, "source_pin": "then", "target_node": fn, "target_pin": fp})
        conns = [c for c in conns if c["source_node"] != begin]
        conns += [
            {"source_node": begin, "source_pin": "then", "target_node": seq, "target_pin": "execute"},
            {"source_node": seq, "source_pin": "then_0", "target_node": fn, "target_pin": fp},
            {"source_node": seq, "source_pin": "then_1", "target_node": dl, "target_pin": "execute"},
        ]
    rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": EG, "connections": conns})
    fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
    if fails:
        LOG["errors"].append({name: fails})
    cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
    LOG["steps"].append("%s: compile err=%s" % (name, cr.get("error_count")))
