---
name: feedback-pc01-trd-smoothing-alpha-0-075
description: PC_01 ABP UpdateTargetRotation trd wraparound smoothing 의 lerp Alpha = 0.075 (Multiply.B). 사용자 PIE 검증 결과 best. 0.5 같은 큰 값은 부작용. SB2 PC_01 적정값으로 잠금.
metadata: 
  node_type: memory
  type: feedback
  date: 2026-05-15
  originSessionId: 9dcc5175-e415-47ad-96d0-959bb0242e16
---

# PC_01 trd 평활화 Alpha = 0.075 (사용자 검증값)

## 룰
PC_01_ABP UpdateTargetRotation Strafe 분기의 trd wraparound smoothing chain에서 lerp 비율 (Multiply 노드의 B 핀) 은 **0.075** 유지. 0.5 / 0.3 / 0.7 같은 큰 값은 부작용 발생.

## Why
- 사용자 PIE 검증 (2026-05-15) 2단계:
  - "0.075 로 곱해주니까 제일 괜찮은 것 같아" — 단발 큰 회전 (락온 반대 질주 종료 등)
  - "이동 커맨드를 매우 빠르게 움직였을 때 회전이 꼬이는 문제가 생겨" — 0.075 만으로는 빠른 연속 입력 lag
- 가설: `TargetRotationDelta` 의 의미가 **target absolute (mesh와 controller 사이의 각도 차)** 일 가능성. 강한 lerp(0.5) 시 mesh 회전 방향 의도와 어긋남. 약한 lerp(0.075) 시 빠른 입력 변화 못 따라감
- Adaptive: 작은 diff(<45°)에서는 mesh 회전 방향 의도와 거의 일치하므로 0.5 안전, 큰 diff(≥45°)에서는 부드러운 0.075 필요

## How to apply
- 본 처방 [[pc01-trd-wraparound-smoothing]] 의 Phase 2 Adaptive 구조 유지
- InRange threshold = ±45° 가 사용자 best — 30°/60° 등은 미검증
- Alpha 값 0.5 / 0.075 양쪽 다 사용자 검증값 — 미세 조정 시 작은쪽 0.4~0.6, 큰쪽 0.05~0.1 범위 안에서만
- 단일 Alpha (Adaptive 폐기) 는 시도하지 말 것 — 두 시나리오 동시 만족 불가능 확인됨

## 관련
- 처방 본문: [[pc01-trd-wraparound-smoothing]]
- ABP 체인: [[pc01-abp-chain]]
- 진단 도구: [ANIM_REC] trd 변동폭 분석
