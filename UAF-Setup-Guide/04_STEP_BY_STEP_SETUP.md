# 04. 단계별 셋업

[<- 이전: 핵심 에셋 이해](./03_CORE_ASSETS.md) | [목차](./00_INDEX.md) | [다음: System EventGraph ->](./05_SYSTEM_EVENTGRAPH.md)

---

> 이 가이드는 David Martinez의 튜토리얼과 커뮤니티 자료를 기반으로 UE 5.7에서 검증된 절차입니다.

## 4.1 사전 준비

- UE 5.7 설치 (소스 빌드 권장)
- 필수 플러그인 활성화 완료 ([02장 참조](./02_PLUGIN_SETUP.md))
- 에디터 재시작 완료

---

## 4.2 Step 1: UAF 에셋 생성

Content Browser에서 에셋을 저장할 폴더로 이동합니다.

### 방법 A: UAF Asset Wizard (자동)

1. Content Browser 빈 공간 **우클릭**
2. **Animation -> UAF Asset Wizard** 선택
3. Destination Folder 지정
4. Skeletal Mesh 선택 (예: `SK_UEFN_Mannequin`)
5. **Create Assets** 클릭

Wizard가 자동으로 Workspace, System, Shared Variables를 생성합니다.

### 방법 B: 수동 생성

Content Browser 빈 공간 우클릭 -> Animation 에서 하나씩 생성:

| 순서 | 메뉴 항목 | 이름 예시 | 설명 |
|------|----------|----------|------|
| 1 | UAF Workspace | `WS_MyCharacter` | 최상위 컨테이너 |
| 2 | UAF System | `Sys_MyCharacter` | 실행 흐름 |
| 3 | UAF Animation Graph | `AG_MyCharacter` | 애니메이션 로직 |
| 4 | UAF Shared Variables | `SV_MyCharacter` | 공유 변수 (선택) |

---

## 4.3 Step 2: Workspace에 에셋 등록

1. `WS_MyCharacter`를 **더블클릭**하여 Workspace 에디터 열기
2. Content Browser에서 `Sys_MyCharacter`와 `AG_MyCharacter`를 **Workspace 패널로 드래그 앤 드롭**
3. 또는 Workspace 패널의 **+ Add** 버튼 사용

등록 후 Workspace 트리:
```
WS_MyCharacter
  |-- Sys_MyCharacter (System)
  |-- AG_MyCharacter (Animation Graph)
  +-- External Modules / Graphs
```

---

## 4.4 Step 3: 캐릭터 Blueprint에 AnimNext Component 추가

### 3-1. 캐릭터 BP 열기

기존 캐릭터 BP 또는 새 BP 생성:
- Mover 사용 시: `BaseAnimatedMannyPawn`을 부모 클래스로 선택
- 기존 캐릭터: 기존 Character BP 사용

### 3-2. AnimNext Component 추가

1. Components 패널에서 **Add Component** 클릭
2. **"AnimNext"** 검색
3. **AnimNext Component** (또는 AnimNext Actor Component) 추가

### 3-3. System 할당

1. 추가된 AnimNext Component 선택
2. Details 패널에서 **Module** (또는 **System**) 속성 찾기
3. `Sys_MyCharacter` 할당
4. **Auto Activate**: 체크

### 3-4. SkeletalMeshComponent 애니메이션 비활성화

> **매우 중요!** 이 단계를 빠뜨리면 UAF가 작동하지 않습니다!

1. SkeletalMeshComponent 선택
2. Details 패널에서 **Animation Mode** 또는 **Enable Animation** 찾기
3. **애니메이션을 완전히 비활성화**
   - Animation Mode: `No Animation`으로 설정
   - 또는 Anim Class: `None`으로 클리어
   - 또는 Enable Animation: 체크 해제

```
변경 전:
  SkeletalMeshComponent
    Animation Mode: Use Anim Blueprint
    Anim Class: ABP_MyCharacter

변경 후:
  SkeletalMeshComponent
    Animation Mode: No Animation    <- 변경!
    Anim Class: None                <- 클리어!
```

---

## 4.5 Step 4: System EventGraph 구성

> 자세한 내용은 [05장 System EventGraph](./05_SYSTEM_EVENTGRAPH.md) 참조

### Initialize 이벤트
실행 핀에서 드래그 -> 노드 추가:
```
Initialize -> Make Reference Pose
```

### PrePhysics 이벤트
실행 핀에서 드래그 -> 노드 추가:
```
PrePhysics -> Evaluate Animation Graph (AG_MyCharacter 지정) -> Write Pose to Mesh
```

### Compile
상단 **Compile** 버튼 클릭 -> 에러 없으면 성공

---

## 4.6 Step 5: Variable Bindings 설정

System의 Details 패널에서 변수 바인딩을 구성합니다.

| 변수명 | 타입 | 바인딩 소스 |
|--------|------|------------|
| `Mover_Component` | Mover Component | `Current Actor.Property` |
| `Skeletal_Mesh_Component` | Skeletal Mesh Component | `Current Actor.Get SkeletalMeshComponent` |
| `CurrentActor` | Object | `Current Actor` |
| `Reference_Pose` | ReferencePose | `None` |

### 바인딩 추가 방법
1. 바인딩 테이블에서 **+** 버튼 클릭
2. 변수 이름과 타입 지정
3. 바인딩 소스 드롭다운에서 **"Add a New Locator Fragment"** 선택:
   - **Current Actor** -- 소유 Actor 참조
   - **Component** -- Actor의 특정 컴포넌트
   - **Property** -- 컴포넌트의 특정 프로퍼티
   - **Function** -- 함수 호출 결과

---

## 4.7 Step 6: Animation Graph 구성

> 자세한 내용은 [06장 Animation Graph](./06_ANIMATION_GRAPH.md) 참조

기본 구성:
```
[Evaluate Chooser]  ->  [Motion Matching]  ->  Output Pose
  (Chooser Table에서       (DB + Trajectory로
   PSD 목록 가져오기)        최적 포즈 검색)
```

---

## 4.8 Step 7: 테스트

1. 레벨에 캐릭터 BP 배치
2. **Play** (PIE) 실행
3. 캐릭터가 Motion Matching 애니메이션으로 움직이면 성공!

---

## 4.9 요약 플로우차트

```
1. 플러그인 활성화 (UAF + UAF Anim Graph)
       |
2. UAF 에셋 생성 (Workspace, System, Animation Graph)
       |
3. Workspace에 System + Graph 등록
       |
4. Character BP에 AnimNextComponent 추가
       |
5. System 할당 + SkeletalMesh 애니메이션 비활성화
       |
6. System EventGraph 구성 (Initialize + PrePhysics)
       |
7. Variable Bindings 설정
       |
8. Animation Graph 구성 (Chooser + Motion Matching)
       |
9. Compile & 테스트
```

---

[<- 이전: 핵심 에셋 이해](./03_CORE_ASSETS.md) | [목차](./00_INDEX.md) | [다음: System EventGraph ->](./05_SYSTEM_EVENTGRAPH.md)
