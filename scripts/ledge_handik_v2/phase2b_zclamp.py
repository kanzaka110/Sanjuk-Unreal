# Phase 2b — 손 리치클램프 Z 보존 재구축 (2026-07-22)
# 문제: 기존 클램프 shoulder + norm3D(target-shoulder)*min(len,R) 가 타깃이 멀면 Z를 어깨쪽으로 평탄화
#       → 이동 중 손이 렛지 아래로 딥 (실측 worldL.z 최대 -23.7cm)
# 수정: XY만 클램프, Z=타깃 유지. 구면 존중: Rxy = sqrt(max(R^2 - dz^2, 100))
#   final = shoulderXY0 + norm(vXY)*min(lenXY,Rxy) + targetZ0
# 배선 변경: VInterpL/R.Target 1핀씩. 구 노드(CF_31~39 체인)는 연결만 남고 미사용(삭제 안 함).
import json
import urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
KML = "KismetMathLibrary"
HT = "Ledge_HandTarget"
LOG = {"steps": [], "fails": []}


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:250])
    return json.loads(txt)


def graph():
    g = call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": HT})
    return {n["id"]: n for n in g["nodes"]}


def pin_src(nodes, nid, pin):
    for p in nodes[nid]["pins"]:
        if p["name"] == pin and p.get("direction") == "input":
            c = p.get("connected_to") or []
            return c[0] if c else None
    return None


def title(nodes, nid):
    return str(nodes.get(nid, {}).get("title", "?")).split(chr(10))[0]


nodes = graph()

# ── 체인 자동 탐지 (L/R) ──
def find_chain(world_var):
    # Set <world_var> ← VInterp ← Target(add=CF vector+vector) ← A(shoulder GetSocket), B(scaled)
    # scaled ← Normalize(sub) × Min ;  sub.A = target(MakeVector), sub.B = shoulder ; Min.B = MaxReach선택
    for nid, n in nodes.items():
        if not nid.startswith("K2Node_VariableSet"):
            continue
        for p in n["pins"]:
            if p["name"] == world_var and p.get("direction") == "input":
                vi = (p.get("connected_to") or [None])[0]
                if not vi:
                    continue
                vi = vi.split(".")[0]
                if "VInterp" not in title(nodes, vi):
                    continue
                add = pin_src(nodes, vi, "Target").split(".")[0]
                shoulder = pin_src(nodes, add, "A").split(".")[0]
                scaled = pin_src(nodes, add, "B").split(".")[0]
                norm = pin_src(nodes, scaled, "A").split(".")[0]
                mn = pin_src(nodes, scaled, "B").split(".")[0]
                sub = pin_src(nodes, norm, "A").split(".")[0]
                target = pin_src(nodes, sub, "A").split(".")[0]
                reach = pin_src(nodes, mn, "B").split(".")[0]
                return {"vinterp": vi, "shoulder": shoulder, "target": target, "reach": reach}
    raise SystemExit("체인 탐지 실패: " + world_var)


L = find_chain("LedgeHandWorldL")
R = find_chain("LedgeHandWorldR")
for k, v in (("L", L), ("R", R)):
    LOG["steps"].append("%s chain: %s" % (k, v))
    for key in ("vinterp", "shoulder", "target", "reach"):
        assert v[key] in nodes, k + "." + key + " 미존재"
# 검증: target은 Make Vector, shoulder는 Get Socket Location, reach는 Select
assert "Make Vector" in title(nodes, L["target"]) and "Make Vector" in title(nodes, R["target"])
assert "Socket" in title(nodes, L["shoulder"]) and "Socket" in title(nodes, R["shoulder"])

