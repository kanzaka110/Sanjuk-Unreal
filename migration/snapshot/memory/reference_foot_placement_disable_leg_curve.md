---
name: FootPlacement DisableLegCurve — 회피/특수 동작 IK off 처방
description: 회피 종료 후 이동 시작 시 다리 stride가 짧게 나오는 문제. IK 파라미터(MaxExtensionRatio, Unplant 임계 등)로는 해결 안 됨. 회피 애님에 IK off 커브 추가가 정답.
type: reference
originSessionId: bf06505c-af74-43de-8c6d-4394ecaefd65
---
## 증상

- 비전투 회피 후 계속 이동 시 다리가 끝까지 안 나오는 stride 압축
- 시간 지나면 자연 회복 (B 케이스 — lock 잔존이 아니라 inertialization/MM 전환 잔존)
- "회피 후만 / 일반 이동은 정상" 패턴

## 무효였던 처방 (시도 후 무효 확인, 2026-04-28 PC_01)

1. `FootPlacement.SpeedThreshold` 60→30, `UnalignmentSpeedThreshold` 200→100
2. `FootPlacement.MaxExtensionRatio` 0.5→0.85
3. `LegIK.SoftPercentLength` 1.0 확인

→ 위 셋 다 무효. **IK가 클램핑하는 문제가 아님**. 애니메이션 포즈 자체가 회피 종료 시 짧은 stride 가짐 (Inertialization 블렌드 / BlendStack 전환 / MM 포즈 픽업 지연 등 합성 효과).

## 효과 본 처방

**FootPlacement 노드의 `DisableLegCurveName` 활용**:

1. ABP의 FootPlacement 노드 Details → `DisableLegCurveName` 필드에 커브 이름 입력 (예: `DisableLegIK`)
   - 기본값 `NAME_None` (커브 게이트 비활성)
2. 회피 애니메이션 에셋에 동일 이름의 float curve 추가
   - 회피 시작~종료까지: 1.0 (IK 완전 off → raw anim 그대로 재생)
   - 종료 후 0.2~0.5초: 1.0 → 0.0 페이드 (IK 부드럽게 재활성)
3. ABP 컴파일 + 회피 애님 저장

## 메커니즘

- 회피 동안 IK off → raw anim의 발 위치 그대로 재생
- 회피 종료 시 IK가 즉시 풀로 켜지는 게 아니라 페이드인 → Inertialization 블렌드와 IK 활성화가 충돌하지 않음
- 결과: 회피→이동 전환 구간에서 IK가 중간 포즈를 plant 기준으로 잡아 stride를 압축하던 부작용 제거

## 관련 커브 (3종)

| 커브 필드 | 효과 | 용도 |
|----------|------|------|
| `DisableLegCurveName` | 그 다리만 IK 통째로 off | 회피/공중/특수 동작 |
| `DisableLockCurveName` | Plant Lock만 off (IK는 유지) | 발이 정해진 위치에 묶이면 안 되는 동작 |
| `DisablePelvisCurveName` | Pelvis 보정만 off | 골반 오프셋이 방해되는 동작 |

## How to apply

- 회피/스텝/대시/공중 동작 → 이동 전환 시 stride 압축 호소 → **1순위로 DisableLegIK 커브 패턴 시도**
- IK 파라미터(Plant 임계/Extension Ratio/SoftPercent)부터 만지면 시간 낭비
- 커브 이름은 임의 (`DisableLegIK`/`IKOff_Leg`/`FootIK_Disable` 등) — ABP 노드 필드와 애님 에셋 커브 이름이 정확히 일치하면 됨
- 페이드 길이는 동작별 조정 (회피=0.3초, 점프 착지=0.1초 등)
