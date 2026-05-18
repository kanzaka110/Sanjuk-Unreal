---
name: PC_01_ABP AnimGraph 체인 전체 구조
description: T3D export 파싱으로 확정한 PC_01_ABP 메인 AnimGraph 노드 순서와 Inertialization/DeadBlending 정확한 위치. 가드 틕튐 분석의 ground truth.
type: project
originSessionId: ebbc629e-a8a1-40ce-8885-386c1ceb4efe
---
PC_01_ABP AnimGraph 22노드 전체 체인 (X좌표 = 업스트림→다운스트림, 왼쪽이 소스)

```
x=-464  StateMachine_0  (Idle/Moving/Falling/SplineMoving/PlayingMontage)
x=-464  BlendStack_0    (MM 블렌드)
x=-288  ★DeadBlending_0  ← StateMachine 뒤 (BlendProfile: InstantFeet_InstantRoot, 0.1s)
x=-112  TwoWayBlend_1
x= 240  BlendSpacePlayer_1
x= 560  ApplyMeshSpaceAdditive_0
x= 976  Slot_2
x=1376  Slot_1, Slot_3
x=1632  LayeredBoneBlend_1
x=2048  OffsetRootBone_0
x=2864  LinkedAnimLayer_5  (IK 레이어 — FootPlacement 연결)
x=3376  LinkedAnimLayer_7  (Overlay 레이어 — Guard 포함)
x=3584  ★Inertialization_0 ← Overlay 뒤 (SaveCachedPose로 캐시)
x=3776  SaveCachedPose_1
x=4400  LayeredBoneBlend_10  (주석: Montage Blend 영향 안 받는 Overlay Curve Override)
x=4800  Slot_0
x=5216  PoseSearchHistoryCollector_0
x=5600  Root_0 (Output)
```

**역할 분담 (설계가 이미 잘 돼있음):**
- **DeadBlending_0**: 로코모션 StateMachine 상태 전환 담당 (InstantFeet_InstantRoot로 발/루트는 스킵)
- **Inertialization_0**: Overlay LinkedAnimLayer_7 내부 포즈 전환 담당

**Overlay ABP 템플릿 (`PC_01_OverlayPose_Base`):**
- BlendListByEnum(MovementState enum: Idle/Moving) + TransitionType=Inertialization, BlendTime=0.1s
- 정적 포즈 2개(`Pose_Stand_Idle`, `Pose_Stand_Move`)만 있음. Start 단계 없음
- Guard Overlay는 이 인터페이스를 구현, Guard_Pose_Idle/Move 변수로 바인딩

**Why:** T3D 복사+Python 파싱으로 확정한 실측 구조.

**How to apply:**
- PC_01 애니메이션 분석 시 이 체인이 기본 참조. 좌표와 노드명은 안정적
- `P_Player_Fist_Normal_Guard01_Start` 같은 가드 몽타주는 **Overlay가 아닌 Slot 경유 재생** (Overlay엔 Start 단계 없음)
- 가드/액션 몽타주 관련 틕튐 문제는 대부분 **Slot 몽타주 Blend Out 설정 문제**이며 ABP 구조는 건드릴 필요 없음
- 몽타주 Blend Out을 Inertialization 모드로 설정하면 `Inertialization_0`이 자동 수신
