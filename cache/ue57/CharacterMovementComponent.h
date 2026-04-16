// Source: EpicGames/UnrealEngine 5.7 branch
// Path: Engine/Source/Runtime/Engine/Classes/GameFramework/CharacterMovementComponent.h (first 500 lines)
// Cached: 2026-04-16
// ============================================================

// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Math/RandomStream.h"
#include "UObject/ObjectMacros.h"
#include "UObject/UObjectGlobals.h"
#include "Engine/NetSerialization.h"
#include "Engine/EngineTypes.h"
#include "Engine/EngineBaseTypes.h"
#include "WorldCollision.h"
#include "AI/Navigation/NavigationTypes.h"
#include "Animation/AnimationAsset.h"
#include "Animation/AnimMontage.h"
#include "GameFramework/RootMotionSource.h"
#include "AI/Navigation/NavigationAvoidanceTypes.h"
#include "AI/RVOAvoidanceInterface.h"
#include "GameFramework/PawnMovementComponent.h"
#include "GameFramework/CharacterMovementReplication.h"
#include "Interfaces/NetworkPredictionInterface.h"
#include "CharacterMovementComponentAsync.h"
#include "CharacterMovementComponent.generated.h"

class ACharacter;
class FDebugDisplayInfo;
class FNetworkPredictionData_Server_Character;
class FSavedMove_Character;
class UPrimitiveComponent;
class INavigationData;
class UCharacterMovementComponent;

DECLARE_DELEGATE_RetVal_ThreeParams(FTransform, FOnProcessRootMotion, const FTransform&, UCharacterMovementComponent*, float)

namespace CharacterMovementConstants
{
	extern const float MAX_STEP_SIDE_Z;
	extern const float VERTICAL_SLOPE_NORMAL_Z;
}

namespace CharacterMovementCVars
{
	// Is Async Character Movement enabled?
	extern ENGINE_API int32 AsyncCharacterMovement;
	extern int32 ForceJumpPeakSubstep;
}

/** 
 * Tick function that calls UCharacterMovementComponent::PostPhysicsTickComponent
 **/
USTRUCT()
struct FCharacterMovementComponentPostPhysicsTickFunction : public FTickFunction
{
	GENERATED_USTRUCT_BODY()

	/** CharacterMovementComponent that is the target of this tick **/
	class UCharacterMovementComponent* Target;

	/** 
	 * Abstract function actually execute the tick. 
	 * @param DeltaTime - frame time to advance, in seconds
	 * @param TickType - kind of tick for this frame
	 * @param CurrentThread - thread we are executing on, useful to pass along as new tasks are created
	 * @param MyCompletionGraphEvent - completion event for this task. Useful for holding the completion of this task until certain child tasks are complete.
	 **/
	virtual void ExecuteTick(float DeltaTime, enum ELevelTick TickType, ENamedThreads::Type CurrentThread, const FGraphEventRef& MyCompletionGraphEvent) override;

	/** Abstract function to describe this tick. Used to print messages about illegal cycles in the dependency graph **/
	virtual FString DiagnosticMessage() override;
	/** Function used to describe this tick for active tick reporting. **/
	virtual FName DiagnosticContext(bool bDetailed) override;
};

template<>
struct TStructOpsTypeTraits<FCharacterMovementComponentPostPhysicsTickFunction> : public TStructOpsTypeTraitsBase2<FCharacterMovementComponentPostPhysicsTickFunction>
{
	enum
	{
		WithCopy = false
	};
};

USTRUCT()
struct FCharacterMovementComponentPrePhysicsTickFunction : public FTickFunction
{
	GENERATED_USTRUCT_BODY()

	/** CharacterMovementComponent that is the target of this tick **/
	class UCharacterMovementComponent* Target;

	/**
	 * Abstract function actually execute the tick.
	 * @param DeltaTime - frame time to advance, in seconds
	 * @param TickType - kind of tick for this frame
	 * @param CurrentThread - thread we are executing on, useful to pass along as new tasks are created
	 * @param MyCompletionGraphEvent - completion event for this task. Useful for holding the completion of this task until certain child tasks are complete.
	 **/
	virtual void ExecuteTick(float DeltaTime, enum ELevelTick TickType, ENamedThreads::Type CurrentThread, const FGraphEventRef& MyCompletionGraphEvent) override;

