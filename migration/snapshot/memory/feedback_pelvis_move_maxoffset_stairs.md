---
name: PelvisSettings Move.MaxOffset은 계단 오르막 pelvis drop 방지용
description: SB2 이동 프로필 MaxOffset=10은 의도적으로 낮춤. 올리면 계단 오르막에서 펠비스가 바닥으로 너무 내려감.
type: feedback
originSessionId: 5c97ced7-4741-424f-8e22-cc55efda4867
---
# Move 프로필 MaxOffset은 10 유지

## 규칙

`PC_01_AnimLayer_IK` 의 `PelvisSettingsMove.MaxOffset = 10`을 **올리지 말 것**. 측면 경사 튜닝 시에도 이 값은 건드리지 않음.

**Why:** 2026-04-23 세션에서 Claude가 MaxOffset 10→18 권장했으나 사용자가 반박: "계단 오르막에서 펠비스가 바닥으로 너무 내려가는 문제가 있어." MaxOffset은 수직 offset 양방향 허용 — 값이 크면 오르막에서 낮은 쪽 발 plant plane 맞추려고 골반이 아래로 drop함. 낮은 값(10)은 이 drop을 캡으로 막는 의도적 설계.

**How to apply:**
- Move 프로필 MaxOffset 변경 제안 금지
- 계단/오르막 컨텍스트에서는 MaxOffset보다 `HeelLiftRatio`를 올려 heel lift를 선호하게 유도 (pelvis drop 대신)
- 다른 PelvisSettings 파라미터 권장은 유효:
  - `MaxOffsetHorizontal` 15→25 (측면 Roll 트리거 억제, MaxOffset과 무관)
  - `bDisablePelvisOffsetInAir` False→True (공중 튐 방지)
  - `HeelLiftRatio` 0.5→0.6 (오르막 pelvis drop 간접 완화)

## 참고

- 현재 SB2 설계: Default=50 / Move=10 / Prone=0 — 이 구조 자체가 잘 튜닝된 상태
- UE 5.7 소스 주석 근거: `MaxOffset: "Max vertical offset from the input pose for the Pelvis. Reaching this limit means the feet may not reach their plant plane"` — 발이 plant plane 못 닿아도 pelvis 위치는 유지됨
- 관련 메모리: `project_pc01_pelvis_profiles.md` (3 프로필 값)
