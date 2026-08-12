# -*- coding: utf-8 -*-
"""NPC_100 드론 — 라이트 연동 배치 + 원거리 모드 어태치/디태치 아크 (2026-08-12)

대상: /Game/Art/Character/NPC/NPC_100/Body/NPC_100_Body_01/Blueprint/NPC_100_Body_01_BP
      /Game/Art/Character/NPC/NPC_100/Body/NPC_100_Body_01/Blueprint/NPC_100_Body_01_ABP
전송: Monolith HTTP JSON-RPC 직결 (POST 127.0.0.1:9316/mcp)

이 파일은 세션에서 실제 적용한 변경의 **재현/문서용**이다.
이미 적용·저장된 상태이므로 그대로 재실행하면 노드가 중복 생성된다.
P4 롤백 등으로 원복됐을 때 구조 참조용으로 사용할 것.

===========================================================================
1. Tick 구성 (EventGraph)
===========================================================================
    Tick → Sequence
            ├ then_0 → Set Vector Parameter Value          (머티리얼)
            ├ then_1 → UpdateDroneAttach(dt)
            │            └ Branch(bHandled) ─ false → UpdateDroneIdle
            └ then_2 → LightAlpha → Set Intensity → Set LightMoveRatio

    BeginPlay → Branch(IsValid FollowTarget)
                  └ false → Set FollowTarget → AddTickPrerequisiteActor
                    ※ 드론이 캐릭터 뒤에 틱하도록 (한 프레임 지연 제거)

===========================================================================
2. 라이트 강도 → 배치 연동
===========================================================================
    LightMoveRatio = FInterpTo(현재, Clamp(Intensity / LightMoveFullIntensity, 0, 1),
                               dt, LightMoveRatioSpeed)

    | 대상            | OFF                | 최대                  |
    |-----------------|--------------------|-----------------------|
    | 이동 리드 X     | MoveLeadDistance   | LightMoveLeadFront    |
    | 추종 지연 보상  | 없음               | SmoothedPCVel × VelFeedforwardTime |
    | 측면 폭 Y       | EscortSideY        | × LightSideScale      |
    | 이동 고도 Z     | EscortHeight       | LightHeight           |
    | Idle Z 범위     | IdleZMin/Max       | LightIdleZMin/Max     |
    | Idle 배회 아크  | ±180°              | ±LightWanderArc       |
    | 긴 이동 확률    | BigMoveChance      | LightBigMoveChance    |
    | 기체 피치       | 0°                 | LightPitchDown        |
    | 시선            | 이동 방향          | 캐릭터 정면 락온      |

    🔴 추종 지연: VInterpTo(속도 k)는 캐릭터가 v[cm/s]로 달릴 때 정상상태 오차 v/k 를
       뒤에 남긴다. 450/6 = 75cm 가 전방 리드(+60)를 통째로 잡아먹어 "옆에만 있다"가
       나왔다. 속도 피드포워드로 상쇄.

    🔴 정면 락온은 **타깃 쪽**에 걸어야 한다. 출력(보간 결과)에 RLerp 로 덮으면
       ratio 1 에서 보간기를 통째로 무시해 1틱 스냅이 된다.
           맞음: 타깃 = RLerp(기존 시선타깃, 캐릭터회전, ratio) → RInterpTo 통과
           틀림: SmoothedLookRot = RLerp(RInterpTo(...), 캐릭터회전, ratio)

===========================================================================
3. 어태치 / 디태치 (신규 함수 5종)
===========================================================================
[UpdateDroneAttach(DeltaTime) -> bHandled]        상태 전이 + 적용
    Cast SBCharacter(GetPlayerCharacter) 실패 → bHandled=false
    GetCurrentStancePhase == 2 (원거리 모드)
      ├ 참 : bDroneAttached=true, bHandAttached=true(ABP 용), DetachAlpha=0
      │      목표 = 손소켓위치 + Rotate(HandAttachLocOffset, 손소켓회전)
      │             소켓 = HandAttachSocket("FX_Hand_L")
      │             메시 = GetComponentByClass(캐릭터, SkeletalMeshComponent)
      └ 거짓
         ├ 직전 어태치중 → 해제 + BuildDetachArc()
         └ 디태치중      → DetachAlpha += dt/DetachArcDurationCur
                           목표 = DetachArcPoint(DetachAlpha)
                           런타임 클램프: SphereTrace(DronePos → 목표)
                               막히면 ImpactPoint + Normal × DetachTraceRadius
                           alpha ≥ 1 → 종료 + SettleAfterDetach()
    [적용] DronePos = VInterpToConstant(→목표, AttachMoveSpeed)
           SetActorLocation(DronePos, teleport)       ← 캡슐이 위치 주인
           SmoothedLookRot = RInterpTo(→AttachLookTarget, HandAttachSettleSpeed)
           Mesh.SetWorldRotation( Combine(
               MakeRotator(Pitch = LightPitchDown × ratio × faceBlend,
                           Yaw   = HandAttachSettleYaw),
               RLerp(SmoothedLookRot, 캐릭터회전, faceBlend) ) )
           faceBlend = MapRangeClamped(DetachAlpha, DetachFaceStart~1 → 0~1)

[BuildDetachArc]                                   디태치 시작 1틱
    EndAngle  = Lerp(Random(AngleMin,Max), LightDetachEndAngle, LightMoveRatio)
                × (RandomBool ? +1 : -1)            ← 양쪽 열렸으면 좌/우 랜덤
    EndRadius = Lerp(Random(RadiusMin,Max), LightDetachEndRadius, ratio)
    EndZ      = Lerp(Random(ZMin,Max),      LightDetachEndZ,      ratio)
    IsDetachArcClear() ? 그대로
      : EndAngle = -EndAngle;  IsDetachArcClear() ? 반전채택
        : EndAngle ×= DetachArcFallbackScale
          EndRadius = Lerp(StartRadius, EndRadius, DetachArcFallbackScale)
    Duration = Clamp(|EndAngle|·rad × (StartRadius+EndRadius)/2 / DetachArcSpeed,
                     DetachMinDuration, DetachMaxDuration)

[IsDetachArcClear -> bClear]                       궤도 전 구간 충돌 검사
    prev = DetachArcPoint(0)
    ForLoopWithBreak 1..DetachArcSamples:
        p = DetachArcPoint(i / DetachArcSamples)    ← 실제 평가 함수를 그대로 재사용
        SphereTrace(prev → p, DetachTraceRadius, Camera, 플레이어 무시)
        막히면 false, Break

[DetachArcPoint(Alpha) -> Pos]                     궤도 평가
    e   = Ease(0, 1, Alpha, EaseInOut, 2)
    Pos = 캐릭터위치
          + Forward(캐릭터Yaw + Lerp(0, EndAngle, e)) × Lerp(StartRadius, EndRadius, e)
          + (0, 0, Lerp(0, EndZ, e))

[SettleAfterDetach]                                Idle 인계 시드 (1틱)
    IdleTargetOffset = UnrotateVector(아크종점 − 캐릭터위치, 캐릭터회전)
    ChosenAngle = PrevChosenAngle = degrees(Atan2(로컬Y, 로컬X))
    IdleRepickTime = 현재 + Random(IdleRepickMin, Max)
    IdleStepCur/IdleInterpCur/IdleTurnCur = WanderMicro*
    CurrentVisualWorld = PrevVisualWorld = 아크종점     ← 시선 델타 리셋
    CurrentBankRoll = CurrentPitchLean = 0
    SmoothedLookRot = 캐릭터회전                        ← 정면 확정

===========================================================================
4. ABP (NPC_100_Body_01_ABP) — 커버 개폐 살림
===========================================================================
    [이전] StateMachine → Slot 'FullBody' → 출력 포즈
           (LightAlpha → TwoWayBlend(CoverClose/CoverOpen) → LayeredBoneBlend 고아)
    [지금] Slot → LayeredBoneBlend.BasePose
           TwoWayBlend → LayeredBoneBlend.BlendPoses_0
           LayeredBoneBlend → 출력 포즈

    LayerSetup (본 필터) — 두 시퀀스 112본 프레임0 전수 비교로 다른 22본을 뽑아 구성:
        gun(1) / wingRing(1) / wingHinge_A~D(4)
        → hatchHinge·mainHatch·subWing·tentacle 포함, bladeRing 계열 32본은 제외
          (프로펠러는 스테이트머신 애니 유지)

    ABP 는 Cast To NPC_100_Body_01_BP 로 다음을 읽어간다 (BP 에서 지우면 안 됨):
        VisWasMoving / CurrentVisualWorld / SpinRemaining / bHandAttached / LightAlpha()

===========================================================================
5. 정리 (비가역)
===========================================================================
    함수 8개 삭제: UpdateFollowMove UpdateVisualHover UpdateGaze UpdateWanderSpin
                   UpdatePositionPipeline UpdateHandAttach UpdateDetachArc UpdateDetachBlend
    변수 55개 삭제 / EventGraph 죽은 노드 56개 삭제
    유지: CanBePooled(C++ 호출) + ABP 참조 변수 4종
    백업: C:\\Users\\SHIFTUP\\drone-backup-20260812\\ , 리포 backup/drone-20260812/ (커밋 5607796)

===========================================================================
6. 이번에 걸린 함정
===========================================================================
- Monolith 는 순수 노드를 **소비처마다 복제**한다. 랜덤 노드를 두 분기에서 쓰면
  서로 다른 난수가 나온다 → 변수에 한 번 저장한 뒤 읽을 것.
- BP exec **출력 핀은 연결 1개만 유지**된다. 기존 연결이 있는 곳에 새로 이으면
  조용히 교체되어 체인이 끊기거나 역방향 루프가 생긴다. 컴파일 0/0 으로 통과하므로
  편집 후 exec 트리를 반드시 재출력해 확인할 것.
- add_node 는 **같은 좌표에 노드가 있으면 그걸 반환**하는 헬퍼를 쓰면 FunctionEntry /
  FunctionResult 와 좌표가 겹쳐 엉뚱한 노드에 배선된다. [0,0] 회피.
- 클래스 핀 기본값은 `default_value` 가 아니라 **`default_object`** 에 들어간다.
  get_graph_data 의 default_value 만 보고 "비어 있다"고 판단하면 오진.
- set_pin_default 가 success 를 반환해도 값이 안 들어가는 경우가 있다(Lerp.A=1.0).
  적용 후 재조회로 검증할 것.
- ACharacter::GetMesh 는 BP 노출이 아니다 → GetComponentByClass(SkeletalMeshComponent).
- 자기 함수 호출 노드는 **compile 선행** 후에야 add_node 로 만들 수 있고,
  target_class 를 주면 실패한다(생략해야 self 로 붙음).
"""