	/** Abstract function to describe this tick. Used to print messages about illegal cycles in the dependency graph **/
	virtual FString DiagnosticMessage() override;
	
	/** Function used to describe this tick for active tick reporting. **/
	virtual FName DiagnosticContext(bool bDetailed) override;
};

template<>
struct TStructOpsTypeTraits<FCharacterMovementComponentPrePhysicsTickFunction> : public TStructOpsTypeTraitsBase2<FCharacterMovementComponentPrePhysicsTickFunction>
{
	enum
	{
		WithCopy = false
	};
};

/** Shared pointer for easy memory management of FSavedMove_Character, for accumulating and replaying network moves. */
typedef TSharedPtr<class FSavedMove_Character> FSavedMovePtr;


//=============================================================================
/**
 * CharacterMovementComponent handles movement logic for the associated Character owner.
 * It supports various movement modes including: walking, falling, swimming, flying, custom.
 *
 * Movement is affected primarily by current Velocity and Acceleration. Acceleration is updated each frame
 * based on the input vector accumulated thus far (see UPawnMovementComponent::GetPendingInputVector()).
 *
 * Networking is fully implemented, with server-client correction and prediction included.
 *
 * @see ACharacter, UPawnMovementComponent
 * @see https://docs.unrealengine.com/latest/INT/Gameplay/Framework/Pawn/Character/
 */

UCLASS(MinimalAPI)
class UCharacterMovementComponent : public UPawnMovementComponent, public IRVOAvoidanceInterface, public INetworkPredictionInterface
{
	GENERATED_BODY()
public:

	/**
	 * Default UObject constructor.
	 */
	ENGINE_API UCharacterMovementComponent(const FObjectInitializer& ObjectInitializer = FObjectInitializer::Get());

protected:

	/** Character movement component belongs to */
	UPROPERTY(Transient, DuplicateTransient)
	TObjectPtr<ACharacter> CharacterOwner;

public:

	/** Custom gravity scale. Gravity is multiplied by this amount for the character. */
	UPROPERTY(Category="Character Movement (General Settings)", EditAnywhere, BlueprintReadWrite)
	float GravityScale;

