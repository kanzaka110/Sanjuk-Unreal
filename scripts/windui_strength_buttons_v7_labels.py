# 윈드 강도 UI v7 — 폰트 절반(54) + 단계명 라벨 (2026-08-05 승호 지시)
#   숫자 -> Extreme/Strong/Moderate/Light/Mild (좌->우, 승호 지정 순서)
#   규격 매핑(Confluence 1692467785): Mild4 Light6 Moderate7.5 Strong9 Extreme12
#   위젯 이동/리네임 없이 자리 재매핑: 라벨 + 그래프 SelValue 핀디폴트 동시 교체
#   (rename_widget은 ComponentBoundEvent 바인딩 파손 위험 -> 내부명 Btn_W4=Extreme12 로 어긋남, 메모리 기록)
import json
import urllib.request
import atexit

URL = "http://localhost:9316/mcp"
WBP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/WBP_WindStrengthButtons"
EG = "EventGraph"
FONT = 54
# 버튼(좌->우 배치 순서) : (새 라벨, 새 적용값)
REMAP = {"Btn_W4": ("Extreme", "12.0"), "Btn_W6": ("Strong", "9.0"), "Btn_W7_5": ("Moderate", "7.5"),
         "Btn_W9": ("Light", "6.0"), "Btn_W12": ("Mild", "4.0")}
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


# ═══ ① 라벨 + 폰트 ═══
for btn, (label, _v) in REMAP.items():
    uiq("set_text", {"asset_path": WBP, "widget_name": "Txt_" + btn, "text": label,
                     "font_size": FONT, "compile": False})
for btn in ("Btn_Push", "Btn_Pull"):
    uiq("set_text", {"asset_path": WBP, "widget_name": "Txt_" + btn, "font_size": FONT, "compile": False})
LOG["steps"].append("라벨 5종 교체 + 폰트 %d OK" % FONT)

# ═══ ② 그래프 SelValue 핀디폴트 재매핑 ═══
g = bpq("get_graph_data", {"asset_path": WBP, "graph_name": EG})
nodes = {n["id"]: n for n in g["nodes"]}


def pins(nid):
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


done = {}
for nid, n in nodes.items():
    if "ComponentBoundEvent" not in nid:
        continue
    title = json.dumps(n.get("title") or n.get("name") or n)
    btn = next((b for b in REMAP if b in title), None)
    if not btn:
        continue
    tc = pins(nid).get("then", {}).get("connected_to") or []
    assert tc, "%s then 미연결" % btn
    s = tc[0]
    ssel = s.rsplit(".", 1)[0] if isinstance(s, str) else (s.get("node") or s.get("node_id"))
    sp = pins(ssel)
    assert "SelValue" in sp, "%s 체인 첫 노드가 SelValue 셋이 아님: %s" % (btn, ssel)
    bpq("set_pin_default", {"asset_path": WBP, "graph_name": EG, "node_id": ssel,
                            "pin_name": "SelValue", "value": REMAP[btn][1]})
    done[btn] = {"node": ssel, "val": REMAP[btn][1]}
assert len(done) == 5, "재매핑 5개 미달: %s" % done
LOG["steps"].append({"핀디폴트 재매핑": done})

cr = bpq("compile_blueprint", {"asset_path": WBP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:200])
assert not cr.get("errors"), "컴파일 에러: %s" % cr
call("editor_query", "save_asset", {"asset_path": WBP})

# ═══ ③ 검증: 핀디폴트 실측 재확인 ═══
g2 = bpq("get_graph_data", {"asset_path": WBP, "graph_name": EG})
n2 = {n["id"]: n for n in g2["nodes"]}
verify = {}
for btn, info in done.items():
    p = {pp["name"]: pp for pp in n2[info["node"]].get("pins", [])}
    verify[btn] = p["SelValue"].get("default_value")
LOG["steps"].append({"verify_defaults": verify})
exp = {b: v[1] for b, v in REMAP.items()}
assert all(str(verify[b]).rstrip("0").rstrip(".") == exp[b].rstrip("0").rstrip(".") for b in exp), \
    "핀디폴트 검증 실패: %s vs %s" % (verify, exp)
LOG["steps"].append("v7 완료 — WBP 저장됨")
