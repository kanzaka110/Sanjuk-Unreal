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

## 펠비스 스프링 v3 — 템플릿 베이크 (2026-07-20)
- 증상: 몸(펠비스)이 팔보다 0.2~0.4s 늦게 따라오고 도착 후 9cm 역행 진동 (`probe_body.py` 실측)
- CR `PC_01_CtrlRig_LedgeDangle` SpringInterpVectorV2: **Strength 3.5→6.0, CriticalDamping 0.7→1.0** (원복값 pelvis_apply.json)
- `ledge_pelvis_spring` 커브 재설계: 구 속도엔벨로프(시작부터 0.82~1.0)를 폐기 →
  **(0,0)(0.40,0)(0.55,1)(0.90,1)(1.25,0)(dur,0)** — 이동구간 애님 100%, 도착 반동 구간만 스프링
- ShortL/R_Wallless 2종 커브 직접 교체 완료 (백업 pelvis_curve_backup.json)
- `mod_pelvis_template.py` — 모디파이어(**AM_SBLedgeIK**, 구명칭 AM_SBLedgeHandIK에서 rename) BakePelvisSpring을
  템플릿 베이크로 교체. 파라미터(인스턴스): PelvisSpringStart 0.40/Full 0.55/HoldEnd 0.90/End 1.25
  패스1 max속도+PelvisMinSpeed 가드 유지 (Idle/저속 애님=상수 0). 구 loop2 엔벨로프는 dead (exec 절단, 추후 graph_cleanup)
- ⚠ 수동 튜닝 커브 있는 애님(벽 Short 2종, StartFalling 계열)엔 Apply 재실행 금지 유지

## 골반 스프링 재설계 — 펠비스 기준 가산 (2026-07-20 저녁, v12)

### ❌ 기존 구조의 근본 결함
```
Target = 펠비스(P) − 속도×게인 ;  Spring = SpringInterp(Target) ;  final = P + (Spring − P) = Spring
```
**최종 포즈가 스프링 결과로 치환된다.** 그래서 강성을 낮추면 애님이 뭉개지고, 높이면 효과가 사라진다 —
어떤 값을 넣어도 "애님 그대로" 아니면 "애님 훼손" 둘 중 하나. 오늘 오래 헤맨 원인.

### ✅ 현재 구조
```
Target = 펠비스(P)                     ← 속도 항 제거(게인 0). 애님의 펠비스 움직임 자체가 입력
offset = (Spring − P) × 비율 × 커브     ← SpringCurveGate 신설, 커브가 세기 게이트
final  = P + Clamp(offset)             ← 애님 100% + 스프링 일부 (가산)
```
- **비율** `MathVectorMul.B = (X 0, Y 0.9, Z 0.5)` — X=앞뒤 차단 / Y=좌우 / Z=상하. 1.0 = 애님 치환이므로 상한
- **강성** 3.0 — 높을수록 지연↓ = 원본 유지. 낮추면 크게 밀리지만 애님이 뭉개짐
- **감쇠** 0.25 — **스프링 체감은 여기서 확보한다** (진폭이 아니라 튕김이라 애님을 훼손하지 않음)
- **클램프** 45 — 진짜 진폭 상한. 비율을 올려도 여기서 잘리면 변화가 없다
- 커브 전달: ABP 가 `ledge_pelvis_spring` 을 `CharVelocity` 핀에 (c,c,c) 로 실어보냄 (속도 경로가 비어서 재활용)

### 커브 스펙 (유저 확정)
**펠비스 수직 정점부터 떨어지는 구간에서 강해진다.** `measure_pelvis_apex.py` 로 애님별 정점/최저점 실측 →
`Start=정점 / Full=정점+0.08 / HoldEnd=최저점(정점+0.45 상한) / End=+0.25`.
낙차 5cm 미만(31종)은 네 값 모두 `dur` → 모디파이어 가드가 키를 안 써서 스프링 off.
예) ShortR 실측 정점 0.333 / 최저 0.667 — 유저 체감(정점 0.3, 반동 0.65~0.7)과 일치

