"""⑤-A: PC_01_ABP에 pure-ish getter 2개 추가 (레이어가 CallFunction으로 읽음).
GetWallHandTargetWorld -> Vector, GetWallHandAlphaValue -> float.
body: VariableGet(self) -> FunctionResult. (foreign VariableGet 불가 우회)
"""
import json, subprocess
MCP = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\abp_getters.txt"
log = []
def w(s): log.append(str(s)); print(s)

def call(action, args):
    p = {"jsonrpc":"2.0","method":"tools/call","id":1,
         "params":{"name":"blueprint_query","arguments":{"action":action, **args}}}
    r = subprocess.run(["curl","-s","-X","POST",MCP,"-H","Content-Type: application/json","-d",json.dumps(p)],
                       capture_output=True, text=True, timeout=40)
    try:
        return json.loads(json.loads(r.stdout)["result"]["content"][0]["text"])
    except Exception:
        return {"_raw": r.stdout[:300]}

def build_getter(fn, var, out_type):
    w(f"\n=== {fn} (var={var}) ===")
    w(str(call("add_function", {"asset_path": ABP, "name": fn, "category": "WallHandIK"})))
    w(str(call("set_function_params", {"asset_path": ABP, "function_name": fn,
              "inputs": [], "outputs": [{"name": "ReturnValue", "type": out_type}]})))
    # Entry/Result 찾기
    gd = call("get_graph_data", {"asset_path": ABP, "graph_name": fn})
    entry = result = None
    for n in gd.get("nodes", []):
        c = n.get("class")
        if c == "K2Node_FunctionEntry": entry = n["id"]
        if c == "K2Node_FunctionResult": result = n["id"]
    w(f"entry={entry} result={result}")
    # VariableGet self var
    vg = call("add_node", {"asset_path": ABP, "graph_name": fn, "node_type": "VariableGet",
                           "variable_name": var, "position": {"x": 200, "y": 100}})
    vgid = vg.get("id")
    w(f"varget {var} -> {vgid} pins={[p['name'] for p in call('get_node_details',{'asset_path':ABP,'graph_name':fn,'node_id':vgid}).get('pins',[])] if vgid else 'NA'}")
    # 연결: VariableGet.<var> -> Result.ReturnValue ; Entry.then -> Result.execute
    def C(sn,sp,tn,tp):
        r = call("connect_pins", {"asset_path": ABP, "graph_name": fn,
                  "source_node": sn, "source_pin": sp, "target_node": tn, "target_pin": tp})
        w(f"  {'OK' if r.get('success') else 'FAIL'} {sn}.{sp}->{tn}.{tp}" + ("" if r.get('success') else f" {r}"))
    C(vgid, var, result, "ReturnValue")
    C(entry, "then", result, "execute")

build_getter("GetWallHandTargetWorld", "WallHandTargetWorld", "struct:Vector")
build_getter("GetWallHandAlphaValue", "WallHandAlpha", "float")

w("\n=== compile ===")
w(str(call("compile_blueprint", {"asset_path": ABP})))
with open(OUT,"w",encoding="utf-8") as f: f.write("\n".join(log))
