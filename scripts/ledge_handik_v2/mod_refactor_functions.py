# AM_SBLedgeHandIK 함수화 리팩토링 (v9.10)
# RemoveLedgeCurves(9커브, Apply전처리+Revert 공용) / WriteExitCurves / WriteIdleCurves / WriteMoveCurves
# EventGraph = 분류 퓨어 + 함수콜 씬레이어로 축소. 컴파일/저장은 별도 (PIE 게이트).
import json, urllib.request

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/TA/AnimModifiers/AM_SBLedgeHandIK"
KML = "KismetMathLibrary"
ABL = "AnimationBlueprintLibrary"
SEQT = "object:AnimSequenceBase"
H = {"l": "ledge_hand_ik_l", "r": "ledge_hand_ik_r"}
HM = {"l": "ledge_hand_move_l", "r": "ledge_hand_move_r"}
F = {"l": "ledge_foot_ik_l", "r": "ledge_foot_ik_r"}
FM = {"l": "ledge_foot_move_l", "r": "ledge_foot_move_r"}
ALL9 = list(H.values()) + list(HM.values()) + list(F.values()) + list(FM.values()) + ["ledge_pelvis_spring"]


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


def harvest(o, tm):
    if isinstance(o, dict):
        if o.get("temp_id") and (o.get("node_id") or o.get("id")):
            tm[o["temp_id"]] = o.get("node_id") or o.get("id")
        else:
            for v in o.values():
                harvest(v, tm)
    elif isinstance(o, list):
        for e in o:
            harvest(e, tm)


class GraphBuilder:
    def __init__(self, graph):
        self.g = graph
        self.nodes, self.defaults, self.conns, self.ex = [], [], [], []

    def N(self, tid, ntype, x, y, **kw):
        d = {"temp_id": tid, "node_type": ntype, "position": [x, y]}
        d.update(kw)
        self.nodes.append(d)

    def C(self, sn, sp, tn, tp):
        self.conns.append({"source_node": sn, "source_pin": sp, "target_node": tn, "target_pin": tp})

    def D(self, nid, pin, val):
        self.defaults.append({"node_id": nid, "pin_name": pin, "value": val})

    def E(self, a, ap, b, tp="execute"):
        self.ex.append({"source_node": a, "source_pin": ap, "target_node": b, "target_pin": tp})

    def commit(self, entry):
        tm = {}
        res = call("blueprint_query", "add_nodes_bulk", {"asset_path": BP, "graph_name": self.g, "nodes": self.nodes})
        harvest(res, tm)
        if len(tm) != len(self.nodes):
            made = set(tm)
            raise SystemExit("%s 노드 %d/%d missing=%s" % (self.g, len(tm), len(self.nodes),
                             [n["temp_id"] for n in self.nodes if n["temp_id"] not in made]))
        for d in self.defaults:
            d["node_id"] = tm.get(d["node_id"], d["node_id"])
        rd = call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": BP, "graph_name": self.g, "defaults": self.defaults})
        df = [x for x in (rd.get("results") or []) if not x.get("success", True)]
        links = self.conns + self.ex
        for c in links:
            c["source_node"] = tm.get(c["source_node"], c["source_node"]) if c["source_node"] != "ENTRY" else entry
            c["target_node"] = tm.get(c["target_node"], c["target_node"]) if c["target_node"] != "ENTRY" else entry
        rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": self.g, "connections": links})
        cf = [x for x in (rc.get("results") or []) if not x.get("success", True)]
        print("%s: nodes=%d defaults_fail=%d links=%d fail=%d" % (self.g, len(tm), len(df), len(links), len(cf)))
        for f in (df + cf)[:8]:
            print("   FAIL:", json.dumps(f, ensure_ascii=False)[:170])
        return tm


def ensure_fn(name):
    graphs = [str(x.get("name", x) if isinstance(x, dict) else x) for x in call("blueprint_query", "list_graphs", {"asset_path": BP}).get("graphs", [])]
    if name not in graphs:
        call("blueprint_query", "add_function", {"asset_path": BP, "name": name})
        call("blueprint_query", "set_function_params",
             {"asset_path": BP, "function_name": name, "inputs": [{"name": "Seq", "type": SEQT}]})
    gf = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": name})
    for n in gf["nodes"]:
        if "FunctionEntry" in n.get("class", ""):
            return n["id"]
    raise SystemExit(name + " entry 미발견")