### ⚠ 오늘 겪은 함정
- **`apply_anim_modifier(persist=True)` 는 인스턴스를 '추가'한다 (갱신 아님)** — 반복 적용 시 누적.
  ShortL 에 9개까지 쌓여 커브가 마지막 것만 반영됐다 → `dedupe_modifier_stack.py` 를 **적용 직후 항상** 실행
- **커브 × 속도 = 0 함정**: 커브가 켜지는 구간(이동 후)에 속도가 이미 0이라 곱이 0.
  실측 결과 spring>0.3 인 398프레임의 입력 |v| 이 **전부 0.0**, 이동중 332프레임 중 spring>0.3 은 **0개**.
  "스프링이 전혀 안 느껴진다" 의 진짜 원인 — 시간축이 겹치지 않는 두 신호를 곱하면 안 된다
- **축 배정은 추측 금지** — 프로브(`probe_spring.py`)로 확인할 것. 전방벡터 (-1,0,0), 이동 성분은 **Y(좌우)**.
  오늘 X/Y를 두 번 헛짚었다
- `EditorAssetLibrary.list_assets(recursive=False)` 가 0을 반환하는 경우가 있다 → recursive=True + 목록 폴백

## 모디파이어 v11 — 창 자동검출 네이티브화 (2026-07-20)
- `DetectWindow(Seq, BoneName, Ratio, PadStart, PadEnd) → (OutStart, OutEnd)` — 순수 BP 81노드
  - 패스1: 프레임 샘플 → 최대속도/피크시각/합·개수 / 패스2: `thr=base+Ratio*(max-base)` 경계 탐색
  - **기준선 = 평균** (파이썬판은 중앙값). ⚠ 배열 금지(Kismet 와일드카드 RPC 함정)라 스트리밍 통계만 가능
  - 가드: max<60 또는 스팬<25 → (0,0)=창없음 / 창길이<0.05 → (0,0)
- `AutoDetectCurves(Seq)` — DetectWindow ×4(hand_l/r, ball_l/r) + PelvisSpring 4종(base=max 손End +0.05/0.20/0.55/0.90, dur 클램프)
  - 노브는 호출 인자: 손 Ratio 0.18/Pad(-0.067,0.033) · 발 Ratio 0.32/Pad(-0.017,0.033)
  - ⚠ `derive_windows2.py`(일괄용)와 노브를 같이 맞출 것
- **OnApply 선두에서 AutoDetectCurves 호출** → "모디파이어 적용"만 눌러도 자동검출 후 커브 생성
- ⚠ **ExecutePythonCommand 함정**: 콘솔 명령이 아니라 **파이썬 코드 문자열**을 받는다.
  `py "경로"` 를 넣으면 SyntaxError 로 조용히 실패 (2026-07-20 로그 확인) → 네이티브 노드로 전환한 이유
- ⚠ **RPC 배선 오결선 실사례**: `FMin(창끝, dur)` 의 B 핀이 `dur` 가 아니라 **`step`(=dur/프레임수, 0.033)** 에
  물려서 창 끝이 항상 0.033 으로 잘렸다 → 길이 가드(0.05)에 탈락 → 전 부위 (0,0) → **`ledge_pelvis_spring` 커브만 생성**
  되는 증상. `connect_pins` 는 "성공" 을 반환했고 컴파일도 통과 — **동일 값을 여러 노드가 소비하면 knot 경유로
  엉뚱한 소스에 붙을 수 있다.** 배선 후 `deknot()` 로 실제 소스 노드까지 역추적 검증할 것
- 검증법: `DetectWindow` 를 `unreal.new_object(AM_SBLedgeIK_C)` 로 직접 call_method 하고 스크래치 변수
  (DwMax/DwPeakT/DwStart/DwEnd)를 같이 덤프 → 내부는 맞는데 출력만 0이면 출력 체인 오결선
- 미구현: 2차 창(HandMove2*/FootMove2*) 네이티브 검출. WriteMoveCurves 는 이미 지원하므로
  파라미터를 채우면 동작 — 현재는 파이썬 일괄 경로(`derive_windows2.py`)만 2차 창을 산출

