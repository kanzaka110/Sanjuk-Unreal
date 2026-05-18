---
name: pc01-psd-gmt-continuing-bias
description: PSD_GroundMovingTransit ContinuingPoseCostBias -0.01 → -0.5 (2026-05-15). 락온 Sprint 종료 시 Transition_Sprint_to_Battle_Jog_* 가 1프레임만 매칭되고 Pivot/Box 시리즈로 swap되던 노이즈 직접 처방.
metadata: 
  node_type: memory
  type: project
  date: 2026-05-15
  originSessionId: 9dcc5175-e415-47ad-96d0-959bb0242e16
---

# PC_01 PSD_GroundMovingTransit ContinuingPoseCostBias 강화 (2026-05-15)

## 증상
- 사용자 호소: "Transition만 나와야 할 구간에 Pivot이 끼어드네, 특히 Turn !!!"
- 시나리오: 락온 Sprint 이후 Jog/Walk 일반 이동 (그리고 Sprint→Battle 종료)

## [ANIM_REC] 실측 패턴 (2026-05-15)

같은 패턴이 1640-1645, 1700-1703, 1815-1818, 1873-1876, 1112-1114, 943-944 등 반복 관찰:

```
f1700 Sprint_Turn_L_180_Rfoot              sc=0.32   (sprint 종료 회전)
f1701 Transition_Sprint_to_Battle_Jog_RL_Lfoot  sc=2.394 ← 의도 매칭, 1프레임만 살아남음
f1702 Fist_Battle_Jog_Pivot_B_F_Rfoot     sc=2.941 ← Pivot 끼어듦
f1703 Fist_Battle_Jog_Box_F_RL_Lfoot      sc=2.941 ← Box 끼어듦
```

**해석**: Transition 클립이 들어가긴 하지만 ContinuingPoseCostBias=-0.01 가 너무 약해서 매 프레임 더 cost 낮은 클립 (Pivot/Box)을 발견 → 즉시 swap. Pivot/Box cost (2.941) < Transition cost (3.718) → 교체 발생.

## 처방 이력

| 단계 | 값 | 배수 | 결과 |
|------|---:|---:|------|
| 원본 | -0.01 | 1× | Pivot/Box 1프레임 swap 빈번 |
| 1차 (2026-05-15 14:xx) | **-0.5** | 50× | 부분 효과. swap 일부 차단되었으나 큰 회전(Sprint_Turn_L/R_180) 직후엔 여전히 발생 |
| 2차 (2026-05-15 15:xx) | **-1.0** | 100× | 사용자 호소 "Turn 끼어듦 다시" 후 추가 강화. 그러나 PSD save가 P4 잠금으로 실패해 PIE 시 디스크 원본 (-0.01) 으로 reload되어 효과 미적용이었음 |
| **3차 검증 (2026-05-15 16:25)** | **-1.0 (디스크 save)** | 100× | **✅ 검증됨**: 사용자가 PSD asset Ctrl+S로 디스크 영구화 후 PIE. 결과 (SB2_2.log 579 frame, 35 transitions): Transition→Pivot/Box swap **16회→0회**, B_Lfoot 5/5 매칭 유지, Pivot/Box 시리즈 매칭 0회. Reface 끼어듦 1회 (락온 OFF 시점, 영향 작음). 처방 결정적 효과 확인 |

## 중요 교훈: save_asset 디스크 반영
`set_cdo_property` 후 `save_asset` 이 P4 잠금으로 실패하면 **메모리만 변경**. PIE 시작 시 에디터가 PSD를 reload하면 디스크 원본값으로 복원되어 처방 무효화. 반드시 사용자가 에디터에서 직접 Ctrl+S + P4 체크아웃 prompt 응답 후 PIE 검증해야 함.

다른 PSD (GroundMoving, GroundIdleTransit 등)는 건드리지 않음.

## 검증
- `set_cdo_property`: old=-0.010000, new=-0.500000 → success
- `save_asset`: 실패 (PSD asset P4 잠금) → 사용자 측 Ctrl+S 필요
- 메모리 상태로는 PIE 즉시 효과 확인 가능

## PIE 검증 시나리오
1. 락온 ON
2. Sprint 시작 + 좌/우 회전
3. Sprint 종료
4. [ANIM_REC] 에서 `Transition_Sprint_to_Battle_Jog_*` 매칭이 **여러 프레임 유지**되는지 확인 (1프레임만 살고 swap 사라지면 됨)

## 부수 사항
- 다른 PSD 영향 0 — 이건 GroundMovingTransit 전용
- LoopingCostBias=-0.005, BaseCostBias=0 은 그대로 유지
- ContinuingInteractionCostBias=0 도 그대로

## 효과 부족 시 다음 단계
- -0.5 → -1.0 추가 강화
- 또는 처방 #2 (Pivot/Box 시리즈만 BaseCostBias +0.5 양수 페널티)

## 관련
- MM 파이프라인 카탈로그: [[pc01-mm-pipeline]] (CostBias 모든 PSD 공통: ContinuingPose=-0.01, Looping=-0.005, Base=0 → 본 처방으로 GMT만 정정)
- PSD_GroundMovingTransit 통계: 210 sequences, 3327 poses, Schema PSS_SM_LocoTransitions (cardinality=34, Group12+Trajectory22), search BruteForce
- 새 진단 도구: `Briefing/_tmp/anim_rec_latest.log` (2415 line, 195 seq transitions)
