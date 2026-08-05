# 윈드 강도 UI v14b — v14 레벨BP 이어서 + 대분류 헤더 재구성 (2026-08-05)
#   v14 완료: 위젯 전부(변수/InitWind확장/함수2/UI/이벤트7) — 실패: SEQ_1.then_4 핀 소실(그래프 변동)
#   v14b:
#   ① InitWind 호출 노드 구조 재특정(핀 Comp+GlobalVolume 유일) -> 리터럴 주입 + refresh 복구
#   ② 대분류 헤더: Hdr_GlobalWind -> "SBGlobalWindVolume"(56, 시안), 신규 "WindActor"(56, 시안)
#      순서 [HdrG, GTest, GStage, HdrWA, HdrWS, Top, Num, HdrTb, TurbStage]
import json
import urllib.request
import atexit

URL = "http://localhost:9316/mcp"
MAP_BP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/SBWind_Weight_TEST01_Map"
WBP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/WBP_WindStrengthButtons"
EG = "EventGraph"
GVOL = ("/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/SBWind_Weight_TEST01_Map.SBWind_Weight_TEST01_Map"
        ":PersistentLevel.SBWindVolume_UAID_30560F6BCAE5D3F202_1767786249")
LOG = {"steps": [], "errors": []}
atexit.register(lambda: print(json.dumps(LOG, ensure_ascii=False, indent=1)))


def call(tool: str, action: str, params: dict, timeout: int = 300) -> dict:
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:500])
    return json.loads(txt)


def bpq(action: str, params: dict) -> dict:
    return call("blueprint_query", action, params)


def uiq(action: str, params: dict) -> dict:
    return call("ui_query", action, params)


def nid_of(r: dict) -> str:
    return r.get("node_id") or r.get("id")


def connect(bp: str, cs: list) -> int:
    rc = bpq("connect_pins_bulk", {"asset_path": bp, "graph_name": EG, "connections": cs})
    fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
    if fails:
        LOG["errors"].append({"conns": fails})
    return len(fails)


def graph_nodes(bp: str) -> dict:
    g = bpq("get_graph_data", {"asset_path": bp, "graph_name": EG})
    return {n["id"]: n for n in g["nodes"]}


def pmn(nodes: dict, nid: str) -> dict:
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


def node_pins(bp: str, nid: str) -> dict:
    det = bpq("get_node_details", {"asset_path": bp, "graph_name": EG, "node_id": nid})
    return {p.get("name"): p for p in (det.get("pins") or [])}


# ═══ ① 레벨BP: InitWind 호출 노드 재특정 + 리터럴 주입 ═══
nodes = graph_nodes(MAP_BP)
inits = [nid for nid in nodes
         if nid.startswith("K2Node_CallFunction")
         and "Comp" in pmn(nodes, nid) and "GlobalVolume" in pmn(nodes, nid)]
if not inits:
    # 컴파일 전이라 새 핀 미노출일 수 있음 -> Comp 핀만으로 특정 후 refresh
    inits = [nid for nid in nodes
             if nid.startswith("K2Node_CallFunction") and "Comp" in pmn(nodes, nid)
             and "self" in pmn(nodes, nid) and "WBP_WindStrengthButtons" in pmn(nodes, nid)["self"].get("type", "")]
assert len(inits) == 1, "InitWind 호출 노드 특정 실패: %s" % inits
init = inits[0]
before = {p: (pmn(nodes, init)[p].get("connected_to") or None) for p in pmn(nodes, init)}
bpq("refresh_node", {"asset_path": MAP_BP, "graph_name": EG, "node_id": init})
init_pins = node_pins(MAP_BP, init)
assert "GlobalVolume" in init_pins, "InitWind 새 핀 미노출: %s" % list(init_pins)
LOG["steps"].append("init=%s (GlobalVolume 핀 노출 OK)" % init)

lit = nid_of(bpq("add_node", {"asset_path": MAP_BP, "graph_name": EG, "node_type": "K2Node_Literal",
                              "position": [-1250, 2850]}))
bpq("set_node_property", {"asset_path": MAP_BP, "graph_name": EG, "node_id": lit,
                          "property_name": "ObjectRef", "value": GVOL})
