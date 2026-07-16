# PC_01 렛지 핸드IK v2→v3 스크립트 (2026-07-13~14 세션)

핸드IK 시스템의 빌드/튜닝/디버그 스크립트.
실행: 에디터 콘솔 `py "<경로>"` 또는 Monolith `editor_query run_console_command`.

## 아키텍처 v3 — 2026-07-14 확정 (상세: 메모리 project-pc01-ledge-dangle-cr)

```
[애님]  ledge_hand_ik_l/r 커브 (166종, AM_SBLedgeHandIK 모디파이어)
[타깃]  Idle 실측 상수(벽/봉 SelectVector, bPickA=LedgeFrontBlocked)
        wall L=(5.23,-3.75,167.07) R=(-6.04,-3.14,166.67)
        wallless L=(7.19,-1.85,166.34) R=(-7.59,-2.02,166.21)
[래치]  ABP Ledge fn 월드래치 (LedgeHandWorldL/R):
        릴리즈(생커브<0.5)      = 손소켓 월드 추적
        플랜트+이동(vel≥15)     = 월드 동결 (그립 고정)
        플랜트+정지(vel<15)     = WorldNow(M2W×상수)로 VInterp 15 수렴
        → InverseTransformLocation → LedgeHandIdleCompL/R → CR 핀
[알파]  커브 → FClamp → 비대칭 FInterp(상승7/하강15) → LedgeHandIKAlphaL/R
[CR]    Lerp.B ← Get HandTargetL/R 직결 (구 내부래치 삭제됨)
        이펙터 회전=애님 손 회전, 폴=애님 lowerarm Location
[발IK]  FootPlacement 렛지 게이트 2중:
        ①SetSmoothedFootIKWeight 함수 Lerp(곱,0,게이트)
        ②Ledge fn 꼬리에서 SmoothedFootIKWeight(뒤 공백!) 직접 0
```

### v3 핵심 실측 (재발 방지)
- **FootPlacement가 "IK 미세 움직임" 주범** — CVar 격리로 gap 8.3→0.1cm. 렛지 중
  UpdateVariables 스무딩 미호출 → SmoothedFootIKWeight 동결(잔값×거대보정=5~8cm 딥)
- **LedgeCalcVelocity 스케일**: 이동 중 4~94(avg30) — 실캡슐속도 아님. 정지판정 15가 정답 (200=홀드 전멸)
- **릴리즈 자가오염**: 알파 하강 느리면(8) 스윙 손을 IK가 끌고 추적이 그걸 따라감 → 재플랜트 31cm 오차. 하강 15~20
- **플랜트 동결 1프레임 지연**(소켓=전프레임 포즈): 고속스윙 시 ~8cm 뒤 동결 — 정지수렴이 마스킹, 근본 해결은 CR 내부 캡처
- **커브 무죄**: ShortL_Wallless 스태거 정상(L 0.067~0.37 / R 0.267~0.53). 0.4s 컷이 R 안무 절단 → 엔지니어 요청(Briefing/2026-07-14)

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

## 좌/우 벌어짐 비대칭 수정 (7/14 저녁)
- 증상: 우측 이동 시 손 벌어짐 과다 (좌측은 정상)
- 원인: ShortR/ShortR_Wallless 커브가 좌측과 다른 시점/파라미터 베이크 잔재 — 애님 자체는 완전 미러(속도 프로파일 일치)인데 커브만 비대칭. ShortR(벽)은 R 릴리즈 0.033~0.633(거의 전체)+L 릴리즈가 0.4s 컷 뒤 → 이동 내내 L 구그립 동결+R 스윙 추적 = 벌어짐 최대. Wallless는 후행 L 플랜트 0.567(좌측은 0.467) → 컷 시점 미드플라이트(226cm/s)에 월드동결
- 수정: `fix_shortr_mirror_curves.py` — 좌측(승인 기준) 커브를 우측 애님에 미러 이식. 좌측 에셋 무수정. 원본 키 백업 = `ledge_lr_compare.json`
- 진단: `ledge_lr_compare.py` — Short/MoveToIdle 8종 커브+궤적+플랜트엣지 일괄 덤프
- ⚠ 자동 재베이크 금지: 벽 변형은 플라이트 94~207 vs 드리프트 90~142가 겹쳐 문턱 140이 나이프엣지 — 미러가 깨진 근본 원인

## v5 — IK 타깃 커브 구동 (7/14 밤)
- 신규 커브 `ledge_hand_move_l/r`: **0=이동전 그립, 1=이동후 그립** — 타깃 위치를 애님 커브로 직접 안무 (팔꼬임 원인=1틱 타깃 스위치 해소)
- ABP: 타깃 = VLerp(Anchor, Dest, 커브). Anchor/Dest 전부 무상태 (WorldNow ∓ 방향×진행/남은거리, 유닛무브 아니면 WorldNow)
- 초기 베이크 = 플라이트 창 스무스텝 (`bake_move_curves.py`) — 에디터에서 키 수동 튜닝 전제
- 알파는 별개 유지: bActive × ledge_hand_ik 커브 (릴리즈=IK off)
- 모디파이어(`sb_ledge_hand_ik.py`)도 move 커브 베이크 지원 (창 없으면 상수 0) — ⚠ apply 시 ik 커브도 재베이크되므로 **수동 튜닝된 벽 Short 2종엔 apply 금지**

