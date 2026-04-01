# 04. Workspace & System 생성

[← 이전: 사전 준비](./03_PREREQUISITES.md) | [목차](./00_INDEX.md) | [다음: Data Interface 구성 →](./05_DATA_INTERFACE.md)

---

## 4.1 개요

이 단계에서는 UAF의 두 가지 최상위 에셋을 생성합니다:

```
Workspace (작업 공간)
  └── System (실행 흐름)
```

**Workspace**는 모든 UAF 에셋을 묶는 컨테이너이고,
**System**은 매 프레임의 실행 순서를 정의합니다.

---

## 4.2 Workspace 생성

### 단계별 생성

1. **Content Browser**에서 `/Game/Animation/UAF/SandboxCharacter/Workspace/` 폴더로 이동합니다

2. 빈 공간에서 **우클릭** → **Animation** → **AnimNext Workspace**를 선택합니다

   > 이 메뉴가 보이지 않으면 AnimNext 플러그인이 활성화되지 않은 것입니다.
   > [03. 사전 준비](./03_PREREQUISITES.md)로 돌아가세요.

3. 이름을 입력합니다: `WS_SandboxCharacter`

4. 더블클릭하여 Workspace 에디터를 엽니다

### Workspace 에디터 화면 구성

```
┌─────────────────────────────────────────────────────────┐
│  WS_SandboxCharacter - Workspace Editor                  │
├──────────────┬──────────────────────────────────────────┤
│              │                                           │
│  Asset Tree  │            Graph Editor                   │
│              │                                           │
│  ▶ Systems   │     (여기서 System, Module, Graph를       │
│  ▶ Modules   │      연결하고 편집합니다)                  │
│  ▶ Graphs    │                                           │
│  ▶ Variables │                                           │
│              │                                           │
├──────────────┼──────────────────────────────────────────┤
│              │            Details Panel                   │
│  My Assets   │     (선택한 에셋의 속성 편집)              │
│              │                                           │
└──────────────┴──────────────────────────────────────────┘
```

### Workspace에 포함될 에셋 미리보기

최종적으로 이 Workspace에는 다음이 포함됩니다:

| 에셋 | 타입 | 역할 |
|------|------|------|
| `Sys_SandboxCharacter` | System | 실행 흐름 정의 |
| `Mod_SandboxCharacter_Logic` | Module | 로직 업데이트 |
| `AG_SandboxCharacter` | Animation Graph | 애니메이션 처리 |

---

## 4.3 System 생성

### System이란?

System은 **"무엇을 어떤 순서로 실행할지"**를 정의하는 에셋입니다.
기존 ABP의 `BlueprintThreadSafeUpdateAnimation` → `Update_Logic` 흐름에 해당합니다.

### 생성 단계

1. Workspace 에디터의 **Asset Tree**에서 **Systems** 우클릭
   → **Add New System**

2. 이름: `Sys_SandboxCharacter`

3. System 그래프가 열립니다

### System 실행 흐름 설정

System 그래프에서 다음 실행 흐름을 구성합니다:

```
[System Start]
     │
     ▼
[Generate Reference Pose]     ← 1단계: 기본 포즈 생성
     │
     ▼
[Update Data Interface]       ← 2단계: 외부 데이터 수집
     │
     ▼
[Execute Module]              ← 3단계: 로직 실행
     │  (Mod_SandboxCharacter_Logic)
     ▼
[Calculate Trajectory]        ← 4단계: Motion Matching용 궤적
     │
     ▼
[Execute Animation Graph]     ← 5단계: 애니메이션 평가
     │  (AG_SandboxCharacter)
     ▼
[Write Pose to Mesh]          ← 6단계: 최종 포즈 적용
     │
     ▼
[System End]
```

### 각 단계 노드 추가 방법

System 그래프에서:

1. **빈 공간 우클릭** → 노드 검색 → 원하는 노드 추가

2. **노드 연결**: 출력 핀 → 입력 핀으로 드래그

3. 주요 노드 타입:

| 노드 | 검색어 | 역할 |
|------|--------|------|
| Generate Reference Pose | "Reference Pose" | 스켈레톤 기본 포즈 |
| Execute Module | "Module" | Module 에셋 실행 |
| Execute Graph | "Graph" / "Animation Graph" | AnimGraph 실행 |
| Write Pose | "Write Pose" / "Apply" | 메시에 포즈 적용 |

### 기존 ABP와의 실행 순서 비교

