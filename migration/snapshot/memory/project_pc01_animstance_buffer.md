# PC_01_ABP AnimStance Buffer 함수 작업 (2026-05-12)

## 배경

UpdateStates 그래프의 `Set AnimStance := PropertyAccess_4.Value` 는 매 틱 외부 소스값을 그대로 받음. 외부(SBActorAnimInstance C++의 GetCurrentAnimStance 추정) 가 GroundMoving 동안 Battle 을 한 틱만 보내면 ABP도 한 틱만 Battle. 즉 디바운스 없음. GroundIdle 에서는 외부 소스가 Battle 유지하므로 멀쩡함.

기존 `UpdateMovementStateWithBuffer` / `UpdatePendingWalkModeWithBuffer` 와 동일한 buffer 패턴을 AnimStance 에도 적용.

## 적용 상태

**Monolith HTTP API 로 완료**:
- 변수 4개 추가 (`/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP`):
  - `CandidateAnimStance : byte` (default 0)
  - `PrevCandidateAnimStance : byte` (default 0, 현재 미사용 — 후속 확장 대비)
  - `AnimStanceAccumulatedTime : double` (default 0.0)
  - `AnimStanceBufferTime : double` (default 0.05, **EditAnywhere=true** — 디자이너 튜닝 가능)
  - 카테고리: 모두 `Buffer`
- 함수 `UpdateAnimStanceWithBuffer` 생성 (26 노드):
  - 입력: `NewStance : byte`
  - 출력: 없음 (함수 내부에서 `Set AnimStance` 직접 호출)
  - 로직:
    ```
    if NewStance == AnimStance:
        AnimStanceAccumulatedTime = 0
        CandidateAnimStance = AnimStance
        return  (AnimStance unchanged)
    else:
        if NewStance == CandidateAnimStance:
            AnimStanceAccumulatedTime += DeltaTime
        else:
            CandidateAnimStance = NewStance
            AnimStanceAccumulatedTime = DeltaTime
        if AnimStanceAccumulatedTime > AnimStanceBufferTime:
            AnimStanceAccumulatedTime = 0
            Set AnimStance = CandidateAnimStance
        else:
            (no change to AnimStance)
    ```
  - byte 비교는 `KismetMathLibrary::EqualEqual_ByteByte` 사용 (EnumEquality는 함수 입력 핀과 호환 문제)
  - double 연산은 `KismetMathLibrary::Add_DoubleDouble`, `Greater_DoubleDouble`
- 단순 컴파일 통과: 함수 단독으로는 0 errors / 0 warnings

## 미완 상태 — UpdateStates 재배선 미적용 (사용자 수동 작업 필요)

**문제**: UpdateStates 는 BlueprintThreadSafe 그래프인데 새 함수 `UpdateAnimStanceWithBuffer` 는 thread-safe 메타데이터가 없어 호출 시 컴파일 에러:
```
UpdateAnimStanceWithBuffer 스레드 세이프 그래프 ... 에서 호출된 스레드 세이프 방식이 아닌 함수
```

Monolith API에는 함수의 `BlueprintThreadSafe` 메타데이터를 설정하는 액션이 없음 (add_function / set_function_params 둘 다 metadata 미지원).

**롤백**: UpdateStates 의 `Set AnimStance` 노드는 원래 구조로 복구되어 있음 (다만 노드 ID는 `K2Node_VariableSet_11` → `K2Node_VariableSet_7` 로 변경). PropertyAccess_4.Value → Set AnimStance.AnimStance 직결 wiring 유지.

**사용자 수동 작업 (1단계만)**:

1. UE 에디터에서 PC_01_ABP 열기
2. 좌측 My Blueprint 패널 → Functions → **UpdateAnimStanceWithBuffer** 선택
3. Details 패널에서 **Graph** 섹션 → "**Thread Safe**" 체크
   - 또는 키워드 "Thread" 검색 → "Is Thread Safe" 체크박스
4. Compile (Ctrl+F7)
5. 다시 Claude (또는 동일 작업) 에게 `UpdateStates 재배선` 만 요청 → 아래 5단계 스크립트로 마무리:

## 마무리 스크립트 (사용자가 ThreadSafe 체크 후 실행)

UpdateStates 재배선만 진행:
```
1. UpdateStates 의 K2Node_VariableSet_7 (Set AnimStance) 노드 위치 1416,1152 근처에 CallFunction(UpdateAnimStanceWithBuffer) 추가
2. K2Node_PropertyAccess_4.Value -> CallFunction.NewStance 연결
3. K2Node_VariableSet_9 (Set PrevAnimStance).then -> K2Node_VariableSet_7 연결 해제
4. K2Node_VariableSet_7 (Set AnimStance) 노드 삭제
5. K2Node_VariableSet_9.then -> CallFunction.execute 연결
6. compile_blueprint
7. save_asset (실패 시 에디터에서 Ctrl+S)
```

