# RevertModifier 그래프 변경 전 (5 노드)

## 실행 흐름

```
K2Node_FunctionEntry_0 (RevertModifier 진입)
  → K2Node_MacroInstance_0 (ForEachLoop, Array: FeetDefinition)
       LoopBody:
         → K2Node_CallFunction_1 (RemoveAnimationNotifyTrack)
              AnimationSequence ← K2Node_VariableGet_3 (Animation Sequence)
              NotifyTrackName   ← ForEachLoop.Array Element_NotifyTrack_4_FF...
```

## 노드 ID 인벤토리

| Node ID | Class | Title | 변경 후 |
|---|---|---|---|
| K2Node_FunctionEntry_0 | FunctionEntry | RevertModifier | 유지 |
| K2Node_VariableGet_2 | VariableGet | Get FeetDefinition | 유지 |
| K2Node_MacroInstance_0 | MacroInstance | ForEachLoop | 유지 |
| K2Node_CallFunction_1 | CallFunction | RemoveAnimationNotifyTrack | **교체 또는 제거** |
| K2Node_VariableGet_3 | VariableGet | Get Animation Sequence | 유지 |

## 변경 옵션

### 옵션 A: 트랙 단위 제거 안 함 + 마커만 제거 (권장)

`RemoveAnimationNotifyTrack` 은 트랙 전체를 삭제 — 다른 모디파이어가 추가한 노티파이까지 날릴 위험. Sync 에선 안전한 마커 단위 제거:

```
ForEach feet:
  → RemoveAnimationSyncMarkersByName(seq, "Foot_L")
  → RemoveAnimationSyncMarkersByName(seq, "Foot_R")
```

하지만 ForEach 안에서 두 마커 제거하면 중복 호출 (피트 2개 × 마커 2개 = 4번). 더 깔끔한 방식:

### 옵션 B: ForEach 제거 + 일괄 제거

```
RevertModifier:
  → RemoveAnimationSyncMarker(seq, "Foot_L")
  → RemoveAnimationSyncMarker(seq, "Foot_R")
```

루프 없이 직접 2번 호출. 노드 수 ~5개. **이걸로 채택.**

## UE API 확인 필요

- `RemoveAnimationSyncMarker` (단수)? 또는 `RemoveAnimationSyncMarkersByName`?
- 정확한 함수명은 `AnimationBlueprintLibrary` 시그니처 확인 후 결정
