# UE C++ / Blueprint 코딩 컨벤션

## 네이밍 규칙

| 대상 | 접두사 | 예시 |
|------|--------|------|
| Actor | A | `AMyCharacter` |
| UObject | U | `UAnimInstance` |
| Interface | I | `IInteractable` |
| Struct | F | `FAnimationData` |
| Enum | E | `ELocomotionState` |
| Template | T | `TArray`, `TMap` |
| Bool 변수 | b | `bIsMoving` |
| Widget (UMG) | W (선택) | `WMainHUD` |

## UPROPERTY / UFUNCTION 패턴

```cpp
// 에디터 노출 + 블루프린트 읽기
UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Animation")
float BlendWeight = 1.0f;

// 블루프린트 호출 가능
UFUNCTION(BlueprintCallable, Category = "Animation")
void PlayMontageSection(FName SectionName);

// 블루프린트 오버라이드 가능
UFUNCTION(BlueprintNativeEvent, Category = "Animation")
void OnAnimationComplete();
```

## 애니메이션 C++ 패턴

- `UAnimInstance` 서브클래스에서 `NativeUpdateAnimation()` 오버라이드
- `FAnimInstanceProxy`로 멀티스레드 안전 업데이트
- Montage 콜백은 `FOnMontageEnded` 델리게이트 바인딩
- AnimNotify는 `UAnimNotify` / `UAnimNotifyState` 서브클래스

## Blueprint 컨벤션

- 이벤트 그래프: 로직 최소화, 복잡한 로직은 C++로 이관
- 변수명: PascalCase (`CurrentSpeed`, `bIsAiming`)
- 함수명: 동사+목적어 (`GetMovementDirection`, `SetBlendWeight`)
- 커스텀 이벤트: `On` 접두사 (`OnLanded`, `OnMontageFinished`)
- 매크로보다 함수 선호 (디버깅 용이)

## 빌드 & 모듈

- `.Build.cs`에서 모듈 의존성 명시 (`AnimGraphRuntime`, `ControlRig` 등)
- Public/Private 폴더 분리 엄수
- 헤더 include 순서: 자기 헤더 → 프로젝트 → 엔진 → 서드파티
- `#pragma once` 필수 (include guard 대신)
- Generated.h는 항상 마지막 include
