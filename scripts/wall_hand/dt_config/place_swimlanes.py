"""Place 7 non-overlapping vertical swimlane comment boxes on UpdateWallHandIK.
Explicit bounds (no node enclosure) -> pure visual labels, additive & safe.
Cut points chosen in node gaps so lanes tile without overlap.
"""
import json, urllib.request, sys

MCP="http://localhost:9316/mcp"
BP="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
G="UpdateWallHandIK"

def call(action, params):
    body={"jsonrpc":"2.0","id":1,"method":"tools/call",
          "params":{"name":"blueprint_query","arguments":{"action":action,"params":params}}}
    req=urllib.request.Request(MCP,data=json.dumps(body).encode(),
                               headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=120) as r:
        raw=json.loads(r.read().decode())
    if "result" in raw and "content" in raw["result"]:
        return json.loads(raw["result"]["content"][0]["text"])
    return raw

Y0=-1700; H=5200
# (label, x_lo, x_hi, color rgba)
A=0.15
lanes=[
 ("① DA 로드 + 설정 Break\n(GetConfig -> RWall/LWall/FWall)", -4240, -3000, (0.20,0.55,0.95,A)),
 ("② 속도 평활(VInterp) + 측면설정 R/L 필드 Select", -3000, -1000, (0.30,0.80,0.45,A)),
 ("③ 트레이스 준비 + 정면 오버레이(AND) Select", -1000, 300, (0.20,0.55,0.95,A)),
 ("④ 벽 트레이스 R/L/정면 실행 + Cast PC_01_ABP", 300, 2200, (0.30,0.80,0.45,A)),
 ("⑤ 상태(GetWallHandState) · SetWallHandConfig · 팔로우Z", 2200, 3400, (0.20,0.55,0.95,A)),
 ("⑥ SetWallHandData 출력 + WHFrontHeld 게이트", 3400, 5200, (0.30,0.80,0.45,A)),
 ("⑦ 정면 오버레이 출력 (SetWallHandFront)", 5200, 7500, (0.20,0.55,0.95,A)),
]

dry = "--go" not in sys.argv
for lbl,lo,hi,(r,g,b,a) in lanes:
    w=hi-lo
    p={"asset_path":BP,"graph_name":G,"text":lbl,
       "position":[lo,Y0],"width":w,"height":H,
       "color":{"r":r,"g":g,"b":b,"a":a},"font_size":28}
    if dry:
        print(f"DRY  [{lo:6d}..{hi:6d}] w={w:5d}  {lbl.splitlines()[0]}")
    else:
        res=call("add_comment_node",p)
        ok=res.get("success", res.get("id","?"))
        print(f"ADD  [{lo:6d}..{hi:6d}] -> {ok}  {lbl.splitlines()[0]}")

if not dry:
    print("compile:", call("compile_blueprint",{"asset_path":BP}))
