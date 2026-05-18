# PC_01 Motion Matching 노이즈 튜닝 (2026-05-14)

## 배경
PC_01 락온 / 일반 이동 시 MM 잦은 매치 스왑으로 자세 노이즈. ContinuingPose 비용을 더 큰 음수로 깎아 현재 시퀀스 유지 편향을 강화 + BlendStack 블렌드 타임을 짧게 해 cross-fade 잔상 축소.

## 적용 변경 (Monolith blueprint_query 직접 호출)

### 1. BlendStack BlendTime
- 에셋: `/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP`
- 그래프: `AnimGraph`
- 노드: `AnimGraphNode_BlendStack_0`
- pin: `BlendTime` (id `601DD0804524F83CA777E0B9D1A20950`)
- **`0.200000` → `0.05`**
- 액션: `blueprint.set_pin_default` (param 이름은 `value`, `default_value` 아님)

### 2. PSD ContinuingPoseCostBias (`-0.05` 목표)
- 액션: `blueprint.set_cdo_property` (PSD = UPoseSearchDatabase → DataAsset CDO 접근 가능)

| PSD | pre | post |
|---|---|---|
| `PSD_GroundMoving` | -0.010000 | **-0.050000** |
| `PSD_GroundMovingTransit` | **-0.050000 (이미 적용 상태)** | 변경 안 함 |
| `PSD_GroundIdleTransit` | -0.010000 | **-0.050000** |

처방서에는 3개 모두 -0.01 → -0.05 라고 했으나 GroundMovingTransit는 이미 -0.05. 누가 언제 바꿨는지 미상 (이력 추적 필요할 경우 P4 history 확인).

## 검증
- BlendStack pin post: `BlendTime=0.05` (`get_node_details` 재조회 확인)
- PSD bias post: 모두 `-0.05000000074505806` (`get_cdo_properties` 재조회 확인)
- compile: success / status=UpToDate / 0 errors 0 warnings
- save: ABP / PSD_GroundMoving / PSD_GroundIdleTransit 모두 `saved=true, was_dirty=true`

## Side-effect 체크
- AnimGraph BlendStack 의 다른 pin (AnimationAsset, AnimationTime=-1, bLoop=true, BlendProfile, Pose 출력) 모두 그대로
- PSD CDO 의 다른 property (Schema 참조, BaseCostBias=0, LoopingCostBias 등) 직접 비교 안 함 — set_cdo_property 는 단일 필드만 건드림이 보장됨
- 변경 안 한 PSD_GroundMovingTransit 미터치

## 향후 관찰 포인트
- ContinuingPoseCostBias 를 -0.05 로 키우면 같은 클립 안에서 더 오래 머무는 편향. 만약 방향 전환 (Turn / Pivot) 클립으로 넘어가야 할 타이밍이 늦어 보이면 -0.03 정도로 완화 검토.
- BlendTime 0.05 는 짧음. 컷처럼 보이면 0.08~0.1 로 완화.
- PSD_GroundMovingTransit 가 이미 -0.05 였던 점 — Transit 류는 사전에 누군가 더 강한 lock 을 걸어둠. Idle/Moving 본체와 일관성 맞춤은 정합.

## 다음 작업 가능 항목
- PIE 에서 ANIM_REC 로 시퀀스 스왑 빈도 모니터링 (svl 패턴과 같이 보면 응답성도 같이 확인)
- 필요 시 PSD_Pivot / PSD_TurnInPlace 등 다른 PSD bias 일괄 점검 (현재 처방엔 미포함)