def add_key(b, tid, x, y, curve, tsrc, val):
    """tsrc: ('def', '0.0') | ('pin', node, pin)"""
    b.N(tid, "CallFunction", x, y, function_name="AddFloatCurveKey", target_class=ABL)
    b.D(tid, "CurveName", curve)
    b.D(tid, "Value", val)
    b.C("ENTRY", "Seq", tid, "AnimationSequenceBase")
    if tsrc[0] == "def":
        b.D(tid, "Time", tsrc[1])
    else:
        b.C(tsrc[1], tsrc[2], tid, "Time")


def add_curve(b, tid, x, y, curve):
    b.N(tid, "CallFunction", x, y, function_name="AddCurve", target_class=ABL)
    b.D(tid, "CurveName", curve)
    b.C("ENTRY", "Seq", tid, "AnimationSequenceBase")


# ── 1) RemoveLedgeCurves: 9커브 exists→remove ──
entry = ensure_fn("RemoveLedgeCurves")
b = GraphBuilder("RemoveLedgeCurves")
prev = [("ENTRY", "then")]
for i, c in enumerate(ALL9):
    x = 250 + i * 430
    b.N("ex%d" % i, "CallFunction", x, 0, function_name="DoesCurveExist", target_class=ABL)
    b.N("br%d" % i, "Branch", x + 140, 0)
    b.N("rm%d" % i, "CallFunction", x + 280, -80, function_name="RemoveCurve", target_class=ABL)
    b.D("ex%d" % i, "CurveName", c)
    b.D("rm%d" % i, "CurveName", c)
    b.C("ENTRY", "Seq", "ex%d" % i, "AnimationSequenceBase")
    b.C("ENTRY", "Seq", "rm%d" % i, "AnimationSequenceBase")
    b.C("ex%d" % i, "ReturnValue", "br%d" % i, "Condition")
    for a, p in prev:
        b.E(a, p, "ex%d" % i)
    b.E("ex%d" % i, "then", "br%d" % i)
    b.E("br%d" % i, "then", "rm%d" % i)
    prev = [("br%d" % i, "else"), ("rm%d" % i, "then")]
b.commit(entry)

# ── 2) WriteExitCurves: 손발 ik 4커브 (0,1)(Hold,1)(Hold+Fade,0) ──
entry = ensure_fn("WriteExitCurves")
b = GraphBuilder("WriteExitCurves")
b.N("g_hold", "VariableGet", 100, 300, variable_name="ExitHoldTime")
b.N("g_fade", "VariableGet", 100, 400, variable_name="ExitFadeTime")
b.N("hf", "CallFunction", 280, 330, function_name="Add_DoubleDouble", target_class=KML)
b.C("g_hold", "ExitHoldTime", "hf", "A")
b.C("g_fade", "ExitFadeTime", "hf", "B")
prev = ("ENTRY", "then")
for i, cn in enumerate([H["l"], H["r"], F["l"], F["r"]]):
    x = 250 + i * 800
    add_curve(b, "ac%d" % i, x, 0, cn)
    add_key(b, "k0_%d" % i, x + 180, 0, cn, ("def", "0.0"), "1.0")
    add_key(b, "k1_%d" % i, x + 360, 0, cn, ("pin", "g_hold", "ExitHoldTime"), "1.0")
    add_key(b, "k2_%d" % i, x + 540, 0, cn, ("pin", "hf", "ReturnValue"), "0.0")
    b.E(prev[0], prev[1], "ac%d" % i)
    b.E("ac%d" % i, "then", "k0_%d" % i)
    b.E("k0_%d" % i, "then", "k1_%d" % i)
    b.E("k1_%d" % i, "then", "k2_%d" % i)
    prev = ("k2_%d" % i, "then")
b.commit(entry)

