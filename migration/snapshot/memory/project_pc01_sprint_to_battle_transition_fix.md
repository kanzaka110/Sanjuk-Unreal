---
name: pc-01-sprint-battle-b-lfoot-abp
description: 락온 + 반대방향 Sprint → Sprint 종료 시 P_Player_Transition_Sprint_to_Battle_Jog_B_Lfoot 클립 root motion 180° 회전과 ABP Strafe 분기 회전 보정 동시 작동 충돌. ABP에서 클립 재생 중 회전 보정 차단.
metadata: 
  node_type: memory
  type: project
  date: 2026-05-13
  originSessionId: e020acca-fb98-4cf6-963d-1d987445e1bd
---

# PC_01_ABP — B_Lfoot 클립 재생 중 회전 보정 차단 게이트

## 문제

- 락온 + 반대방향(180°) Sprint → Sprint 종료
- MM이 `P_Player_Transition_Sprint_to_Battle_Jog_B_Lfoot` (180° root motion 클립) 선택
- 동시에 PC_01_ABP `UpdateTargetRotation` 함수의 **Strafe 분기**가 mesh rotation 보정 수행
- 두 회전 소스 충돌 → 캐릭터 회전/모션 이상

## 처방

`UpdateTargetRotation` Strafe 분기의 `Set TargetRotationDelta` 데이터 게이트:
- 클립 재생 중이면 `TargetRotationDelta = 0` (회전 보정 차단)
- 클립 재생 안 중이면 기존 `NormalizeAxis(NormalizedDeltaRotator.Yaw * -1)` 그대로

## 구현 (2026-05-13)

### Phase 1: 신규 변수
- `bIsPlayingTransitionBack` (bool, category=Buffer, default=false)
- IE=false, BPRO=false

### Phase 2: UpdateVariables 매 틱 판정
새 노드 3개 + exec chain 삽입:
- `Get CurrentSequenceName` (string, DrawDebug에서 set, ThreadSafe read 안전)
- `EqualEqual_StrStr` (KismetStringLibrary), B 핀 literal = `"P_Player_Transition_Sprint_to_Battle_Jog_B_Lfoot"`
- `Set bIsPlayingTransitionBack` ← `EqualEqual_StrStr.ReturnValue`

**exec 삽입 위치**: `K2Node_VariableSet_47 (Set WriggleMoveType).then` 직후, `K2Node_IfThenElse_3 (CurrAnimTag Branch).execute` 직전. ExecutionSequence_3 then_11 leg의 합류점 직전이라 매 틱 1회 실행 보장.

### Phase 3: UpdateTargetRotation Strafe 분기 SelectFloat 게이트
**기존**: `K2Node_CallFunction_4 (NormalizeAxis).ReturnValue` → `K2Node_VariableSet_3.TargetRotationDelta`

**변경 후**:
```
CF4.ReturnValue       ─→ SelectFloat.A
literal 0.0           ─→ SelectFloat.B
Get bIsPlayingTransitionBack ─→ Not_PreBool.A
Not_PreBool.ReturnValue      ─→ SelectFloat.bPickA
SelectFloat.ReturnValue      ─→ K2Node_VariableSet_3.TargetRotationDelta
```

**동작 로직**:
| bIsPlayingTransitionBack | NOT | bPickA | 선택 | TargetRotationDelta |
|---|---|---|---|---|
| false (정상) | true | true | A | NormalizeAxis 결과 (기존 동작) |
| true (B_Lfoot 재생 중) | false | false | B | **0.0 (회전 보정 차단)** |

## 영향 범위

- **건드린 그래프**: `UpdateVariables`, `UpdateTargetRotation`
- **추가 노드**: 총 6개 (UpdateVariables 3 + UpdateTargetRotation 3)
- **수정 노드**: 4개 (VariableSet_47 then 재배선, IfThenElse_3 execute 합류 추가, VariableSet_3 입력 갱신, CF4 출력 갱신)
- **else 분기**: 손대지 않음 (IsStrafe=false 케이스)
- **기존 NormalizeAxis / Multiply / NormalizedDeltaRotator 노드**: 보존

## 부작용 분석

- 일반 strafe 시점에 `bIsPlayingTransitionBack=false` → NOT=true → bPickA=true → A(기존 결과) 선택 → 기존 동작 100% 보존
- 다른 클립(B_Lfoot 외) 재생 중에도 false → 영향 0
- 컨텍스트 게이팅 정확: 특정 클립명 1개만 매치

## 검증

- compile_blueprint: success=true, status=UpToDate, errors=0, warnings=0
- save_asset: was_dirty=true, saved=true
- side-effect dump diff: UpdateTargetRotation/UpdateVariables 모두 의도된 변경만 (else 분기·다른 노드 무손상)

## 사용자 PIE 검증 안내

1. 락온 상태에서 Sprint 시작
2. 반대 방향(180°) 으로 sprint 중에 sprint 키 release
3. B_Lfoot 클립 재생 (root motion 180° 회전 발생)
4. 캐릭터가 자연스럽게 회전하고 mesh rotation 보정에 의한 튐 없는지 확인
5. 일반 strafe (락온 + 임의 방향) 회전은 기존과 동일하게 작동하는지 확인

## 백업

- pre dump: `Saved/Logs/UpdateTargetRotation_pre_20260513_2051.json`, `Saved/Logs/UpdateVariables_pre_20260513_2051.json`, `Saved/Logs/ABP_vars_pre_20260513_2051.json`
- post dump: `..._post_20260513_2051.json` 동명 3개

## 관련

- 노드 ID (post): UpdateTargetRotation → SelectFloat=K2Node_CallFunction_7, NOT=K2Node_CallFunction_8, GetBack=K2Node_VariableGet_3
- 노드 ID (post): UpdateVariables → Get CurrentSequenceName=K2Node_VariableGet_56, EqualEqual_StrStr=K2Node_CallFunction_31, Set bIsPlayingTransitionBack=K2Node_VariableSet_37
- 스크립트: `scripts/add_transition_back_gate.py`, `scripts/wire_exec_phase2.py`, `scripts/phase3_gate.py`
- 별개 접근 (Montage Override 계획): `project_pc01_sprint_to_battle_transition.md`
- ABP 체인: `project_pc01_abp_chain.md`
