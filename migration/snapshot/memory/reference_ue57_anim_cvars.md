---
name: UE 5.7 AnimNode 디버그 CVar 치트시트
description: FootPlacement/OrientationWarping/SlopeWarping/LegIK 내장 CVar 목록. ABP bDrawDebug 대신 런타임 콘솔 토글로 대체 가능.
type: reference
originSessionId: c0b37efc-71b6-4348-a2e2-afba5093f18e
---
UE 5.7 Epic 공식 소스 확인 결과. 표준 AnimNode는 `bDrawDebug` 플래그 외에 콘솔 CVar가 내장됨.
네이밍 패턴: `a.AnimNode.<NodeName>.Debug` + `.Enable`

**FootPlacement** (AnimNode_FootPlacement.cpp):
- `a.AnimNode.FootPlacement.Enable` (bool, default true)
- `a.AnimNode.FootPlacement.Enable.Lock` (bool, default true) — 발 잠금만 분리
- `a.AnimNode.FootPlacement.Debug` (bool) — 메인 비주얼
- `a.AnimNode.FootPlacement.Debug.Traces` (bool) — 지면 트레이스 라인
- `a.AnimNode.FootPlacement.Debug.DrawHistory` (int) — 과거 N프레임 히스토리

**OrientationWarping** (AnimNode_OrientationWarping.cpp):
- `a.AnimNode.OrientationWarping.Enable` (bool)
- `a.AnimNode.OrientationWarping.Debug` (bool)
- `a.AnimNode.OrientationWarping.Verbose` (bool) — 그래프 텍스트 디버그
- `a.AnimNode.OrientationWarping.Debug.Transparency` (bool) — 블렌드 가중치 기반 투명도

**SlopeWarping** (AnimNode_SlopeWarping.cpp):
- `a.AnimNode.SlopeWarping.Enable` (int32, default 1)
- `a.AnimNode.SlopeWarping.Debug` (int32, default 0)

**LegIK** (AnimNode_LegIK.cpp):
- `a.AnimNode.LegIK.Enable` (int32, default 1)
- `a.AnimNode.LegIK.Debug` (int32, default 0)
- `a.AnimNode.LegIK.MaxIterations` (int32, 0=노드 기본값)
- `a.AnimNode.LegIK.TargetReachStepPercent` (float, default 0.7)
- `a.AnimNode.LegIK.PullDistribution` (float, default 0.5) — 0=발, 0.5=밸런스, 1=힙

**사용법:** PIE 중 `~` → 위 명령어 입력. 값 0/1 또는 숫자 직접 지정.

**장점 vs ABP bDrawDebug:**
- 재컴파일 불필요
- 런타임 실시간 토글
- 여러 노드 동시 비교 쉬움
- 빌드 에셋에 흔적 안 남음 (Details 체크박스는 저장됨)

**커스텀 노드(FootClamp 등)에 추가하는 법:**
```cpp
static TAutoConsoleVariable<bool> CVarFootClampDebug(
    TEXT("a.AnimNode.FootClamp.Debug"), false,
    TEXT("..."));
// Evaluate에서 GetValueOnAnyThread() 체크
```

**검증:** 2026-04-20, Epic GitHub 5.7 브랜치 cpp 원문에서 직접 추출.
