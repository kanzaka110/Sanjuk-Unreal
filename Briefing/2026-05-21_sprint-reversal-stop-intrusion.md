# 질주 반전 onset Stop 끼임 — 원인 확정 (2026-05-21, 진행중)

IsPivoting F→B 해결([2026-05-21_ispivoting-fb-pivot-smoothedvelocity.md])의 잔존 과제 — 락온 질주 반전 onset에서 `Sprint_turn_Stop_*` 1~3프레임 끼임 — 의 **원인을 실측으로 확정**. 1차 처방은 레버 오인으로 회귀, revert. 처방 미적용 상태로 마감.

## 원인 (확정)

ANIM_REC 86개 onset 그룹 전수 분석:

```
frame  ms ms_l   sp   sv    fv   acc    rrr          seq
633     1   0   630  628  630  1200  None          Sprint_Start          ← 질주 풀스피드
634     1   0   458  588    0     0  LockOnTarget  →Sprint_turn_Stop_R ⚠️ ← fv/acc 붕괴, rrr 플립
635     1   6   331  525    0     0  None          Sprint_turn_Stop_R    ← 잔존, ip 켜짐
636     1   6   141  435  530  1200  None          →Sprint_Turn_R_180    ← fv 복구→Turn
```

**메커니즘**: 반전 inflection에서 미래 트라젝토리 속도 `fv` 0 통과 → 그 틱에 `RetransitReason=LockOnTarget` Re-Transit to GroundIdle 발동 → `_toTTGI`→TransitToGroundIdle → EvieAnimChooser GroundIdle sub-chooser가 **Stop DB(PSD_GroundIdleTransit)를 MM 검색셋(ValidAnimFromChooser)에 주입** → fv=0이라 MM이 Stop을 최저 cost로 매칭.

- onset 86건 **전부** `rrr=LockOnTarget`·`rrt=true`·`sv 577~588`·`ms=1`. 단일 예외 없음.
- 검증 교차: Stop seq 라인 119개 `rrr=LockOnTarget`(트리거) / 1803개 `None`(잔존).

## 1차 처방 실패 → revert

`FromGroundMoving→TransitToGroundIdle` 전이의 `NOT(IsMoving)`을 dip-tolerant `NOT((sv>50)OR(Speed2D>50))`로 교체 → **회귀**: 정상 jog-stop 비정상 + B→F 피봇 깨짐.
**오인 이유**: 끼임은 `ms=1`(Moving)·IsMoving=true 상태라 그 Idle 전이는 발동조차 안 함(범인 아님). B→F 피봇은 GroundMoving 재전이 의존인데 차단됨. → revert 완료.

## 다음 처방 (미적용)

`Re-Transit to GroundIdle → _toTTGI` 6 variant 중 **`RetransitReason==LockOnTarget` 포함 variant**의 룰에:
```
기존 AND NOT( (VSizeXY(SmoothedVelocity)>50) OR (Speed2D>50) )
```
- 이동 중 LockOnTarget→GroundIdle 재전이 차단 → fv=0 dip에 Stop DB 주입 안 됨.
- 진짜 정지(sv→0) 통과 → 정상. B→F(GroundMoving 경로) 무손상.

**⚠️ 적용 전 안전 확인**: rrr=LockOnTarget 871프레임 중 가드가 막을 855개에 TURN 296·Sprint류 포함. Turn은 PSD_GroundMovingTransit(다른 경로)라 안전 추정이나, **해당 variant 룰 T3D 배선 확인 후 적용**(회귀 2회 = 배선 미확인 편집). 사용자에게 T3D 요청해둠. 노드 편집은 에디터 수동 + Ctrl+S.

## 핵심 통찰

- `fv`(TrjFutureVelocity)·`acc`가 "반전 vs 진짜정지" 판별자. `sv`는 inflection 관통해 안정 → 유일 신뢰 신호.
- 끼임은 **MM/Chooser 레이어**(GroundIdle 재전이 DB 주입)지 SM Idle 전이 아님.
- 신규 도구: `scripts/analyze_reversal_asymmetry.py` (ms_l 전환으로 F↔B 반전 자동 검출).

## 참고

- 메모리: `project_pc01_sprint_reversal_stop_intrusion.md`
- 전 작업: `2026-05-21_ispivoting-fb-pivot-smoothedvelocity.md`
- ABP 변경은 Perforce(SB2) 별도 submit.
