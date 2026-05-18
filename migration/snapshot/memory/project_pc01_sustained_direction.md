# PC_01 SustainedDirection (Pivot 트리거) 시스템 — **[폐기됨 / ARCHIVED 2026-05-13]**

## **Step 10 — 전면 제거 / 원상 복귀 (2026-05-13)**

### 배경 / 결정
Step 9 까지 IsPivoting if 분기를 `sdpt 단독`까지 단순화했음에도 Pivot 동작 검증 불충분. 사용자 결정: SustainedDirection 시스템을 **전면 폐기**하고 Pivot 문제는 다른 접근(MM DB feature/Chooser bias 등)으로 재시작. 본 메모리는 이력 보존용 archive.

### 제거 내역
- **변수 6개 삭제**: SustainedDirTime, bSustainedDirPivotTrigger, SustainedDirMinTime, SustainedDirAngleThreshold, SustainedDirStableThreshold, SustainedDirMinSpeed
- **함수 1개 삭제**: UpdateSustainedDirectionWithBuffer
- **호출 1건 제거**: UpdateStates 의 ExecutionSequence_0.then_3 위치 USDB 호출 (Step 3 의 역작업)
- **ANIM_REC 정리**: `K2Node_FormatText_1` (sdt/tta/sdpt chain) + 3개 Get 노드 (SustainedDirTime, TrjTurnAngle, bSustainedDirPivotTrigger) 제거. FT_8.Result → FT_2.prev 직결 재배선. clip 키 (FT_2 + CurrAnimTag Get) 보존.
- **BTSUA exec 체인 원상 복귀**: Trajectory → UpdateVariables → UpdateStates ⇒ **Trajectory → UpdateStates → UpdateVariables** (Step 3 이전 원형)

### IsPivoting 함수 결정 (사용자 처방 vs 실측)
- **처방 가정**: if 분기 = `bSustainedDirPivotTrigger` 단독 → `IsLockOn AND (MoveSide≠PrevMoveSide)` 로 원상 복귀
- **실측**: if 분기에 이미 사용자가 T3D 로 추가한 `IsLockOn AND (MoveSide≠PrevMoveSide) AND bPrevIsMoving` 3-pin AND 구성됨. sdpt Get 노드 자체가 IsPivoting 그래프에 없음.
- **결정**: **변경 없음** — bPrevIsMoving 추가 부분은 사용자가 의도적으로 넣은 안전장치로 보존. SustainedDir 제거 작업과 분리. else 분기도 원본 그대로 (`|rotDelta|>=threshold AND NOT TrjIsCircling`).

### 검증
- compile_blueprint: success, errors=0, warnings=0 (Phase 1 + Phase 3 두 번 모두)
- validate_blueprint: node_errors=0, SustainedDir 관련 disconnected 0건. 기존 disconnected 17개는 SustainedDir 무관 (UpdateVariables PrevFullBodySlotWeight/PrevAnimTag, DrawDebug PrintString 들 등 사전부터 존재).
- search_nodes "SustainedDir": **0 matches** (전체 1953 노드 중 잔존 없음)
- save_asset: Monolith 응답 실패 (알려진 ABP 한계). 사용자 에디터 Ctrl+S 필수.

### 백업 파일
- pre vars/funcs/graphs: `C:/Dev/Sanjuk-Unreal/Saved/teardown_pre_phase1_*.json`, `teardown_pre_{IsPivoting,UpdateStates,BTSUA,AnimRewindRecorderEmit}_20260513.json`
- phase별 결과: `teardown_p1b_*`, `teardown_p1c_disc/conn{1..3}`, `teardown_p2a_remove_func`, `teardown_p2b_rm_*`, `teardown_p3a_*`
- post: `teardown_post_phase1_{BTSUA,UpdateStates}_20260513.json`, `teardown_post_phase2_{vars,funcs}_20260513.json`, `teardown_post_phase3_AREE_20260513.json`, `teardown_post_IsPivoting_20260513.json`
- 검증: `teardown_final_{compile,validate,save}.json`, `teardown_post_search_residue.json` (0 matches)

### 다음 작업 (Pivot 재시작)
- MM 데이터베이스 검색 bias (Pivot 클립에 가중치) 또는 Chooser Table tag 우선순위로 접근 권장
- IsPivoting 함수는 원본 식 (실측 기준 `IsLockOn AND MoveSide≠PrevMoveSide AND bPrevIsMoving` / else `|rotDelta|>=threshold AND NOT TrjIsCircling`) 유지. SustainedDirection 의존 없음.

