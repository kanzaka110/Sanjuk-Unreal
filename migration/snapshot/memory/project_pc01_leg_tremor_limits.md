---
name: PC_01 오버레이 시 다리 Tremor — UE 5.7 엔진 한계
description: Overlay ON 상태에서 LegIK 출력 다리 떨림 문제. 파라미터/구조/Control Rig/Inertialization 모두 무효 — 엔진 C++ 커스텀 AnimNode 필요.
type: project
originSessionId: a42ec142-c2aa-46c8-806c-b19970eff37b
---
## 증상
- Overlay 애니메이션(Guard 등) ON 상태에서 LegIK이 다리를 프레임당 미세 변동 → 상시 tremor
- LegIK Alpha=0으로 끄면 떨림 없음 but 슬로프/계단 IK 품질 손실
- PrimaryIK=LegIK (FootPlacement가 VB ik_foot 제어 → LegIK이 체인 풀이)

## 원인 (확정)
1. FootPlacement 출력 (pelvis 보정 + VB ik_foot 위치)가 overlay 체인 거쳐 오는 동안 sub-cm 단위 변동
2. LegIK FABRIK이 ReachPrecision=0.01(1cm) 이하의 입력 변동에도 매 프레임 재솔브
3. UE 5.7 표준 AnimGraph 노드에 **continuous temporal smoothing**이 존재하지 않음
   - Inertialization/DeadBlending: blend 이벤트(state 전환) 트리거 기반 — 상시 tremor엔 무효
   - BlendStack: Motion Matching용, smoothing 아님
4. Control Rig 커스텀 (LegSmooth, TwoBoneLegIK) — Python API 사용 시 BP 변수 추가 단계에서 크래시 발생 경로 있음

## 무효화된 시도 (2026-04-22 세션 전체)
| # | 시도 | 결과 |
|---|------|------|
| 1 | LegIK bSmoothRootBone, bEnableKneeTwistCorrection, HingeRotationAxis 등 플래그 | 무효 |
| 2 | LegIK ReachPrecision=2.0, MaxIterations=1 (극단 damping) | 부분 완화, 불충분 |
| 3 | FootPlacement AnkleTwistReduction, PelvisSettings 튜닝 | 무효 |
| 4 | IK를 Overlay 앞으로 이동 | 슬로프 IK 약화, 무효 |
| 5 | TwoBoneIKSimplePerItem Control Rig 교체 | 축 mirror 지옥, 동일 tremor |
| 6 | Custom smoothing Control Rig (BP 변수 + Lerp) | API 불일치로 크래시 |
| 7 | AnimGraphNode_Inertialization 삽입 (LegIK 뒤) | 무효 (이벤트 기반) |

## 남은 경로
### A. 수용
상시 tremor를 콘솔 스펙 허용 범위로 보고 종료. 현재 PC_01_ABP엔 효과 없는 Inertialization_0 (x=4900) 남아있음 — 제거 권장.

### B. SB2 엔진팀에 Custom AnimNode 요청
```cpp
struct FAnimNode_TransformSmoothing : public FAnimNode_SkeletalControlBase {
    UPROPERTY(EditAnywhere) float HalfLife = 0.02f;
    UPROPERTY(EditAnywhere) TArray<FBoneReference> BonesToSmooth;
    TMap<FBoneReference, FTransform> PrevTransforms; // frame-to-frame state
}
```
Exponential smoothing (`new = lerp(prev, cur, alpha)`) per bone, bone array에 thigh/calf/foot (L/R) 추가. 엔진팀 1~2일 작업.

### C. 아트/기획 재검토
Overlay 작동 중 로코모션 요구 완화 또는 overlay를 MM DB 분리 방식으로 재설계.

**Why:** UE 5.7 엔진 한계를 확인했으므로 파라미터 튜닝은 비용 낭비. C/B 중 선택해야 함.

**How to apply:** 
- 유사 증상 발생 시 이 메모리부터 확인해서 재시도 낭비 방지
- Overlay+IK+locomotion 조합 설계 시 처음부터 smoothing AnimNode 요구사항으로 포함