	/** Maximum height character can step up */
	UPROPERTY(Category="Character Movement: Walking", EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0", UIMin="0", ForceUnits="cm"))
	float MaxStepHeight;

	/** Initial velocity (instantaneous vertical acceleration) when jumping. */
	UPROPERTY(Category="Character Movement: Jumping / Falling", EditAnywhere, BlueprintReadWrite, meta=(DisplayName="Jump Z Velocity", ClampMin="0", UIMin="0", ForceUnits="cm/s"))
	float JumpZVelocity;

	/** Fraction of JumpZVelocity to use when automatically "jumping off" of a base actor that's not allowed to be a base for a character. (For example, if you're not allowed to stand on other players.) */
	UPROPERTY(Category="Character Movement: Jumping / Falling", EditAnywhere, BlueprintReadWrite, AdvancedDisplay, meta=(ClampMin="0", UIMin="0"))
	float JumpOffJumpZFactor;


private:
	FCharacterMovementComponentAsyncCallback* AsyncCallback;

protected:
	// This is the most recent async state from simulated. Only safe for access on physics thread.
	TSharedPtr<FCharacterMovementComponentAsyncOutput, ESPMode::ThreadSafe> AsyncSimState;
	bool bMovementModeDirty = false; // Gamethread changed movement mode, need to update sim.
private:

	/**
	 * Max angle in degrees of a walkable surface. Any greater than this and it is too steep to be walkable.
	 */
	UPROPERTY(Category="Character Movement: Walking", EditAnywhere, meta=(ClampMin="0.0", ClampMax="90.0", UIMin = "0.0", UIMax = "90.0", ForceUnits="degrees"))
	float WalkableFloorAngle;

	/**
	 * Minimum Z value for floor normal. If less, not a walkable surface. Computed from WalkableFloorAngle.
	 */
	UPROPERTY(Category="Character Movement: Walking", VisibleAnywhere)
	float WalkableFloorZ;

	/**
	 * A normalized vector representing the direction of gravity for gravity relative movement modes: walking, falling,
	 * and custom movement modes. Gravity direction remaps player input as being within the plane defined by the gravity
	 * direction. Movement simulation values like velocity and acceleration are maintained in their existing world coordinate
	 * space but are transformed internally as gravity relative (for instance moving forward up a vertical wall that gravity is
	 * defined to be perpendicular to and jump "up" from that wall). If ShouldRemainVertical() is true the character's capsule
	 * will be oriented to align with the gravity direction.
	 */
	UPROPERTY(Category="Character Movement: Gravity", VisibleAnywhere, BlueprintReadOnly, meta = (AllowPrivateAccess = true))
	FVector GravityDirection;

	/**
	 * A cached quaternion representing the rotation from world space to gravity relative space defined by GravityDirection.
	 */
	UPROPERTY(Category="Character Movement: Gravity", VisibleAnywhere, BlueprintReadOnly, meta = (AllowPrivateAccess = true))
	FQuat WorldToGravityTransform;

	/**
	 * A cached quaternion representing the inverse rotation from world space to gravity relative space defined by GravityDirection.
	 */
	UPROPERTY(Category="Character Movement: Gravity", VisibleAnywhere, BlueprintReadOnly, meta = (AllowPrivateAccess = true))
	FQuat GravityToWorldTransform;

	/** Whether the character has custom local gravity set. Cached in SetGravityDirection(). */
	bool bHasCustomGravity;
public:
	
	/**
	 * Actor's current movement mode (walking, falling, etc).
	 *    - walking:  Walking on a surface, under the effects of friction, and able to "step up" barriers. Vertical velocity is zero.
	 *    - falling:  Falling under the effects of gravity, after jumping or walking off the edge of a surface.
	 *    - flying:   Flying, ignoring the effects of gravity.
	 *    - swimming: Swimming through a fluid volume, under the effects of gravity and buoyancy.
	 *    - custom:   User-defined custom movement mode, including many possible sub-modes.
	 * This is automatically replicated through the Character owner and for client-server movement functions.
	 * @see SetMovementMode(), CustomMovementMode
	 */
	UPROPERTY(Category="Character Movement: MovementMode", BlueprintReadOnly)
	TEnumAsByte<enum EMovementMode> MovementMode;

	/**
	 * Current custom sub-mode if MovementMode is set to Custom.
	 * This is automatically replicated through the Character owner and for client-server movement functions.
	 * @see SetMovementMode()
	 */
	UPROPERTY(Category="Character Movement: MovementMode", BlueprintReadOnly)
	uint8 CustomMovementMode;

	/** The default direction that gravity points for movement simulation.  */
	static ENGINE_API const FVector DefaultGravityDirection;

	/** Smoothing mode for simulated proxies in network game. */
	UPROPERTY(Category="Character Movement (Networking)", EditAnywhere, BlueprintReadOnly)
	ENetworkSmoothingMode NetworkSmoothingMode;

	/**
	 * Setting that affects movement control. Higher values allow faster changes in direction.
	 * If bUseSeparateBrakingFriction is false, also affects the ability to stop more quickly when braking (whenever Acceleration is zero), where it is multiplied by BrakingFrictionFactor.
	 * When braking, this property allows you to control how much friction is applied when moving across the ground, applying an opposing force that scales with current velocity.
	 * This can be used to simulate slippery surfaces such as ice or oil by changing the value (possibly based on the material pawn is standing on).
	 * @see BrakingDecelerationWalking, BrakingFriction, bUseSeparateBrakingFriction, BrakingFrictionFactor
	 */
	UPROPERTY(Category="Character Movement: Walking", EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0", UIMin="0"))
	float GroundFriction;

#if UE_WITH_REMOTE_OBJECT_HANDLE
	/**
	* An extra scaling factor on the impact physics force applied to pushing object when the component is doing substepping 
	*/
	float PhysicsForceSubsteppingFactor = 1.0f;
#endif
	

	/** Saved location of object we are standing on, for UpdateBasedMovement() to determine if base moved in the last frame, and therefore pawn needs an update. */
	UPROPERTY(Transient)
	FQuat OldBaseQuat;

	/** Saved location of object we are standing on, for UpdateBasedMovement() to determine if base moved in the last frame, and therefore pawn needs an update. */
	UPROPERTY(Transient)
	FVector OldBaseLocation;

	/** The maximum ground speed when walking. Also determines maximum lateral speed when falling. */
	UPROPERTY(Category="Character Movement: Walking", EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0", UIMin="0", ForceUnits="cm/s"))
	float MaxWalkSpeed;

	/** The maximum ground speed when walking and crouched. */
	UPROPERTY(Category="Character Movement: Walking", EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0", UIMin="0", ForceUnits="cm/s"))
	float MaxWalkSpeedCrouched;

	/** The maximum swimming speed. */
	UPROPERTY(Category="Character Movement: Swimming", EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0", UIMin="0", ForceUnits="cm/s"))
	float MaxSwimSpeed;

	/** The maximum flying speed. */
	UPROPERTY(Category="Character Movement: Flying", EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0", UIMin="0", ForceUnits="cm/s"))
	float MaxFlySpeed;

	/** The maximum speed when using Custom movement mode. */
	UPROPERTY(Category="Character Movement: Custom Movement", EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0", UIMin="0", ForceUnits="cm/s"))
	float MaxCustomMovementSpeed;

	/** Max Acceleration (rate of change of velocity) */
	UPROPERTY(Category="Character Movement (General Settings)", EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0", UIMin="0"))
	float MaxAcceleration;

	/** The ground speed that we should accelerate up to when walking at minimum analog stick tilt */
	UPROPERTY(Category = "Character Movement: Walking", EditAnywhere, BlueprintReadWrite, meta = (ClampMin = "0", UIMin = "0", ForceUnits="cm/s"))
	float MinAnalogWalkSpeed;

	/**
	 * Factor used to multiply actual value of friction used when braking.
	 * This applies to any friction value that is currently used, which may depend on bUseSeparateBrakingFriction.
	 * @note This is 2 by default for historical reasons, a value of 1 gives the true drag equation.
	 * @see bUseSeparateBrakingFriction, GroundFriction, BrakingFriction
	 */
	UPROPERTY(Category="Character Movement (General Settings)", EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0", UIMin="0"))
	float BrakingFrictionFactor;

	/**
	 * Friction (drag) coefficient applied when braking (whenever Acceleration = 0, or if character is exceeding max speed); actual value used is this multiplied by BrakingFrictionFactor.
	 * When braking, this property allows you to control how much friction is applied when moving across the ground, applying an opposing force that scales with current velocity.
	 * Braking is composed of friction (velocity-dependent drag) and constant deceleration.
	 * This is the current value, used in all movement modes; if this is not desired, override it or bUseSeparateBrakingFriction when movement mode changes.
	 * @note Only used if bUseSeparateBrakingFriction setting is true, otherwise current friction such as GroundFriction is used.
	 * @see bUseSeparateBrakingFriction, BrakingFrictionFactor, GroundFriction, BrakingDecelerationWalking
	 */
	UPROPERTY(Category="Character Movement (General Settings)", EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0", UIMin="0", EditCondition="bUseSeparateBrakingFriction"))
	float BrakingFriction;

	/**
	 * Time substepping when applying braking friction. Smaller time steps increase accuracy at the slight cost of performance, especially if there are large frame times.
	 */
	UPROPERTY(Category="Character Movement (General Settings)", EditAnywhere, BlueprintReadWrite, AdvancedDisplay, meta=(ClampMin="0.0166", ClampMax="0.05", UIMin="0.0166", UIMax="0.05"))
	float BrakingSubStepTime;

	/**
	 * Deceleration when walking and not applying acceleration. This is a constant opposing force that directly lowers velocity by a constant value.
	 * @see GroundFriction, MaxAcceleration
	 */
	UPROPERTY(Category="Character Movement: Walking", EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0", UIMin="0"))
	float BrakingDecelerationWalking;

	/**
	 * Lateral deceleration when falling and not applying acceleration.
	 * @see MaxAcceleration
	 */
	UPROPERTY(Category="Character Movement: Jumping / Falling", EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0", UIMin="0"))
	float BrakingDecelerationFalling;

	/**
	 * Deceleration when swimming and not applying acceleration.
	 * @see MaxAcceleration
	 */
	UPROPERTY(Category="Character Movement: Swimming", EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0", UIMin="0"))
	float BrakingDecelerationSwimming;

	/**
	 * Deceleration when flying and not applying acceleration.
	 * @see MaxAcceleration
	 */
	UPROPERTY(Category="Character Movement: Flying", EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0", UIMin="0"))
	float BrakingDecelerationFlying;

	/**
	 * When falling, amount of lateral movement control available to the character.
	 * 0 = no control, 1 = full control at max speed of MaxWalkSpeed.
	 */
	UPROPERTY(Category="Character Movement: Jumping / Falling", EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0", UIMin="0"))
	float AirControl;

	/**
	 * When falling, multiplier applied to AirControl when lateral velocity is less than AirControlBoostVelocityThreshold.
	 * Setting this to zero will disable air control boosting. Final result is clamped at 1.
	 */
	UPROPERTY(Category="Character Movement: Jumping / Falling", EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0", UIMin="0"))
	float AirControlBoostMultiplier;

	/**
	 * When falling, if lateral velocity magnitude is less than this value, AirControl is multiplied by AirControlBoostMultiplier.
	 * Setting this to zero will disable air control boosting.
	 */
	UPROPERTY(Category="Character Movement: Jumping / Falling", EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0", UIMin="0"))
	float AirControlBoostVelocityThreshold;

	/**
	 * Friction to apply to lateral air movement when falling.
	 * If bUseSeparateBrakingFriction is false, also affects the ability to stop more quickly when braking (whenever Acceleration is zero).
	 * @see BrakingFriction, bUseSeparateBrakingFriction
	 */
	UPROPERTY(Category="Character Movement: Jumping / Falling", EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0", UIMin="0"))
	float FallingLateralFriction;

	/** Collision half-height when crouching (component scale is applied separately) */
	UE_DEPRECATED_FORGAME(5.0, "Public access to this property is deprecated, and it will become private in a future release. Please use SetCrouchedHalfHeight and GetCrouchedHalfHeight instead.")
	UPROPERTY(Category="Character Movement (General Settings)", EditAnywhere, BlueprintReadWrite, BlueprintSetter=SetCrouchedHalfHeight, BlueprintGetter=GetCrouchedHalfHeight, meta=(ClampMin="0", UIMin="0", ForceUnits=cm))
	float CrouchedHalfHeight;

	/** Water buoyancy. A ratio (1.0 = neutral buoyancy, 0.0 = no buoyancy) */
	UPROPERTY(Category="Character Movement: Swimming", EditAnywhere, BlueprintReadWrite)
	float Buoyancy;

	/**
	 * Don't allow the character to perch on the edge of a surface if the contact is this close to the edge of the capsule.
	 * Note that characters will not fall off if they are within MaxStepHeight of a walkable surface below.
	 */
	UPROPERTY(Category="Character Movement: Walking", EditAnywhere, BlueprintReadWrite, AdvancedDisplay, meta=(ClampMin="0", UIMin="0", ForceUnits=cm))
	float PerchRadiusThreshold;

	/**
	 * When perching on a ledge, add this additional distance to MaxStepHeight when determining how high above a walkable floor we can perch.
	 * Note that we still enforce MaxStepHeight to start the step up; this just allows the character to hang off the edge or step slightly higher off the floor.
	 * (@see PerchRadiusThreshold)
	 */
	UPROPERTY(Category="Character Movement: Walking", EditAnywhere, BlueprintReadWrite, AdvancedDisplay, meta=(ClampMin="0", UIMin="0", ForceUnits=cm))
	float PerchAdditionalHeight;

	/** Change in rotation per second, used when UseControllerDesiredRotation or OrientRotationToMovement are true. Set a negative value for infinite rotation rate and instant turns. */
	UPROPERTY(Category="Character Movement (Rotation Settings)", EditAnywhere, BlueprintReadWrite)
	FRotator RotationRate;

	/**
	 * If true, BrakingFriction will be used to slow the character to a stop (when there is no Acceleration).
	 * If false, braking uses the same friction passed to CalcVelocity() (ie GroundFriction when walking), multiplied by BrakingFrictionFactor.
	 * This setting applies to all movement modes; if only desired in certain modes, consider toggling it when movement modes change.
	 * @see BrakingFriction
	 */
	UPROPERTY(Category="Character Movement (General Settings)", EditDefaultsOnly, BlueprintReadWrite)
	uint8 bUseSeparateBrakingFriction:1;

	/** 
	 * True means while the jump key is held, we will not allow the vertical speed to fall below the JumpZVelocity tuning value 
	 * even if a stronger force, such as gravity, is opposing the jump. 
	 */
	UPROPERTY(Category="Character Movement: Jumping / Falling", EditAnywhere, BlueprintReadWrite, AdvancedDisplay)
	uint8 bDontFallBelowJumpZVelocityDuringJump:1;

	/**
	 *	Apply gravity while the character is actively jumping (e.g. holding the jump key).
	 *	Helps remove frame-rate dependent jump height, but may alter base jump height.
	 */
	UPROPERTY(Category="Character Movement: Jumping / Falling", EditAnywhere, BlueprintReadWrite, AdvancedDisplay)
	uint8 bApplyGravityWhileJumping:1;
	/**
	 * If true, smoothly rotate the Character toward the Controller's desired rotation (typically Controller->ControlRotation), using RotationRate as the rate of rotation change. Overridden by OrientRotationToMovement.
	 * Normally you will want to make sure that other settings are cleared, such as bUseControllerRotationYaw on the Character.
	 */
	UPROPERTY(Category="Character Movement (Rotation Settings)", EditAnywhere, BlueprintReadWrite)
	uint8 bUseControllerDesiredRotation:1;

	/**
	 * If true, rotate the Character toward the direction of acceleration, using RotationRate as the rate of rotation change. Overrides UseControllerDesiredRotation.
	 * Normally you will want to make sure that other settings are cleared, such as bUseControllerRotationYaw on the Character.
	 */
	UPROPERTY(Category="Character Movement (Rotation Settings)", EditAnywhere, BlueprintReadWrite)
	uint8 bOrientRotationToMovement:1;

	/**
	 * Whether or not the character should sweep for collision geometry while walking.
	 * @see USceneComponent::MoveComponent.
	 */
	UPROPERTY(Category="Character Movement: Walking", EditAnywhere, BlueprintReadWrite)
	uint8 bSweepWhileNavWalking:1;

private:

	// Tracks whether or not we need to update the bSweepWhileNavWalking flag do to an upgrade.
	uint8 bNeedsSweepWhileWalkingUpdate:1;

protected:

	/**
	 * True during movement update.
	 * Used internally so that attempts to change CharacterOwner and UpdatedComponent are deferred until after an update.
	 * @see IsMovementInProgress()
	 */
	UPROPERTY()
	uint8 bMovementInProgress:1;

public:

	/**
	 * If true, high-level movement updates will be wrapped in a movement scope that accumulates updates and defers a bulk of the work until the end.
	 * When enabled, touch and hit events will not be triggered until the end of multiple moves within an update, which can improve performance.
	 *
	 * @see FScopedMovementUpdate
	 */
	UPROPERTY(Category="Character Movement (General Settings)", EditAnywhere, AdvancedDisplay)
	uint8 bEnableScopedMovementUpdates:1;

	/**
	 * Optional scoped movement update to combine moves for cheaper performance on the server when the client sends two moves in one packet.
	 * Be warned that since this wraps a larger scope than is normally done with bEnableScopedMovementUpdates, this can result in subtle changes in behavior
	 * in regards to when overlap events are handled, when attached components are moved, etc.
	 *
	 * @see bEnableScopedMovementUpdates
	 */
	UPROPERTY(Category="Character Movement (General Settings)", EditAnywhere, AdvancedDisplay)
	uint8 bEnableServerDualMoveScopedMovementUpdates : 1;

	/** Ignores size of acceleration component, and forces max acceleration to drive character at full velocity. */
	UPROPERTY()
	uint8 bForceMaxAccel:1;    

	/**
	 * If true, movement will be performed even if there is no Controller for the Character owner.
	 * Normally without a Controller, movement will be aborted and velocity and acceleration are zeroed if the character is walking.
	 * Characters that are spawned without a Controller but with this flag enabled will initialize the movement mode to DefaultLandMovementMode or DefaultWaterMovementMode appropriately.
	 * @see DefaultLandMovementMode, DefaultWaterMovementMode
	 */
	UPROPERTY(Category="Character Movement (General Settings)", EditAnywhere, BlueprintReadWrite, AdvancedDisplay)