`scripts/dumps/_post_20260512_*.json` 에 함수 그래프 / UpdateStates / 변수 dump 저장됨. 마무리 후 동일 dump 재실행해 비교.

## 검증 체크리스트 (PIE에서 사용자 확인)

ThreadSafe 체크 + 재배선 완료 후:

- [ ] PIE 진입, GroundMoving 상태에서 외부 AnimStance 가 1틱 Battle pulse 발생 시 ABP 의 `AnimStance` 값이 Battle 로 전환되지 **않는지** (BufferTime 0.05초 = 약 3틱 미만이면 무시)
- [ ] AnimStance 가 BufferTime 이상 (0.05초+) 유지되면 ABP 의 AnimStance 가 전환되는지
- [ ] GroundIdle 에서 AnimStance 가 안정적으로 Battle 유지되는지 (기존 정상 동작 유지)
- [ ] `AnimStanceBufferTime` 을 0.1 ~ 0.2 로 늘려서 더 강한 디바운스 효과 확인 (디자이너 튜닝 포인트)
- [ ] 컴파일 에러/경고 0개 유지

## 백업 파일

- `scripts/dumps/_pre_20260512_abp_vars.json`
- `scripts/dumps/_pre_20260512_us_summary.json`
- `scripts/dumps/_pre_20260512_updatestates_export.json`
- `scripts/dumps/_post_20260512_abp_vars.json`
- `scripts/dumps/_post_20260512_us_summary.json`
- `scripts/dumps/_post_20260512_updatestates_export.json`
- `scripts/dumps/_post_20260512_animstancebuffer_export.json`
- `scripts/dumps/_post_20260512_animstancebuffer_sig.json`

## 빌드 스크립트

`scripts/build_animstance_buffer.py` — 함수 노드 생성 + wiring (idempotent하지 않음 — 함수가 비어 있을 때만 실행)

## HoldTimeThreshold 0.03 → 0.2 변경 (2026-05-13)

회피→질주 transition 시 사용자 호소: PendingWalkMode 2→4 한 틱 점프 + ms_l 진동 → 노이즈.

### 변경 전 진단

PC_01_ABP 의 Buffer 변수 구조 확정:

| 함수 | HoldTime 변수 사용 방식 |
|---|---|
| `UpdatePendingWalkModeWithBuffer` | 변수 `HoldTimeThreshold` GET 으로 graph 내부 직접 참조 (입력 파라미터 없음) |
| `UpdateMovementStateWithBuffer` | 입력 파라미터 `InHoldTimeThreshold` 로 받음. UpdateStates 호출처가 `K2Node_VariableGet_29.HoldTimeThreshold` 전달 |
| `UpdateAnimStanceWithBuffer` | `AnimStanceBufferTime` 별도 변수 사용 (전용, EditAnywhere=true) |
| `DrawDebug` | `HoldTimeThreshold` GET 으로 디버그 표시 |

→ `HoldTimeThreshold` 는 **PendingWalkMode + MovementState 공유 변수** (AnimStance 만 분리됨). 따라서 PendingWalkMode 강화는 MovementState 도 동시에 강화. 사용자 호소 (pwm 점프 + ms_l 진동) 두 가지 모두를 같이 디바운스하는 효과 → 처방 의도와 정합.

### 변경 결정

`HoldTimeThreshold` default 0.030000 → 0.200000 (약 6.7배, 처방 "최소 0.2" 충족).

분리 옵션 (B안) 보류: 추후 사용자가 MovementState 만 0.03 유지 원하면 새 변수 `PendingWalkModeHoldTimeThreshold` 추가 + UpdatePendingWalkModeWithBuffer.K2Node_VariableGet_2 / DrawDebug.K2Node_VariableGet_56 두 군데 재배선 필요.

### 적용 결과

- `set_variable_defaults` → success
- `compile_blueprint` → UpToDate, errors=0, warnings=0
- `save_asset` → saved=true, was_dirty=true (디스크 적용 확인)
- side effect diff: 135 변수 중 `HoldTimeThreshold` 1개만 변동, 나머지 모두 동일

### 백업

- `Saved/holdtime_pre_20260513_vars.json` (변수 dump)
- `Saved/holdtime_pre_20260513_funcs.json`
- `Saved/holdtime_pre_20260513_pwm_graph.json` / `_ms_graph.json` (graph export)
- `Saved/holdtime_pre_20260513_us_msnode.json` / `_us_pwmnode.json` (CallFunction 노드 dump)
- `Saved/holdtime_post_20260513_vars.json`

### PIE 재테스트 체크