bpq("refresh_node", {"asset_path": MAP_BP, "graph_name": EG, "node_id": lit})
lit_pins = node_pins(MAP_BP, lit)
out_pin = next(p for p in lit_pins if lit_pins[p].get("direction") != "input" and p not in ("execute", "then"))
LOG["steps"].append("Literal OK (핀=%s, 타입=%s)" % (out_pin, lit_pins[out_pin].get("type")))
f = connect(MAP_BP, [{"source_node": lit, "source_pin": out_pin, "target_node": init, "target_pin": "GlobalVolume"}])
assert f == 0, "리터럴 배선 실패"

# refresh로 끊긴 연결 복구
nodes = graph_nodes(MAP_BP)
ip = pmn(nodes, init)
relink = []
for pin, conn in before.items():
    if conn and pin in ip and not (ip[pin].get("connected_to") or []):
        s = conn[0]
        src_n, src_p = (tuple(s.rsplit(".", 1)) if isinstance(s, str)
                        else (s.get("node") or s.get("node_id"), s.get("pin") or s.get("pin_name")))
        if pin == "then":
            relink.append({"source_node": init, "source_pin": pin, "target_node": src_n, "target_pin": src_p})
        else:
            relink.append({"source_node": src_n, "source_pin": src_p, "target_node": init, "target_pin": pin})
if relink:
    f = connect(MAP_BP, relink)
    LOG["steps"].append({"refresh 복구 재배선": relink, "fail": f})
    assert f == 0, "복구 재배선 실패"

cr = bpq("compile_blueprint", {"asset_path": MAP_BP})
assert not cr.get("errors"), "레벨BP 컴파일 에러: %s" % cr
LOG["steps"].append("레벨BP OK (컴파일 클린)")

# ═══ ② 대분류 헤더 재구성 ═══
uiq("set_text", {"asset_path": WBP, "widget_name": "Hdr_GlobalWind", "text": "SBGlobalWindVolume",
                 "font_size": 56, "text_color": "#7FD9FF", "compile": False})
uiq("add_widget", {"asset_path": WBP, "widget_class": "TextBlock", "widget_name": "Hdr_WindActor",
                   "parent_name": "WindBtnCol", "compile": False})
uiq("set_text", {"asset_path": WBP, "widget_name": "Hdr_WindActor", "text": "WindActor",
                 "font_size": 56, "text_color": "#7FD9FF", "compile": False})
for w in ("Hdr_WindStrength", "WindRowTop", "WindRowNum", "Hdr_Turbulence", "WindRowTurbStage"):
    uiq("move_widget", {"asset_path": WBP, "widget_name": w, "new_parent_name": "WindBtnCol"})
for row in ("WindRowGTest", "WindRowGStage", "WindRowTop", "WindRowNum", "WindRowTurbStage"):
    uiq("set_slot_property", {"asset_path": WBP, "widget_name": row, "h_align": "Right",
                              "padding": {"left": 0, "top": 8, "right": 0, "bottom": 0}, "compile": False})
for hdr, top, sz in (("Hdr_GlobalWind", 0, 56), ("Hdr_WindActor", 30, 56),
                     ("Hdr_WindStrength", 10, 44), ("Hdr_Turbulence", 18, 44)):
    uiq("set_slot_property", {"asset_path": WBP, "widget_name": hdr, "h_align": "Right",
                              "padding": {"left": 0, "top": top, "right": 4, "bottom": 2}, "compile": False})
cr = uiq("compile_widget", {"asset_path": WBP})
assert not cr.get("errors"), "위젯 컴파일 에러: %s" % cr
call("editor_query", "save_asset", {"asset_path": WBP})

# ═══ ③ 검증 ═══
tree = uiq("get_widget_tree", {"asset_path": WBP})


def kids(node, target):
    if node.get("name") == target:
        return [c.get("name") for c in node.get("children", [])]
    for c in node.get("children", []):
        r = kids(c, target)
        if r is not None:
            return r
    return None


order = kids(tree.get("root", {}), "WindBtnCol")
nodes = graph_nodes(MAP_BP)
ip = pmn(nodes, init)
lvl = {p: bool(ip[p].get("connected_to")) for p in ("execute", "then", "self", "Comp", "GlobalVolume")}
LOG["steps"].append({"row_order": order, "init_pins": lvl})
assert order == ["Hdr_GlobalWind", "WindRowGTest", "WindRowGStage", "Hdr_WindActor",
                 "Hdr_WindStrength", "WindRowTop", "WindRowNum", "Hdr_Turbulence", "WindRowTurbStage"], order
assert all(lvl.values()), "init 핀 연결 검증 실패: %s" % lvl
LOG["steps"].append("v14b 완료 — WBP 저장됨, 맵 미저장")
