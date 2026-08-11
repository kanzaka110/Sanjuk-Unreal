"""NPC_100 드론 — 씬 밝기 연동 라이트 + 라이트 강도 연동 배치 (2026-08-11)

대상: /Game/Art/Character/NPC/NPC_100/Body/NPC_100_Body_01/Blueprint/NPC_100_Body_01_BP
전송: Monolith HTTP JSON-RPC 직결 (POST 127.0.0.1:9316/mcp)

이 스크립트는 세션에서 실제 적용한 변경의 **재현/문서용**이다.
이미 적용·저장(P4 체크아웃)된 상태이므로 재실행하면 노드가 중복 생성된다.
P4 롤백 등으로 원복됐을 때만 사용할 것.

--------------------------------------------------------------------------
최종 구조
--------------------------------------------------------------------------
[BP 함수 LightAlpha]
    LightAlpha = Clamp((LightOffEV - AvgSceneEV100) / (LightOffEV - LightFullEV), 0, 1)
        입력 = SBBlueprintLibrary::GetPlayerViewLightingMetrics → OutAverageSceneEV100

[EventGraph Tick → Sequence.then_1]
    Intensity      = FInterpTo(현재, pow(LightAlpha, LightCurveExp) * LightMaxIntensity, dt, 5)
    LightMoveRatio = FInterpTo(현재, Clamp(Intensity / LightMoveFullIntensity, 0, 1), dt, LightMoveRatioSpeed)

[UpdateFollowMove]
    앵커 오프셋   = VLerp(FollowOffset, LightFrontOffset, LightMoveRatio)
    배회 반각     = Lerp(WanderArcHalfAngle, LightWanderArc, LightMoveRatio)
    앵커 갱신조건 = 기존 OR (Abs(LightMoveRatio - PrevLightMoveRatio) > 0.02)
                    ※ CachedAnchor는 캐릭터가 AnchorUpdateDistance(150cm) 이상
                       움직여야만 갱신되므로, 정지 상태에서 라이트 연동이
                       반영되지 않는 문제를 이 조건으로 해소

[UpdateWanderSpin]
    이동 중 리드 = Lerp(MoveLeadDistance, LightMoveLeadFront, LightMoveRatio)  → MakeVector.X

[UpdateRotationGaze]
    최종 MakeRotator(Yaw=-90).Pitch = LightPitchDown * LightMoveRatio

[UpdatePositionPipeline]  — 벽 클램프
    hit          = LineTraceByChannel(캐릭터위치 → 목표위치, Visibility, ignore=[FollowTarget])
    clamped      = SelectVector(ImpactPoint + ImpactNormal*DroneWallClearance, 목표, hit)
    DroneDrawPos = SelectVector(clamped, VInterpTo(DroneDrawPos, clamped, dt, DroneClampSpeed),
                                Distance(DroneDrawPos, clamped) > 300)   ← 큰 격차는 즉시 스냅
    메시 SetRelativeLocation ← DroneDrawPos
    ※ 상태 변수 CurrentVisualWorld 는 원본 유지. 클램프 값을 상태에 쓰면
       다음 프레임 스무딩 입력으로 재사용되어 누적 피드백이 발생한다.

--------------------------------------------------------------------------
신규 변수 (최종값)
--------------------------------------------------------------------------
Drone|Light
    LightOffEV             5.0     이 EV100 이상이면 완전 소등
    LightFullEV           -2.0     이 EV100 이하면 최대 강도
    LightMaxIntensity  300000.0    암흑에서의 SpotLight Intensity (Unitless)
    LightCurveExp          5.0     클수록 중간 밝기에서 약하게 (1 = 선형)
    LightMoveFullIntensity 20000.0 이 강도 이상이면 전방 배치 100%
    LightFrontOffset  (120,90,110) 라이트 최대일 때 앵커 오프셋
    LightMoveLeadFront    60.0     라이트 최대일 때 이동 중 전방 리드
    LightWanderArc        45.0     라이트 최대일 때 배회 반각
    LightPitchDown        -7.5     라이트 최대일 때 기체 피치
    LightMoveRatioSpeed    1.5     배치 전환 저역 필터 속도
    LightMoveRatio         -       (transient) 라이트 강도 → 배치 비율
    PrevLightMoveRatio     -       (transient) 앵커 갱신 판정용

Drone|Collision
    DroneWallClearance    15.0     히트 지점에서 법선 방향 여유
    DroneClampSpeed       15.0     클램프 위치 수렴 속도
    DroneDrawPos           -       (transient) 실제 그리는 위치

--------------------------------------------------------------------------
PIE 실측 (2026-08-11)
--------------------------------------------------------------------------
EV100        위치별 편차 큼 — 넓은 실외 7.5~8.0 / 중간 5.5~5.8 / 어두운 구역 0.5~1.2
Intensity    exp 3 → 60k / exp 4 → 35k / exp 5 → 21k / exp 6 → 12k (EV≈0.9 기준)
배치         정지 시 상대각 -78°~+62°, 이동 중(속도 450) -29°~+23° — 전방 반구 유지
피드백루프   300k 풀강도에서도 EV100 ≤2 유지 → 라이트가 스스로 EV를 올려 꺼지는 루프 없음
캡슐         벽 근처에서 메시-캡슐 거리 0.6~2.5cm 밀착, CamAvoid=0 → 캡슐 충돌 아님

--------------------------------------------------------------------------
미해결 (내일 이어서)
--------------------------------------------------------------------------
- 벽 근처 떨림이 스무딩 클램프로 해소됐는지 육안 검증 대기
- ABP(NPC_100_Body_01_ABP)의 AnimGraph에 LightAlpha를 쓰는 TwoWayBlend
  (CoverClose/CoverOpen)가 출력 미연결 고아 상태 — 살릴지 제거할지 미정
- GetPlayerViewLightingMetrics 의 성공 bool 미사용 → 실패 시 EV=0 취급되어
  alpha 1(풀 밝기)로 fail. 안전 방향이 반대
- GetPlayerViewLightingMetrics 는 화면 전체 평균이라 드론 국소 조도가 아님
"""