# ── 노드 스펙 (한 손당 17개) ──
def specs_for(side, x0, y0):
    s = []

    def add(tid, fn, px, py):
        s.append({"temp_id": side + "_" + tid, "node_type": "CallFunction", "function_name": fn,
                  "target_class": KML, "position": [x0 + px, y0 + py]})

    add("maskxy", "MakeVector", 0, 0)        # (1,1,0)
    add("maskz", "MakeVector", 0, 100)       # (0,0,1)
    add("v", "Subtract_VectorVector", 200, 0)          # target - shoulder
    add("vxy", "Multiply_VectorVector", 400, 0)        # v * (1,1,0)
    add("vz", "Multiply_VectorVector", 400, 100)       # v * (0,0,1)
    add("len2", "VSize", 600, 0)                        # |vxy|
    add("dz", "VSize", 600, 100)                        # |vz|
    add("rsq", "Multiply_DoubleDouble", 600, 200)       # R*R
    add("dzsq", "Multiply_DoubleDouble", 800, 100)      # dz*dz
    add("rxy2", "Subtract_DoubleDouble", 1000, 150)     # R^2 - dz^2
    add("rxy2c", "FMax", 1200, 150)                     # max(,100)
    add("rxy", "Sqrt", 1400, 150)
    add("lenc", "FMin", 1600, 0)                        # min(len2, rxy)
    add("norm", "Normal", 800, 0)                       # norm(vxy)
    add("scaled", "Multiply_VectorFloat", 1800, 0)      # norm * lenc
    add("sxy", "Multiply_VectorVector", 1800, 200)      # shoulder * (1,1,0)
    add("tz", "Multiply_VectorVector", 1800, 300)       # target * (0,0,1)
    add("add1", "Add_VectorVector", 2000, 100)          # sxy + scaled
    add("add2", "Add_VectorVector", 2200, 100)          # + tz
    return s

specs = specs_for("l", 5000, 3000) + specs_for("r", 5000, 3600)
res = call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": HT, "nodes": specs})
tm = {}


def harvest(o):
    if isinstance(o, dict):
        if o.get("temp_id") and (o.get("node_id") or o.get("id")):
            tm[o["temp_id"]] = o.get("node_id") or o.get("id")
        else:
            for v in o.values():
                harvest(v)
    elif isinstance(o, list):
        for e in o:
            harvest(e)


harvest(res)
if len(tm) != 38:
    raise SystemExit("노드 생성 %d/38: " % len(tm) + json.dumps(res)[:400])
LOG["steps"].append("nodes 38 created")

# 마스크 디폴트 (float 핀 — 신뢰 가능)
defaults = []
for side in ("l", "r"):
    defaults += [
        {"node_id": tm[side + "_maskxy"], "pin_name": "X", "value": "1.0"},
        {"node_id": tm[side + "_maskxy"], "pin_name": "Y", "value": "1.0"},
        {"node_id": tm[side + "_maskxy"], "pin_name": "Z", "value": "0.0"},
        {"node_id": tm[side + "_maskz"], "pin_name": "X", "value": "0.0"},
        {"node_id": tm[side + "_maskz"], "pin_name": "Y", "value": "0.0"},
        {"node_id": tm[side + "_maskz"], "pin_name": "Z", "value": "1.0"},
        {"node_id": tm[side + "_rxy2c"], "pin_name": "B", "value": "100.0"},
    ]
call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": ABP, "graph_name": HT, "defaults": defaults})

