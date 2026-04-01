# 09. 기술 아키텍처

[<- 이전: Mover 2.0 연동](./08_MOVER_INTEGRATION.md) | [목차](./00_INDEX.md) | [다음: 문제 해결 ->](./10_TROUBLESHOOTING.md)

---

> 이 장은 RemRemRemRe의 기술 분석을 기반으로 UAF 내부 구조를 설명합니다.
> 초보자는 건너뛰어도 됩니다.

## 9.1 RigVM 실행 엔진

UAF의 모든 로직은 **RigVM (Rig Virtual Machine)** 위에서 실행됩니다.
원래 Control Rig을 위해 개발되었으나 UAF의 런타임으로 확장되었습니다.

### RigVM 특성
- **멀티스레드**: 여러 Worker Thread에서 동시 실행
- **데이터 지향**: 연속 메모리 버퍼에서 작업
- **스택 기반**: MemStack (LIFO)을 사용한 평가 (재귀 함수 호출 아님)
- **캐시 친화적**: 연속 메모리 레이아웃으로 캐시 미스 최소화

### 주요 RigVM 타입

| 타입 | 역할 |
|------|------|
| `FRigUnit_AnimNextRunAnimationGraph_v2` | Graph 실행 진입점 |
| `FRigUnit_AnimNextExecuteBindings_GT` | Game Thread 바인딩 |
| `FRigUnit_AnimNextExecuteBindings_WT` | Worker Thread 바인딩 |
| `FRigUnit_AnimNextModuleEventBase` | Module 이벤트 기본 클래스 |

---

## 9.2 Trait 시스템

### 매크로 기반 Trait 정의

```cpp
// 1단계: 인터페이스 선언
DECLARE_ANIM_TRAIT_INTERFACE(IMyTraitInterface)

// 2단계: 트레이트 선언
class FMyTrait : public FAdditiveTrait
{
    DECLARE_ANIM_TRAIT(FMyTrait, 0x12345678, FAdditiveTrait)

    // 공유 데이터 (읽기 전용, 설정값)
    using FSharedData = FMyTraitSharedData;

    // 인스턴스 데이터 (동적, 런타임)
    using FInstanceData = FMyTraitInstanceData;
};

// 3단계: 구현 생성
GENERATE_ANIM_TRAIT_IMPLEMENTATION(FMyTrait, ...)

// 4단계: 전역 레지스트리 등록
AUTO_REGISTER_ANIM_TRAIT(FMyTrait)
AUTO_REGISTER_ANIM_TRAIT_INTERFACE(IMyTraitInterface)
```

### Trait Interface UID
- FNV1a 해시로 클래스 이름에서 생성
- 컴파일 타임 상수로 빠른 런타임 조회

---

## 9.3 노드 메모리 아키텍처

### FNodeTemplate
- TraitSet의 조합 템플릿
- 여러 Animation Graph에서 동일한 템플릿 공유 가능
- Trait를 연속 `FTraitTemplate` 메모리로 저장

```
FNodeTemplate:
  +-- NodeSharedDataSize (정렬된 공유 데이터 크기)
  +-- NodeInstanceDataSize (정렬된 인스턴스 데이터 크기)
  +-- FTraitTemplate[] (연속 메모리)
```

### FNodeDescription
- Animation Graph 내의 읽기 전용 데이터 (8바이트 + 공유 데이터)
- `UAnimNextAnimationGraph::SharedDataBuffer`에 저장
- `TemplateHandle`로 FNodeTemplate 참조

### FNodeInstance
- 런타임 인스턴스 데이터 (16바이트 + 인스턴스/Latent 데이터)
- 참조 카운팅 내장
- 활성 Animation Graph 인스턴스별 생성

---

## 9.4 전역 레지스트리

| 레지스트리 | 용도 | 최적화 |
|-----------|------|--------|
| **FTraitRegistry** | Trait 객체 관리 | 8KB StaticTraitBuffer (메모리 로컬리티) |
| **FTraitInterfaceRegistry** | Interface ID -> 스마트 포인터 맵 | 단순 맵 |
| **FNodeTemplateRegistry** | 노드 템플릿 관리 | 연속 메모리 할당 보장 |

---

## 9.5 실행 파이프라인 상세

### Update Phase (FUpdateTraversalContext)
```
1. MemStack에 스택 할당 (재귀 없음)
2. Trait 트리를 깊이 우선 탐색
3. 각 Trait를 2번 실행:
   - IUpdate::PreUpdate  (전방향)
   - IUpdate::PostUpdate (후방향)
4. OnBecomeRelevant 콜백 (활성화 시)
```

### Evaluate Phase (FEvaluateTraversalContext)
```
1. FEvaluationProgram에서 FAnimNextEvaluationTask 목록 로드
2. FEvaluationVMStack에서 태스크 실행
3. 태스크 = 평가 가상 머신의 마이크로 명령어
4. 입출력은 내부 스택 상태를 통해 관리
```

---

## 9.6 AnimNextComponent C++ API

```cpp
class UAnimNextComponent : public UActorComponent
{
    // 실행할 UAF Module/System
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    TObjectPtr<UAnimNextModule> Module;

    // 변수 설정 (여러 타입 오버로드)
    void SetVariable(FName Name, int32 Value);
    void SetVariable(FName Name, float Value);
    void SetVariable(FName Name, bool Value);
    void SetVariable(FName Name, FVector Value);

    // 스레드 안전 변수 프록시
    FAnimNextInstanceVariableDataProxy PublicVariablesProxy;

    // 활성화/비활성화
    void SetEnabled(bool bEnabled);
};
```

### Python API

```python
import unreal

comp = unreal.AnimNextComponent()
comp.module          # AnimNextModule 참조
comp.auto_activate   # bool
comp.set_enabled(True)
```

---

## 9.7 엔진 소스 코드 구조

```
Engine/Plugins/Experimental/
  |-- UAF/                          (UE 5.7, 이전: AnimNext/)
  |   |-- UAF/                      핵심 런타임
  |   |   |-- Source/
  |   |       |-- UAF/
  |   |       |   |-- Public/
  |   |       |   |   |-- Component/AnimNextComponent.h
  |   |       |   |   |-- TraitStack.h
  |   |       |   |   |-- Trait.h
  |   |       |   +-- Private/
  |   |       +-- UAFEditor/         에디터 전용
  |   |
  |   |-- UAFAnimGraph/              애니메이션 그래프
  |   |-- UAFUncookedOnly/           에디터 전용 데이터
  |   +-- UAFAnimGraphUncookedOnly/
  |
  |-- UAFPoseSearch/                 Motion Matching 연동
  |-- UAFChooser/                    Chooser Table 연동
  |-- UAFControlRig/                 Control Rig 연동
  |-- UAFWarping/                    워핑 연동
  |-- UAFMirroring/                  미러링 연동
  |-- UAFStateTree/                  StateTree 연동
  |-- MoverAnimNext/                 Mover 연동
  +-- MetaHuman/MetaHumanCharacterUAF/  MetaHuman 연동
```

---

[<- 이전: Mover 2.0 연동](./08_MOVER_INTEGRATION.md) | [목차](./00_INDEX.md) | [다음: 문제 해결 ->](./10_TROUBLESHOOTING.md)
