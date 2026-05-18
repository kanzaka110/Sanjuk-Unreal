---
name: UE 5.7 FootPlacement 공식 소스 기반 실제 기본값 및 enum
description: Epic GitHub UnrealEngine 5.7 브랜치의 AnimNode_FootPlacement.h에서 직접 추출한 정확한 기본값 및 enum 정의. 모든 FootPlacement 조언의 ground truth.
type: reference
originSessionId: 38491534-e53a-4fee-be48-740ab304fcba
---
**출처**: `https://github.com/EpicGames/UnrealEngine/blob/5.7/Engine/Plugins/Animation/AnimationWarping/Source/Runtime/Public/BoneControllers/AnimNode_FootPlacement.h`

## FFootPlacementPelvisSettings (기본값)

| 필드 | 타입 | 기본값 | 한글명(SB2) |
|------|------|--------|-------------|
| MaxOffset | float | 50.0 | 최대 오프셋 |
| LinearStiffness | float | 350.0 | 선형 강성 |
| LinearDamping | float | 1.0 | 선형 감쇠 |
| HorizontalRebalancingWeight | float | 0.3 (0~1) | 가로 리밸런싱 가중치 |
| MaxOffsetHorizontal | float | 10.0 | 최대 오프셋 가로 |
| HeelLiftRatio | float | 0.5 (0~1) | 힐 리프트 비율 |
| PelvisHeightMode | enum | AllLegs | 골반높이 모드 |
| ActorMovementCompensationMode | enum | SuddenMotionOnly | 액터 무브먼트 보정 모드 |
| bEnableInterpolation | bool | true | 보간 활성화 |
| bDisablePelvisOffsetInAir | bool | true | 골반 오프셋 비활성화 (공중) |
| DisablePelvisCurveName | FName | NAME_None | 골반 커브 이름 비활성화 |

## EPelvisHeightMode

```cpp
enum class EPelvisHeightMode : uint8 {
    AllLegs,                    // 평지/완경사. 기본값.
    AllPlantedFeet,             // 잠긴 발만 — 지지 다리 기준
    FrontPlantedFeetUphill_FrontFeetDownhill  // 오르막: 앞발. 내리막: 양발 (알고리즘이 낮은 발 선호, 단 과압축 방지)
};
```

**중요**: `FrontPlantedFeetUphill_FrontFeetDownhill`이 **방향별 처리를 엔진 내부에서 이미 구현**. Modify Bone 같은 커스텀 해법 불필요.

## EActorMovementCompensationMode

```cpp
enum class EActorMovementCompensationMode : uint8 {
    ComponentSpace,     // 수직 이동 전부 따라감. 부드러운 지면/무빙 플랫폼에 적합.
    WorldSpace,         // 수직 이동 무시, 월드 고정 + 스프링 보간
    SuddenMotionOnly    // 기본. 급변 시만 월드 유지, 스프링 보간. 무빙 플랫폼 불가.
};
```

공식 코멘트: 카메라가 캐릭터에 직접 붙고 스무딩 거의 없으면 `ComponentSpace` 권장. 큰 계단에서 덜컥 방지엔 `SuddenMotionOnly` 또는 `WorldSpace` 시도.

## 스프링 파라미터 주의

공식 기본값 `LinearStiffness = 350`, `LinearDamping = 1.0`은 UE 내부 spring model에서 정상 작동하는 값. 다른 스프링 공식(`damping ≈ 2√stiffness`)을 직접 적용하면 **값 체계가 달라 잘못 계산**. 외부 공식으로 변환 전에 UE 구현 확인 필요.

## How to apply

- FootPlacement 파라미터 권장값 제시 시 이 파일 값을 ground truth로 사용.
- 사용자가 기본값에서 크게 벗어난 값을 쓰고 있다면 이유 파악 후 조정.
- 다른 UE 버전(5.6/5.8) 값이 다를 수 있음 — 필요 시 해당 브랜치 재조회:
  `gh api "repos/EpicGames/UnrealEngine/contents/.../AnimNode_FootPlacement.h?ref=5.X"`
