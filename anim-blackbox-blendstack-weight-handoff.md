# BlendStack 시퀀스별 블렌드 weight 노출 — C++ 핸드오프

애님 블랙박스(리와인드 베이크) 툴에서 **순정 Rewind Debugger "웨이트 블렌드" 트랙과 동일한** "동시 재생 중인 시퀀스별 실제 blend weight"를 얻기 위한 작업 스펙.

## 배경 / 왜 C++가 필요한가

- 동시 시퀀스별 weight는 `FAnimNode_BlendStack`(MotionMatching BlendStack)의 내부 `TArray<FBlendStackAnimPlayer> AnimPlayers` 에 있고, 각 weight는 `FBlendStackAnimPlayer::GetBlendInWeight()` (C++ 메서드, private 멤버 `TotalBlendInTime`/`CurrentBlendInTime` 기반 계산)로만 얻는다.
- **BP/Python 미노출 확인**: `UBlendStackAnimNodeLibrary` 는 현재 최상단 1개(`GetCurrentBlendStackAnimAsset`)만 노출. `UAnimInstance` 의 weight 함수는 슬롯 몽타주용(`Blueprint_GetSlotMontageLocalWeight`)뿐. per-sample 배열/weight BP 함수 없음.
- 따라서 `AnimPlayers` 를 순회해 `(이름, weight)` 를 뽑는 **작은 C++ 접근자 1개**가 필요하다. (그 외 ABP 배선 + 툴 렌더는 BP/Python)

소스 근거: `Engine/Plugins/.../AnimNode_BlendStack.h` (UE 5.7)
- `FAnimNode_BlendStack_Standalone::AnimPlayers` (public `TArray<FBlendStackAnimPlayer>`)
- `FBlendStackAnimPlayer` public: `GetAnimationName()` / `GetAnimationAsset()` / `GetBlendInWeight()` / `GetBlendInPercentage()` / `IsActive()`

## ① C++ — BlueprintCallable 접근자 (이것만 C++)

게임 모듈에 추가. 모듈 의존성에 BlendStack 노드가 있는 모듈(`AnimGraphRuntime` 또는 BlendStack 정의 모듈) 추가 필요.

```cpp
#include "AnimNodes/AnimNode_BlendStack.h"
#include "BlendStack/BlendStackAnimNodeLibrary.h"   // FBlendStackAnimNodeReference
#include "Kismet/BlueprintFunctionLibrary.h"

// UBlueprintFunctionLibrary 파생 클래스 안에:
UFUNCTION(BlueprintCallable, Category="BlendStack Debug", meta=(BlueprintThreadSafe))
static void GetBlendStackSamples(const FBlendStackAnimNodeReference& Ref,
                                 TArray<FName>& OutAnimNames,
                                 TArray<float>& OutWeights)
{
    OutAnimNames.Reset();
    OutWeights.Reset();
    FAnimNode_BlendStack* Node = Ref.GetAnimNodePtr<FAnimNode_BlendStack>();
    if (!Node) return;
    for (const FBlendStackAnimPlayer& P : Node->AnimPlayers)   // public 배열
    {
        const UAnimationAsset* A = P.GetAnimationAsset();
        OutAnimNames.Add(A ? A->GetFName() : NAME_None);
        OutWeights.Add(P.GetBlendInWeight());                  // 실제 mix weight
    }
}
```

주의: `GetBlendInWeight()` 가 정규화(합≈1) weight 인지, raw 인지는 빌드 후 로그로 확인 권장(필요 시 합으로 나눠 정규화). 비활성(blending-out) 샘플도 포함됨 — 전부 반환(렌더 측에서 필터).

## ② ABP — BlendStack 노드에 호출 배선 (BP)

PC_01_ABP (프로덕션 — 편집 승인 필요):

1. AnimInstance 멤버 변수 2개 추가:
   - `BlendStackSampleNames` : Array of Name (Transient)
   - `BlendStackSampleWeights` : Array of Float (Transient)
2. AnimGraph 의 BlendStack 노드에 **anim node function (On Update)** 바인딩:
   - 함수 안에서 `node`(BlendStack 노드 reference) → `UBlendStackAnimNodeLibrary::ConvertToBlendStackNode(node)` 로 `FBlendStackAnimNodeReference` 획득
   - `GetBlendStackSamples(ref, BlendStackSampleNames, BlendStackSampleWeights)` 호출 → 두 멤버 배열에 매 틱 기록
   - (SB2 ABP 는 이미 anim node function 바인딩을 쓰므로 패턴 동일)

→ 결과: 매 틱 `BlendStackSampleNames[i]` / `BlendStackSampleWeights[i]` 에 현재 BlendStack 의 (시퀀스명, weight) 쌍이 채워짐.

## ③ 툴 (Python — 내가 처리, ①② 들어오면 바로)

- 캡처: `ai.get_editor_property("BlendStackSampleNames")` / `"BlendStackSampleWeights")` 를 매 프레임 수집 (이미 변수 캡처 인프라 있음).
- 베이크: 프레임별 (이름→weight) 맵 → 시퀀스별 weight 시계열 → **Rewind Debugger "웨이트 블렌드" 처럼 스택 리본** 렌더 (시퀀서 섹션 Weight 또는 툴 tkinter 패널).
- 이때 현재 재구성(Cur Anim 기반 근사)을 **진짜 weight 로 교체** → 3-way 동시 블렌드까지 정확.

## 검증

1. 빌드 후 PIE → BlendStack 노드 함수가 매 틱 호출되는지 (배열에 값 들어오는지) 로그.
2. 우리 툴 캡처에서 `BlendStackSampleWeights` 합이 ~1 인지, 전환 시 2~3개가 동시에 0<w<1 로 뜨는지.
3. 순정 Rewind Debugger "웨이트 블렌드" 트랙과 같은 시점 비교 → 이름/weight 일치 확인.

## 범위 한 줄 요약

**C++는 `GetBlendStackSamples` 함수 1개뿐.** ABP는 변수 2개 + 노드 함수 배선, 툴은 캡처/렌더 — 모두 BP/Python(내가 처리).
