# 드론 이동 로직 백업 (2026-08-12)

새 이동 시스템(V2)을 만들기 전, 기존 상태를 되돌릴 수 있도록 남긴 스냅샷.

## 대상 에셋
`/Game/Art/Character/NPC/NPC_100/Body/NPC_100_Body_01/Blueprint/NPC_100_Body_01_BP`

## 이 폴더 내용
- `variables.json` — BP 변수 124개 전량 (이름/타입/기본값/카테고리/플래그)
- `graph_*.json` — 이동 관련 그래프 8종의 노드·핀·연결 전체 덤프

| 그래프 | 노드 | 역할 |
|---|---:|---|
| EventGraph | 98 | Tick 진입, 함수 호출 순서 |
| UpdateFollowMove | 155 | CachedAnchor, WanderAngle, 캡슐 이동, 섹터 트레이스 |
| UpdateWanderSpin | 159 | CurrentVisualWander (배회·호위 오프셋) |
| UpdateCamAvoid | 36 | CurrentCamAvoid |
| UpdateSmoothedVel | 7 | SmoothedPCVel |
| UpdateVisualHover | 11 | 위 4개 + 파이프라인 + 회전 호출 |
| UpdatePositionPipeline | 271 | 최종 좌표 조립 + 메시/캡슐 위치 기록 |
| UpdateRotationGaze | 124 | SmoothedLookRot (회전) |

## uasset 원본 백업
`C:\Users\SHIFTUP\drone-backup-20260812\` 에 `.uasset` 2개(BP/ABP) 복사본.
완전 복원이 필요하면 **에디터를 닫고** 이 파일을 P4 워크스페이스 경로에 덮어쓴 뒤
`p4 edit` 상태를 확인할 것. (덮어쓰기 전 반드시 현재 파일을 따로 보관)

## 복원 수준
1. **값만 되돌리기** — `variables.json`의 default_value 를 `blueprint set_variable_defaults` 로 재적용 (가장 안전)
2. **배선까지 되돌리기** — `graph_*.json` 을 참고해 수동 재배선 (RPC로 자동 복원은 노드 ID가 달라져 불가)
3. **통째 복원** — uasset 덮어쓰기

## 기존 위치 파이프라인 요약 (V2 설계 참고용)
```
최종좌표 = 캐릭터 + (target - 캐릭터) 방향 × Clamp(거리, IdleRingRadiusMin, RingRoutState)
  target = CurrentVisualWorld + [VInterpTo(CurrentVisualWorld → 진짜목표, VisualWorldInterpSpeed) - CurrentVisualWorld]
                              + 시선방향 보정
  진짜목표 = CachedAnchor + CurrentVisualWander + SmoothedPCVel×VelFeedforwardTime + 봅/드리프트
  CachedAnchor = 캐릭터 + Rotate(VLerp(FollowOffset, LightFrontOffset, LightMoveRatio), SmoothedAnchorYaw)
  SmoothedAnchorYaw ← WanderAngle = (charYaw + Lerp(180, 선택섹터, LightMoveRatio)) + Random(±WanderArc)
```
핵심: 위치 결정이 4개 함수에 흩어져 있고 서로 덮어쓴다. V2는 이 체인을 하나로 합치는 것이 목적.
