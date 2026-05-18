---
name: PlantSettings.LockType=PivotAroundAnkle은 PC_01에서 "발목 고정" 유발
description: PC_01 LockType=PivotAroundAnkle이 전투 대기/공격 시 "발목이 한 점에 박혀 다리가 밀리는" 체감을 만든다. PivotAroundBall 권장.
type: feedback
originSessionId: 915e0a07-84b5-49c5-85a3-b1bae72cd4e4
---
PC_01에서 PlantSettings의 `LockType = PivotAroundAnkle` 사용 금지. **PivotAroundBall** 사용.

**Why:**
- 사용자(SB2 애니 TA)가 2026-04-29 보고: 전투 대기/공격에서 "발목이 고정되어 다리가 밀리는" 증상. LockType을 `PivotAroundBall`로 변경 → 즉시 해소
- 메커니즘: PivotAroundAnkle은 **발목 위치 자체를 plant point에 고정**하고 발은 발목 기준 회전만 허용. 캐릭터 모션이 발목을 옮기려 하면 IK가 본을 끌어당겨 다리가 밀리는 형태. 사용자 체감 = "발목이 박혀있다"
- PivotAroundBall은 발끝(ball)을 pivot으로 → 발목은 ball 중심 호 안에서 자연스럽게 움직임 → 모션 추종 가능
- 즉 PC_01에서는 ball 기준 lock이 발목 기준보다 모션 친화적

**How to apply:**
- 신규 PlantSettings 변수 만들 때 **default LockType = PivotAroundBall**
- 기존 변수에서 LockType=PivotAroundAnkle 발견 시 의심하고 사용자 확인
- 단 PivotAroundBall도 UnplantRadius/UnplantAngle이 크면 lock 지속 → 다른 캐릭터에서 비슷한 증상 호소 시 LockType만이 아니라 Unplant 임계도 같이 점검
- Combat/Default 분기 신설로 해결하려 하지 말 것 — 단일 PlantSettings에서 LockType만 Ball로 두면 충분 (사용자 결정: "전투 시 값 따로 안 빼도 됨")

**관련 메모리:**
- `reference_foot_placement_source_5_7.md` — UE 5.7 LockType enum (PivotAroundBall=0, PivotAroundAnkle=1, Unlocked=2)
- `cache/ue57/AnimNode_FootPlacement.h` L210~225 — LockType 정의