---

## (이하 Step 1~9 이력 — 폐기됨, 참고용)

## 상태 (2026-05-13 기준 / 폐기 시점)
- Step 1 (변수 5개 추가) — 완료
- Step 2 (UpdateSustainedDirectionWithBuffer 함수 생성 + 노드 19 + 연결 21) — 완료
- compile OK (errors=0, warnings=0)
- save_asset 실패 (P4 source control / 메모리 한계로 예상된 케이스)
- ThreadSafe 메타 — 사용자 수동 ON 완료 + Ctrl+S + ThreadSafe 경고 사라짐 확인
- Step 3 (UpdateStates exec 배선) — **완료 (2026-05-13)**
- Step 4 (IsPivoting else 분기 AND 게이트) — **완료 (2026-05-13)**
- Step 5 (게이트 위치 정정: else → if=Strafe=true 분기로 이동) — **완료 (2026-05-13)**
- Step 6 (SustainedDirMinTime/MinSpeed 튜닝) — **완료 (2026-05-13)**
- Step 7 (IsPivoting Branch 조건을 IsStrafe → IsLockOn 으로 + if 분기 식 재설계) — **완료 (2026-05-13)**
- Step 8 (UpdateSustainedDirectionWithBuffer 함수 내부 각도 게이트 제거 — sdpt=Time≥MinTime, DirStable=Speed≥MinSpeed만) — **완료 (2026-05-13)**
- Step 9 (IsPivoting if 분기 식 단순화 — `IsLockOn AND MoveSide≠PrevMoveSide AND sdpt` → `sdpt` 단독) — **완료 (2026-05-13)**

## Step 3 적용 — UpdateStates exec 체인
- 삽입 위치: `K2Node_ExecutionSequence_0.then_3` (빈 시퀀스 핀, 기존 결선 무손상)
- 새 노드: `K2Node_CallFunction_2` (`UpdateSustainedDirectionWithBuffer` 호출)
- diff: 노드 67→68, 결선 +1
- 사전/사후: `Saved/updatestates_pre_step3_20260513.json`, `Saved/updatestates_post_step3_20260513.json`

## Step 4 적용 — IsPivoting else 분기 AND 게이트 (※ Step 5에서 이동됨)
- 방식: 새 AND(BooleanAND/KismetMathLibrary) 노드 1개 직렬 삽입 (기존 CommutativeAssociative AND 핀 확장 대신 안전한 새 노드 방식)
- 변경:
  - `K2Node_CommutativeAssociativeBinaryOperator_1.ReturnValue → K2Node_FunctionResult_1.ReturnValue` 끊기
  - `AND_1.ReturnValue → new_AND(_9).A`
  - `Get bSustainedDirPivotTrigger (VG_8) → new_AND(_9).B`
  - `new_AND(_9).ReturnValue → FunctionResult_1.ReturnValue`
- ~~최종 else 식~~: Step 5 에서 원복 → else 식은 원본 그대로 `(|TargetRotationDelta| >= ...) AND (NOT TrjIsCircling)`
- **AND** (논리곱) 게이트 — 사용자 명시. OR 아님.
- diff: 노드 25→27, 결선 +3, 끊기 -1
- 사전/사후: `Saved/ispivoting_pre_step4_20260513.json`, `Saved/ispivoting_post_step4_20260513.json`

## Step 5 적용 — 게이트 위치를 if(Strafe=true) 분기로 이동 (2026-05-13)
- **사용자 요청**: "IsPivoting 에서 락온시에만 작동해야 해서 기본상태가 아닌 IsStrafe 가 트루일떄로 다시 적용"
- **이유**: SustainedDirection 트리거는 락온 시 strafe 회전 검출용. Strafe=false (일반 이동) 분기에 게이트를 두면 일반 이동에서도 영향. 본래 의도는 락온 strafe 분기 전용.
- 변경 A — else (Strafe=false) 분기 원복:
  - `K2Node_CallFunction_9` (BooleanAND, Step 4의 새 AND) 제거
  - `K2Node_VariableGet_8` (Get bSustainedDirPivotTrigger) 제거
  - `K2Node_CommutativeAssociativeBinaryOperator_1.ReturnValue → K2Node_FunctionResult_1.ReturnValue` 복원