ENDPOINT = "http://127.0.0.1:9316/mcp"
BP = "/Game/Art/Character/NPC/NPC_100/Body/NPC_100_Body_01/Blueprint/NPC_100_Body_01_BP"
ABP = "/Game/Art/Character/NPC/NPC_100/Body/NPC_100_Body_01/Blueprint/NPC_100_Body_01_ABP"

# ---------------------------------------------------------------------------
# 최종 파라미터
# ---------------------------------------------------------------------------
DRONE_LIGHT = {
    "LightOffEV": 5.0,                  # 이 EV100 이상이면 소등
    "LightFullEV": -2.0,                # 이 EV100 이하면 최대 강도
    "LightMaxIntensity": 300000.0,
    "LightCurveExp": 6.0,               # 클수록 중간 밝기에서 약하게
    "LightMoveFullIntensity": 20000.0,  # 이 강도 이상이면 전방 배치 100%
    "LightMoveRatioSpeed": 1.5,
    "LightMoveLeadFront": 60.0,
    "LightSideScale": 0.5,
    "LightHeight": 130.0,               # 캐릭터 캡슐 반높이 82 → 머리끝 +48
    "LightIdleZMin": 100.0,
    "LightIdleZMax": 190.0,
    "LightWanderArc": 45.0,
    "LightBigMoveChance": 0.08,
    "LightPitchDown": -25.0,
    "LightDetachEndAngle": -330.0,      # 라이트 최대일 때 한 바퀴 돌아 정면
    "LightDetachEndRadius": 120.0,
    "LightDetachEndZ": 150.0,
}

