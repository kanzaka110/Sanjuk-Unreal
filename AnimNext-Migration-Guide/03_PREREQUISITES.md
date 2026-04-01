# 03. 사전 준비

[← 이전: AnimNext 개념 이해](./02_ANIMNEXT_CONCEPTS.md) | [목차](./00_INDEX.md) | [다음: Workspace & System 생성 →](./04_WORKSPACE_AND_SYSTEM.md)

---

## 3.1 필요한 플러그인 확인

UAF를 사용하려면 여러 플러그인이 필요합니다.
일부는 이미 MonolithTest 프로젝트에 활성화되어 있습니다.

### 이미 활성화된 플러그인 (변경 불필요)

이 플러그인들은 기존 ABP에서도 사용 중이므로 그대로 유지합니다:

| 플러그인 | 역할 | 상태 |
|---------|------|------|
| `PoseSearch` | Motion Matching | 이미 활성화 |
| `Chooser` | 조건 기반 에셋 선택 | 이미 활성화 |
| `BlendStack` | 블렌드 스택 | 이미 활성화 |
| `AnimationWarping` | 애니메이션 워핑 | 이미 활성화 |
| `MotionWarping` | 모션 워핑 | 이미 활성화 |
| `Mover` | 차세대 캐릭터 무브먼트 | 이미 활성화 |
| `Locomotor` | 로코모션 보조 | 이미 활성화 |

### 새로 활성화해야 할 플러그인

> **중요**: UE 5.7에서 AnimNext는 **UAF**로 리브랜딩되었습니다.
> 플러그인 이름이 `AnimNext`가 아니라 `UAF`입니다!

| 플러그인 | 역할 | 필수 여부 |
|---------|------|----------|
| `UAF` | UAF 코어 런타임 (Unreal Animation Framework) | **필수** |
| `UAFAnimGraph` | UAF 애니메이션 그래프 | **필수** |
| `UAFPoseSearch` | UAF + Pose Search(Motion Matching) 통합 | **필수** |
| `UAFChooser` | UAF + Chooser 통합 | **필수** |
| `UAFWarping` | UAF + Animation Warping 통합 | 권장 |
| `MoverAnimNext` | Mover + UAF 연동 | **필수** (Mover 프로젝트) |

---

## 3.2 플러그인 활성화 방법

### 방법 1: .uproject 파일 직접 수정 (권장)

1. Unreal Editor를 **종료**합니다

2. 프로젝트 폴더에서 `.uproject` 파일을 텍스트 에디터로 엽니다
   ```
   MonolithTest/MonolithTest.uproject
   ```

3. `"Plugins"` 배열에 다음을 추가합니다:

   ```json
   {
       "Name": "UAF",
       "Enabled": true
   },
   {
       "Name": "UAFAnimGraph",
       "Enabled": true
   },
   {
       "Name": "UAFPoseSearch",
       "Enabled": true
   },
   {
       "Name": "UAFChooser",
       "Enabled": true
   },
   {
       "Name": "UAFWarping",
       "Enabled": true
   },
   {
       "Name": "MoverAnimNext",
       "Enabled": true
   }
   ```

4. 파일을 저장합니다

5. Unreal Editor를 다시 엽니다

### 방법 2: Unreal Editor에서 활성화

1. Unreal Editor 메뉴: **Edit → Plugins**

2. 검색창에 "AnimNext"를 입력합니다

3. 다음 플러그인들을 찾아 **Enabled** 체크박스를 활성화합니다:
   - AnimNext
   - AnimNext AnimGraph
   - AnimNext Uncooked Only

4. **Restart Now** 버튼을 클릭하여 에디터를 재시작합니다

### 활성화 확인

에디터 재시작 후 확인 방법:

1. **Content Browser** → 우클릭 → **Animation** 카테고리 확인
   - "AnimNext Workspace" 등의 에셋 타입이 보이면 성공

2. 또는 **Edit → Plugins** → "AnimNext" 검색 → Enabled 상태 확인

---

## 3.3 프로젝트 폴더 구조 생성

UAF 에셋을 체계적으로 관리하기 위한 폴더 구조를 만듭니다.

### Content Browser에서 폴더 생성

다음 경로로 폴더를 생성합니다:

