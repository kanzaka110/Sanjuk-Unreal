---
name: SB2는 Motion Matching (Pose Search) 기반
description: SB2 PC_01 캐릭터가 BlendSpace가 아닌 Motion Matching을 사용. Guard Overlay ABP도 MM 기반. OverlaySystem + MotionMatching 폴더 구조.
type: project
originSessionId: e6d479b5-60ae-4f17-9866-6f6bdbc6b8cd
---
SB2 PC_01 캐릭터 애니메이션은 **Motion Matching (Pose Search)** 기반.

**Why:** 사용자가 직접 확인 — "블렌드 스페이스가 아닌 모션매칭을 쓰고 있어"

**How to apply:**
- PC_01 관련 분석/제안 시 BlendSpace 기반으로 추측하지 말 것
- Guard Overlay ABP도 Pose Search DB + Chooser Table 패턴으로 분석
- 에셋 경로: `/Game/ART/Character/PC/PC_01/MotionMatching/` (MM DB), `/Game/ART/Character/PC/PC_01/OverlaySystem/` (Overlay ABP)
- Pose Search Schema에서 상체 본(hand_l/r) 가중치 확인 필요
