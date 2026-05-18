---
name: project-pc01-evade-interpolation
description: 2026-05-18 PC_01 회피 시 다리 IK 지연 해결 — HasEvade 게이트 + InterpolationSettingsEvade 변수 추가. UnplantStiffness 강화.
metadata: 
  node_type: memory
  type: project
  originSessionId: 9dcc5175-e415-47ad-96d0-959bb0242e16
---

# PC_01 회피 시 FootPlacement 다리 지연 해결

## 문제

회피 같은 순간적 빠른 움직임 시 발이 ground 에 latch 되어 메시 따라오지 못함 (IK lag). 시각적으로 다리만 뒤에 끌리는 현상.

## 핵심 발견

PC_01 의 `AnimGraphNode_FootPlacement.Settings` (InterpolationSettings) 가 **inline default 가 아니라 BP 함수에서 동적 공급**:
- `GetFootPlacementInterpolationSettings` (pure function, is_pure=True)
- 3개 instance 변수 분기: `InterpolationSettingsDefault` / `InterpolationSettingsStops` / `InterpolationSettingsFullBody`
- 분기 조건: BlendStackInputs.Tags Contains + IsFullBodySlotActive

**중요**: AnimGraph 노드의 inline default 수정은 무시됨. 분기 변수의 default 만 적용.

## 처방

`GetFootPlacementInterpolationSettings` 함수에 HasEvade 게이트 추가 (가장 바깥):

```
FunctionEntry
  → IfThenElse_3 (HasEvade) [NEW]
    True  → FunctionResult_3 → InterpolationSettingsEvade [NEW VAR]
    False → IfThenElse_2 (IsFullBodySlotActive)
      ... (기존 트리 보존)
```

## 신규 변수: InterpolationSettingsEvade

| 멤버 | Default | Evade | 배수 |
|---|---|---|---|
| UnplantLinearStiffness | 250 | **600** | ×2.4 |
| UnplantAngularStiffness | 450 | **700** | ×1.6 |
| UnplantLinearDamping | 1.0 | **0.5** | ÷2 |
| 나머지 | (Default 와 동일) | | |

보수적 시작값 — 효과 부족 시 더 강화 (1000/1000/0.3), 떨림 시 약화 (400/500/1.0).

## 스크립트

`scripts/add_evade_interpolation_settings.py` — 변수 추가 + Branch 추가 + wire 6개 연결. compile success / 0 errors.

## 작업 메모

- 새 FunctionResult 노드 만들었지만 ReturnValue pin auto-gen 안 됨 → monolith 가 기존 dangling FunctionResult_3 에 자동 wire 라우팅. 신기한 동작이지만 결과 정확.
- save 안 함 — 사용자 Ctrl+S 필요.

## 후속 작업 / 확장

PC_01 의 `PlantSettings` 도 유사 구조 (`GetFootPlacementPlantSettings` 함수) — 회피 케이스 추가 강화 시 같은 패턴으로 `PlantSettingsEvade` 추가 가능. 주요 멤버:
- `LockType` = `PivotAroundBall` ([[feedback-plant-settings-locktype-ankle-pitfall]])
- `MaxLockedTime` 단축 (0.3 → 0.10)
- `AnkleTwistReduction` 0

## 관련

- [[reference-foot-placement-source-5-7]] — UE 5.7 FootPlacement ground truth
- [[reference-foot-placement-gasp]] — GASP 4단계 파이프라인
- [[project-pc01-pelvis-profiles]] — Pelvis 도 같은 3프로필 패턴
- [[project-pc01-hasevade-pipeline]] — HasEvade 트리거 시스템
- [[feedback-plant-settings-locktype-ankle-pitfall]] — PivotAroundAnkle 함정
- [[project-pc01-anim-rec-unmapped-added]] — ANIM_REC 의 `he/hed` 필드로 회피 추적