```
기존 ABP:                           UAF System:
┌─────────────────────────┐         ┌─────────────────────────┐
│ NativeUpdateAnimation   │         │ Generate Reference Pose │
│   ↓                     │         │   ↓                     │
│ ThreadSafeUpdate        │         │ Update Data Interface   │
│   ↓                     │    ≈    │   ↓                     │
│ Update_Logic            │         │ Execute Module          │
│   ↓                     │         │   ↓                     │
│ AnimGraph 평가           │         │ Execute Animation Graph │
│   ↓                     │         │   ↓                     │
│ 포즈 → SMC              │         │ Write Pose to Mesh      │
└─────────────────────────┘         └─────────────────────────┘
```

---

## 4.4 Workspace 공유 변수 정의

Workspace 레벨에서 공유 변수를 정의할 수 있습니다.
이 변수들은 Module과 Animation Graph에서 모두 접근 가능합니다.

### 공유 변수 추가 방법

1. Workspace 에디터의 **Variables** 섹션 클릭
2. **+** 버튼으로 변수 추가

### 기존 ABP 변수 중 공유가 필요한 것들

모든 76개 변수를 공유 변수로 만들 필요는 없습니다.
Data Interface가 대부분 자동 처리하기 때문입니다.

**Workspace 공유 변수로 정의할 것** (Module ↔ Graph 간 공유 필요):

| 변수명 | 타입 | 용도 |
|--------|------|------|
| `StateMachineState` | byte (enum) | 현재 SM 상태 (Module에서 설정, Graph에서 읽기) |
| `BlendStackInputs` | S_BlendStackInputs | 블렌드 스택 입력 |
| `MovementDirection` | byte (enum) | 이동 방향 |
| `TargetRotation` | Rotator | 목표 회전값 |
| `OffsetRootBoneEnabled` | bool | 루트 오프셋 활성화 |

**Data Interface가 대체할 것** (공유 변수 불필요):

| 기존 변수 | Data Interface 소스 |
|----------|-------------------|
| `Velocity`, `Acceleration`, `Speed2D` | MoverComponent에서 자동 |
| `MovementMode`, `Gait`, `Stance` | MoverComponent에서 자동 |
| `CharacterTransform` | Actor Transform에서 자동 |
| `Trajectory` | Pose Search가 자동 생성 |

---

## 4.5 저장 및 확인

### 저장

1. Workspace 에디터에서 **Ctrl+S**로 저장
2. Content Browser에서 Workspace 에셋 우클릭 → **Save**

### 확인 체크리스트

- [ ] `WS_SandboxCharacter` Workspace 생성됨
- [ ] `Sys_SandboxCharacter` System 생성됨
- [ ] System 실행 흐름 노드 배치됨 (아직 Module/Graph 연결은 안 해도 됨)
- [ ] Workspace 공유 변수 기본 정의됨
- [ ] 에셋 저장 완료

### 현재 진행 상태

```
Phase 0: 사전 준비              ✅ 완료
Phase 1: 기반 구축
  ├── Workspace 생성            ✅ 완료 (이번 단계)
  ├── System 생성               ✅ 완료 (이번 단계)
  └── Data Interface 정의       ⬜ 다음 단계
Phase 2: 애니메이션 파이프라인   ⬜ 대기
Phase 3: 로직 이전              ⬜ 대기
Phase 4: 통합 & 검증            ⬜ 대기
```

---

## 4.6 문제 해결

### "AnimNext Workspace" 메뉴가 안 보일 때

1. 플러그인 활성화 확인: Edit → Plugins → "AnimNext" 검색
2. 에디터 재시작
3. `.uproject` 파일에서 직접 플러그인 확인

### System 노드를 찾을 수 없을 때

1. Workspace를 먼저 생성해야 System을 추가할 수 있습니다
2. Workspace 에디터 내에서 System을 생성하세요 (Content Browser가 아님)
3. UE 5.7 기준으로 일부 노드 이름이 다를 수 있습니다. 키워드로 검색하세요.

### 에디터 크래시

1. 자주 저장하세요 (Ctrl+S)
2. 자식 노드를 더블클릭하지 마세요 → 우클릭 메뉴 사용
3. 크래시 발생 시 `Saved/Logs/` 폴더의 로그를 확인하세요

---

[← 이전: 사전 준비](./03_PREREQUISITES.md) | [목차](./00_INDEX.md) | [다음: Data Interface 구성 →](./05_DATA_INTERFACE.md)
