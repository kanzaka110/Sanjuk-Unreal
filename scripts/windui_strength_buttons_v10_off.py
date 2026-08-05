# 윈드 강도 UI v10 — Turb 윗단 Off 버튼 (2026-08-05 승호 지시)
#   WindRowTurbOff 줄(버튼 1개 "Off") 을 강도줄과 Turb줄 사이에 배치
#   순서 제어 = 같은 부모 move_widget 재append (v9 실측 ✅)
#   동작 = ApplyTurb(0.0) — Turbulence 0 이면 Spd/Size 무의미
import json
import urllib.request
import atexit

URL = "http://localhost:9316/mcp"
WBP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/WBP_WindStrengthButtons"
EG = "EventGraph"
FONT = 54
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


# ═══ ① Off 줄 + 버튼 ═══
uiq("add_widget", {"asset_path": WBP, "widget_class": "HorizontalBox", "widget_name": "WindRowTurbOff",
                   "parent_name": "WindBtnCol", "compile": False})
uiq("set_slot_property", {"asset_path": WBP, "widget_name": "WindRowTurbOff", "h_align": "Right",
                          "padding": {"left": 0, "top": 12, "right": 0, "bottom": 0}, "compile": False})
uiq("add_widget", {"asset_path": WBP, "widget_class": "Button", "widget_name": "Btn_TOff",
                   "parent_name": "WindRowTurbOff", "compile": False})
uiq("add_widget", {"asset_path": WBP, "widget_class": "TextBlock", "widget_name": "Txt_Btn_TOff",
                   "parent_name": "Btn_TOff", "compile": False})
uiq("set_text", {"asset_path": WBP, "widget_name": "Txt_Btn_TOff", "text": "Off",
                 "font_size": FONT, "justification": "Center", "compile": False})
uiq("set_slot_property", {"asset_path": WBP, "widget_name": "Btn_TOff",
                          "padding": {"left": 10, "top": 0, "right": 10, "bottom": 0}, "compile": False})
uiq("set_widget_is_variable", {"wbp_path": WBP, "widget_name": "Btn_TOff", "is_variable": True})
LOG["steps"].append("WindRowTurbOff + Btn_TOff OK")

# ═══ ② 줄 순서 재배치: Top, Num, TurbOff, Turb, Spd, Size ═══
for row in ("WindRowTurb", "WindRowTurbSpd", "WindRowTurbSize"):
    uiq("move_widget", {"asset_path": WBP, "widget_name": row, "new_parent_name": "WindBtnCol"})
    uiq("set_slot_property", {"asset_path": WBP, "widget_name": row, "h_align": "Right",
                              "padding": {"left": 0, "top": 12, "right": 0, "bottom": 0}, "compile": False})
LOG["steps"].append("줄 순서 재배치 OK")

# ═══ ③ Btn_TOff -> ApplyTurb(0.0) ═══
ev = nid_of(bpq("add_node", {"asset_path": WBP, "graph_name": EG, "node_type": "ComponentBoundEvent",
                             "position": [0, 7600], "component_name": "Btn_TOff",
                             "delegate_property_name": "OnClicked"}))
ap = nid_of(bpq("add_node", {"asset_path": WBP, "graph_name": EG, "node_type": "CallFunction",
                             "position": [400, 7600], "function_name": "ApplyTurb"}))
bpq("set_node_property", {"asset_path": WBP, "graph_name": EG, "node_id": ap,
                          "property_name": "FunctionReference",
                          "value": '(MemberParent=None,MemberName="ApplyTurb",bSelfContext=True)'})
bpq("refresh_node", {"asset_path": WBP, "graph_name": EG, "node_id": ap})
bpq("set_pin_default", {"asset_path": WBP, "graph_name": EG, "node_id": ap, "pin_name": "Amount", "value": "0.0"})
rc = bpq("connect_pins_bulk", {"asset_path": WBP, "graph_name": EG, "connections": [
    {"source_node": ev, "source_pin": "then", "target_node": ap, "target_pin": "execute"}]})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
assert not fails, "Off 체인 배선 실패: %s" % fails
LOG["steps"].append("Off 체인 OK")

cr = bpq("compile_blueprint", {"asset_path": WBP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:200])
assert not cr.get("errors"), "컴파일 에러: %s" % cr
call("editor_query", "save_asset", {"asset_path": WBP})

# ═══ ④ 검증: 줄 순서 + 이벤트 수 ═══
tree = uiq("get_widget_tree", {"asset_path": WBP})


def child_names(node, target):
    if node.get("name") == target:
        return [c.get("name") for c in node.get("children", [])]
    for c in node.get("children", []):
        r = child_names(c, target)
        if r is not None:
            return r
    return None


order = child_names(tree.get("root", {}), "WindBtnCol")
g = bpq("get_graph_data", {"asset_path": WBP, "graph_name": EG})
evn = sum(1 for n in g["nodes"] if "ComponentBoundEvent" in n["id"])
LOG["steps"].append({"row_order": order, "ev_count": evn})
assert order == ["WindRowTop", "WindRowNum", "WindRowTurbOff", "WindRowTurb", "WindRowTurbSpd", "WindRowTurbSize"], \
    "줄 순서 불일치: %s" % order
assert evn == 23, "이벤트 수 불일치: %d" % evn
LOG["steps"].append("v10 완료 — WBP 저장됨")