- 변경 B — if (Strafe=true) 분기에 게이트 추가:
  - 새 노드: `K2Node_CallFunction_10` (BooleanAND/KismetMathLibrary), `K2Node_VariableGet_10` (Get bSustainedDirPivotTrigger)
  - `K2Node_CallFunction_3.ReturnValue → FunctionResult_0.ReturnValue` 끊기
  - `K2Node_CallFunction_3.ReturnValue → K2Node_CallFunction_10.A` 연결
  - `K2Node_VariableGet_10.bSustainedDirPivotTrigger → K2Node_CallFunction_10.B` 연결
  - `K2Node_CallFunction_10.ReturnValue → K2Node_FunctionResult_0.ReturnValue` 연결
- **최종 식**
  - if (Strafe=true): `(IsLockOn AND (MoveSide != PrevMoveSide)) AND bSustainedDirPivotTrigger`
  - else (Strafe=false): `(|TargetRotationDelta| >= PivotAngleThreshold[WalkMode]) AND (NOT TrjIsCircling)` (원상 복귀)
- diff: 노드 27→27 (제거 2, 추가 2), 결선 net 0 (끊기 4, 추가 4)
- 컴파일: success, errors=0, warnings=0
- validate: IsPivoting 새 노드들 정상 연결 (다른 그래프 기존 disconnected 와 무관)
- save: saved=true, was_dirty=true (디스크 반영)
- 사전/사후: `Saved/ispivoting_pre_strafe_move_20260513.json`, `Saved/ispivoting_post_strafe_move_20260513.json`

### PIE 검증 안내 (Step 5)
- **락온 + 측면 strafe** 중: 즉시 좌↔우 반전은 Pivot 불발 (SustainedDirMinTime=0.4 미만), 0.4s 이상 유지 후 큰 방향 전환 시에만 Pivot 발생
- **일반 이동 (Strafe=false)**: SustainedDirection 게이트 영향 없음 — 원본 `(rotDelta≥threshold) AND (NOT TrjIsCircling)` 그대로 동작
- 락온 분기에서 bSustainedDirPivotTrigger=false 동안 Pivot 차단되는지 확인

## 통합 검증
- `compile_blueprint`: success, errors=0, warnings=0 (ThreadSafe 경고 재발 없음)
- `validate_blueprint`: node_errors=0, IsPivoting 새 노드들 모두 정상 연결 (disconnected 17개는 사전부터 존재한 기존 노드)
- `save_asset`: saved=true

## 미정리 / 다음 세션 후보
1. **orphan 청소** — IsPivoting의 `Get BlendStackInputs → Break → Contains("Pivot") → NOT` 체인 (어디에도 연결 안 됨). 보류 — 별도 작업으로.
2. **PIE 검증** — 사용자가 다음 시나리오 관찰:
   - 즉시 방향 전환 (한 틱 입력 반전) → Pivot 불발생 확인 (`SustainedDirMinTime` 미만)
   - MinTime 이상 새 방향 유지 → Pivot 발생 확인
   - Strafe (락온+측면이동) Pivot 은 기존 동작 그대로
   - `SustainedDirMinTime` / `SustainedDirMinSpeed` 추가 튜닝 시 반응 변화

## Step 6 — 패드 입력 게이트 튜닝 (2026-05-13)
PIE 로그 (f.270~294 좌→우 strafe) 분석 후 두 변수 default 하향:

| 변수 | 이전 | 새 default | 의도 |
|---|---|---|---|
| SustainedDirMinTime | 1.5 | **0.25** | 재무장 시간 단축 (~0.27s) |
| SustainedDirMinSpeed | 50.0 | **20.0** | 패드 감속 구간에도 누적 유지 |

근거: f.289 Pivot 정상 발생, f.290~291 sp=18.7/41.5 급감 → Speed 50 게이트가 sdt 누적 차단 → 다음 반전까지 ~0.47s 필요. 사용자 패드 반전 빈도가 그보다 빠르면 두번째부터 Pivot 미발생.

유지: SustainedDirAngleThreshold=90, SustainedDirStableThreshold=15.

검증:
- compile success errors=0 warnings=0
- 338개 CDO properties 중 정확히 2개만 변경 (side effect 없음)
- instance_editable=true, blueprint_read_only=false 보존
- save_asset 2회 시도 모두 Monolith 응답 실패 (메모리 알려진 한계) — 변경은 in-memory dirty 상태. 사용자가 에디터에서 수동 Ctrl+S 필요.

