# PC_01 렛지 핸드IK v2 스크립트 (2026-07-13 세션)

CR-내부 래치(FootLock 패턴) 기반 핸드IK 시스템의 빌드/튜닝/디버그 스크립트.
실행: 에디터 콘솔 `py "<경로>"` 또는 Monolith `editor_query run_console_command`.

## 아키텍처 (상세: 메모리 project-pc01-ledge-dangle-cr)

```
[애님] ledge_hand_ik_l/r 커브 (166종, AM_SBLedgeHandIK 모디파이어로 베이크)
[ABP]  GetCurveValue → 비대칭 FInterp(상승10/하강25) + 정착 디바운스(FInterp 8, >0.75)
       + 양손 준정지 AND 결합 + 알파 래칫(min(현재,커브)) → LedgeHandIKAlphaL/R
       LedgeMeshToWorld(월드변환), ledge_pelvis_spring → CharVelocity 게이트
[CR]   PC_01_CtrlRig_LedgeDangle: 알파<0.9 → HandTarget:=월드(애님손) 추적 / ≥0.9 동결
       Lerp.B=역변환(HandTarget), 폴벡터=애님 lowerarm 위치(Location), HandZBias 노브
```

## 빌드 (신규 재적용 순서 — 크래시 등으로 CR 소실 시)
1. `build_cr_latch.py` → `build_cr_latch2.py` — CR 래치 (수동 선행: 변수 MeshToWorld/Set노드 2개)
2. `fix_ik_pole.py` — 폴벡터 = 애님 팔꿈치 Location
3. `add_hand_zbias.py` — 손 타깃 Z 오프셋 노브 (기본 0)
4. `raise_latch_threshold.py` — 래치 동결 문턱 0.9
5. `zero_offset_z.py` — 댕글 오프셋게인 Z=0 (펠비스 수직 차단)
6. (선택) `build_pelvis_clamp.py` — 펠비스 Z 하한 클램프 (유저 롤백 상태, MaxDrop 노브)

## 튜닝 노브
- ABP 핀 디폴트: 정착문턱 0.35(Less B), 디바운스 0.75/속도8, 알파 상승10/하강25
- CR: HandZBiasL/R.B(Z), LatchLessL/R.B(0.9), PvClampLimit.B(무력화=200)
- 모디파이어: FlightSpeedThreshold 140(MoveToIdle 4종=10), 램프 2/3

## 디버그
- `handik_v2_debug.py` — 손 구체(빨강0↔초록1)+알파 텍스트 (토글)
- `probe_ikv2.py` — 커브/알파/손변위 로그 → ikv2.log
- `probe_pelvis_dip.py` — 펠비스 월드/캡슐/상대Z 분해 → pelvis_dip.log
- `toggle_handik.py` — 핀 IK 온오프 (bLedgeHandPinDisabled — v1 유물, v2 재확인 필요)
- LedgeDebugs 그래프(ABP)에 인게임 마커 내장 (LedgeDebug 토글)

## ⚠ 함정 (재발 방지)
- CR 수정 후 PIE 진입 전 **무조건 저장** (크래시 소실 이력)
- BP_EM_Ledge 컴파일 금지 — SBZoneEnvActor::BeginPlay:467 널참조 크래시
- CR 애님노드 노출 핀은 미연결이어도 디폴트를 매프레임 푸시 — 내부래치 변수(HandTargetL/R)는 핀 언체크 필수
- K2Node ID는 에디터 재시작 간 불안정 — 배선 전 search_nodes 재탐색
- 커브 같은 프레임 키 2개 = SetCurveControlKey 어설션 즉사