DRONE_ATTACH = {
    "HandAttachSocket": "FX_Hand_L",
    "HandAttachFlySpeed": 800.0,
    "HandAttachSettleSpeed": 4.0,
    "HandAttachSettleYaw": -90.0,       # 메시 앞면이 로컬 −Y
    "DetachArcEndAngleMin": -270.0,
    "DetachArcEndAngleMax": -160.0,
    "DetachArcEndRadiusMin": 110.0,
    "DetachArcEndRadiusMax": 190.0,
    "DetachArcEndZMin": 50.0,
    "DetachArcEndZMax": 110.0,
    "DetachArcStartRadius": 45.0,
    "DetachArcSpeed": 500.0,
    "DetachArcSamples": 6,
    "DetachArcFallbackScale": 0.4,
    "DetachTraceRadius": 18.0,
    "DetachMinDuration": 0.35,
    "DetachMaxDuration": 1.2,
    "DetachMoveSpeed": 6000.0,          # 경로 추종 정확도 (낮추면 아크가 뭉개짐)
    "DetachFaceStart": 0.6,             # 이 알파부터 캐릭터 정면으로 블렌드
}

ABP_COVER_LAYERS = [{"bones": [
    {"bone": "gun", "depth": 1},
    {"bone": "wingRing", "depth": 1},
    {"bone": "wingHinge_A", "depth": 4},
    {"bone": "wingHinge_B", "depth": 4},
    {"bone": "wingHinge_C", "depth": 4},
    {"bone": "wingHinge_D", "depth": 4},
]}]

LIVE_FUNCTIONS = [
    "UpdateDroneIdle", "UpdateDroneIdleMove", "UpdateCamAvoid", "DrawDroneIdleRange",
    "UpdateRotationGaze", "UpdateSmoothedVel", "LightAlpha",
    "UpdateDroneAttach", "BuildDetachArc", "IsDetachArcClear",
    "DetachArcPoint", "SettleAfterDetach",
    "CanBePooled",  # C++ 풀링 시스템이 호출
]

if __name__ == "__main__":
    print(__doc__)