- [ ] 회피→질주 시 PendingWalkMode 2→4 한 틱 점프 사라졌는가
- [ ] 같은 시점 ms_l 진동도 줄었는가 (MovementState 도 같은 변수 공유하므로 영향 받음)
- [ ] 정상 walk→jog→sprint 의도된 전환은 0.2초+ 충분히 길어 영향 없는지
- [ ] GroundIdle 진입 응답성 저하 없는지 (0.2초 = 약 12프레임 @60FPS)
- [ ] AnimStance 디바운스는 별도 변수 `AnimStanceBufferTime=0.05` 로 영향 없음 확인

응답성 저하 호소 시 0.1~0.15 로 조정 (`set_variable_defaults` 한 번 재호출).

## Monolith 한계 발견

- 함수 metadata (BlueprintThreadSafe 등) 설정 액션 없음
- K2Node_EnumEquality 의 wildcard 핀에 함수 입력 (byte) 직접 연결 거부 — `Get <enum var>` 같은 변수 GET 으로 promote 필요. 함수 입력의 byte 와는 비호환. **우회**: `KismetMathLibrary::EqualEqual_ByteByte` 사용
- PropertyAccess 노드의 source binding (외부 SBCharacter 의 어느 property 인지) 은 get_node_details / export_graph 에 노출 안 됨
- save_asset 실패해도 디스크 적용 가능성 있음 (메모리 `reference_monolith_animgraph_editing_limits.md`)

## 2026-05-15 복구 (재구축)

작업이 사라진 상태에서 동일 구조 재구축. 처방서 + `scripts/build_animstance_buffer.py` 재사용.

### 결과

| 항목 | 결과 |
|---|---|
| 변수 4개 추가 | success (CandidateAnimStance/PrevCandidateAnimStance byte default=0; AnimStanceAccumulatedTime/AnimStanceBufferTime double; AnimStanceBufferTime EditAnywhere=true, default=0.05) |
| 함수 `UpdateAnimStanceWithBuffer` 생성 | success (NewStance byte 입력, 출력 없음) |
| 26 노드 그래프 | success (FunctionEntry 1, FunctionResult 1, IfThenElse 3, VariableGet 9, VariableSet 7, CallFunction 4, CastByteToEnum 1 자동) |
| UpdateStates 재배선 | success — Set PrevAnimStance.then → CallFunction(UpdateAnimStanceWithBuffer).execute, PropertyAccess_4.Value → CallFunction.NewStance, Set AnimStance(K2Node_VariableSet_11) 노드 삭제 |
| compile_blueprint | **0 errors (우리 변경)** — 잔존 4 errors는 `AnimRewindRecorderEmit` 의 K2Node_CallFunction_21 `SkeletalMeshComponent Target` 미연결로, 사전 dump에도 존재한 기존 에러 |
| save_asset | saved=true, was_dirty=true (디스크 적용) |
| side effect diff | 변수 143 → 147 (+4 신규), 기존 변수 변경 NONE |

### Monolith API 갱신점 (2026-05-15)

- `add_variable` 파라미터: `variable_name`/`variable_type` 아님 — **`name`/`type`** 이 정답. 2026-05-12 시점과 동일 (메모리 기존 명세 그대로 유효)
- `add_function` 호출 시 inputs 파라미터 무시됨. 함수 생성 후 `set_function_params` 로 `inputs:[{name,type}]` 별도 호출 필요
- `disconnect_pins` 는 `node_id`/`pin_name` 필수 (source_node/source_pin 인터페이스 아님)
- 전체 컴파일 ThreadSafe 에러 **발생 안 함** — 2026-05-12 의 ThreadSafe 우려 사항이 재현되지 않음. 가능성 (a) UpdateStates 가 BlueprintThreadSafe 가 아님, (b) 함수 metadata 자동 상속. 어쨌든 사용자 수동 ThreadSafe 체크 작업 불필요

### 백업 파일

- `Saved/Logs/animstance_restore/vars_pre.json` / `vars_post.json` / `vars_step1.json`
- `Saved/Logs/animstance_restore/list_pre.json` / `list_post.json`
- `Saved/Logs/animstance_restore/us_pre.json` / `us_post.json`
- `Saved/Logs/animstance_restore/func_initial.json` / `func_after_input.json` / `func_built.json`
- `Saved/Logs/animstance_restore/compile_final.json`
- `scripts/dumps/_build_nodemap.json` (재실행으로 갱신됨)

### PIE 검증 체크 (사용자 확인 필요)

- [ ] GroundMoving 상태에서 외부 AnimStance 가 1틱 Battle pulse 발생 시 ABP `AnimStance` 가 전환되지 **않는지** (BufferTime 0.05s ≈ 3틱)
- [ ] 0.05초+ 유지 시 AnimStance 전환 발생하는지
- [ ] GroundIdle 에서 AnimStance Battle 안정성 유지
- [ ] `AnimStanceBufferTime` 0.1~0.2로 늘려 디바운스 강도 조정 가능 (디자이너 튜닝 포인트)
