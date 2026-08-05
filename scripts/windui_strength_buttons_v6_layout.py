# 윈드 강도 UI v6 — 2줄 배치 + 3배 확대 (2026-08-05 승호 지시)
#   위줄 = Push/Pull, 아래줄 = 4/6/7.5/9/12, 폰트 36 -> 108 (3배)
#   구조: Canvas -> VerticalBox(WindBtnCol, 우상단) -> HorizontalBox(WindRowTop / WindRowNum)
#   기존 버튼은 move_widget 재부모화 (바운드 이벤트는 변수 기준이라 무영향), 구 WindBtnRow 제거
import json
import urllib.request
import atexit

URL = "http://localhost:9316/mcp"
WBP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/WBP_WindStrengthButtons"
FONT = 108
NUM_BTNS = ["Btn_W4", "Btn_W6", "Btn_W7_5", "Btn_W9", "Btn_W12"]
TOP_BTNS = ["Btn_Push", "Btn_Pull"]
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


def uiq(action: str, params: dict) -> dict:
    return call("ui_query", action, params)


# ═══ ① 새 컨테이너 ═══
uiq("add_widget", {"asset_path": WBP, "widget_class": "VerticalBox", "widget_name": "WindBtnCol",
                   "parent_name": "CanvasPanel", "anchor_preset": "top_right", "auto_size": True,
                   "position": {"x": -40, "y": 40}, "compile": False})
uiq("set_slot_property", {"asset_path": WBP, "widget_name": "WindBtnCol",
                          "alignment": {"x": 1.0, "y": 0.0}, "auto_size": True, "compile": False})
uiq("add_widget", {"asset_path": WBP, "widget_class": "HorizontalBox", "widget_name": "WindRowTop",
                   "parent_name": "WindBtnCol", "compile": False})
uiq("add_widget", {"asset_path": WBP, "widget_class": "HorizontalBox", "widget_name": "WindRowNum",
                   "parent_name": "WindBtnCol", "compile": False})
for row, pad_bottom in (("WindRowTop", 12), ("WindRowNum", 0)):
    uiq("set_slot_property", {"asset_path": WBP, "widget_name": row, "h_align": "Right",
                              "padding": {"left": 0, "top": 0, "right": 0, "bottom": pad_bottom},
                              "compile": False})
LOG["steps"].append("WindBtnCol + 2줄 컨테이너 OK")

# ═══ ② 버튼 재부모화 + 슬롯 재설정 ═══
for btn in TOP_BTNS:
    uiq("move_widget", {"asset_path": WBP, "widget_name": btn, "new_parent_name": "WindRowTop"})
for btn in NUM_BTNS:
    uiq("move_widget", {"asset_path": WBP, "widget_name": btn, "new_parent_name": "WindRowNum"})
for btn in TOP_BTNS + NUM_BTNS:
    uiq("set_slot_property", {"asset_path": WBP, "widget_name": btn,
                              "padding": {"left": 10, "top": 0, "right": 10, "bottom": 0}, "compile": False})
LOG["steps"].append("버튼 7개 재부모화 OK")

# ═══ ③ 구 컨테이너 제거 + 3배 확대 ═══
uiq("remove_widget", {"asset_path": WBP, "widget_name": "WindBtnRow"})
for btn in TOP_BTNS + NUM_BTNS:
    uiq("set_text", {"asset_path": WBP, "widget_name": "Txt_" + btn, "font_size": FONT, "compile": False})
LOG["steps"].append("WindBtnRow 제거 + 폰트 %d OK" % FONT)

cr = uiq("compile_widget", {"asset_path": WBP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:250])
call("editor_query", "save_asset", {"asset_path": WBP})

# ═══ ④ 트리 검증 ═══
tree = uiq("get_widget_tree", {"asset_path": WBP})
tj = json.dumps(tree)
checks = {
    "WindBtnCol": '"WindBtnCol"' in tj,
    "WindRowTop": '"WindRowTop"' in tj,
    "WindRowNum": '"WindRowNum"' in tj,
    "old_row_gone": '"WindBtnRow"' not in tj,
    "btn_count": tj.count('"class": "Button"'),
}
LOG["steps"].append({"verify": checks})
assert checks["WindBtnCol"] and checks["old_row_gone"] and checks["btn_count"] == 7, "트리 검증 실패: %s" % checks
LOG["steps"].append("v6 완료 — WBP 저장됨")