# 배선
conns = []
for side, C in (("l", L), ("r", R)):
    t = lambda k: tm[side + "_" + k]
    reach_out = "ReturnValue"
    conns += [
        {"source_node": C["target"], "source_pin": "ReturnValue", "target_node": t("v"), "target_pin": "A"},
        {"source_node": C["shoulder"], "source_pin": "ReturnValue", "target_node": t("v"), "target_pin": "B"},
        {"source_node": t("v"), "source_pin": "ReturnValue", "target_node": t("vxy"), "target_pin": "A"},
        {"source_node": t("maskxy"), "source_pin": "ReturnValue", "target_node": t("vxy"), "target_pin": "B"},
        {"source_node": t("v"), "source_pin": "ReturnValue", "target_node": t("vz"), "target_pin": "A"},
        {"source_node": t("maskz"), "source_pin": "ReturnValue", "target_node": t("vz"), "target_pin": "B"},
        {"source_node": t("vxy"), "source_pin": "ReturnValue", "target_node": t("len2"), "target_pin": "A"},
        {"source_node": t("vz"), "source_pin": "ReturnValue", "target_node": t("dz"), "target_pin": "A"},
        {"source_node": C["reach"], "source_pin": reach_out, "target_node": t("rsq"), "target_pin": "A"},
        {"source_node": C["reach"], "source_pin": reach_out, "target_node": t("rsq"), "target_pin": "B"},
        {"source_node": t("dz"), "source_pin": "ReturnValue", "target_node": t("dzsq"), "target_pin": "A"},
        {"source_node": t("dz"), "source_pin": "ReturnValue", "target_node": t("dzsq"), "target_pin": "B"},
        {"source_node": t("rsq"), "source_pin": "ReturnValue", "target_node": t("rxy2"), "target_pin": "A"},
        {"source_node": t("dzsq"), "source_pin": "ReturnValue", "target_node": t("rxy2"), "target_pin": "B"},
        {"source_node": t("rxy2"), "source_pin": "ReturnValue", "target_node": t("rxy2c"), "target_pin": "A"},
        {"source_node": t("rxy2c"), "source_pin": "ReturnValue", "target_node": t("rxy"), "target_pin": "A"},
        {"source_node": t("len2"), "source_pin": "ReturnValue", "target_node": t("lenc"), "target_pin": "A"},
        {"source_node": t("rxy"), "source_pin": "ReturnValue", "target_node": t("lenc"), "target_pin": "B"},
        {"source_node": t("vxy"), "source_pin": "ReturnValue", "target_node": t("norm"), "target_pin": "A"},
        {"source_node": t("norm"), "source_pin": "ReturnValue", "target_node": t("scaled"), "target_pin": "A"},
        {"source_node": t("lenc"), "source_pin": "ReturnValue", "target_node": t("scaled"), "target_pin": "B"},
        {"source_node": C["shoulder"], "source_pin": "ReturnValue", "target_node": t("sxy"), "target_pin": "A"},
        {"source_node": t("maskxy"), "source_pin": "ReturnValue", "target_node": t("sxy"), "target_pin": "B"},
        {"source_node": C["target"], "source_pin": "ReturnValue", "target_node": t("tz"), "target_pin": "A"},
        {"source_node": t("maskz"), "source_pin": "ReturnValue", "target_node": t("tz"), "target_pin": "B"},
        {"source_node": t("sxy"), "source_pin": "ReturnValue", "target_node": t("add1"), "target_pin": "A"},
        {"source_node": t("scaled"), "source_pin": "ReturnValue", "target_node": t("add1"), "target_pin": "B"},
        {"source_node": t("add1"), "source_pin": "ReturnValue", "target_node": t("add2"), "target_pin": "A"},
        {"source_node": t("tz"), "source_pin": "ReturnValue", "target_node": t("add2"), "target_pin": "B"},
    ]
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": HT, "connections": conns})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
LOG["fails"] += fails
LOG["steps"].append("data links %d (%d fails)" % (len(conns), len(fails)))

# VInterp.Target 교체
for side, C in (("l", L), ("r", R)):
    call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": HT,
                                                "node_id": C["vinterp"], "pin_name": "Target"})
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": HT, "connections": [
    {"source_node": tm["l_add2"], "source_pin": "ReturnValue", "target_node": L["vinterp"], "target_pin": "Target"},
    {"source_node": tm["r_add2"], "source_pin": "ReturnValue", "target_node": R["vinterp"], "target_pin": "Target"},
]})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
LOG["fails"] += fails

cp = call("blueprint_query", "compile_blueprint", {"asset_path": ABP})
LOG["steps"].append("compile: success=%s err=%s warn=%s" % (cp.get("success"), cp.get("error_count"), cp.get("warning_count")))

# 사후검증
nodes = graph()
for side, C in (("l", L), ("r", R)):
    got = pin_src(nodes, C["vinterp"], "Target")
    LOG["steps"].append("%s VInterp.Target <- %s (기대 %s)" % (side, got, tm[side + "_add2"] + ".ReturnValue"))

json.dump(LOG, open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/phase2b_zclamp.json", "w"), indent=1, ensure_ascii=False)
print("PHASE2B_DONE fails=%d" % len(LOG["fails"]))
for s in LOG["steps"]:
    print("  " + s)
if LOG["fails"]:
    print("FAILS:", json.dumps(LOG["fails"], ensure_ascii=False)[:600])
