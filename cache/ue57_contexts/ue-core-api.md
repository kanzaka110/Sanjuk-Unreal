# UE 5.7 Core API Reference

## Class Hierarchy

```
UObject
├── AActor
│   ├── APawn → ACharacter
│   ├── AController → APlayerController
│   ├── AInfo
│   │   ├── AGameModeBase → AGameMode
│   │   ├── AGameStateBase → AGameState
│   │   └── APlayerState
│   ├── AHUD
│   ├── AVolume → ATriggerVolume
│   └── ALight (APointLight, ASpotLight, ADirectionalLight)
├── UActorComponent
│   ├── USceneComponent
│   │   ├── UPrimitiveComponent
│   │   │   ├── UMeshComponent (UStaticMeshComponent, USkeletalMeshComponent)
│   │   │   ├── UShapeComponent (UBoxComponent, USphereComponent, UCapsuleComponent)
│   │   │   └── UDecalComponent
│   │   ├── UCameraComponent, USpringArmComponent, UAudioComponent
│   │   ├── ULightComponent (UPointLightComponent, USpotLightComponent, UDirectionalLightComponent)
│   │   ├── UArrowComponent, UChildActorComponent
│   ├── UMovementComponent (UCharacterMovementComponent, UProjectileMovementComponent, UFloatingPawnMovement)
│   ├── UInputComponent → UEnhancedInputComponent
│   └── UWidgetComponent
├── USubsystem (UWorldSubsystem, UGameInstanceSubsystem, ULocalPlayerSubsystem)
├── UGameInstance, UWorld, UAnimInstance
├── UBlueprintFunctionLibrary, UDataAsset → UPrimaryDataAsset
├── UDeveloperSettings
└── UVisual → UWidget → UUserWidget
```

## Common Structs

| Struct | Description |
|--------|-------------|
| `FVector` | 3D vector (X, Y, Z as double) |
| `FRotator` | Rotation (Pitch, Yaw, Roll in degrees) |
| `FTransform` | Location + Rotation + Scale |
| `FQuat` | Quaternion rotation |
| `FColor` / `FLinearColor` | 8-bit RGBA / Float RGBA (linear) |
| `FHitResult` | Trace/sweep hit data |
| `FActorSpawnParameters` | Parameters for SpawnActor |
| `FTimerHandle` | Timer management handle |
| `FName` / `FText` / `FString` | Immutable name / Localizable text / Mutable string |
| `FSoftObjectPath` | Asset path for soft references |
| `FGameplayTag` | Hierarchical gameplay tag |
| `FLatentActionInfo` | Info for latent Blueprint actions |

## UPROPERTY Specifiers

### Visibility & Editability

| Specifier | Effect |
|-----------|--------|
| `EditAnywhere` | Editable in defaults and instances |
| `EditDefaultsOnly` | Editable in class defaults only |
| `EditInstanceOnly` | Editable on placed instances only |
| `VisibleAnywhere` | Read-only in defaults and instances |
| `VisibleDefaultsOnly` | Read-only in class defaults only |
| `VisibleInstanceOnly` | Read-only on placed instances only |

### Blueprint Access

| Specifier | Effect |
|-----------|--------|
| `BlueprintReadWrite` | Read and write from Blueprint |
| `BlueprintReadOnly` | Read-only from Blueprint |
| `BlueprintAssignable` | For multicast delegates — bind in BP |
| `BlueprintCallable` | For multicast delegates — callable in BP |
| `EditFixedSize` | Array: prevent size changes |

### Metadata & Behavior

| Specifier | Effect |
|-----------|--------|
| `Category = "Name"` | Details panel category |
| `meta = (AllowPrivateAccess = "true")` | Expose private member to BP |
| `meta = (ClampMin = "0", ClampMax = "100")` | Numeric slider range |
| `meta = (ExposeOnSpawn)` | Show as pin on SpawnActor node |
| `Transient` | Not serialized (runtime-only) |
| `DuplicateTransient` | Not copied on duplication |
| `SaveGame` | Included in save game serialization |
| `Replicated` | Replicated to clients |
| `ReplicatedUsing = "OnRep_Func"` | Replicated with callback |
| `Interp` | Animatable via Sequencer |
| `Config` | Loaded from config file |
| `AdvancedDisplay` | Hidden under "Advanced" in Details |
| `NoClear` | Prevents "Clear" on object refs |
| `Instanced` | Component-like per-instance subobject |
| `SkipSerialization` | Skips all serialization |

