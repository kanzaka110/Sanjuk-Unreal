# PC_01 Chooser Table 인벤토리 + 재정리 계획

**날짜**: 2026-04-29
**대상**: SB2 PC_01 (UE 5.7.4 custom)
**스코프**: PC_01 폴더 내 ChooserTable 클래스 6종
**조사 방법**: Monolith `project_query.find_references` (실패) → 파일 시스템 grep으로 의존성 직접 확인

---

## 1. 현재 상태 (실측)

### 1-1. PC_01 ChooserTable 6종

| # | 현재 경로 | Input Enum/Struct | Output Struct | 명명 패턴 |
|---|-----------|-------------------|---------------|----------|
| 1 | `StateMachine/EvieAnimChooser_StateMachine` | `E_SBMovementMode`, `ESBStateMachineState` | `SBStateMachineChooserOut` | `*AnimChooser_*` (캐릭명 포함) |
| 2 | `StateMachine/GroundIdle` | `ESBStateMachineState`, `ESBStateMachineMoveSide` | `SBStateMachineChooserOut` | **무접두** ⚠️ |
| 3 | `StateMachine/GroundMoving` | `ESBStateMachineState`, `ESBStateMachineMoveSide` | `SBStateMachineChooserOut` | **무접두** ⚠️ |
| 4 | `StateMachine/Falling` | `ESBStateMachineState`, `ESBStateMachineMoveSide` | `SBStateMachineChooserOut` | **무접두** ⚠️ |
| 5 | `OverlaySystem/PC_01_Overlays` | `E_OverlayPose`, `PDA_OverlayData` | `OverlayPose` | `<Char>_<Sys>` |
| 6 | `TravelSystem/CHT_PC_Travel` | `S_TravelChooserInputs` | `S_TravelChooserOutputs` | `CHT_<Char>_<Sys>` |

### 1-2. 의존성 트리 (root → leaf)

```
[Locomotion]
PC_01_ABP
└── EvieAnimChooser_StateMachine    (root, MovementMode dispatch)
    ├── GroundIdle                  (sub, idle 변형 선택)
    ├── GroundMoving                (sub, jog/sprint 등 이동)
    └── Falling                     (sub, jump/fall/land)

[Overlay]
PC_01_BP / PC_01_BP_Base / PC_01_BP_Sanjuk
└── PC_01_Overlays                  (Default/Feminine/Injured DA 선택)

[Travel/Traversal]
AC_Travel_Logic (Actor Component)
└── CHT_PC_Travel                   (Mantle/Hurdle 몽타주 선택)
```

### 1-3. Rename 영향 범위

| Chooser | 외부 referrer | dirty 되는 에셋 수 | 위험도 |
|---------|---------------|-------------------|-------|
| GroundIdle / GroundMoving / Falling | (없음, root만) | 1 (root) | **낮음** |
| EvieAnimChooser_StateMachine | `PC_01_ABP` | 1 | 낮음 |
| PC_01_Overlays | `PC_01_BP`, `PC_01_BP_Base`, `PC_01_BP_Sanjuk` | 3 | 중간 |
| CHT_PC_Travel | `AC_Travel_Logic` | 1 | 낮음 |

---

## 2. 진단

### 문제점
1. **명명 5종 혼재**: `*AnimChooser_*` / 무접두 / `<Char>_<Sys>` / `CHT_<Char>_<Sys>`
2. **무접두 3개**: `Falling`/`GroundIdle`/`GroundMoving`은 다른 BP의 일반 이름과 충돌 위험
3. **캐릭터 ID 표기 불일치**: `Evie` vs `PC_01` vs `PC` 혼재
4. **Root vs Sub 가시성 없음**: `EvieAnimChooser_StateMachine`이 root인지 이름만 보고 모름

### 좋은 점 (유지)
- Locomotion은 `SBStateMachineChooserOut` struct로 통일
- 폴더 분리는 이미 시스템별 (StateMachine / OverlaySystem / TravelSystem)
- Travel은 자체 Input/Output struct 패턴 정착

---

## 3. 제안 컨벤션 (B+C 조합)

**규칙**: `CHT_<Owner>_<Category>[_<SubKey>]`

- Prefix: `CHT_` (ChooserTable 약자, SB2 기존 사용)
- Owner: `PC01` (캐릭터 ID, `Evie`/`PC` 폐지)
- Category: `LocoRoot` / `Loco` / `Overlay` / `Travel` (필요 시 추가)
- SubKey: 선택적 (Loco substate 식별)

