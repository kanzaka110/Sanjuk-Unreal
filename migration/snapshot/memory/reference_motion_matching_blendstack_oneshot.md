---
name: BlendStack + Motion Matching — 1회성 anim 처리 원칙 (UE 5.7)
description: Motion Matching 기반 ABP 에서 Land/Stagger/Knockdown 같은 1회성 anim을 Chooser row로 둘 때 output struct UseMotionMatching=False 가 기본. SB2 PC_01 freeze 사례에서 검증.
type: reference
originSessionId: 3c08abb7-30a4-4914-aa98-a67f4e1039a6
---

# Motion Matching + BlendStack 1회성 anim 일반 원칙

## 배경
UE 5.7 의 PoseSearch + BlendStack 기반 ABP (예: GASP, SB2 PC_01) 에서, Chooser Table 의 result output struct 에 `UseMotionMatching` 플래그가 있음. 이 플래그가 BlendStack 에 입력되는 anim 의 재생 방식을 결정.

## 두 모드 비교

| 모드 | UseMotionMatching=True | UseMotionMatching=False |
|---|---|---|
| 시작 프레임 | Pose Search DB에서 best matching pose 검색 → 그 프레임으로 jump-in | 첫 프레임부터 정상 재생 |
| 진행 | 매 frame DB에서 다음 best pose 검색 | 시간순 자연 진행 |
| anim 끝 | DB 의 다른 anim 으로 자연 chain | BlendOut → 다음 state 트랜지션 |
| DB에 anim 포즈 없을 시 | **stuck → freeze** ⚠️ | 영향 없음 (DB 미사용) |

## 어느 anim 이 어느 모드?

### MM=True 적합 (Locomotion 류)
- Idle Loop
- Walk / Jog / Run / Sprint Loop
- Stop (Walk_Stop, Jog_Stop 등) — DB에 등록된 것
- Strafe / Pivot
- Lean / Aim Offset

특징: **연속 / 반복 가능 / DB 풍부**

### MM=False 적합 (1회성 류) ⭐
- **Jump / Land** (`Jump_F_Land_Stand_*` 등)
- **Stagger / Hit / Knockdown**
- **Roll / Dodge** (특정 시점에서만 시작)
- **Mount / Dismount** (Mountable, Vehicle 진입)
- **Cinematic / Show 시퀀스**
- **Guard Start / Guard End**

특징: **시작-진행-끝 구조 / 1회 재생 / DB 미포함 또는 부분만**

## SB2 PC_01 검증 사례 (2026-04-29)

`N_Idle_Land` sub-chooser 의 row 0 (`P_Player_Jump_F_Land_Stand_Light_Lfoot`) output struct 가 `UseMotionMatching=True` 였음 → 점프 후 제자리 착지 시 freeze.

해결: output struct UseMotionMatching=False 로 변경 → freeze 해소.

상세는 `project_pc01_jump_land_freeze.md` 참조.

## 진단 체크리스트

freeze / Land 포즈 stuck / 특정 anim 에서 stop 가 보이면:

1. **어느 Chooser row 가 매칭되었는가** 확인 (Chooser Debug 또는 Animation Insights)
2. 그 row 의 **output struct 의 UseMotionMatching 값** 확인
3. 매칭된 anim 이 **1회성 vs Locomotion** 분류
4. 1회성인데 MM=True → 처방: MM=False 로 변경

## 변경 위치 — 두 가지 옵션

### 옵션 A (권장): Chooser row output struct 레벨
- 변경 위치: ChooserTable 에셋의 result output 컬럼 InstancedStruct
- 장점: 격리된 컨텍스트. 같은 anim 이 다른 Chooser 에서 MM=True 로 쓰여도 영향 없음
- 단점: 동일 row 가 여러 chooser 에 있으면 각각 변경

### 옵션 B (비권장): 시퀀스 자체 옵션
- 변경 위치: AnimSequence 자산의 root motion / sampling 옵션
- 단점: 모든 chooser/state 에서 영향 → 의도치 않은 곳에서 동작 변화
- 사용 시점: 그 anim 이 *어디서든* MM 쓰면 안 되는 본질적 1회성일 때만

## How to apply
- ABP 에 Land/Stagger/Knockdown 등 1회성 anim row 추가 시 **UseMotionMatching=False 디폴트로 설정**
- "freeze / 한 포즈에서 멈춤" 증상은 가장 먼저 이 플래그부터 의심
- 진단할 때 Chooser row output struct 까지 캡처에 포함
- DB(PoseSearchDatabase) 에 등록된 anim 만 MM=True 안전. 등록되지 않은 anim 은 무조건 False
