# AddNotify 그래프 변경 전 (18 노드)

## 실행 흐름

```
K2Node_FunctionEntry_0 (입력: StartTime, Volume, Pitch)
  → K2Node_CallFunction_11 (AddAnimationNotifyEvent)
       inputs:
         AnimationSequenceBase ← K2Node_VariableGet_20 (Animation Sequence)
         NotifyTrackName       ← K2Node_VariableGet_2 (FootDefinition.NotifyTrack_4_FF...)
         StartTime             ← K2Node_CallFunction_0 (Clamp 0~10000)
         NotifyClass           ← K2Node_VariableGet_2 (FootDefinition.AnimNotify_7_CE...)
       output: ReturnValue (AnimNotify)
  → K2Node_DynamicCast_2 (Cast To AN_SBFootStepNotify)
       output: AsAN_SBFootStepNotify
  → K2Node_VariableSet_14 (Set SocketName)
       value: ← K2Node_VariableGet_10 (FootDefinition.SocketName_8_83...) = "FX_Foot_L/R"
  → K2Node_VariableSet_16 (Set Volume)
       value: ← K2Node_VariableGet_1 (Volume from FunctionEntry)
  → K2Node_VariableSet_0  (Set Pitch)
       value: ← K2Node_VariableGet_0 (Pitch from FunctionEntry)
  → K2Node_VariableSet_1  (Set FootStepSetKey)
       value: ← K2Node_VariableGet_3 (FootStepSetKey 변수)
```

## 노드 ID 인벤토리 (제거/유지 표시)

| Node ID | Class | Title | 변경 후 |
|---|---|---|---|
| K2Node_FunctionEntry_0 | FunctionEntry | AddNotify | 유지 |
| K2Node_CallFunction_11 | CallFunction | AddAnimationNotifyEvent | **교체** → AddAnimationSyncMarker |
| K2Node_DynamicCast_2 | DynamicCast | Cast To AN_SBFootStepNotify | **제거** |
| K2Node_VariableSet_14 | VariableSet | Set SocketName | **제거** |
| K2Node_VariableSet_16 | VariableSet | Set Volume | **제거** |
| K2Node_VariableSet_0 | VariableSet | Set Pitch | **제거** |
| K2Node_VariableSet_1 | VariableSet | Set FootStepSetKey | **제거** |
| K2Node_CallFunction_0 | CallFunction | Clamp (Float) | 유지 |
| K2Node_VariableGet_2 | VariableGet | Get FootDefinition (NotifyTrack pin) | 유지 (NotifyTrack pin만 사용) |
| K2Node_VariableGet_20 | VariableGet | Get Animation Sequence | 유지 |
| K2Node_VariableGet_10 | VariableGet | Get FootDefinition (SocketName pin) | **제거** |
| K2Node_VariableGet_1 | VariableGet | Get Volume | **제거** |
| K2Node_VariableGet_0 | VariableGet | Get Pitch | **제거** |
| K2Node_VariableGet_3 | VariableGet | Get FootStepSetKey | **제거** |
| K2Node_Knot_0/1/2/3 | Knot | 경유 노드 | **제거** (Cast 후 체인용) |

## 변경 후 예상 노드 (~7~8개)

```
K2Node_FunctionEntry_0 (입력: StartTime, Volume, Pitch)  ← 시그니처 유지
  → K2Node_CallFunction_NEW (AddAnimationSyncMarker)
       inputs:
         AnimationSequence  ← K2Node_VariableGet_20 (유지)
         NotifyTrackName    ← K2Node_VariableGet_2 (유지)
         Time               ← K2Node_CallFunction_0 (Clamp 유지)
         MarkerName         ← K2Node_Select_NEW (IsLeftSide bool → "Foot_L"/"Foot_R")
                                  ← K2Node_VariableGet_NEW (Get IsLeftSide)
```

추가 신규 노드:
- AddAnimationSyncMarker call
- Select node (bool → name)  
- Get IsLeftSide variable
- 2개 default name pin: "Foot_L" / "Foot_R"