백업: `C:\Dev\Sanjuk-Unreal\Saved\vars_pre_tuning_20260513.json`, `vars_post_tuning_20260513.json`, `cdo_all_pre.json`, `cdo_all_post.json`.

## Step 7 — IsPivoting Branch 조건 IsStrafe → IsLockOn 으로 변경 + if 분기 재설계 (2026-05-13)

### 배경
Step 5/6 까지 적용했음에도 PIE 실측: 패드 입력 IsStrafe 가 좌↔우 전환 순간 false 로 잠깐 토글 → 그 순간 `bSustainedDirPivotTrigger=true` 한 틱이 발생해도 if(Strafe) 분기로 흐르지 않아 Pivot 발생 실패. 사용자 선택: 분기 게이트를 IsStrafe 가 아닌 IsLockOn 으로 변경 — 락온 중이면 패드 전환 미세 토글 영향 없음.

### 변경 사항
- **Branch.Condition 재배선**: `K2Node_VariableGet_1 (IsStrafe) → K2Node_IfThenElse_0.Condition` 끊고 `K2Node_VariableGet_2 (IsLockOn) → K2Node_IfThenElse_0.Condition` 으로 교체
- **if 분기 식 재설계** (else는 손대지 않음)
- **제거 노드 (5개)**:
  - `K2Node_CallFunction_3` (BooleanAND — `IsLockOn AND MoveSide≠PrevMoveSide`)
  - `K2Node_CallFunction_0` (NotEqual_ByteByte — `MoveSide ≠ PrevMoveSide`)
  - `K2Node_VariableGet_3` (Get MoveSide)
  - `K2Node_VariableGet_4` (Get PrevMoveSide)
  - `K2Node_VariableGet_1` (Get IsStrafe — 더 이상 IsPivoting 에서 사용 안 됨)
- **추가 노드 (4개)**:
  - `K2Node_VariableGet_11` (Get TrjTurnAngle)
  - `K2Node_CallFunction_11` (Abs / KismetMathLibrary)
  - `K2Node_VariableGet_12` (Get SustainedDirAngleThreshold)
  - `K2Node_CallFunction_12` (GreaterEqual_DoubleDouble / KismetMathLibrary)
- **재활용 노드 (2개)**:
  - `K2Node_CallFunction_10` (Step 5 의 외부 AND — A 입력만 새 GE 로 갈아끼움)
  - `K2Node_VariableGet_10` (Get bSustainedDirPivotTrigger — B 입력 그대로)
- **결선**:
  - TrjTurnAngle (VG_11) → Abs (CF_11) .A
  - Abs (CF_11) .ReturnValue → GE (CF_12) .A
  - SustainedDirAngleThreshold (VG_12) → GE (CF_12) .B
  - GE (CF_12) .ReturnValue → AND (CF_10) .A
  - bSustainedDirPivotTrigger (VG_10) → AND (CF_10) .B (보존)
  - AND (CF_10) .ReturnValue → FunctionResult_0.ReturnValue (보존)

### 최종 식
- **if (IsLockOn=true)**: `bSustainedDirPivotTrigger AND (|TrjTurnAngle| >= SustainedDirAngleThreshold)`
- **else (IsLockOn=false, 일반 이동)**: `(|TargetRotationDelta| >= PivotAngleThreshold[PendingWalkMode]) AND (NOT TrjIsCircling)` (원본 보존)

### 검증
- compile_blueprint: success, errors=0, warnings=0
- 노드 카운트: 23 → 22 (제거 5, 추가 4, net -1)
- post-dump 결선 검증 완료 (모든 핀 의도대로 연결)
- save_asset: Monolith 응답 실패 (알려진 ABP 한계) — 사용자가 에디터에서 수동 Ctrl+S 필요

### 백업
- pre: `C:/Dev/Sanjuk-Unreal/Saved/ispivoting_pre_lockon_branch_20260513.json`
- post: `C:/Dev/Sanjuk-Unreal/Saved/ispivoting_post_lockon_branch_20260513.json`

