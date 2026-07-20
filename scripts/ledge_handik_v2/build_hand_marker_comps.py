# LedgeDebugs v6 — 손 IK 마커를 소켓 어태치 실컴포넌트로 (draw 1틱 지연 근본 해결)
#  스폰 1회: AddComponentByClass(StaticMeshComponent) -> Cast -> 구체메시/어태치(hand_l/r)/스케일/콜리전off/MID
#  매 틱  : MID Color = SelectColor(밝/어둠, α>=0.5) [기존 selL/R 재사용], SetVisibility(true)
#  else   : (LedgeDebug off 또는 렛지 비활성) IsValid 가드 후 SetVisibility(false)
#  구 DrawDebugSphere 2개(43/46)는 체인에서 제거
# ⚠ 로컬 python 전용
import json, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
G = "LedgeDebugs"
KSL = "KismetSystemLibrary"
SEL = {"L": "K2Node_CallFunction_42", "R": "K2Node_CallFunction_45"}  # SelectColor 기존
OLD_SPH = {"L": "K2Node_CallFunction_43", "R": "K2Node_CallFunction_46"}
BRMV = "K2Node_IfThenElse_1"
GATE = "K2Node_IfThenElse_6"
STR14 = "K2Node_CallFunction_14"
SETML = "K2Node_VariableSet_1"


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:300])
    return json.loads(txt)


# ── 1) 변수 ──
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": ABP}).get("variables", [])}
for nm, ty in (("LedgeDbgSphL", "object:StaticMeshComponent"), ("LedgeDbgSphR", "object:StaticMeshComponent"),
               ("LedgeDbgMidL", "object:MaterialInstanceDynamic"), ("LedgeDbgMidR", "object:MaterialInstanceDynamic")):
    if nm not in existing:
        call("blueprint_query", "add_variable", {"asset_path": ABP, "name": nm, "type": ty,
                                                 "category": "LedgeDebug", "instance_editable": False, "transient": True})
        print("var+", nm)

# ── 2) 노드 ──
nodes, defaults, conns = [], [], []


def N(tid, ntype, x, y, **kw):
    d = {"temp_id": tid, "node_type": ntype, "position": [x, y]}
    d.update(kw)
    nodes.append(d)


def C(sn, sp, tn, tp):
    conns.append({"source_node": sn, "source_pin": sp, "target_node": tn, "target_pin": tp})


def D(nid, pin, val):
    defaults.append({"node_id": nid, "pin_name": pin, "value": val})


N("pawn", "CallFunction", -3400, 3000, function_name="TryGetPawnOwner")
N("ownc", "CallFunction", -3400, 3100, function_name="GetOwningComponent")
for s, sock, y in (("L", "hand_l", 3000), ("R", "hand_r", 3600)):
    N("gv" + s, "VariableGet", -3200, y, variable_name="LedgeDbgSph" + s)
    N("iv" + s, "CallFunction", -3050, y, function_name="IsValid", target_class=KSL)
    C("gv" + s, "LedgeDbgSph" + s, "iv" + s, "Object")
    N("br" + s, "Branch", -2900, y)
    C("iv" + s, "ReturnValue", "br" + s, "Condition")
    N("add" + s, "CallFunction", -2700, y + 100, function_name="AddComponentByClass", target_class="Actor")
    C("pawn", "ReturnValue", "add" + s, "self")
    D("add" + s, "Class", "StaticMeshComponent")
    N("cast" + s, "DynamicCast", -2450, y + 100, cast_class="StaticMeshComponent")
    C("add" + s, "ReturnValue", "cast" + s, "Object")
    N("mesh" + s, "CallFunction", -2200, y + 100, function_name="SetStaticMesh", target_class="StaticMeshComponent")
    D("mesh" + s, "NewMesh", "/Engine/BasicShapes/Sphere.Sphere")
    N("att" + s, "CallFunction", -1950, y + 100, function_name="K2_AttachToComponent", target_class="SceneComponent")
    C("ownc", "ReturnValue", "att" + s, "Parent")
    D("att" + s, "SocketName", sock)
    D("att" + s, "LocationRule", "SnapToTarget")
    D("att" + s, "RotationRule", "SnapToTarget")
    D("att" + s, "ScaleRule", "KeepWorld")
    N("scl" + s, "CallFunction", -1700, y + 100, function_name="SetWorldScale3D", target_class="SceneComponent")
    D("scl" + s, "NewScale", "(X=0.09,Y=0.09,Z=0.09)")
    N("col" + s, "CallFunction", -1450, y + 100, function_name="SetCollisionEnabled", target_class="PrimitiveComponent")
    D("col" + s, "NewType", "NoCollision")
    N("mid" + s, "CallFunction", -1200, y + 100, function_name="CreateDynamicMaterialInstance", target_class="PrimitiveComponent")
    D("mid" + s, "ElementIndex", "0")
    D("mid" + s, "SourceMaterial", "/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")
    N("sv" + s, "VariableSet", -950, y + 100, variable_name="LedgeDbgSph" + s)
    N("sm" + s, "VariableSet", -700, y + 100, variable_name="LedgeDbgMid" + s)
    C("mid" + s, "ReturnValue", "sm" + s, "LedgeDbgMid" + s)
    # 매 틱 색/가시성
    N("gm" + s, "VariableGet", -450, y, variable_name="LedgeDbgMid" + s)
    N("svp" + s, "CallFunction", -280, y, function_name="SetVectorParameterValue", target_class="MaterialInstanceDynamic")
    C("gm" + s, "LedgeDbgMid" + s, "svp" + s, "self")
    D("svp" + s, "ParameterName", "Color")
    C(SEL[s], "ReturnValue", "svp" + s, "Value")
    N("gv2" + s, "VariableGet", -280, y + 90, variable_name="LedgeDbgSph" + s)
    N("vis" + s, "CallFunction", -100, y, function_name="SetVisibility", target_class="SceneComponent")
    C("gv2" + s, "LedgeDbgSph" + s, "vis" + s, "self")
    D("vis" + s, "bNewVisibility", "true")
    # else 숨김
    N("gv3" + s, "VariableGet", -3200, y + 300, variable_name="LedgeDbgSph" + s)
    N("iv2" + s, "CallFunction", -3050, y + 300, function_name="IsValid", target_class=KSL)
    C("gv3" + s, "LedgeDbgSph" + s, "iv2" + s, "Object")
    N("brh" + s, "Branch", -2900, y + 300)
    C("iv2" + s, "ReturnValue", "brh" + s, "Condition")
    N("hid" + s, "CallFunction", -2700, y + 300, function_name="SetVisibility", target_class="SceneComponent")
    C("gv3" + s, "LedgeDbgSph" + s, "hid" + s, "self")
    D("hid" + s, "bNewVisibility", "false")

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


