# -*- coding: utf-8 -*-
"""훅샷 공중 이동 피직스 프로파일 추가 (2026-08-27)

대상: /Game/Art/Character/PC/PC_01/Body/PC_01_Body_001/PC_01_Body_001_PhysicControl

1) Profiles["HookshotAir"] 신규 = Spine + LegLeft + LegRight 를 Simulated 로
2) Profiles["Kinematic"].ModifierUpdates 에 Spine 추가
   -> 없으면 훅샷 종료 후 상체가 Kinematic 으로 안 돌아온다.
      LegLeft/LegRight 항목은 건드리지 않으므로 렛지 동작 불변.

값 출처: LedgeDangle 프로파일 실측 복제.
  - 다리 = LedgeDangle 과 동일값 (AngStrength 3.0 / BlendWeight 0.7)
  - Spine = ⚠추정 초기값 (AngStrength 6.0 = 다리보다 단단, BlendWeight 0.5)
    상체는 조준 AO·스윙 기울기와 경합하므로 보수적으로 시작. 노브로 튜닝.

phase: dry | apply
"""
import json
import sys
import urllib.request

MCP = "http://127.0.0.1:9316/mcp"
ASSET = "/Game/Art/Character/PC/PC_01/Body/PC_01_Body_001/PC_01_Body_001_PhysicControl"

# --- LedgeDangle 실측 복제 템플릿 -------------------------------------------
CTRL = ("(LinearStrength=0.000000,LinearDampingRatio=1.000000,LinearExtraDamping=0.000000,"
        "MaxForce=0.000000,AngularStrength={astr:.6f},AngularDampingRatio={adr:.6f},"
        "AngularExtraDamping={aed:.6f},MaxTorque=0.000000,LinearTargetVelocityMultiplier=1.000000,"
        "AngularTargetVelocityMultiplier={atvm:.6f},CustomControlPoint=(X=0.000000,Y=0.000000,Z=0.000000),"
        "bEnabled=True,bUseCustomControlPoint=False,bUseSkeletalAnimation=True,bDisableCollision=False,"
        "bOnlyControlChildObject=False,bEnableLinearStrength=True,bEnableLinearDampingRatio=True,"
        "bEnableLinearExtraDamping=True,bEnableMaxForce=True,bEnableAngularStrength=True,"
        "bEnableAngularDampingRatio=True,bEnableAngularExtraDamping=True,bEnableMaxTorque=True,"
        "bEnableLinearTargetVelocityMultiplier=True,bEnableAngularTargetVelocityMultiplier=True,"
        "bEnableCustomControlPoint=True,bEnablebEnabled=True,bEnablebUseCustomControlPoint=True,"
        "bEnablebUseSkeletalAnimation=True,bEnablebDisableCollision=True,bEnablebOnlyControlChildObject=True)")

MOD = ("(MovementType={mt},CollisionType=QueryAndPhysics,GravityMultiplier={grav:.6f},"
       "PhysicsBlendWeight={bw:.6f},KinematicTargetSpace=OffsetInBoneSpace,"
       "bUpdateKinematicFromSimulation=True,bEnableMovementType=True,bEnableCollisionType=True,"
       "bEnableGravityMultiplier=True,bEnablePhysicsBlendWeight=True,bEnableKinematicTargetSpace=True,"
       "bEnablebUpdateKinematicFromSimulation=True)")

LEG_CTRL = CTRL.format(astr=3.0, adr=1.5, aed=0.5, atvm=1.2)
SPINE_CTRL = CTRL.format(astr=6.0, adr=1.5, aed=0.5, atvm=1.2)   # 추정 초기값
LEG_MOD = MOD.format(mt="Simulated", grav=0.8, bw=0.7)
SPINE_MOD = MOD.format(mt="Simulated", grav=0.8, bw=0.5)         # 추정 초기값
KINEMATIC_MOD = MOD.format(mt="Kinematic", grav=0.0, bw=0.0)


def named(name, data):
    return '(Name="{0}",Data={1})'.format(name, data)


HOOKSHOT_PROFILE = "(ControlUpdates=({0},{1},{2}),ControlMultiplierUpdates=(),ModifierUpdates=({3},{4},{5}))".format(
    named("ParentSpace_Spine", SPINE_CTRL),
    named("ParentSpace_LegLeft", LEG_CTRL),
    named("ParentSpace_LegRight", LEG_CTRL),
    named("Spine", SPINE_MOD),
    named("LegLeft", LEG_MOD),
    named("LegRight", LEG_MOD),
)


def call(tool, args, timeout=120):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": args}}
    req = urllib.request.Request(MCP, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(txt[:800])
    try:
        return json.loads(txt)
    except Exception:
        return {"raw": txt}


def main():
    phase = sys.argv[1] if len(sys.argv) > 1 else "dry"
    dry = (phase == "dry")

    out = call("blueprint_query", {
        "action": "set_property_at_path",
        "asset_path": ASSET,
        "path": "Profiles[HookshotAir]",
        "value": HOOKSHOT_PROFILE,
        "create_missing_keys": True,
        "strict": True,
        "dry_run": dry,
    })
    print(json.dumps(out, ensure_ascii=False)[:2000])


if __name__ == "__main__":
    main()
