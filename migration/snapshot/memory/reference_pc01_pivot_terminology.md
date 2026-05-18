---
name: PC_01 Pivot 용어 = *_Turn_*_{090,180} 시리즈
description: SB2 PC_01에서 "Pivot 모션"은 명명 _Pivot_ 클립이 아니라 의미상 방향 전환 모션. 실제 자산은 *_Turn_*_{090,180} 시리즈가 그 역할.
type: reference
originSessionId: a44afb55-887c-4d27-8ee8-e38c3eca007b
---
## 사실

SB2 PC_01에서 사용자가 부르는 **"Pivot 모션"**은:
- 명명에 `_Pivot_`이 들어간 클립이 **아니라**
- 의미상 **방향 전환 모션** = `P_Player_{Walk,Jog,Run,Sprint}_Turn_{L,R}_{090,180}_{Lfoot,Rfoot}` 시리즈

명명 _Pivot_ 클립은 PC_01엔 `P_Player_Fist_Battle_{Walk,Jog}_Pivot_*` 30종만 존재 (전투 자세 한정).
평시(Peaceful) Pivot 클립은 PC_01에 _Pivot_ 명명으로는 없고, Turn 시리즈로 대체.

## PC_01 Turn 시리즈 (PSD_GroundMovingTransit 실측)
- Walk: `*_Walk_Turn_{L,R}_{90,180}_{Lfoot,Rfoot}` — 8개
- Jog:  `*_Jog_Turn_{L,R}_{090,180}_{Lfoot,Rfoot}` — 8개
- Run:  `*_Run_Turn_{L,R}_{090,180}_{Lfoot,Rfoot}` — 8개
- Sprint:`*_Sprint_Turn_{L,R}_{090,180}_{Lfoot,Rfoot}` — 8개
- + Turn_045 12개, Turn_135 8개 (Other 등급)

180도 = 반대방향 입력, 90도 = side 입력 시 사용.

## PSD 등록 여부 (2026-05-15 정정)

**이전 메모리 "PSD_GroundMoving 57개 시퀀스에 Turn 0개" → 잘못된 결론.**

실제: Turn 시리즈는 `PSD_GroundMoving` (Loop용)이 아니라 **`PSD_GroundMovingTransit` (Transit용)에 정확히 32개(90/180) + 추가 12+8개(45/135) 등록**되어 있음. PSD 자체엔 정상.

→ "Pivot이 안 나와" 호소의 원인은 **PSD 미등록 아님**. 다음 중 하나:
1. Chooser row에서 Pivot 분기가 적절한 조건(Speed, TurnAngle, MoveSide)으로 도달 못 함
2. Chooser row의 `UseMotionMatching` 토글이 false → MM이 호출 안 되고 row Result 첫 항목 그대로 BlendStack
3. 같은 PSD의 `Reface_Start_*_090/180` 49개와 매칭 경쟁에서 밀림
4. PSS_SM_LocoTransitions Trajectory 채널(cardinality 22/34) 미가동 (`bGenerateTrajectory=False`)

## 영향
- "Pivot이 안 나와" 호소 → **Chooser row 시각 확인이 1순위 처방** (PSD 추가/수정 아님)
- 에디터에서 EvieAnimChooser_StateMachine 열어서 Turn row 조건 + UseMotionMatching/CostLimit 확인 필요

## Why
2026-05-11 세션에서 "Pivot" 명명만 좁게 추정해 PSD에 Turn 시리즈 부재가 "orphan" 처방으로 잘못 이어질 뻔함. 2026-05-15 Inspector 실측으로 등록 위치 확정 (PSD_GroundMovingTransit).

## How to apply
- PC_01 작업 시 사용자가 "Pivot" 언급하면 `*_Turn_*` 시리즈로 매핑해서 해석
- "Pivot 안 나와" → PSD 점검 말고 Chooser row + PSS 채널 보강 방향으로 진단
