# LineSnap 2차 주입 (2026-07-25) — 최종 출력 LedgeHandWorldL/R 매 프레임 라인 Z 스냅
# 근거(linesnap.log): 앵커는 라인 위(resAnc ±0.07)인데 슬라이드 중 타깃 ±10~16cm 이탈 +
#   플랜트 후 재래치서 11.7cm 팝. 슬라이드 경로가 앵커와 별개 소스라 최종 출력단에서 스냅.
# 구조: Ledge_LineSnap(최종값L, 최종값R) 호출을 Set_20 직전 exec에 삽입(경로 2개 수렴) →
#   Set 값핀에 +(0,0,LedgeSnapDzL/R) Add. 정지 시 Dz≈0 멱등, 무효/스테일은 게이트로 0.
# 실행: py linesnap2_build.py         (사전 점검)
#       py linesnap2_build.py apply   (적용)
import json
import sys
import urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GT = "Ledge_HandTarget"
KML = "KismetMathLibrary"
APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"

SET_L = "K2Node_VariableSet_20"
SET_R = "K2Node_VariableSet_21"
SRC_L = ("K2Node_Knot_73", "OutputPin")            # L 값 소스
SRC_R = ("K2Node_CallFunction_177", "ReturnValue")  # R 값 소스 (VInterpTo)
EXEC_SRCS = [("K2Node_VariableSet_14", "then"), ("K2Node_Knot_70", "OutputPin")]  # Set_20.execute 유입 2개


def call(tool: str, action: str, params: dict, timeout: int = 300) -> dict:
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:400])
    return json.loads(txt)


def bq(action: str, params: dict) -> dict:
    p = {"asset_path": ABP}
    p.update(params)
    return call("blueprint_query", action, p)


def graph() -> dict:
    return {n["id"]: n for n in bq("get_graph_data", {"graph_name": GT})["nodes"]}


def pins(nodes: dict, nid: str) -> dict:
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


def pie_on() -> bool:
    r = call("editor_query", "run_python", {
        "command": "import unreal;print(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is not None)",
        "mode": "execute_file"})
    return "True" in json.dumps(r.get("output", []))


ht = graph()
checks = [
    (pins(ht, SET_L)["LedgeHandWorldL"]["connected_to"] == [SRC_L[0] + "." + SRC_L[1]], "Set_20 값 ← Knot_73 (삽입 전)"),
    (pins(ht, SET_R)["LedgeHandWorldR"]["connected_to"] == [SRC_R[0] + "." + SRC_R[1]], "Set_21 값 ← CF_177 (삽입 전)"),
    (sorted(pins(ht, SET_L)["execute"]["connected_to"]) == sorted([a + "." + b for a, b in EXEC_SRCS]), "Set_20.execute ← 2경로 (삽입 전)"),
]
ok = True
for good, label in checks:
    print("[PF]", "OK " if good else "FAIL", label)
    ok = ok and good
if not APPLY:
    print("[PF] 사전 점검", "통과 — apply로 실행" if ok else "실패")
    sys.exit(0 if ok else 1)
assert ok, "사전 점검 실패"
assert not pie_on(), "PIE 실행 중 — 종료 후 재실행"

# ── 1) 호출 노드 + exec 삽입 ──
r = bq("add_node", {"graph_name": GT, "node_type": "CallFunction",
                    "function_class": "PC_01_ABP_C", "function_name": "Ledge_LineSnap",
                    "position": [-8600, 4600]})
callnid = r.get("id") or r.get("node_id")
print("[CALL]", callnid)
bq("connect_pins", {"graph_name": GT, "source_node": SRC_L[0], "source_pin": SRC_L[1],
                    "target_node": callnid, "target_pin": "CandL"})
bq("connect_pins", {"graph_name": GT, "source_node": SRC_R[0], "source_pin": SRC_R[1],
                    "target_node": callnid, "target_pin": "CandR"})
for src_node, src_pin in EXEC_SRCS:
    bq("disconnect_pins", {"graph_name": GT, "source_node": src_node, "source_pin": src_pin,
                           "target_node": SET_L, "target_pin": "execute"})
    bq("connect_pins", {"graph_name": GT, "source_node": src_node, "source_pin": src_pin,
                        "target_node": callnid, "target_pin": "execute"})