### Rename 매핑

| # | 현재 | → 신규 | dirty 에셋 |
|---|------|--------|----------|
| 1 | `StateMachine/EvieAnimChooser_StateMachine` | `StateMachine/CHT_PC01_LocoRoot` | PC_01_ABP |
| 2 | `StateMachine/GroundIdle` | `StateMachine/CHT_PC01_Loco_GroundIdle` | (root만) |
| 3 | `StateMachine/GroundMoving` | `StateMachine/CHT_PC01_Loco_GroundMoving` | (root만) |
| 4 | `StateMachine/Falling` | `StateMachine/CHT_PC01_Loco_Falling` | (root만) |
| 5 | `OverlaySystem/PC_01_Overlays` | `OverlaySystem/CHT_PC01_Overlay` | PC_01_BP × 3 |
| 6 | `TravelSystem/CHT_PC_Travel` | `TravelSystem/CHT_PC01_Travel` | AC_Travel_Logic |

**폴더는 옮기지 않음** — 시스템별 폴더(StateMachine/OverlaySystem/TravelSystem) 유지가 안전. Rename만으로 가시성 충분.

---

## 4. 실행 순서 (위험 낮은 것부터)

### Step 1 — Locomotion sub 3개 rename (가장 안전)
- `GroundIdle` → `CHT_PC01_Loco_GroundIdle`
- `GroundMoving` → `CHT_PC01_Loco_GroundMoving`
- `Falling` → `CHT_PC01_Loco_Falling`
- 영향: root 1개만 자동 fixup
- 검증: PIE에서 idle/move/fall 정상 재생 확인

### Step 2 — Locomotion root rename
- `EvieAnimChooser_StateMachine` → `CHT_PC01_LocoRoot`
- 영향: PC_01_ABP 1개
- 검증: ABP 컴파일 + PIE

### Step 3 — Travel rename
- `CHT_PC_Travel` → `CHT_PC01_Travel`
- 영향: AC_Travel_Logic 1개
- 검증: Mantle/Hurdle 동작 확인

### Step 4 — Overlay rename (마지막, dirty 가장 많음)
- `PC_01_Overlays` → `CHT_PC01_Overlay`
- 영향: PC_01_BP × 3 (Base/Sanjuk/메인)
- 검증: 가드 ON/OFF 시 Overlay 전환 정상

---

## 5. 알려진 제약

- **Monolith에 rename 액션 없음** (실측 v0.12.0): editor/project namespace 26개 액션 중 rename/move/fixup 0개 (`delete_assets`만 존재). **에디터에서 수동 rename 필수**.
- **Monolith Chooser 편집 protected** — Row 수정도 에디터 수동 (`reference_monolith_animgraph_editing_limits.md`)
- **P4 체크아웃**: 각 Step마다 영향 받는 모든 에셋 체크아웃 → rename → save → submit
- **Redirector**: 에디터 rename 후 redirector 자동 생성됨. 모든 referrer 컴파일 후 Content Browser에서 `Fix Up Redirectors in Folder` 실행
- **백업**: Step 시작 전 P4 changelist 별도 분리 (롤백 용)

---

## 6. 작업 흐름 (에디터 수동 기준)

각 Step별 표준 절차:

1. P4에서 신규 changelist 생성 (`PC_01 Chooser rename - Step N`)
2. Content Browser에서 대상 chooser 우클릭 → `Rename` (또는 F2)
3. 신규 이름 입력 → Enter (참조 ABP/BP 자동 dirty)
4. 영향 받는 referrer 에셋 컴파일 (Compile All Affected)
5. 폴더에서 `Fix Up Redirectors in Folder` 실행 (redirector 정리)
6. PIE 검증 (Step별 시나리오)
7. P4 submit

---

## 7. 사용자 결정 필요

1. **컨벤션 승인** — `CHT_PC01_<Category>_<Sub>` 패턴 OK?
2. **순서 OK?** — Step 1(Loco sub 3개)부터 진행?
3. **수동 진행** — Monolith rename 불가 확인됨. 사용자가 에디터에서 직접 rename → 내가 옆에서 검증 스크립트로 dirty/redirector 상태 확인하는 흐름으로 진행?