# ── 3) WriteIdleCurves: 4 ik 상수1 ──
entry = ensure_fn("WriteIdleCurves")
b = GraphBuilder("WriteIdleCurves")
prev = ("ENTRY", "then")
for i, cn in enumerate([H["l"], H["r"], F["l"], F["r"]]):
    x = 250 + i * 420
    add_curve(b, "ac%d" % i, x, 0, cn)
    add_key(b, "k_%d" % i, x + 180, 0, cn, ("def", "0.0"), "1.0")
    b.E(prev[0], prev[1], "ac%d" % i)
    b.E("ac%d" % i, "then", "k_%d" % i)
    prev = ("k_%d" % i, "then")
b.commit(entry)

# ── 4) WriteMoveCurves: 손발 ik 창 + move 램프 ──
entry = ensure_fn("WriteMoveCurves")
b = GraphBuilder("WriteMoveCurves")
b.N("g_rr", "VariableGet", 100, 500, variable_name="ReleaseRampTime")
b.N("g_pr", "VariableGet", 100, 600, variable_name="PlantRampTime")
SPEC = [  # (접두, ik커브, move커브, Start변수, End변수)
    ("hl", H["l"], HM["l"], "MoveStartL", "MoveEndL"),
    ("hr", H["r"], HM["r"], "MoveStartR", "MoveEndR"),
    ("fl", F["l"], FM["l"], "FootMoveStartL", "FootMoveEndL"),
    ("fr", F["r"], FM["r"], "FootMoveStartR", "FootMoveEndR"),
]
prev = ("ENTRY", "then")
for row, (pf, ik, mv, vs, ve) in enumerate(SPEC):
    y = row * 350
    b.N("gs_" + pf, "VariableGet", 100, y + 120, variable_name=vs)
    b.N("ge_" + pf, "VariableGet", 100, y + 200, variable_name=ve)
    # rel = FMax(Start-RR, 0), pe = End+PR
    b.N("sub_" + pf, "CallFunction", 300, y + 150, function_name="Subtract_DoubleDouble", target_class=KML)
    b.C("gs_" + pf, vs, "sub_" + pf, "A")
    b.C("g_rr", "ReleaseRampTime", "sub_" + pf, "B")
    b.N("rel_" + pf, "CallFunction", 470, y + 150, function_name="FMax", target_class=KML)
    b.C("sub_" + pf, "ReturnValue", "rel_" + pf, "A")
    b.D("rel_" + pf, "B", "0.0")
    b.N("pe_" + pf, "CallFunction", 470, y + 250, function_name="Add_DoubleDouble", target_class=KML)
    b.C("ge_" + pf, ve, "pe_" + pf, "A")
    b.C("g_pr", "PlantRampTime", "pe_" + pf, "B")
    # ik: (0,1)(rel,1)(S,0)(E,0)(pe,1)
    x = 700
    add_curve(b, "ac_" + pf, x, y, ik)
    add_key(b, "k0_" + pf, x + 170, y, ik, ("def", "0.0"), "1.0")
    add_key(b, "k1_" + pf, x + 340, y, ik, ("pin", "rel_" + pf, "ReturnValue"), "1.0")
    add_key(b, "k2_" + pf, x + 510, y, ik, ("pin", "gs_" + pf, vs), "0.0")
    add_key(b, "k3_" + pf, x + 680, y, ik, ("pin", "ge_" + pf, ve), "0.0")
    add_key(b, "k4_" + pf, x + 850, y, ik, ("pin", "pe_" + pf, "ReturnValue"), "1.0")
    # move: (S,0)(E,1)
    add_curve(b, "mac_" + pf, x + 1050, y, mv)
    add_key(b, "mk0_" + pf, x + 1220, y, mv, ("pin", "gs_" + pf, vs), "0.0")
    add_key(b, "mk1_" + pf, x + 1390, y, mv, ("pin", "ge_" + pf, ve), "1.0")
    chain = ["ac_" + pf, "k0_" + pf, "k1_" + pf, "k2_" + pf, "k3_" + pf, "k4_" + pf, "mac_" + pf, "mk0_" + pf, "mk1_" + pf]
    b.E(prev[0], prev[1], chain[0])
    for i in range(len(chain) - 1):
        b.E(chain[i], "then", chain[i + 1])
    prev = (chain[-1], "then")
b.commit(entry)
print("FUNCTIONS_BUILT")
