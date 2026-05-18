---
name: SB2 PC_01 Pose Search Database 구조
description: PC_01의 PSD 에셋 역할 분담 — GroundMoving(loop) vs GroundMovingTransit(전환+곡선). 시퀀스 추가 시 DB 선택 기준.
type: reference
originSessionId: 5c97ced7-4741-424f-8e22-cc55efda4867
---
## PSD 에셋 6개 (경로: `/Game/Art/Character/PC/PC_01/MotionMatching/PSD/`)

| 에셋 | 스키마 | 시퀀스 | 검색 | 용도 |
|---|---|---|---|---|
| `PSD_Falling` | - | - | - | 낙하 |
| `PSD_GroundIdleTransit` | - | - | - | 정지↔이동 전환 |
| **`PSD_GroundMoving`** | PSS_SM_LocoLoops (cardinality 1) | 58 | PCAKDTree | **순수 loop** (Walk/Jog/Run/Sprint 루프) |
| **`PSD_GroundMovingTransit`** | PSS_SM_LocoTransitions (cardinality 34) | 214 | BruteForce | **전환 + 복잡 trajectory** |
| `PSD_Idles` | PSS_SM_Idles | - | - | Idle 포즈 |
| `PSD_WriggleGroundMoving` / `Transit` | - | - | - | Wriggle (기어가기) |

## GroundMoving vs Transit DB 선택 기준

### PSD_GroundMoving (LocoLoops)
- **Schema cardinality 1** — 간단한 pose feature
- **PCAKDTree** — 빠른 근사 검색
- 수록: Walk_Loop_F/B/LL/RL, Jog_Loop_F/B/LL/RL, Sprint_Loop_F/L_20/R_20, Walk_Circle_Strafe_L/R (idx 22, 23), Fist_Battle_Walk/Jog_B/F/LL/RL
- **용도:** 일정한 속도/방향의 지속 loop

### PSD_GroundMovingTransit (LocoTransitions)
- **Schema cardinality 34** — 풍부한 pose feature (trajectory 정밀)
- **BruteForce** — 정확한 cost 평가 (느리지만)
- 수록: Arc_Small/Tight/Wide, Transition_Sprint_to_*, 회전 시퀀스 대량
- **용도:** 속도/방향 전환 + 곡선 trajectory (Circle Strafe 포함)

## 곡선 Strafe 시퀀스는 Transit DB가 더 적합 (실증)

PC_01 Fist_Battle_Jog_Circle_Strafe_L/R 테스트 시:
- GroundMoving DB에 넣으면 MM이 cost 평가해도 선택 빈도 낮음 (간단 스키마로 곡선 표현 부족)
- Transit DB에 넣으면 자연스러운 블렌딩 + 주변 시퀀스와 섞임 (실사용 관찰)
- Schema cardinality가 회전 방향/속도 feature를 담으니 곡선 cost 낮게 평가

**교훈:** "loop 시퀀스니까 GroundMoving" 이라는 단순 분류는 틀림. **시퀀스의 trajectory 복잡도** 기준으로 DB 선택.

## Monolith 액션 (검증됨)

```bash
# DB 조회
animation_query / get_database_stats                # sequence_count, schema, 등
animation_query / get_pose_search_database          # sequences 배열 전체 반환

# 시퀀스 추가/제거
animation_query / add_database_sequence             # param: anim_path (animation_path 아님!)
animation_query / remove_database_sequence          # param: sequence_index

# 속성 변경
animation_query / set_database_sequence_properties  # base_cost_bias, enabled 등

# 인덱스 재계산
animation_query / rebuild_pose_search_index
```

### 주의
- `add_database_sequence`의 응답 index는 순서 비결정적일 수 있음 (병렬 시 바뀜) — 추가 후 `get_pose_search_database`로 실제 index 재확인 필수
- `save_asset`은 P4 체크아웃 없으면 실패 — 에디터에서 수동 저장 필요
- `base_cost_bias` 범위: 일반적으로 `-0.1 ~ +0.1`. 음수 = 선호 (cost 낮춤), 양수 = 페널티

## How to apply
- 신규 loop 시퀀스 추가 시 **trajectory 복잡도 평가**:
  - 직선/단순 방향: PSD_GroundMoving
  - 곡선/회전/전환: PSD_GroundMovingTransit
- Chooser Row에 직접 시퀀스 참조하는 방식보다 **DB 등록 + MM cost bias** 조정이 SB2 설계 패턴과 맞음
