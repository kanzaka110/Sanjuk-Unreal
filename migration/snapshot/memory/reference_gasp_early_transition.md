---
name: gasp-bp-notifystate-earlytransition
description: GASP CMC ABP에서 Transition 도중 안전 윈도우에 다음 Transition 재선택/Loop 합류를 허용하는 노티 패턴. SB2 PC_01 Transition 노이즈 처방 후보.
metadata: 
  node_type: memory
  type: reference
  originSessionId: 9ea7c598-8cce-49a9-8048-20a2afaf6c13
---

## 위치 (GASP 5.6+)
- `C:\Users\SHIFTUP\Documents\Unreal Projects\GameAnimationSample\Content\Blueprints\AnimNotifies\`
  - `BP_NotifyState_EarlyTransition.uasset` — AnimNotifyState
  - `E_EarlyTransition_Condition.uasset` — 발화 조건 enum
  - `E_EarlyTransition_Destination.uasset` — 행선지 enum
- 소비측: `SandboxCharacter_CMC_ABP` / `SandboxCharacter_Mover_ABP` (BPI_SandboxCharacter_ABP 인터페이스 구현)

## 노티 구조

**2 프로퍼티**:
- `TransitionCondition: E_EarlyTransition_Condition`
  - `GaitNotEqual` — 현재 Gait가 노티 셋업 Gait와 다를 때만 발화
  - `Always` — 무조건 발화
- `TransitionDestination: E_EarlyTransition_Destination`
  - `ReTransition` — "다음 Transition 후보를 다시 골라봐" (MM 재검색 허용)
  - `ToLoop` ("Transition To Loop") — "이젠 Loop DB로 합류"

**NotifyTick 로직**:
1. IsBlendingOut 체크 (블렌드 아웃 중이면 차단)
2. Condition 평가 (GaitNotEqual 또는 Always)
3. Destination 분기 → AnimBP 인터페이스 호출:
   - `Set_NotifyTransition_ReTransition()` 또는
   - `Set_NotifyTransition_ToLoop()`

## 소비측 (AnimBP)

AnimBP는 두 인터페이스 함수를 구현해 내부 bool 또는 Trajectory feature로 들고 있다가, **Motion Matching Chooser/BlendStack의 PSS 입력**으로 흘려보냄.

## 디자인 의도

- Transition 애니메이션은 풋플랜팅+무게중심 변화 묶음 — 끝까지 안 보면 발 슬립 위험
- 그래서 MM은 Transition 시작 시 block, 다른 후보 검색 차단
- 그러나 플레이어 입력은 그 짧은 사이에도 바뀜 → block 그대로면 "input lag"
- 해결: 안전 윈도우(다음 풋플랜트 직전 등)에 노티 깔고, 그 동안만 `ReTransition=true` 켜서 MM 재검색 허용

## 두 신호 사용처

| 신호 | 의미 | 트리거 예 |
|------|------|---------|
| `NotifyTransition_ReTransition` | 새 Transition 후보 재선택 허용 | Walk→Run 중 입력이 다시 Walk로 → Run→Walk Transition으로 갈아타기 |
| `NotifyTransition_ToLoop` | 타겟 Gait 도착, Loop로 합류 | Sprint→Run 후반부에서 Run loop로 일찍 합류 |

## SB2 PC_01 적용 검토

PC_01 적용 시 효과/제약:

**효과 있음**:
- 입력 lag 해소 (Transition 끝까지 봐서 늦게 반영)
- 풋플랜트 깨짐 방지 (윈도우만 풀어주므로 안전)
- 블렌드 팝 (`ToLoop` + Inertialization)
- Pivot 도배 추가 차단 (Cooldown과 결합)

**효과 제한적**:
- Sprint→Battle B_Lfoot 잔존 회전 → root motion 누적 문제, ReTransition 무관
- Chooser 1회 평가 — flag만 켜진다고 재진입 안 함, Chooser row 조건 입력으로도 넣어야 함
- 락온 strafe 잔존 root motion 미적용 → OnResetOffsetRootBoneEvent 영역

**도입 비용**:
1. PSD 분리 (Transition vs Loop) — 부분 도입 가능
2. 인터페이스 추가 (`Set_NotifyTransition_ReTransition`/`ToLoop`)
3. ABP 변수 2개 + 윈도우 만료 타이머 (Pivot Cooldown 패턴 재사용 가능)
4. Chooser 입력 확장 (`bAllowReTransition`/`bAllowToLoop` 컬럼)
5. 노티 부착 (Transition 클립 수십~수백 개에 윈도우 수동 깔기 — 최비용)

**권장 도입 순서**:
1. 단기: 보류. Stop/Pivot PSD orphan 해소 + Chooser row 정밀화 먼저 (Inspector 2026-05-15 결과: PSD orphan은 거짓 가설, Chooser row가 진짜 처방 포인트)
2. 중기: Sprint↔Battle / Sprint→Jog 잔존 회전 잦은 transition만 부분 적용. `ToLoop` 부터 (블렌드 팝 해소, 비용 낮음)
3. 장기: 전체 Transition 클립 일괄 노티 + Chooser 입력 표준화

## How to apply
- "Transition 노이즈" 류 호소 시 — EarlyTransition이 답인지 아닌지 케이스별 판별
- 발 슬립/블렌드 팝/입력 lag → 도움
- Root motion 누적/잘못된 MM 선택/PSD 미가동 → 무관 (다른 처방 필요)