## 모디파이어 인스턴스 값 일괄 세팅 (2026-07-20)
- `apply_mod_params.py` — LedgeClimbing 166종의 AM_SBLedgeIK **인스턴스 파라미터**를 시퀀스별로 세팅.
  이제 모디파이어를 **일괄 Apply해도 각 애님의 현재 안무가 그대로 재생성**된다 (수동 튜닝 보존)
- 인스턴스 접근 경로: `seq.asset_user_data → AnimationModifiersAssetUserData
  → animation_modifier_instances → AM_SBLedgeIK_C` (set_editor_property로 읽기/쓰기 가능 ✅ 실측)
- ❌ **1차 시도(커브 역산) 폐기 — 순환논리**: 커브가 이미 동일 템플릿(0.1/0.37)으로 일괄 베이크된 상태라
  역산하면 그 템플릿이 그대로 돌아옴. 166종 전부 같은 값이 됐다. 커브는 여기선 ground truth가 아니다.
- ✅ **2차(채택): 본 속도 실측 — 측정/판정 분리**
  1. `measure_profiles.py` (에디터) — AnimPose 프레임 샘플 → 원시 속도 프로파일 `bone_profiles.json` (166종, 에러 0)
  2. `derive_windows.py` (로컬) — 창 판정. **재측정 없이 판정식만 바꿔 초 단위 재튜닝** ← 이 분리가 핵심
  3. `apply_measured_params.py` (에디터) — 인스턴스 기록. **set 110 / skip_class 17 / skip_nowindow 37 / preserved 2 / error 0**
- ⚠ **속도 프로파일엔 3구간이 공존**: 스윙(~250) / 그립 중 드리프트(~110, in-place 애님) / 완전정지(~4).
  루트모션 유무가 애님마다 달라 **전역 고정문턱은 원리적으로 불가** (v8 자동검출 폐기의 진짜 원인)
- 판정식: 피크 ±0.5s **국소 중앙값**을 기준선 → `thr = base + 0.25*(peak-base)`, 피크에서 양방향 확장
  - ⚠ 국소 **최소값**을 기준선으로 쓰면 정지구간(~4)이 반경에 들어올 때 문턱 붕괴 → 좌우 스윙이 한 덩어리로 뭉개짐 (실측 확인)
  - 발 PAD `end +0.067` — 창 종료 후 IK 고정이라 짧으면 **"발이 오래 붙잡힌" 증상** (유저 리포트 2026-07-20)
  - 검증: ShortL_Wallless 우손 시작 측정 0.267 vs 유저 튜닝 0.26 — 거의 일치
- PelvisSpring 4종 = **⚠ 가설**: base(=max 손 플랜트) + 0.05/0.20/0.55/0.90 (검증값 델타 유지, dur 클램프)
- `PRESERVE` = 벽없음 Short 2종 — 유저 PIE 검증값(L 0.15~0.32 / R 0.26~0.32, 스프링 0.40/0.55/0.90/1.25) 유지.
  측정창(L 0.067~0.3 / R 0.267~0.633)과 불일치 — 측정은 스윙 전구간, 검증값은 타깃 lerp 구간이라 의미가 다름

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

## 디버그 (2026-07-20 LedgeDebugs 네이티브화 — 파이썬 드로어 폐기)
- **LedgeDebugs(ABP) 노드가 단일 출처** (`build_ledgedebugs_v5.py`로 빌드):
  - 구체 = LedgeHandWorldL/R(IK 구속점, CR 실소비값) — 밝음=α≥0.5 활성 / 어두움=비활성 (SelectColor)
  - Anchor/Dest 박스 = bTransitMoving 중만 (Idle 스테일 래치 숨김)
  - Dest 박스+경로 라인(Anchor→Dest, 두께 0.2) = |Dest-Anchor|>20cm (v14 게이트 통과=커밋) 시만
- 스테일 소켓 구체 4개 제거 — GetSocketLocation을 업데이트 시점(평가 전=전프레임 포즈)에 읽던 오표시 원인
- `debug_dest_preview.py`(파이썬 드로어)는 **폐기** — draw_debug가 다음 프레임 렌더라 움직이는 본에 1프레임 지연.
  월드 고정값은 무관하지만 유저 결정으로 전부 LedgeDebugs 노드로 이관

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
