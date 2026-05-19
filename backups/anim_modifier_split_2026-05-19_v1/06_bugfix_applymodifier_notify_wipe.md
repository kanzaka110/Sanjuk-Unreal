# 🚨 버그 수정: Sync ApplyModifier가 FX 노티파이 지우는 문제

## 발견 경위

2026-05-19 — 사용자가 시퀀스 1개에 `AM_SBFootSyncNotifies` 적용 테스트.
결과: **기존 Step 모디파이어가 박았던 FX/Sound 노티파이가 전부 사라짐.**

## 원인

Sync의 `ApplyModifier` 그래프가 Step의 100% 복제본이라 다음 호출을 그대로 가지고 있었음:

```
K2Node_CallFunction_11 (RemoveAnimationNotifyEventsByTrack)
  - 입력 트랙: "Footstep Left", "Footstep Right" (= FootDefinition.NotifyTrack)
  - 효과: 해당 트랙의 모든 AnimNotify 이벤트 삭제
```

이 호출은 ApplyModifier 시작부에 있어서 "트랙 초기화" 역할.
Step에선 어차피 다음에 FX notify를 다시 박으니 OK.
**Sync에선 FX를 박지 않으므로 → FX 노티파이가 영원히 사라짐.**

이전 청소에서 RevertModifier의 `RemoveAnimationNotifyTrack`은 같은 이유로 교체했지만, 
ApplyModifier 안의 동일 호출은 놓쳤음 (검토 누락).

## 수정

- `K2Node_CallFunction_11` (RemoveAnimationNotifyEventsByTrack) **제거**
- 신규 `K2Node_CallFunction_7` (RemoveAnimationSyncMarkersByTrack) 추가
- 연결 동일 (IfThenElse.then → execute, VariableGet_8.AnimSeq → AnimationSequence, Knot_1 → NotifyTrackName)

이제 Sync ApplyModifier는 다음 동작:
1. 각 TargetNotifiyTrackes 트랙에 대해:
   - 트랙 있으면: **sync marker만** 제거 (notify 보존) ← 수정됨
   - 없으면: 트랙 생성
2. ProcessFoot → AddNotify (sync marker 추가)

## 복구 (잃은 시퀀스)

테스트로 노티파이를 잃은 시퀀스에 다음 순서로 복구:
1. `AM_SBFootStepNotifies` Apply → FX/Sound 노티파이 재생성
2. (수정된) `AM_SBFootSyncNotifies` Apply → sync marker 추가, FX 보존 확인

## 교훈

분리 작업에서 검토 부족 — `RemoveAnimationNotifyTrack` 만 떠올리고 `RemoveAnimationNotifyEventsByTrack` 패턴은 검색 안 함. 
이후 비슷한 분리 작업 시 **"notify를 삭제/수정하는 모든 함수 호출"을 그래프 전체에서 search_nodes로 검색** 필수.

검색 패턴 (다음 패스에 적용):
```python
for fn in ["AddAnimationNotifyEvent", "RemoveAnimationNotifyEventsByTrack", "RemoveAnimationNotifyTrack", "AddAnimationNotifyTrack", "AddAnimationSyncMarker", "RemoveAnimationSyncMarkersByTrack", "RemoveAnimationSyncMarkersByName"]:
    search_nodes(asset_path, fn)
```

## 검증

- ✅ 컴파일 0 error / 0 warning
- ✅ 저장됨
- 🔲 사용자 PIE/Persona 검증 대기

## 영향 받지 않은 사항

`AddAnimationNotifyTrack` (K2Node_CallFunction_10) — 트랙이 없을 때 생성. 
이 호출은 둘 다(Step/Sync) 필요 (sync marker도 트랙 위에 박힘). **유지.**
