---
name: SB2 PC_01 OverlaySystem 실제 구조
description: Python 스크립트로 확인한 SB2 PC_01의 오버레이 시스템 에셋 구조. ChooserTable + DataAsset + Additive Pose 패턴.
type: project
originSessionId: e6d479b5-60ae-4f17-9866-6f6bdbc6b8cd
---
SB2 PC_01 OverlaySystem 에셋 경로: `/Game/ART/Character/PC/PC_01/OverlaySystem/`

**구조 (2026-04-16 Python 스크립트 확인):**
```
OverlaySystem/
├── PC_01_OverlayPose_Base (ABP)           — 오버레이 포즈 처리 베이스
├── PC_01_Overlays (ChooserTable)          — 조건 기반 오버레이 선택
├── PC_OverlayLayerBlending (ABP)          — 레이어 블렌딩 담당
├── BasePoses/
│   └── PC_01_Overlay_Stand_Base_Pose (AnimSequence) — Additive 기준 포즈
├── Data/
│   ├── E_OverlayPose (UserDefinedEnum)    — 오버레이 종류 열거형
│   └── PDA_OverlayData (Blueprint)        — 데이터 에셋 구조 정의
└── Poses/Fist_Normal_Guard/
    ├── PC_01_Fist_Normal_Gaurd_Overlay_DA (PDA_OverlayData_C) — DA 인스턴스 (typo: Gaurd)
    ├── PC_01_Fist_Normal_Guard_Overlay_ABP (AnimBlueprint)
    ├── PC_01_Fist_Normal_Guard_Pose_Idle (AnimSequence) — 정지 가드 포즈
    └── PC_01_Fist_Normal_Guard_Pose_Move (AnimSequence) — 이동 가드 포즈
```

**패턴:** ALS 스타일 Additive Pose Overlay (MM이 아닌 단일 프레임 포즈 기반)
- 로코모션은 Motion Matching, 오버레이는 Pose 2장 (Idle/Move)
- ChooserTable이 E_OverlayPose enum으로 오버레이 선택
- PDA_OverlayData가 각 오버레이의 ABP + 포즈 참조

**Why:** Python 스크립트로 에디터에서 직접 확인한 실측 데이터.

**How to apply:**
- Guard 오버레이 분석 시 MotionMatching 폴더가 아닌 OverlaySystem/Poses/ 확인
- 새 오버레이 추가 시 Poses/ 하위에 폴더 생성 + DA + ABP + Pose 시퀀스 패턴 따름
