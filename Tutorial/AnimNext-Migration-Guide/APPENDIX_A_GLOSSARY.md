# 부록 A: 용어 사전

[← 이전: 디버깅 & 검증](./10_DEBUGGING_AND_VALIDATION.md) | [목차](./00_INDEX.md) | [다음: 참고 자료 →](./APPENDIX_B_REFERENCES.md)

---

## ABP ↔ UAF 용어 대응표

| ABP 용어 | UAF 용어 | 설명 |
|---------|---------|------|
| Animation Blueprint (ABP) | **Workspace** | 최상위 에셋 컨테이너 |
| AnimInstance | **AnimNextComponent** | 캐릭터에 부착되는 컴포넌트 |
| EventGraph | **Module** | 로직 작성 공간 |
| AnimGraph | **Animation Graph** | 애니메이션 평가 그래프 |
| Animation Node | **Trait** | 애니메이션 기능 단위 |
| Node Tree | **TraitStack** | Trait의 스택 구조 |
| State Machine | **Chooser Table + Motion Matching** | 상태 기반 → 데이터 기반 |
| Transition Rule | **Chooser Row** | 조건 기반 전환 규칙 |
| AnimInstance Variable | **Data Interface Variable** | 데이터 바인딩 변수 |
| BlueprintThreadSafeUpdate | **System** | 실행 흐름 정의 |
| Output Pose | **Write Pose to Mesh** | 최종 포즈 출력 |
| Cast to ABP | **(불필요)** | Data Interface가 자동 처리 |
| Get Anim Instance | **(불필요)** | AnimNextComponent가 직접 관리 |

---

## UAF 핵심 용어 사전

### A

**Additive Trait**
: Base Trait 위에 추가되는 Trait. 여러 개를 쌓을 수 있다. 예: Aim Offset, Lean, Foot IK.

**AnimNextComponent**
: Pawn에 추가하는 UAF 컴포넌트. Workspace를 참조하고 매 프레임 애니메이션을 평가한다.

**Animation Graph**
: TraitStack을 포함한 애니메이션 평가 그래프. 기존 AnimGraph에 해당.

### B

**Base Trait**
: TraitStack의 기반 포즈를 제공하는 Trait. 하나의 스택에 1개만 존재 가능. 예: Motion Matching, Sequence Player.

### C

**Chooser Table**
: 조건-결과 매핑 테이블. 런타임에 조건을 평가하여 최적의 결과(DB, 에셋 등)를 반환한다.

### D

**Data Interface**
: 컴포넌트 간 데이터를 자동으로 바인딩하는 시스템. 기존의 수동 변수 전달을 대체한다.

### E

**EvaluationProgram**
: TraitStack의 평가 태스크를 저장하는 프로그램. FEvaluationVMStack에서 실행된다.

### F

**FInstanceData**
: Trait의 인스턴스별 동적 데이터. 각 애니메이션 그래프 인스턴스마다 별도로 존재한다.

**FSharedData**
: Trait의 읽기 전용 공유 데이터. 같은 그래프의 모든 인스턴스가 공유한다.

### L

**Latent Property**
: SharedData이지만 인스턴스화가 필요한 프로퍼티. FInstanceData 뒤에 배치된다.

### M

**MemStack**
: TraitStack 평가에 사용되는 메모리 스택. LIFO 방식으로 깊이 우선 탐색을 수행한다.

**Module**
: 로직을 작성하는 공간. 기존 ABP의 EventGraph에 해당. Data Interface와 연동하여 변수를 계산한다.

**Motion Matching**
: Pose Search 기반 애니메이션 선택 시스템. 현재 포즈와 궤적을 기반으로 DB에서 최적 포즈를 검색한다.

### P

**Pose Search Database**
: Motion Matching에서 사용하는 애니메이션 데이터베이스. 인덱싱된 포즈와 궤적 데이터를 포함한다.

**PublicVariablesProxy**
: AnimNextComponent가 Game Thread와 Worker Thread 간 데이터를 안전하게 교환하는 프록시.

### R

**RigVM**
: UAF의 실행 가상 머신. 멀티스레드 애니메이션 평가를 가능하게 한다.

### S

**System**
: UAF의 실행 흐름 정의 에셋. "무엇을 어떤 순서로 실행할지"를 선언한다.

### T

**Trait**
: 애니메이션 기능의 기본 단위. Base Trait(기반 포즈)과 Additive Trait(추가 효과)로 나뉜다.

**TraitStack**
: 1개의 Base Trait + N개의 Additive Trait로 구성된 스택. 기존 노드 트리를 레이어 쌓기로 대체한다.

**Trajectory**
: Motion Matching에서 캐릭터의 과거/현재/미래 이동 궤적. 포즈 검색의 핵심 입력 데이터.

### U

**UAF (Unreal Animation Framework)**
: AnimNext의 공식 리브랜딩 명칭 (UE 5.7~). 차세대 애니메이션 프레임워크.

### W

**Workspace**
: UAF의 최상위 컨테이너 에셋. System, Module, Animation Graph, 공유 변수를 모두 관리한다.

---

[← 이전: 디버깅 & 검증](./10_DEBUGGING_AND_VALIDATION.md) | [목차](./00_INDEX.md) | [다음: 참고 자료 →](./APPENDIX_B_REFERENCES.md)
