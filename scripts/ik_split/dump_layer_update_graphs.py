# -*- coding: utf-8 -*-
"""AnimLayer_IK 업데이트 체인(EventGraph/ThreadSafe/UpdateWallRunLimbIK) 덤프 + 변수 Write/Read 분석."""
import json, subprocess, io, os, collections
MCP = "http://localhost:9316/mcp"
HERE = os.path.dirname(os.path.abspath(__file__))
LAY = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"

def call(action, args):
    p = {"jsonrpc":"2.0","method":"tools/call","id":1,
         "params":{"name":"blueprint_query","arguments":{"action":action, **args}}}
    r = subprocess.run(["curl","-s","-X","POST",MCP,"-H","Content-Type: application/json","-d",json.dumps(p)],
                       capture_output=True, text=True, timeout=120)
    return r.stdout

SECTIONS = {
 "WallHand": ["WallHandTarget","WallHandAlpha","bWallHandRight","WallHandSpineLean","bWallHandFront","WallHandTargetL","WHFrontBlend","WHReleased","WHElbowRad"],
 "Ledge": ["LedgeDangleAlpha","LedgePelvisSpring","LedgeHandIKAlphaL","LedgeHandIKAlphaR","LedgeHandWorldPredL","LedgeHandWorldPredR","LedgeFootIdleCompL","LedgeFootIdleCompR","LedgeFootIKAlphaL","LedgeFootIKAlphaR","LedgeSlopeDzBody","LedgePhysProfileOn","LedgePhysWanted","LedgePhysAnimAlpha"],
 "WallRun": ["WRIKTargetHandL","WRIKTargetHandR","WRIKTargetFootL","WRIKTargetFootR","WRIKAlphaHandL","WRIKAlphaHandR","WRIKAlphaFootL","WRIKAlphaFootR","WallRunIKWallDist","WRIKPlanePointCS","WRIKNormalCS","WRIKMasterAlpha"],
 "Ladder": ["LadderHandTargetL","LadderHandTargetR","LadderFootTargetL","LadderFootTargetR","LadderHandAlphaL","LadderHandAlphaR","LadderFootAlphaL","LadderFootAlphaR","LadderPelvisTarget"],
}
VAR2SEC = {v: s for s, vs in SECTIONS.items() for v in vs}

graphs = {}
for g in ["EventGraph", "BlueprintThreadSafeUpdateAnimation", "UpdateWallRunLimbIK"]:
    out = call("get_graph_data", {"asset_path": LAY, "graph_name": g})
    io.open(os.path.join(HERE, f"layer_{g}.json"), "w", encoding="utf-8").write(out)
    inner = json.loads(json.loads(out)["result"]["content"][0]["text"])
    graphs[g] = inner
    print(f"== {g}: {len(inner['nodes'])} nodes ==")
    # 변수 Set/Get 집계
    per = collections.defaultdict(lambda: {"set": [], "get": [], "other": []})
    for n in inner["nodes"]:
        cls, title = n["class"], n["title"].replace("\n", " / ")
        for sec, vs in SECTIONS.items():
            for v in vs:
                if v in title:
                    kind = "set" if "VariableSet" in cls else ("get" if "VariableGet" in cls else "other")
                    per[sec][kind].append(f"{title} [{n['id']}]")
    for sec, d in sorted(per.items()):
        print(f"  [{sec}] set={len(d['set'])} get={len(d['get'])} other={len(d['other'])}")
        for k in ("set", "other"):
            for e in d[k]:
                print(f"     {k}: {e}")
    # 함수 호출 노드 (어디서 값 오는지)
    calls = [n["title"].replace("\n"," / ") for n in inner["nodes"] if n["class"] == "K2Node_CallFunction"]
    hist = collections.Counter(calls)
    print("  calls:", dict(hist.most_common(20)))
    print()