### PIE 재테스트 안내 (Step 7)
- **락온 ON + 패드 좌↔우 빠른 반전**: IsStrafe transition 한 틱 토글 무관하게 Pivot 발동 여부 확인. SustainedDirAngleThreshold(=90°) 이상 회전 + sdpt=true 순간 트리거.
- **락온 OFF + 일반 이동**: else 분기 무변경. `(rotDelta ≥ threshold) AND (NOT TrjIsCircling)` 그대로.
- **락온 ON + 작은 회전(<90°)**: sdpt=true 이어도 GE 게이트 차단 → Pivot 발생 안 함. SustainedDirection 시스템 자체의 ange 게이트와 중복되지만 안전망 역할.

### 남은 작업
- orphan 청소 (`Get BlendStackInputs → Break → Contains("Pivot") → NOT` 체인) — 별도 단계로 보류
- 사용자 수동 Ctrl+S (에디터)

## Step 8 — UpdateSustainedDirectionWithBuffer 내부 각도 게이트 제거 (2026-05-13)

### 배경
Step 7 (IsPivoting 분기 재설계) 후, 각도 GE 게이트가 IsPivoting if 분기에 이미 존재 (`|TrjTurnAngle| >= SustainedDirAngleThreshold`). 함수 내부의 같은 angle 체크 + Stable 체크는 중복/이중 게이트 → 단순화로 제거. 함수 책임을 "시간×속도 누적기"로 축소.

### 변경 사항
- **Disconnect 6개** (D1~D6): TrjTurnAngle→Abs→Less<Stable→AND→NOT→AND 체인의 모든 결선 절단
- **Remove 7개** (R1~R7):
  - `K2Node_VariableGet_0` (Get TrjTurnAngle)
  - `K2Node_CallFunction_0` (Abs Float)
  - `K2Node_VariableGet_1` (Get SustainedDirStableThreshold)
  - `K2Node_CallFunction_1` (Less<Stable, DirStable 체크)
  - `K2Node_CallFunction_9` (DirStable AND Speed)
  - `K2Node_CallFunction_4` (NOT Boolean)
  - `K2Node_CallFunction_5` (sdpt 최종 AND)
- **Connect 2개** (C1, C2):
  - `K2Node_CallFunction_8.ReturnValue (Speed2D ≥ MinSpeed)` → `K2Node_IfThenElse_0.Condition` (Branch 직접 게이트)
  - `K2Node_CallFunction_2.ReturnValue (Time ≥ MinTime)` → `K2Node_VariableSet_0.bSustainedDirPivotTrigger`

### 최종 식
- **bSustainedDirPivotTrigger** = `(SustainedDirTime >= SustainedDirMinTime)` — 시간 누적 단일 게이트
- **Branch (Time 누적 분기)** = `(Speed2D >= SustainedDirMinSpeed)` — true: Time += DT, false: Time = 0
- 함수에서 TrjTurnAngle 의존 완전 제거. 각도 판정은 IsPivoting if(IsLockOn) 분기의 `|TrjTurnAngle| >= SustainedDirAngleThreshold` GE 노드가 단독 담당.

### 검증
- compile_blueprint: success, status=UpToDate, errors=0, warnings=0
- 노드 카운트: 21 → 14 (제거 7, net -7)
- 결선 13개 전수 확인 (Step 8 처방 검증 체크리스트 PASS)
- validate_blueprint: node_errors=[], 본 그래프 disconnected 0건 (다른 그래프의 사전 disconnected 노드와 무관)
- unused_variables 에 `SustainedDirStableThreshold` 등장 — 의도된 결과 (변수 자체는 보존; 다른 그래프 사용처 확인 후 별도 단계로 정리 예정)
- save_asset: Monolith 응답 실패 (알려진 ABP 한계) — 사용자가 에디터에서 수동 Ctrl+S 필요

### 백업
- pre: `C:/Dev/Sanjuk-Unreal/Saved/sustained_func_pre_step8_20260513.json`
- post: `C:/Dev/Sanjuk-Unreal/Saved/sustained_func_post_step8_20260513.json`
- 추가 pre (inspector 시점): `C:/Dev/Sanjuk-Unreal/Saved/sustained_func_pre_angle_removal_20260513.json`

