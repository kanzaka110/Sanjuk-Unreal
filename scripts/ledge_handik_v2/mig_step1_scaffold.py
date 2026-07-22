# 렛지→AnimLayer_IK 이관 1단계: 스캐폴드 (변수 54종 + 함수 8개 시그니처)
# 전제: ABP 현 상태 저장 완료 후 실행. 입력: scratchpad/migration_prep.json
# 실행 후: 유저가 에디터에서 함수별 그래프 노드 Ctrl+C/V 복붙 → 2단계(검증/재배선)로
import json
import os
import sys
import urllib.request

URL = "http://localhost:9316/mcp"
IK = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"
PREP = os.path.join(
    r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\H---------Claude-Sanjuk-Unreal",
    r"c50ce0ed-e0f3-4aaa-a60f-bbb911681a90\scratchpad", "migration_prep.json")
DRY = "--apply" not in sys.argv
LOG = {"steps": [], "fails": []}


def call(tool, action, params, timeout=180):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:250])
    return json.loads(txt)


prep = json.load(open(PREP, encoding="utf-8"))
vars_to_create = prep["vars_to_create"]
sigs = prep["func_signatures"]

print("[%s] 변수 %d종 / 함수 %d개" % ("DRY-RUN" if DRY else "APPLY", len(vars_to_create), len(sigs)))

# 이미 있는 것 재확인 (재실행 안전)
cur_vars = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": IK})["variables"]}
cur_graphs = call("blueprint_query", "list_graphs", {"asset_path": IK})
cur_graphs = {g.get("name") if isinstance(g, dict) else g
              for g in (cur_graphs.get("graphs") or cur_graphs.get("graph_names") or [])}

for v in vars_to_create:
    if v["name"] in cur_vars:
        LOG["steps"].append("skip var(exists): " + v["name"])
        continue
    if DRY:
        print("  +var", v["name"], v["type"])
        continue
    try:
        call("blueprint_query", "add_variable",
             {"asset_path": IK, "name": v["name"], "type": v["type"], "category": "Ledge"})
        LOG["steps"].append("var " + v["name"])
    except RuntimeError as e:
        LOG["fails"].append({"var": v["name"], "err": str(e)[:150]})

for fn, sig in sigs.items():
    if fn in cur_graphs:
        LOG["steps"].append("skip func(exists): " + fn)
        continue
    ins = [{"name": i["name"], "type": i["type"]} for i in sig["inputs"]]
    if DRY:
        print("  +func", fn, "inputs:", ins)
        continue
    try:
        call("blueprint_query", "add_function", {"asset_path": IK, "name": fn, "category": "Ledge"})
        if ins:
            call("blueprint_query", "set_function_params",
                 {"asset_path": IK, "function_name": fn, "inputs": ins})
        LOG["steps"].append("func %s (in=%d)" % (fn, len(ins)))
    except RuntimeError as e:
        LOG["fails"].append({"func": fn, "err": str(e)[:150]})

if not DRY:
    cp = call("blueprint_query", "compile_blueprint", {"asset_path": IK})
    LOG["steps"].append("compile: " + json.dumps(cp)[:150])
    print("DONE fails=%d" % len(LOG["fails"]))
    for s in LOG["steps"]:
        print("  " + s)
    if LOG["fails"]:
        print("FAILS:", json.dumps(LOG["fails"], ensure_ascii=False)[:600])
else:
    print("dry-run 완료 — 적용은 --apply")
