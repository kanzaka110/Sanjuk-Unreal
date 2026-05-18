---
name: PC_01 FootClamp 전투/비전투 분기 작업 (옵션 B 폐기 → 옵션 A 폴백)
description: 전투 대기에서 FootClamp ON 시 다리 밀림. 클램프 값 분기로 해결 시도(옵션 B) 실패 → 노드 Alpha OFF 분기(옵션 A)로 전환. 미완 — 사용자 수동 wire 단계 남음.
type: project
originSessionId: 915e0a07-84b5-49c5-85a3-b1bae72cd4e4
---

## 증상

- **비전투** (Peaceful) 대기/이동: FootClamp ON 정상. 슬로프 발목 보호 작동
- **전투 대기** (Battle + Idle): FootClamp ON 시 살짝 다리 밀림
  - 클램프 (-180, 180) no-op 값으로도 잔존
  - **ControlRig 노드 Alpha=0 (노드 자체 OFF)** 시 즉시 정상

## 원인 — FootClamp 노드 알고리즘 자체의 부작용

클램프 값 무관. 노드 실행 자체가 발목 transform 미세 변경:
- Quat → ZYX Euler → Quat 왕복으로 회전 손실 (Gimbal lock 근방 분해 발산 가능)
- bPropagateToChildren=True로 발목 미세 변화가 ball/toe까지 전파
- SetTransform Translation을 GetTransform(bone) 원본으로 강제 복원 — IK가 만든 발 위치에 영향
- bUseUEHandyness 부호 반전 효과 누적

비전투 모션은 발목 자세가 단순/대칭이라 Euler 분해 결과 안정. 전투 모션은 비대칭/비표준 자세라 부작용 드러남.

## 폐기된 옵션 B (변수 분기, 시도 후 실패)

ABP에 변수 6개 추가됨 (현재 미사용 상태로 잔존):

에셋: `/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP`
카테고리: `Foot Placement / FootClamp`, 타입: FVector2D, instance_editable=True

| 변수명 | Default (X=Min, Y=Max) |
|---|---|
| Angle_Clamp_Pitch_NonCombat | (-5, 10) |
| Angle_Clamp_Roll_NonCombat | (-10, 10) |
| Angle_Clamp_Yaw_NonCombat | (-15, 15) |
| Angle_Clamp_Pitch_Combat | (-12, 22) |
| Angle_Clamp_Roll_Combat | (-25, 25) |
| Angle_Clamp_Yaw_Combat | (-25, 25) |

ABP 변수 수: 129 → 135. 컴파일 success, P4 lock으로 save_asset 실패.

**시도 결과:** 1단계(보수) → 2단계(표준) → (-180, 180) 모두 다리 밀림 잔존. 옵션 B 폐기.

## 채택된 옵션 A (노드 Alpha 분기)

**게이트:**
```
Alpha = (AnimStance == CHARACTER_STANCE_BATTLE
         AND MovementState == IDLE) ? 0.0 : 1.0
```

**enum 값 (실측):**
- `SBCharacterStance::CHARACTER_STANCE_BATTLE` = 2
  - 전체: NONE=0, PEACEFUL=1, BATTLE=2, GROGGY=3, DOWN=4, DEAD=5, AIRBORNE=6, NUM=7
- `E_SBMovementState::IDLE` = 0

**효과 매트릭스:**

| Stance | MoveState | Alpha | 효과 |
|---|---|---|---|
| Peaceful | any | 1.0 | FootClamp ON (슬로프 보호 유지) |
| Battle | **Idle** | **0.0** | **FootClamp OFF (대기 다리 밀림 해소)** |
| Battle | Walk/Run/공격 | 1.0 | FootClamp ON |
| 그 외 | any | 1.0 | FootClamp ON |

전투 walk/run/공격에서 다리 밀림 보고되면 조건 확장 (BATTLE + (IDLE OR WALK))으로 완화.

## 2026-04-30 진행 상황

**RotationOrder 버그 해결 (근본 원인):**
- `PC_01_CtrlRig_FootClamp`: ToEuler=YXZ / FromEuler=ZYX 불일치 → ZYX→YXZ 통일
- (-180,180) no-op 후 밀림 없음 확인 → Alpha=0 방식 폐기, 클램프 값 분기로 전환

**IK Layer 현재 변수 상태 (property_count=84):**
- NonCombat 3개: Pitch(-5,10), Roll(-15,15), Yaw(-10,10) ← 신규 생성
- Combat 3개: Pitch(-20,35), Roll(-25,25), Yaw(-20,20) ← 신규 생성
- Default/Battle 각 3개 (구형, 정리 대상): Default=NonCombat값, Battle=(-180,180) no-op
- FootClampAlpha=1.0 (ABP에서 SwitchEnum으로 Battle→0.0 설정 중 → 제거 필요)

## 미완료 (다음 세션)

1. **ABP 저장** — 사용자가 PC_01_ABP 에디터에서 Ctrl+S, P4 Check Out 수락 (변수 6개 디스크 반영)
2. **IK Layer Alpha wire** — PC_01_AnimLayer_IK AnimGraph에서:
   - ControlRig 노드 Details: `Alpha Input Type = Float` 확인, Alpha 핀 노출
   - `Get AnimStance` + `== BATTLE` (bool A)
   - `Get MovementState` + `== IDLE` (bool B)
   - `AND(A, B)` → `Select<Float>(0.0, 1.0)` → ControlRig.Alpha
3. **Compile + Save**
4. **PIE 검증** — Peaceful idle/walk, Battle idle, Battle walk/공격 각 케이스
5. **잔여 변수 6개 처리 결정** — 옵션 A 검증 완료 후 보존 vs 삭제 (Task #12)

## 관련 컨텍스트

- 같은 세션에 PlantSettings.LockType 처리: PivotAroundAnkle → PivotAroundBall로 발목 고정 해소 (`feedback_plant_settings_locktype_ankle_pitfall.md`)
- IK Layer LinkedAnimLayer 노드: `AnimGraphNode_LinkedAnimLayer_0` (구 메모리 `_5`는 stale)
- IK Layer PelvisSettings 4프로필 (Default/Move/Traversal/Prone) — 구 메모리 3프로필은 stale
- FootClamp Rig 변수 default 실측 (옵션 A 폴백 시점): Pitch(-5,10), Roll(-10,10), Yaw(-15,15) — 구 메모리 (-180,180) no-op은 stale (누군가 슬로프 보호용으로 좁힘)

## 산출물

- Before dump: `dumps/pc01_abp_vars_before.json` (129 vars)
- After dump: `dumps/pc01_abp_vars_after.json` (135 vars)

**Why:** 사용자(SB2 애니 TA) 2026-04-29 진행. 옵션 B 단계적 시도 후 실증으로 노드 자체가 원인임 확인 → 옵션 A 폴백 결정. Alpha=0 검증된 상태에서 stop. 다음 세션에서 wire 작업 + PIE 검증.

**How to apply:** 다음 세션 시작 시 이 메모리 + `feedback_plant_settings_locktype_ankle_pitfall.md` 함께 참조. wire 작업 = IK Layer 안 ControlRig.Alpha 핀에 stance+movementstate 분기 결과 wire. 결과에 따라 조건 확장.