import json
import urllib.request

ENDPOINT = "http://127.0.0.1:9316/mcp"
BP = "/Game/Art/Character/NPC/NPC_100/Body/NPC_100_Body_01/Blueprint/NPC_100_Body_01_BP"


def call(tool, action, **kw):
    args = {"action": action}
    args.update(kw)
    body = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": tool, "arguments": args},
    }).encode()
    req = urllib.request.Request(
        ENDPOINT, data=body,
        headers={"Content-Type": "application/json",
                 "Accept": "application/json, text/event-stream"},
    )
    r = json.load(urllib.request.urlopen(req, timeout=60))
    txt = r["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except ValueError:
        return txt


VARIABLES = [
    ("LightOffEV",             "float",         "5.0",     "Drone|Light",     True),
    ("LightFullEV",            "float",         "-2.0",    "Drone|Light",     True),
    ("LightMaxIntensity",      "float",         "300000.0", "Drone|Light",    True),
    ("LightCurveExp",          "float",         "5.0",     "Drone|Light",     True),
    ("LightMoveFullIntensity", "float",         "20000.0", "Drone|Light",     True),
    ("LightFrontOffset",       "struct:Vector", "(X=120.000000,Y=90.000000,Z=110.000000)", "Drone|Light", True),
    ("LightMoveLeadFront",     "float",         "60.0",    "Drone|Light",     True),
    ("LightWanderArc",         "float",         "45.0",    "Drone|Light",     True),
    ("LightPitchDown",         "float",         "-7.5",    "Drone|Light",     True),
    ("LightMoveRatioSpeed",    "float",         "1.5",     "Drone|Light",     True),
    ("DroneWallClearance",     "float",         "15.0",    "Drone|Collision", True),
    ("DroneClampSpeed",        "float",         "15.0",    "Drone|Collision", True),
]

TRANSIENT = [
    ("LightMoveRatio",     "float",         "0.0", "Drone|Light"),
    ("PrevLightMoveRatio", "float",         "0.0", "Drone|Light"),
    ("DroneDrawPos",       "struct:Vector", "(X=0.000000,Y=0.000000,Z=0.000000)", "Drone|Collision"),
]


def ensure_variables():
    """변수만 재생성한다. 그래프 배선은 노드 ID 의존이라 수동 재작업 필요."""
    existing = {v["name"] for v in call("blueprint_query", "get_variables", blueprint_path=BP)["variables"]}
    for name, tp, default, cat, editable in VARIABLES:
        if name in existing:
            call("blueprint_query", "set_variable_defaults", asset_path=BP, name=name, default_value=default)
            print(f"  update {name} = {default}")
        else:
            call("blueprint_query", "add_variable", asset_path=BP, name=name, type=tp,
                 default_value=default, category=cat, instance_editable=editable)
            print(f"  add    {name} = {default}")
    for name, tp, default, cat in TRANSIENT:
        if name not in existing:
            call("blueprint_query", "add_variable", asset_path=BP, name=name, type=tp,
                 default_value=default, category=cat, instance_editable=False, transient=True)
            print(f"  add    {name} (transient)")


def report():
    """현재 값 확인."""
    for v in call("blueprint_query", "get_variables", blueprint_path=BP)["variables"]:
        if v["name"].startswith(("Light", "Drone")):
            print(f"  {v['name']:24s} {v['default_value']}")


if __name__ == "__main__":
    print("현재 값:")
    report()