harvest(call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": G, "nodes": nodes}))
if len(tm) != len(nodes):
    raise SystemExit("노드 %d/%d missing=%s" % (len(tm), len(nodes), [n["temp_id"] for n in nodes if n["temp_id"] not in tm]))
# 캐스트 출력핀(로컬라이즈) 동적 탐색
castpin = {}
for s in ("L", "R"):
    d = call("blueprint_query", "get_node_details", {"asset_path": ABP, "graph_name": G, "node_id": tm["cast" + s]})
    n = d.get("node") or d
    p = [p["name"] for p in n.get("pins", []) if p["name"].startswith("As")]
    if not p:
        raise SystemExit("cast 출력핀 미발견 " + s)
    castpin[s] = p[0]
    for tgt in ("mesh", "att", "scl", "col", "mid"):
        C(tm["cast" + s], p[0], tm[tgt + s], "self")
    C(tm["cast" + s], p[0], tm["sv" + s], "LedgeDbgSph" + s)
for d in defaults:
    d["node_id"] = tm[d["node_id"]]
rd = call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": ABP, "graph_name": G, "defaults": defaults})
dfails = [x for x in (rd.get("results") or []) if not x.get("success", True)]
print("defaults fails:", dfails if dfails else 0)
for c in conns:
    c["source_node"] = tm.get(c["source_node"], c["source_node"])
    c["target_node"] = tm.get(c["target_node"], c["target_node"])

# ── 3) exec 절단/재배선 ──
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": G, "node_id": GATE, "pin_name": "then"})
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": G, "node_id": STR14, "pin_name": "then"})
for s in ("L", "R"):
    call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": G, "node_id": OLD_SPH[s], "pin_name": "then"})
ex = []


def E(a, ap, b, bp="execute"):
    ex.append({"source_node": tm.get(a, a), "source_pin": ap, "target_node": tm.get(b, b), "target_pin": bp})


# then 경로: 게이트 → 스폰/갱신 → 기존 체인(SETML)
E(GATE, "then", "brL")
E("brL", "then", "brR")
E("brL", "else", "addL")
E("addL", "then", "castL")
E("castL", "then", "meshL")
E("meshL", "then", "attL")
E("attL", "then", "sclL")
E("sclL", "then", "colL")
E("colL", "then", "midL")
E("midL", "then", "svL")
E("svL", "then", "smL")
E("smL", "then", "brR")
E("brR", "then", "svpL")
E("brR", "else", "addR")
E("addR", "then", "castR")
E("castR", "then", "meshR")
E("meshR", "then", "attR")
E("attR", "then", "sclR")
E("sclR", "then", "colR")
E("colR", "then", "midR")
E("midR", "then", "svR")
E("svR", "then", "smR")
E("smR", "then", "svpL")
E("svpL", "then", "visL")
E("visL", "then", "svpR")
E("svpR", "then", "visR")
E("visR", "then", SETML)
# else 경로: 숨김
E(GATE, "else", "brhL")
E("brhL", "then", "hidL")
E("hidL", "then", "brhR")
E("brhL", "else", "brhR")
E("brhR", "then", "hidR")
# 구 구체 스킵: 14 → brmv
E(STR14, "then", BRMV)
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": G, "connections": conns + ex})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
print("links: %d req %d fail" % (len(conns) + len(ex), len(fails)))
for f in fails[:15]:
    print("  FAIL:", json.dumps(f, ensure_ascii=False)[:200])
# 구 구체 노드 제거
for s in ("L", "R"):
    try:
        call("blueprint_query", "remove_node", {"asset_path": ABP, "graph_name": G, "node_id": OLD_SPH[s]})
    except RuntimeError as e:
        print("remove old sphere", s, str(e)[:100])
r = call("blueprint_query", "compile_blueprint", {"asset_path": ABP})
print("compile:", r.get("success"), "errors:", r.get("error_count"), (r.get("errors") or [])[:3])
if not fails and r.get("success"):
    s = call("editor_query", "save_asset", {"asset_path": ABP})
    print("save:", s.get("saved"))
