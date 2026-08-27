# -*- coding: utf-8 -*-
"""Kinematic 프로파일에 Spine 복귀 항목 추가 (2026-08-27)

훅샷이 Spine 을 Simulated 로 바꾸므로, 되돌릴 항목이 Kinematic 프로파일에 있어야 한다.
LegLeft/LegRight 는 실측값 그대로 복제 -> 렛지 동작 불변.

phase: dry | apply
"""
import json
import sys
import urllib.request

MCP = "http://127.0.0.1:9316/mcp"
ASSET = "/Game/Art/Character/PC/PC_01/Body/PC_01_Body_001/PC_01_Body_001_PhysicControl"

KIN = ("(MovementType=Kinematic,CollisionType=QueryAndPhysics,GravityMultiplier=0.000000,"
       "PhysicsBlendWeight=0.000000,KinematicTargetSpace=OffsetInBoneSpace,"
       "bUpdateKinematicFromSimulation=True,bEnableMovementType=True,bEnableCollisionType=True,"
       "bEnableGravityMultiplier=True,bEnablePhysicsBlendWeight=True,bEnableKinematicTargetSpace=True,"
       "bEnablebUpdateKinematicFromSimulation=True)")

VALUE = [
    '(Name="LegLeft",Data=%s)' % KIN,
    '(Name="LegRight",Data=%s)' % KIN,
    '(Name="Spine",Data=%s)' % KIN,
]


def call(args, timeout=120):
    b = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
         "params": {"name": "blueprint_query", "arguments": args}}
    r = json.load(urllib.request.urlopen(
        urllib.request.Request(MCP, json.dumps(b).encode(), {"Content-Type": "application/json"}), timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(txt[:800])
    try:
        return json.loads(txt)
    except Exception:
        return {"raw": txt}


dry = (sys.argv[1] if len(sys.argv) > 1 else "dry") == "dry"
print(json.dumps(call({
    "action": "set_property_at_path",
    "asset_path": ASSET,
    "path": "Profiles[Kinematic].ModifierUpdates",
    "value": VALUE,
    "strict": True,
    "dry_run": dry,
}), ensure_ascii=False)[:1500])
