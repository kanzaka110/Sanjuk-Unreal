# AM_SBLedgeIK — 자동검출 기능 전면 제거 (2026-07-20 유저 결정)
# 사유: OnApply 는 인스턴스의 임시 복사본에서 실행되므로 자동 계산값을 시퀀스 모디파이어 파라미터에
#       되돌려 쓸 수 없다 → 패널에 반영 안 됨 → 자동 기능의 실효성 없음.
#       워크플로는 "스크립트로 인스턴스 값 1회 기록 → 이후 패널에서 수작업 수정 → 재적용" 으로 확정.
# 제거: OnApply 분기/호출, AutoDetectCurves·DetectWindow 그래프, bAutoDetect(+Request), Dw* 스크래치
# ⚠ 로컬 python 전용
import json, urllib.request

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/TA/AnimModifiers/AM_SBLedgeIK"
VARS = ["bAutoDetect", "bAutoDetectRequest", "DwMax", "DwSum", "DwCount",
        "DwPeakT", "DwPrevPos", "DwStart", "DwEnd", "DwEndSet"]
GRAPHS = ["AutoDetectCurves", "DetectWindow"]


def call(tool, action, params, timeout=240):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:200])
    return json.loads(txt)


G = "EventGraph"
ns = {n["id"]: n for n in call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": G})["nodes"]}


def pins(n):
    return {p["name"]: p for p in n.get("pins", [])}


# 1) OnApply 체인 복원: Event.then → (분기/자동검출 건너뛰고) 원래 첫 노드
ev = [i for i, n in ns.items() if "On Apply" in n.get("title", "").replace("\n", " ")][0]
cur = (pins(ns[ev]).get("then", {}).get("connected_to") or [])
chain = []
node = cur[0].split(".")[0] if cur else None
while node and node in ns and len(chain) < 8:
    chain.append(node)
    t = ns[node].get("title", "").replace("\n", " ")
    if "Remove Ledge Curves" in t:
        break
    nxt = None
    for pin in ("then", "Then"):
        c = pins(ns[node]).get(pin, {}).get("connected_to") or []
        if c:
            nxt = c[0].split(".")[0]
            break
    if ns[node]["class"] == "K2Node_IfThenElse":
        c = pins(ns[node]).get("then", {}).get("connected_to") or []
        nxt = c[0].split(".")[0] if c else None
    node = nxt
target = [n for n in chain if "Remove Ledge Curves" in ns[n].get("title", "").replace("\n", " ")]
target = target[0] if target else None
print("OnApply 체인:", [ns[c].get("title", "").replace("\n", "/")[:22] for c in chain], "→ 복원 타깃:", target)
if target:
    call("blueprint_query", "disconnect_pins", {"asset_path": BP, "graph_name": G, "node_id": ev, "pin_name": "then"})
    call("blueprint_query", "connect_pins", {"asset_path": BP, "graph_name": G,
                                             "source_node": ev, "source_pin": "then",
                                             "target_node": target, "target_pin": "execute"})
    print("OnApply → RemoveLedgeCurves 직결")

# 2) 중간 노드 제거 (분기 / AutoDetectCurves 호출 / bAutoDetect Get)
for i in list(chain):
    if i == target:
        continue
    t = ns[i].get("title", "").replace("\n", " ")
    try:
        call("blueprint_query", "remove_node", {"asset_path": BP, "graph_name": G, "node_id": i})
        print("노드 제거:", i, t[:34])
    except RuntimeError as e:
        print("노드 제거 실패:", i, str(e)[:70])
for i, n in list(ns.items()):
    if n["class"] == "K2Node_VariableGet" and "bAutoDetect" in n.get("title", ""):
        try:
            call("blueprint_query", "remove_node", {"asset_path": BP, "graph_name": G, "node_id": i})
            print("Get 제거:", i)
        except RuntimeError:
            pass

# 3) 그래프 / 변수 제거
for g in GRAPHS:
    try:
        call("blueprint_query", "remove_function", {"asset_path": BP, "name": g})
        print("그래프 제거:", g)
    except RuntimeError as e:
        print("그래프 제거 실패:", g, str(e)[:70])
have = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": BP}).get("variables", [])}
for v in VARS:
    if v in have:
        try:
            call("blueprint_query", "remove_variable", {"asset_path": BP, "name": v})
            print("변수 제거:", v)
        except RuntimeError as e:
            print("변수 제거 실패:", v, str(e)[:70])

r = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
print("compile:", r.get("success"), "errors:", r.get("error_count"), (r.get("errors") or [])[:3])