### PIE 검증 안내 (Step 8)
- **락온 ON + 패드 좌↔우 빠른 반전**: Speed2D 가 MinSpeed(=20) 이상 유지되는 한 SustainedDirTime 단조 누적. MinTime(=0.25s) 경과 시 sdpt=true 한 틱. IsPivoting 의 angle≥90 GE 가 단독 angle 게이트 역할.
- **속도 급감 (감속 구간)**: Speed<20 순간 Time=0 리셋. 다음 가속 후 0.25s 재대기.
- **락온 OFF**: else 분기는 본 변경 무관 (sdpt 미사용).

## Step 9 — IsPivoting if 분기 식 단순화: sdpt 단독 (2026-05-13)

### 배경
Step 7~8 후에도 90도 회전 시 Pivot 미발동 호소. 데이터 분석: sdpt=true 발동 OK, IsStarting=true 유지(=> IsPivoting=false 추정).
**실측 함수 구조 (사전 dump)**: Step 7 memo와 실제 그래프가 다름 — 실제 if 분기 식은 3-pin CommutativeAssociativeBinaryOperator AND:
- A: IsLockOn (`K2Node_VariableGet_14`)
- B: EnumInequality (`K2Node_EnumInequality_0`, MoveSide≠PrevMoveSide)
- C: bSustainedDirPivotTrigger (`K2Node_VariableGet_10`)
- Branch.Condition: **IsStrafe** (Step 7 의 "IsLockOn 으로 변경"이 어디선가 되돌려진 상태)

`MoveSide≠PrevMoveSide` 가 90도 회전 시 충족 안 됨 (MoveSide enum 은 입력 벡터 4분면 단위라 90도 한 번에서는 같은 quadrant 유지 가능) → if 분기 false. 사용자 선택: MoveSide 조건 제거, sdpt 단독.

### 변경 사항 (옵션: sdpt 단독)
- **Disconnect 1건**: `K2Node_CommutativeAssociativeBinaryOperator_0.ReturnValue` 의 모든 연결 (→ FunctionResult_0.ReturnValue 끊김)
- **Connect 1건**: `K2Node_VariableGet_10.bSustainedDirPivotTrigger` → `K2Node_FunctionResult_0.ReturnValue` 직결
- **Remove 5건**:
  - `K2Node_CommutativeAssociativeBinaryOperator_0` (3-pin AND)
  - `K2Node_EnumInequality_0` (MoveSide≠PrevMoveSide)
  - `K2Node_VariableGet_15` (Get MoveSide)
  - `K2Node_VariableGet_17` (Get PrevMoveSide)
  - `K2Node_VariableGet_14` (Get IsLockOn — 본 그래프 단일 사용처라 같이 제거)

### 최종 식
- **if (IsStrafe=true)**: `bSustainedDirPivotTrigger` (단독)
- **else (IsStrafe=false)**: `(|TargetRotationDelta| >= PivotAngleThreshold[PendingWalkMode]) AND (NOT TrjIsCircling)` (원본 보존 — 손대지 않음)

### 검증
- compile_blueprint: success, status=UpToDate, errors=0, warnings=0
- 노드 카운트: 19 → 14 (제거 5, net -5)
- 사후 dump 결선 확인:
  - `FunctionResult_0.ReturnValue ← VariableGet_10.bSustainedDirPivotTrigger` ✅
  - `FunctionResult_1.ReturnValue ← CommutativeAssociativeBinaryOperator_1.ReturnValue` (else AND, A=GE 게이트, B=NOT TrjIsCircling) — 보존 ✅
  - `IfThenElse_0.Condition ← VariableGet_13.IsStrafe` — 보존 ✅
- save_asset: Monolith 응답 실패 (알려진 ABP 한계) — 사용자가 에디터에서 수동 Ctrl+S 필요

### 백업
- pre: `C:/Dev/Sanjuk-Unreal/Saved/ispivoting_pre_remove_moveside_20260513.json`
- post: `C:/Dev/Sanjuk-Unreal/Saved/ispivoting_post_remove_moveside_20260513.json`

### Branch 조건 메모
사전 dump에서 Branch.Condition 이 **IsStrafe**로 관찰됨 (Step 7 memo의 "IsLockOn으로 교체"가 어디선가 되돌려짐 — 본 작업에서 손대지 않음). 사용자가 락온 전용 게이트가 의도이면 별도로 IsStrafe → IsLockOn 재변경 필요.

