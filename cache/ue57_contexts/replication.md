# UE 5.7 Replication & Networking Reference

## Property Replication Macros

```cpp
// In GetLifetimeReplicatedProps:
DOREPLIFETIME(AMyActor, Health);                                          // Always replicate
DOREPLIFETIME_CONDITION(AMyActor, Data, COND_OwnerOnly);                 // With condition
DOREPLIFETIME_CONDITION_NOTIFY(AMyActor, Health, COND_None, REPNOTIFY_Always); // Force RepNotify even if same value
```

### RepNotify Pattern
```cpp
UPROPERTY(ReplicatedUsing = OnRep_Health)
float Health;

UFUNCTION()
void OnRep_Health();          // Or: void OnRep_Health(float OldHealth);
```
Note: In C++, OnRep only fires on clients. Call manually on server if needed.

## Replication Conditions

| Condition | Description |
|-----------|-------------|
| `COND_None` | Always replicate |
| `COND_InitialOnly` | Only on initial replication |
| `COND_OwnerOnly` | Only to owning connection |
| `COND_SkipOwner` | Everyone except owner |
| `COND_SimulatedOnly` | Simulated actors only |
| `COND_AutonomousOnly` | Autonomous proxy only |
| `COND_SimulatedOrPhysics` | Simulated or physics |
| `COND_InitialOrOwner` | Initial or to owner |
| `COND_Custom` | Custom condition check |

## Push Model Replication (UE5)

More efficient — only marks dirty when actually changed.

```cpp
// Mark property dirty when changed
void AMyActor::SetHealth(float NewHealth)
{
    Health = NewHealth;
    MARK_PROPERTY_DIRTY_FROM_NAME(AMyActor, Health, this);
}

// In GetLifetimeReplicatedProps
FDoRepLifetimeParams Params;
Params.bIsPushBased = true;
DOREPLIFETIME_WITH_PARAMS_FAST(AMyActor, Health, Params);
```

## RPC Specifiers

| Specifier | Description |
|-----------|-------------|
| `Server` | Client → Server |
| `Client` | Server → Owning client |
| `NetMulticast` | Server → All clients (+ server) |
| `Reliable` | Guaranteed delivery (use sparingly) |
| `Unreliable` | May be dropped (for frequent updates) |
| `WithValidation` | Adds `_Validate` function for cheat prevention |

### RPC Declaration Patterns
```cpp
// Server RPC (client calls, server executes)
UFUNCTION(Server, Reliable, WithValidation)
void ServerDoAction(FVector Target);
// Implement: ServerDoAction_Implementation, ServerDoAction_Validate

// Client RPC (server calls, owning client executes)
UFUNCTION(Client, Reliable)
void ClientShowMessage(const FString& Message);
// Implement: ClientShowMessage_Implementation

// Multicast RPC (server calls, all clients + server execute)
UFUNCTION(NetMulticast, Reliable)
void MulticastPlayEffect(FVector Location);
// Implement: MulticastPlayEffect_Implementation
```

## Network Roles

| Role | Meaning |
|------|---------|
| `ROLE_Authority` | Server (has authority) |
| `ROLE_AutonomousProxy` | Locally controlled client |
| `ROLE_SimulatedProxy` | Replicated from server |
| `ROLE_None` | Not replicated |

```cpp
if (HasAuthority()) { /* Server-side logic */ }
ENetRole LocalRole = GetLocalRole();
ENetRole RemoteRole = GetRemoteRole();
```
