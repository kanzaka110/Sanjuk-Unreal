---
name: PC_01_CtrlRig_FootClamp 구조 + 수정 내역
description: PC_01의 Foot Rotation Clamp Control Rig. T3D 파싱으로 구조 분석 + Clamp 축 매핑 스왑 + Clamp 범위 전체 개방으로 발목 꺾임 해결.
type: project
originSessionId: ebbc629e-a8a1-40ce-8885-386c1ceb4efe
---
**에셋 경로:** `/Game/ART/Character/PC/PC_01/Rig/PC_01_CtrlRig_FootClamp`
**형태:** ControlRigBlueprint, Forwards Solve only (Backwards Solve 없음)

**기능 의도:** `BoneNames` 배열의 각 본을 순회하며 부모 대비 로컬 회전을 Euler로 변환 → 축별 Clamp → 다시 Quat으로 변환하여 본 Rotation만 덮어쓰기. Translation/Scale은 원본 유지. "발목 등 Rotation 범위 보정" 용.

**구조 (T3D 실측):**
```
BeginExecution
  → For_Each (BoneNames)
      per bone:
        1. Current  = GetTransform(bone, Global)
        2. Parent   = GetTransform(Parent(bone), Global)
        3. Local    = Inverse(Parent) × Current
        4. EulerL   = QuaternionToEuler(Local.Rot, ZYX)
        5. EulerC   = Clamp(EulerL, Min/Max)
        6. QuatC    = QuaternionFromEuler(EulerC, ZYX)
        7. LocalC   = MakeTransform(Local.Trans, QuatC, Local.Scale)
        8. GlobalC  = Parent × LocalC
        9. Set Transform:
             Rotation = GlobalC.Rotation
             Translation = GetTransform(bone).Translation (원본)
             Scale = GetTransform(bone).Scale (원본)
             bPropagateToChildren=True
```

**Clamp 노드 축 매핑 버그 (수정 전):**
- Clamp.X ← Angle_Clamp_Pitch 변수 (X축은 Roll이어야 함)
- Clamp.Y ← Angle_Clamp_Roll 변수 (Y축은 Pitch이어야 함)
- Clamp.Z ← Angle_Clamp_Yaw 변수 (정상)

UE 5.7 `EulerFromQuat(ZYX)` 결과 벡터 축 = X:Roll, Y:Pitch, Z:Yaw이므로 Pitch/Roll 변수가 서로 교차된 축에 연결된 상태였음.

**수정 (2026-04-17):**
- 스크립트: `scripts/fix_footclamp_rig.py` (스왑), `scripts/revert_footclamp_rig.py` (원복)
- Clamp_1 노드의 X/Y Min/Max 4개 링크를 스왑:
  - Minimum.X, Maximum.X ← VariableNode_4(Pitch) → **VariableNode_2(Roll)** 로
  - Minimum.Y, Maximum.Y ← VariableNode_2(Roll) → **VariableNode_4(Pitch)** 로
- Clamp 변수 기본값을 모두 `(-180, 180)` 로 개방 → Clamp 기능 사실상 비활성화

**구조 실측 (2026-04-30 uasset 스캔 + Monolith dump — 최신 ground truth):**
- 노드 25개. ForEach(BoneNames=[foot_l, foot_r]) 순회
- `ToEuler_1.RotationOrder` = **YXZ** (분해)
- `FromEuler.RotationOrder` = ~~ZYX~~ → **YXZ** (2026-04-30 수정, 아래 참조)
- `Clamp_1` (VectorClamp): X←Roll var, Y←Pitch var, Z←Yaw var 결선
- `SetTransform.bPropagateToChildren=True`

**2026-04-30 수정 — RotationOrder 불일치 버그 해소:**
- 버그: ToEuler=YXZ / FromEuler=ZYX → 분해/합성 순서 달라 (-180,180) no-op도 identity 아님 → 포즈 무관 발목 왜곡
- 수정: `RigVMFunction_MathQuaternionFromEuler.RotationOrder` ZYX → **YXZ**로 통일
- 결과: compile success, save success (P4 체크아웃 포함), 다른 핀 연결 무변화
- 수정 후: round-trip identity → 클램프 범위 안에서만 실제 제한 발생
- post dump: `C:\Dev\Sanjuk-Unreal\dumps\footclamp_graph_data_post.json`

**현재 Clamp 변수 default (CDO 실측):**
- `Angle_Clamp_Pitch` = (-5, 10)
- `Angle_Clamp_Yaw` = (-10, 10)
- `Angle_Clamp_Roll` = (-15, 15)

**다음 PIE 검증 사항:**
1. Battle idle + 평지: Alpha=1.0으로 복원 후 발목 꺾임 없는지 확인 (RotationOrder 수정 효과)
2. 경사: Alpha=1.0으로 발목 제한 유지되는지 확인
3. 정상이면 ABP의 SwitchEnum(Battle→FootClampAlpha=0.0) 로직 제거 가능

**Why:** RotationOrder 불일치(YXZ↔ZYX)가 (-180,180) no-op 클램프에서도 꺾임이 남았던 진짜 원인. 통일로 근본 해결.

**How to apply:**
- Clamp Rig 디버깅 순서: Rig on/off 격리 → RotationOrder ToEuler/FromEuler 동일성 확인 → 축 매핑 확인 → 값 범위 조정
- Monolith `set_pin_default`는 `node_id` + fully-qualified `pin_name` 형식 필요. ControlRig RigVM도 blueprint_query로 핀 변경 가능.
- ToEuler와 FromEuler의 RotationOrder는 항상 동일하게 유지 (짝으로 동기화 필수).
