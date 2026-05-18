---
name: UE 5.7 Quaternion↔Euler 변환 축 매핑
description: UE 5.7의 AnimationCore::EulerFromQuat / QuaternionFromEuler 에서 Result FVector의 축 의미 및 bUseUEHandyness 부호 반전. RigVM Math 노드와 Control Rig에서 Euler clamp 구현 시 참조.
type: reference
originSessionId: ebbc629e-a8a1-40ce-8885-386c1ceb4efe
---
UE 5.7 `AnimationCore::EulerFromQuat(Quat, RotationOrder, bUseUEHandyness=true)` 의 결과 FVector 축 의미.

**소스 위치:** `Engine/Source/Runtime/AnimationCore/Private/AnimationCoreLibrary.cpp:263+`

**Result 벡터 축 매핑 (ZYX order 기준):**
- `Result.X` = **Roll**  (X축 회전)
- `Result.Y` = **Pitch** (Y축 회전)
- `Result.Z` = **Yaw**   (Z축 회전)

**bUseUEHandyness 효과 (기본값 true):**
```cpp
if (bUseUEHandyness) {
    Result.X = -Result.X;   // Roll 부호 반전
    Result.Y = -Result.Y;   // Pitch 부호 반전
}
return Result * 180.0 / DOUBLE_PI;
```
→ Roll/Pitch 값이 실제 각도와 **부호 반대**로 저장됨 (Yaw만 정상 부호).

**RigVM Math 노드 동작:**
- `FRigVMFunction_MathQuaternionToEuler_Execute()` 는 `AnimationCore::EulerFromQuat(Value, RotationOrder)` 호출 (3번째 인자 생략 → 기본 true).
- `FRigVMFunction_MathQuaternionFromEuler_Execute()` 도 동일 기본 처리.
- 둘 다 bUseUEHandyness=true이므로 round-trip (Quat→Euler→FromEuler)은 identity.

**Clamp 노드 설계 시 유의:**
- Euler 벡터의 X/Y에 Clamp 적용 → 실제 Roll/Pitch는 부호 반전된 상태로 제한됨
- **대칭 범위** (예: -30~30) 설정 시 부호 영향 없음
- **비대칭 범위** (예: -30~20) 설정 시 실제론 (-20~30)처럼 작동 → 의도와 반대
- Clamp 변수 설정할 때 이 부호 반전 고려 필요

**How to apply:**
- Control Rig에서 Pitch/Roll Clamp 설정 시 비대칭 범위는 한 번 더 확인. 의도와 다르면 부호 뒤집기.
- 실제 애니 각도 범위를 확인하려면 PIE + ShowDebug Animation 으로 실측이 가장 확실.
- Clamp 문제 디버깅 시 범위 `(-180, 180)`으로 개방해서 no-op 상태 먼저 확인 → 원인이 Clamp인지 다른 로직인지 격리.