### PIE 재테스트 안내 (Step 9)
- **Strafe ON + 90도 회전**: sdpt=true 한 틱 시 IsPivoting=true 즉시 발동 → IsStarting release(Pivot Tag 검출/IsPivoting() NOT 게이트 양쪽). Start 해제되고 Pivot 클립으로 전환되는지 확인.
- **Strafe ON + 즉시 좌↔우 반전**: SustainedDirMinTime(=0.25s) 미만이면 sdpt=false 유지 → IsPivoting=false (정상).
- **Strafe OFF**: else 분기 무변경. 기존 `(rotDelta≥threshold) AND (NOT TrjIsCircling)` 그대로.
- **부작용 체크**: 일반 패드 입력 시 sdpt가 너무 자주 true가 되지 않는지 (Speed≥20, Time≥0.25 두 조건이 단독 게이트라 일반 이동에서도 발동 가능). 과도 발동 시 SustainedDirMinTime 상향 또는 GE(|TrjTurnAngle|≥SustainedDirAngleThreshold)를 다시 if 분기에 직렬로 추가.

## 목적
TrjTurnAngle 기반 "방향 지속 시간" + "큰 방향 전환" 검출. 
- 안정 임계(15°) 이하로 작은 회전이 지속되면 SustainedDirTime 누적
- 0.4s 이상 유지 후 큰 방향 전환(>=90°) 발생 시 1틱 트리거 (bSustainedDirPivotTrigger)
- IsPivoting 게이트로 사용 예정

## 변수 (모두 신규 추가, 5개)
| 변수 | type | category | default | RO | IE |
|---|---|---|---|---|---|
| SustainedDirTime | float | Buffer | 0.0 | false | false |
| bSustainedDirPivotTrigger | bool | Essential Values | false | **false** | false |
| SustainedDirMinTime | float | Essential Values | 0.4 | false | true |
| SustainedDirAngleThreshold | float | Essential Values | 90.0 | false | true |
| SustainedDirStableThreshold | float | Essential Values | 15.0 | false | true |

주의: bSustainedDirPivotTrigger는 사용자 사양상 RO=true 였지만 함수 내부에서 Set 하므로 컴파일 차단 → RO=false로 변경. UE에서 "외부 BP만 write 차단"은 불가, "전체 차단(RO=true)" 또는 "전체 허용(RO=false)" 둘 중 선택.

## 함수: UpdateSustainedDirectionWithBuffer
- 경로: PC_01_ABP
- 카테고리: Buffer
- 입력/출력: 없음 (void)
- 노드: 20 (Entry 1 + 19 추가)
- 연결: 21
- exec 흐름: Entry → SetTrigger → Branch → (True: SetTime ← Time + DeltaTime) / (False: SetTime ← 0.0)
- data: TrjTurnAngle → Abs → (Less<Stable=DirStable, GE>=Angle=angleExceeded). Time>=MinTime=minTimeReached. NOT(DirStable) AND minTimeReached AND angleExceeded → bSustainedDirPivotTrigger.

## 알려진 후속 작업
1. ThreadSafe 메타 수동 체크 (UE 에디터 함수 details 패널 "Thread Safe")
2. asset 디스크 저장 (P4 checkout + Save in editor)
3. UpdateStates 또는 UpdateVariables 그래프에서 새 함수 호출 (exec 배선) — Step 3
4. IsPivoting 함수에 bSustainedDirPivotTrigger OR-게이트 추가 — Step 4

## 백업 파일
- pre vars: `C:/Dev/Sanjuk-Unreal/Saved/vars_pre_sustaineddir_inner.json` (133 vars)
- post vars: `C:/Dev/Sanjuk-Unreal/Saved/vars_post_sustaineddir_step1_inner.json` (138 vars)
- pre funcs: `C:/Dev/Sanjuk-Unreal/Saved/functions_pre_sustaineddir_inner.json` (48 funcs)
- post funcs: `C:/Dev/Sanjuk-Unreal/Saved/functions_post_sustaineddir_inner.json` (49 funcs)
- post function graph: `C:/Dev/Sanjuk-Unreal/Saved/sustained_dir_func_post_step2_inner.json` (20 nodes)

## 참고 패턴
기존 `UpdatePendingWalkModeWithBuffer` 그래프 분석 후 동일 BuiltIn 함수(`Add_DoubleDouble`, `Greater_DoubleDouble`) 패턴 채택. 차이: 본 함수는 시간 누적 + 트리거 한 틱 펄스 (Walk Mode 버퍼는 후보→확정 latch 패턴).