## UFUNCTION Specifiers

| Specifier | Effect |
|-----------|--------|
| `BlueprintCallable` | Callable from Blueprint (exec pins) |
| `BlueprintPure` | Pure node — no exec pins |
| `BlueprintImplementableEvent` | Implement in Blueprint only |
| `BlueprintNativeEvent` | C++ `_Implementation`, overridable in BP |
| `BlueprintAuthorityOnly` | Only on server |
| `BlueprintCosmetic` | Only on clients with viewport |
| `Category = "Name"` | Blueprint palette category |
| `CallInEditor` | Button in Details panel |
| `Exec` | Console command binding |
| `Server` / `Client` / `NetMulticast` | RPC direction |
| `Reliable` / `Unreliable` | RPC delivery guarantee |
| `WithValidation` | Requires `_Validate` for RPC |
| `meta = (WorldContext = "Obj")` | Auto-fill world context |
| `meta = (DeterminesOutputType = "P")` | Return type matches param class |
| `meta = (DisplayName = "Name")` | Override display name in BP |
| `meta = (ExpandEnumAsExecs = "P")` | Enum param → exec pins |
| `meta = (DefaultToSelf = "P")` | Auto-fill with self ref |
| `meta = (DeprecatedFunction)` | Mark deprecated |

## UCLASS Specifiers

| Specifier | Effect |
|-----------|--------|
| `Blueprintable` | Can create Blueprint subclass |
| `BlueprintType` | Can be used as variable type in BP |
| `Abstract` | Cannot be instantiated |
| `MinimalAPI` | Only export type info |
| `Within = OuterClass` | Must be subobject of outer |
| `Transient` | Never saved to disk |
| `Config = Name` | Config file binding |
| `HideCategories = (...)` | Hide categories in Details |
| `EditInlineNew` | Allow inline subobject creation |
| `NotPlaceable` / `Placeable` | Level placement control |

## Common Include Paths

| Class/Type | Include |
|------------|---------|
| `AActor` | `"GameFramework/Actor.h"` |
| `APawn` | `"GameFramework/Pawn.h"` |
| `ACharacter` | `"GameFramework/Character.h"` |
| `APlayerController` | `"GameFramework/PlayerController.h"` |
| `AGameModeBase` | `"GameFramework/GameModeBase.h"` |
| `AGameStateBase` | `"GameFramework/GameStateBase.h"` |
| `APlayerState` | `"GameFramework/PlayerState.h"` |
| `UActorComponent` | `"Components/ActorComponent.h"` |
| `USceneComponent` | `"Components/SceneComponent.h"` |
| `UStaticMeshComponent` | `"Components/StaticMeshComponent.h"` |
| `USkeletalMeshComponent` | `"Components/SkeletalMeshComponent.h"` |
| `UCapsuleComponent` | `"Components/CapsuleComponent.h"` |
| `UBoxComponent` | `"Components/BoxComponent.h"` |
| `USphereComponent` | `"Components/SphereComponent.h"` |
| `UCameraComponent` | `"Camera/CameraComponent.h"` |
| `USpringArmComponent` | `"GameFramework/SpringArmComponent.h"` |
| `UCharacterMovementComponent` | `"GameFramework/CharacterMovementComponent.h"` |
| `UInputAction` | `"InputAction.h"` |
| `UInputMappingContext` | `"InputMappingContext.h"` |
| `UEnhancedInputComponent` | `"EnhancedInputComponent.h"` |
| `UAnimInstance` | `"Animation/AnimInstance.h"` |
| `UUserWidget` | `"Blueprint/UserWidget.h"` |
| `UWidgetComponent` | `"Components/WidgetComponent.h"` |
| `UDataAsset` | `"Engine/DataAsset.h"` |
| `UGameInstance` | `"Engine/GameInstance.h"` |
| `UWorld` | `"Engine/World.h"` |
| `UMaterialInstanceDynamic` | `"Materials/MaterialInstanceDynamic.h"` |
| `UNiagaraComponent` | `"NiagaraComponent.h"` |
| `FTimerManager` | `"TimerManager.h"` |
| `FGameplayTag` | `"GameplayTagContainer.h"` |
