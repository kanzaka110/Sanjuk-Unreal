---
name: SB2 Mutable Crowd 시스템 — Mass AI + AnimNext + Mutable + ABP Hybrid
description: SB2의 군중(Crowd) 캐릭터는 Mass Entity + AnimNext Module + Mutable CO + 표준 ABP 4중 병렬 구조. 18개 AnimNext 에셋 + Mutable CO + 공용 Crowd_Base_ABP로 수백 명 처리.
type: project
originSessionId: ebbc629e-a8a1-40ce-8885-386c1ceb4efe
---
SB2 군중 시스템은 **4중 병렬 구조**로 성능+외형 다양성 확보.

**경로:** `/Game/ART/Character/Mutable/`

## 구성 요소

### 1. Mass AI Entity (Mass framework)
- Crowd 개체별 위치/속도/LocomotionState 관리
- Fragment: `ESBMassCrowdLocomotionState` (SB2 커스텀 enum)
- 수백~수천 entity 동시 처리

### 2. AnimNext (Mutable/AnimNext/ 18 assets)
- **Workspace_Crowd_Default** — 편집 컨테이너
- **M_Crowd_Default** (`UAFModule`) — 런타임 엔트리, 589KB
  - InitializeEvent + PrePhysicsEvent (TickGroup 지정)
  - ExecuteBindings_GT (GameThread) / _WT (Worker Thread) 분리
  - RunAnimationGraph → AG_Crowd_Default/Head/Hair + CHT_Crowd_Facial
- **UAFSV_Crowd_Default** — Shared Variables (12개 Crowd* 변수)
- **AG_Crowd_Default** (933KB) — 메인 AG, **594개 trait**
  - BlendLayer×128 (HT_ 기반), ApplyAdditive×70, SequencePlayer×64
  - BlendSpacePlayer×50, BlendStack×49, BlendByBool×43
  - MakeDynamicAdditive×27, NotifyDispatcher×25, BlendTwoWay×17
  - BlendSmoother×13, BlendInertializer×10, ControlRigTrait×1
- **HT_Crowd_*** × 7 (`HierarchyTable_TableType_Skeleton` + `ElementType_Mask`)
  - ArmL, ArmR, Spine, UpperBody, LowerBody, FullBody_Test, Facial
  - 전체 스켈레톤의 모든 본 포함 + 본별 mask weight (UE 5.6+ 신규 에셋)
  - Facial 321KB (얼굴 본 추가로 다른 HT의 5.8배)
- **CHT_Crowd_Facial** — enum `AnimStanceType` → Evie 페이셜 시퀀스 매핑 (Basic/Battle/Groggy)
- **CR_Crowd_Foot_IK** — Foot IK Control Rig
- **AG_Crowd_Hair/Head/IK** + **AG_Sub_Crowd_ControlRig_Skirt** — 서브 그래프
- **BS_Crowd_Walk** — 기존 BlendSpace (재사용)

### 3. Mutable (Anticto 플러그인)
- `/Game/ART/Character/Mutable/Crowd/Crowd_01..04/` — 캐릭터 variant
- 각 Crowd_N 내:
  - `CO/Crowd_N_Common_CO` (UCustomizableObject) — 파츠 조합 그래프
  - `CO/*_COI` (UCustomizableObjectInstance) — 런타임 instance
  - `Parts/Body/Head/Hair/Upper/Lower/` — 교체 가능 파츠
  - `Fixed/CrowdMan_001~005` — 이름있는 NPC
  - `Blueprints/Crowd_01_ABP` — 얇은 래퍼 (Crowd_Base_ABP 상속)
- **HairStrandsMutableExtension__Grooms** — Groom 헤어 통합
- 교차 캐릭터 파츠 참조 가능 (Crowd_01의 CO가 Crowd_03의 hair 참조)

### 4. 표준 ABP (Crowd_Base_ABP)
- Walk 시퀀스 12종 (F/B/L/R/FL/FR/BL/BR + InPlace 변형), Flee, Idle
- AnimGraph 노드: FootPlacement, LegIK, DeadBlending, LayeredBoneBlend, BoneScale(SB2 커스텀), LinkedAnimLayer
- **LinkedAnimLayer를 통해 AnimNext 결과 주입** (추정 — 정확한 지점은 T3D 필요)

## 통합 지점

Crowd Actor에 다음 컴포넌트들:
- `SkeletalMeshComponent` — Crowd_Body_Skeleton + Crowd_01_ABP(→ Crowd_Base_ABP 상속)
- `CustomizableSkeletalMeshComponent` — Mutable 외형 조합
- **`AnimNextModuleInjectionComponent`** — M_Crowd_Default 런타임 실행

**런타임 Flow:**
```
Mass Entity 상태 → AnimNext Bindings → Variables 갱신
   → AG_Crowd_Default/Head/Hair 평가 (Worker Thread)
   → 결과 pose → ABP의 LinkedAnimLayer로 주입
   → ABP가 IK/FootPlacement 마감 → SkeletalMesh 렌더
```

## SB2 커스텀 C++ 레이어

- `FSBCrowdAnimNextInputData` / `MontageData` / `PoseCurveData` (struct)
- `ESBMassCrowdLocomotionState` (enum)
- `ESBBoneControlSpace` / `ESBBoneModificationMode` (enum)
- `AnimGraphNode_BoneScale` — 커스텀 ABP 노드

## 주요 인사이트

- **ABP 완전 폐기 아님**: AnimNext는 레이어링/상태 기반 포즈 담당, IK/FootPlacement 등 검증된 기능은 ABP 유지 (점진 전환)
- **HierarchyTable = LayeredBoneBlend Branch Filter의 현대적 대체**: 에셋으로 분리해 재사용 + 에디터 페인터
- **Worker Thread 분산**: 무거운 블렌드 계산을 워커 스레드로 (Mass AI 수백 entity 성능 유지)
- **페이셜 공유**: Crowd가 PC_01(Evie) 페이셜 시퀀스 재사용 (`EVIE_Facial_Idle_*`) — 스켈레톤 호환
- **Workspace_ 에셋**: AnimNext 편집용 허브, 런타임엔 Module만 필요

## 분석 파일 위치

- 분석 시점: 2026-04-17
- T3D/세부 노드 구조는 미분석 (문자열 패턴 기반 요약 수준)
- 정확한 ABP↔AnimNext 주입 지점 확인엔 Crowd_Base_ABP의 AnimGraph T3D copy 필요

**Why:** 사용자(SB2 애니 TA)의 요청으로 Mutable 폴더 AnimNext 내용 체계 분석. 18개 에셋 + Crowd 4종 + CO 시스템 파악.

**How to apply:**
- Crowd/Mass AI/AnimNext 관련 요청 시 이 구조를 기반으로 답변
- AnimNext 개별 에셋 분석이 필요하면 Workspace_Crowd_Default를 에디터에서 열어 그래프 시각화 추천
- HierarchyTable 편집은 에셋 더블클릭 후 본별 mask painter로 (Maya vertex weight paint와 유사)
- SB2의 `FSBCrowd*` struct와 `ESBMassCrowd*` enum은 엔진 팀 C++ — 헤더/구현 확인 시 Monolith source_query 또는 팀 문의