```
Content/
├── Animation/                          ← 기존 애니메이션 에셋
│   └── UAF/                            ← UAF 전용 폴더 (새로 생성)
│       ├── SandboxCharacter/           ← 캐릭터별 UAF 에셋
│       │   ├── Workspace/              ← Workspace 에셋
│       │   ├── Systems/                ← System 에셋
│       │   ├── Modules/                ← Module 에셋
│       │   ├── Graphs/                 ← Animation Graph 에셋
│       │   └── DataInterfaces/         ← Data Interface 에셋
│       └── Shared/                     ← 공유 에셋 (여러 캐릭터 공통)
│           ├── Choosers/               ← Chooser Table
│           └── Traits/                 ← 커스텀 Trait
│
├── Blueprints/                         ← 기존 폴더 (건드리지 않음)
│   ├── SandboxCharacter_CMC_ABP        ← 기존 ABP (유지)
│   └── ...
│
└── Characters/                         ← 기존 캐릭터 에셋
    └── UEFN_Mannequin/                 ← 기존 스켈레톤/메시
```

### 폴더 생성 순서

1. Content Browser에서 `Content` 폴더 우클릭 → **New Folder** → `Animation`
   (이미 존재하면 건너뛰기)

2. `Animation` 폴더 안에 → **New Folder** → `UAF`

3. `UAF` 폴더 안에 → **New Folder** → `SandboxCharacter`

4. `SandboxCharacter` 폴더 안에 다음 폴더들 생성:
   - `Workspace`
   - `Systems`
   - `Modules`
   - `Graphs`
   - `DataInterfaces`

5. `UAF` 폴더 안에 → **New Folder** → `Shared`

6. `Shared` 폴더 안에:
   - `Choosers`
   - `Traits`

---

## 3.4 테스트 캐릭터 준비

**중요**: 기존 캐릭터를 직접 수정하지 마세요.
별도의 테스트 캐릭터를 만들어 UAF를 실험합니다.

### 테스트 캐릭터 생성 단계

1. **기존 캐릭터 BP 복제**
   - Content Browser에서 기존 캐릭터 BP를 찾습니다
   - 우클릭 → **Duplicate**
   - 이름: `BP_TestCharacter_UAF`
   - 저장 위치: `/Game/Blueprints/Test/`

2. **테스트 레벨 준비**
   - 기존 레벨을 복제하거나 새 레벨을 생성합니다
   - 이름: `L_UAF_Test`
   - 테스트 캐릭터를 배치합니다

3. **버전 관리**
   - 작업 전 반드시 Git/Perforce 커밋
   - UAF 실험은 별도 브랜치에서 진행하는 것을 권장합니다
   ```
   git checkout -b feature/uaf-experiment
   ```

---

## 3.5 기존 에셋 백업 체크리스트

UAF 작업 시작 전 다음을 확인합니다:

- [ ] `.uproject` 파일 백업 완료
- [ ] 기존 ABP (`SandboxCharacter_CMC_ABP`) 수정하지 않을 것을 확인
- [ ] 기존 캐릭터 BP 수정하지 않을 것을 확인
- [ ] Git/Perforce에 현재 상태 커밋 완료
- [ ] (선택) 별도 브랜치 생성 완료
- [ ] UAF 플러그인 3개 활성화 완료
- [ ] 에디터 재시작 후 정상 동작 확인
- [ ] 폴더 구조 생성 완료
- [ ] 테스트 캐릭터 복제 완료

---

## 3.6 빌드 설정 (C++ 프로젝트인 경우)

C++ 프로젝트에서 UAF를 사용하려면 빌드 모듈 의존성을 추가해야 합니다.

### Build.cs 수정

프로젝트의 `.Build.cs` 파일에 다음 모듈을 추가합니다:

```csharp
// MonolithTest.Build.cs
PublicDependencyModuleNames.AddRange(new string[]
{
    // 기존 모듈들...
    "AnimNext",           // UAF 코어
    "AnimNextAnimGraph",  // UAF 애니메이션 그래프
});
```

> **Blueprint-Only 프로젝트**: Build.cs 수정이 필요 없습니다.
> 플러그인 활성화만으로 충분합니다.

---

## 3.7 알려진 문제 및 주의사항 (UE 5.7)

### 에디터 크래시 방지

| 상황 | 주의사항 |
|------|---------|
| Workspace 에디터에서 자식 노드 더블클릭 | 크래시 가능 → 우클릭 메뉴 사용 |
| Module 편집 중 언두(Ctrl+Z) | 불안정할 수 있음 → 자주 저장 |
| 대규모 Animation Graph | 에디터 성능 저하 가능 → 그래프 분할 권장 |

### 호환성 참고

- UAF는 `SkeletalMeshComponent`의 애니메이션을 **반드시 비활성화**해야 합니다
- UAF와 기존 ABP를 **동시에 사용할 수 없습니다** (같은 캐릭터에서)
- Pose Search DB, Chooser Table은 ABP와 UAF에서 **공유 가능**합니다

---

[← 이전: AnimNext 개념 이해](./02_ANIMNEXT_CONCEPTS.md) | [목차](./00_INDEX.md) | [다음: Workspace & System 생성 →](./04_WORKSPACE_AND_SYSTEM.md)