## 모디파이어 v8 — 네이티브 노드 (2026-07-15, 파이썬 커맨드 폐기)
- AM_SBLedgeHandIK = 순수 BP 62노드. **파라미터 템플릿 베이크** (자동 창검출 폐기)
- 이름 3분류: `ToLadder/End/BackwardJump`→이탈(ik 1→0), `Idle`→정지(ik 1), 그 외→이동(ik 창 + move 램프)
- 파라미터(인스턴스): HandMoveStartL/EndL/StartR/EndR (⚠7/16 유저 rename: Move*→HandMove*), FootMoveStart/End ×4,
  ReleaseRampTime(0.07)/PlantRampTime(0.1), ExitHoldTime(0.05)/ExitFadeTime(0.1), PelvisMinSpeed(60)/PelvisFallFrames(6)
- **v9.10 함수화** (`mod_refactor_functions.py`): EventGraph=분류+콜 15노드. 함수 5개:
  `RemoveLedgeCurves`(9커브, Apply전처리+Revert 공용) / `WriteExitCurves` / `WriteIdleCurves` / `WriteMoveCurves` / `BakePelvisSpring`
- pelvis_spring 통합(v9.9, `mod_pelvis_rebuild.py`): 2패스 샘플링 엔벨로프 — **⚠ Kismet 배열 와일드카드 핀은 RPC 연결이 컴파일에서 정리됨** → 배열 금지, 프레임별 AddFloatCurveKey
- ABL 핀명 함정: `AnimationSequenceBase`, Branch `then/else`, GetBonePose `BoneName`, ForEachLoop `Exec`

## 함수 구조 (v7, 2026-07-15 함수화)
```
Ledge (오케스트레이터 30노드)
├─ Ledge_CalcVelocity  — 속도/위상게인/스무딩 → LedgeCalcVelocity
├─ Ledge_DangleAlpha   — 게이팅/디바운스/엔벨로프 → LedgeDangleAlpha/PhysAlpha
├─ Ledge_HandAlpha     — 커브×bActive → LedgeHandIKAlphaL/R
├─ (본체 잔류)          — LedgeMeshToWorld / LedgePelvisSpring
├─ Ledge_HandTarget    — Anchor/Dest 래치+mc안무+신전클램프 → HandWorld/IdleComp
│                        + 공유신호 캡처(v9.1): LedgeRelatch/Stopped/MoveOffset/PreOffset (VS_29 앞)
├─ Ledge_FootTarget    — (v9) 발 벽짚기 미러: FootAnchor 래치+foot커브 안무+클램프76
│                        → FootWorld/IdleComp/IKAlpha (알파=ledge_foot_ik×FrontBlocked, 파라미터 0)
└─ Ledge_FootGate      — SmoothedFootIKWeight/FootIKScale/PrevWorldNowL
```
호출 순서 고정 (상류 변수 의존 — FootTarget은 HandTarget의 캡처 변수 소비). 노드 편집 시 해당 서브함수 그래프에서.

## Foot IK (v9, 2026-07-15)
- CR: `cr_foot_ik.py` (FootIK L/R TwoBoneIK thigh/calf/foot, 폴=무릎+바이어스, 클램프76, FootLerp 알파0=패스스루)
- ABP: `refactor_foot_function.py` (Ledge_FootTarget 신설 — 최초 HandTarget 인라인 빌드 `build_foot_chain.py`를 함수 분리로 대체)
- 커브: `bake_foot_curves.py` (초기 수동 베이크 — 이후 모디파이어 출력으로 대체)
- 모디파이어: `mod_add_foot.py` — AM_SBLedgeHandIK에 발 4커브 통합, 파라미터 FootMoveStartL/EndL/StartR/EndR
  (램프/Exit 타이밍은 손 파라미터 공유). 재적용 164애님. Short 실측: 선행 0.1~0.35(L)/0.4(R), 후행 0.15~0.5
- 잔여: CR 변수 4개(FootTargetL/R, FootAlphaL/R) 수동 생성 → `cr_foot_wire.py`, AnimGraph 핀 노출 → 직결

## 그래프 위생 (v6)
- `graph_reachability.py` — Ledge fn 도달성 분석 (exec체인+데이터 폐포, 로컬 HTTP·컨텍스트 무부담). dead 노드 목록 산출
- `graph_cleanup.py` — 죽은노드 반복 제거+미사용변수 Set 스플라이스+GWDS 통합. ⚠ 연쇄 exec 제거는 매 제거 후 그래프 재조회 필수 (스테일 스냅샷 스플라이스 = 체인 절단 사고 이력, v6 복구 완료)
- 2026-07-14 대청소: 375→304 노드, GetWorldDeltaSeconds 11→1, 변수 4종 삭제

## 디버그 (v4 신규)
- `debug_dest_preview.py` — 이동 시 손 도착지(Dest) 프리뷰 구체 (L=시안/R=마젠타 + 손→도착지 라인). LedgeDebug 토글 연동. ABP v4 래치와 동일 수식(Idle상수+평면방향×남은거리) 파이썬 재현 — 상수 변경 시 여기도 갱신

## 디버그 (v3 신규)
- `probe_drift.py` — 양손 풀 프로브(커브/알파/타깃/손/갭/vel/fb/컴포넌트좌표) → ikdrift.log. 도착부 분석 표준
- `probe_isolate.py` — CVar 자동 격리(base→RigidBody off→FootPlacement off→LegIK off→복원, 5s 페이즈) → ikiso.log. 범인 판정용
- `measure_idle_hands.py` — Idle 애님 손위치 루프평균 실측 (타깃 상수 산출)
- `curve_timeline.py` — 애님 커브 키 vs 손 궤적/속도 타임라인 대조 (커브 유죄/무죄 판정)
- `cr_fix_right.py` — CR 오른손 이펙터 Lerp_1 경유 원복 (수동편집 오염 복구)
- `cr_cleanup_latch.py` — CR 구 내부래치 클러스터 삭제 (v3 전환 청소)

## 디버그 (v2 유물)
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
