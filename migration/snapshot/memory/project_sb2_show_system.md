---
name: SB2 Show 시스템 — 액션/스킬 연출 커스텀 시스템
description: SB2의 Show는 AnimSequence+FX+Sound+SkillStep을 타임라인으로 묶은 커스텀 연출 에셋. Guard/Skill 액션은 Show 에셋으로 재생됨. Art/Show/ 폴더.
type: project
originSessionId: ebbc629e-a8a1-40ce-8885-386c1ceb4efe
---
SB2의 **Show 시스템** — 애니메이션/이펙트/사운드/스킬로직을 타임라인으로 묶은 커스텀 연출 시스템.

**에셋 경로:** `/Game/ART/Show/PC/Player/`
```
Show/PC/Player/
├── FX/
├── Interaction/
├── ItemUse/
├── LinkSkill/
├── Revival/
└── Skill/
    ├── P_Player_Fist_Normal_Guard_Start  ← 가드 시작 Show
    ├── P_Player_Fist_Normal_Guard_End    ← 가드 해제 Show
    └── ... (다른 스킬 Show들)
```

**Show 에셋 내부 구조 (uasset 바이너리 string dump 확인):**
- `ShowKeyGroup_Animation` — AnimSequence 재생 트랙 (`AnimSequencePath` 필드로 시퀀스 지정)
- `ShowKeyGroup_Fx` — VFX/Niagara 트리거 트랙
- `ShowKeyGroup_Sound` — 사운드 트리거 트랙
- `ShowKeyGroup_SkillStep` — 스킬 로직 스텝 (데미지/판정 윈도우 등)
- `ShowPath` — 연결된 경로 데이터

**미확인 (추가 조사 필요):**
- ShowKey_Animation이 AnimSequence를 재생하는 API (PlayAnimation vs PlaySlotAnimationAsDynamicMontage vs ABP SequencePlayer)
- Show를 실행하는 엔트리 포인트 (C++ vs BP)
- Show → ABP 복귀 시의 블렌드 처리 여부

**Why:** "가드시작→가드대기 틕튐" 조사 중 `Art/Show/PC/Player/Skill/P_Player_Fist_Normal_Guard_Start.uasset`가 Guard01_Start 시퀀스를 참조하는 것을 발견. 사용자가 "show로 처리되고 있어"라고 언급.

**How to apply:**
- Skill/Guard 액션 재생 경로 분석 시 `Animation/Body/Attack/`의 AnimSequence가 아닌 `Art/Show/PC/Player/Skill/`의 Show 에셋부터 확인
- ABP(PC_01_ABP) 쪽을 건드리지 말고 **Show 에셋 자체의 KeyGroup 설정**이나 **참조된 AnimSequence의 커브**를 수정하는 방향 우선
- Show가 AnimInstance bypass 재생이면 Inertialization/Overlay 커브는 Show 끝난 후에야 작동 → 시퀀스 자체에 커브 박아두거나 블렌드 아웃 구간 확보 필요
