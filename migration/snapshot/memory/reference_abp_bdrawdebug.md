---
name: ABP 노드 bDrawDebug로 플레이 중 시각 디버그
description: FootPlacement/LegIK/ControlRig 등 ABP 노드 Details 패널의 bDrawDebug 켜면 PIE 월드에 기즈모·라인이 뜸. ShowDebug Animation보다 직관적.
type: reference
originSessionId: c0b37efc-71b6-4348-a2e2-afba5093f18e
---
UE 애니메이션 노드 대부분은 Details 패널에 `bDrawDebug` (또는 `Debug Draw`) 플래그를 노출.
켜면 PIE 플레이 화면에 해당 노드의 계산 결과를 3D 기즈모·라인으로 오버레이.

**지원 노드 (확인됨):**
- `AnimNode_FootPlacement` — 발 IK 타겟, ground trace, pelvis offset 시각화
- `AnimNode_LegIK` — 다리 체인 + 타겟 위치
- `AnimNode_ControlRig` / Control Rig 내부 노드 — 본 변환, 솔버 결과
- `KawaiiPhysics` 노드 — 시뮬레이션 본 + 콜리전
- 커스텀 솔버 노드 다수 (FootClamp 포함 가능)

**사용법:**
1. ABP 열기 → AnimGraph에서 대상 노드 선택
2. Details 패널에서 `bDrawDebug` / `Debug Draw` 체크
3. ABP 컴파일 + 저장
4. PIE 실행 → 해당 캐릭터 월드에 디버그 오버레이

**ShowDebug 콘솔과의 차이:**
- `ShowDebug Animation`: 텍스트 오버레이 (상태명, 가중치 값)
- `bDrawDebug`: 3D 공간에 기즈모 (IK 타겟, 트레이스 라인, 본 축)
- **둘 다 켜두면 전체 그림 파악 최적**

**주의:**
- 프로덕션 빌드 전 반드시 끄기 (퍼포먼스)
- 노드별로 개별 플래그 — State Machine 전체 단위 아님
- 일부 노드는 `DrawDebug` 카테고리 아래 세부 플래그 (색상, 스케일 등) 별도