bq("connect_pins", {"graph_name": GT, "source_node": callnid, "source_pin": "then",
                    "target_node": SET_L, "target_pin": "execute"})

# ── 2) 값핀 Add 삽입 ──
made = {}
for s, (set_node, val_pin, src) in {
        "L": (SET_L, "LedgeHandWorldL", SRC_L),
        "R": (SET_R, "LedgeHandWorldR", SRC_R)}.items():
    yo = 4600 if s == "L" else 4800
    r = bq("add_node", {"graph_name": GT, "node_type": "VariableGet",
                        "variable_name": "LedgeSnapDz" + s, "position": [-8400, yo]})
    gv = r.get("id") or r.get("node_id")
    r = bq("add_node", {"graph_name": GT, "node_type": "CallFunction", "function_class": KML,
                        "function_name": "MakeVector", "position": [-8250, yo]})
    mk = r.get("id") or r.get("node_id")
    r = bq("add_node", {"graph_name": GT, "node_type": "CallFunction", "function_class": KML,
                        "function_name": "Add_VectorVector", "position": [-8100, yo]})
    ad = r.get("id") or r.get("node_id")
    made[s] = (gv, mk, ad)
    bq("connect_pins", {"graph_name": GT, "source_node": gv, "source_pin": "LedgeSnapDz" + s,
                        "target_node": mk, "target_pin": "Z"})
    bq("disconnect_pins", {"graph_name": GT, "source_node": src[0], "source_pin": src[1],
                           "target_node": set_node, "target_pin": val_pin})
    bq("connect_pins", {"graph_name": GT, "source_node": src[0], "source_pin": src[1],
                        "target_node": ad, "target_pin": "A"})
    bq("connect_pins", {"graph_name": GT, "source_node": mk, "source_pin": "ReturnValue",
                        "target_node": ad, "target_pin": "B"})
    bq("connect_pins", {"graph_name": GT, "source_node": ad, "source_pin": "ReturnValue",
                        "target_node": set_node, "target_pin": val_pin})
    print("[ADD]", s, ad)

# ── 3) 컴파일 + 검증 ──
r = bq("compile_blueprint", {})
print("[COMPILE]", json.dumps(r)[:200])

ht2 = graph()
v = []
for s, (set_node, val_pin, src) in {
        "L": (SET_L, "LedgeHandWorldL", SRC_L),
        "R": (SET_R, "LedgeHandWorldR", SRC_R)}.items():
    gv, mk, ad = made[s]
    v.append((pins(ht2, set_node)[val_pin]["connected_to"] == [ad + ".ReturnValue"], f"Set {s} 값 ← Add"))
    v.append((pins(ht2, ad)["A"]["connected_to"] == [src[0] + "." + src[1]], f"Add {s}.A ← 원소스"))
    v.append((pins(ht2, ad)["B"]["connected_to"] == [mk + ".ReturnValue"], f"Add {s}.B ← MakeVector"))
    v.append((pins(ht2, mk)["Z"]["connected_to"] == [gv + ".LedgeSnapDz" + s], f"MakeVector {s}.Z ← SnapDz{s}"))
v.append((sorted(pins(ht2, callnid)["execute"]["connected_to"]) == sorted([a + "." + b for a, b in EXEC_SRCS]), "call.execute ← 2경로"))
v.append((pins(ht2, SET_L)["execute"]["connected_to"] == [callnid + ".then"], "call.then → Set_20"))
v.append((pins(ht2, callnid)["CandL"]["connected_to"] == [SRC_L[0] + "." + SRC_L[1]], "call.CandL ← Knot_73"))
v.append((pins(ht2, callnid)["CandR"]["connected_to"] == [SRC_R[0] + "." + SRC_R[1]], "call.CandR ← CF_177"))
allok = True
for good, label in v:
    print("[CHK]", "OK " if good else "FAIL", label)
    allok = allok and good
assert allok, "링크 검증 실패"
print("[DONE] 컴파일+검증 통과 — PIE 실측 대기")
