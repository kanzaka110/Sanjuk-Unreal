# SB2 PC_01 OverlaySystem 구조 덤프

수집일: 2026-04-16  
Monolith 버전: 0.12.1  
기준 경로: `/Game/Art/Character/PC/PC_01/OverlaySystem/`

---

## 1. OverlaySystem ABP 에셋 목록

| 에셋명 | 경로 | 역할 |
|--------|------|------|
| **PC_01_OverlayPose_Base** | `.../OverlaySystem/PC_01_OverlayPose_Base` | 오버레이 포즈 베이스 클래스 |
| **PC_OverlayLayerBlending** | `.../OverlaySystem/PC_OverlayLayerBlending` | 오버레이 레이어 블렌딩 로직 |
| **Evie_ALI_Overlay** | `/Game/Art/Character/PC/Evie/OverlaySystem/Evie_ALI_Overlay` | Evie 오버레이 ALI |
| **Evie_ABP_Overlay_Default** | `.../Evie/OverlaySystem/OverlayAnimation/Evie_ABP_Overlay_Default` | Evie 기본 오버레이 |
| **Evie_ABP_Overlay_Feminine** | `.../Evie/OverlaySystem/OverlayAnimation/Stance_Feminin/` | Evie 여성스러운 자세 |
| **Evie_ABP_Overlay_Injured** | `.../Evie/OverlaySystem/OverlayAnimation/Stance_Injured/` | Evie 부상 자세 |
| **PC_01_Fist_Normal_Guard_Overlay_ABP** | `.../OverlaySystem/Poses/Fist_Normal_Guard/` | 주먹 일반 가드 포즈 |

---

## 2. PC_01_OverlayPose_Base

```
asset_path:      /Game/Art/Character/PC/PC_01/OverlaySystem/PC_01_OverlayPose_Base
skeleton:        PC_01_Body_001_Skeleton
parent_class:    AnimInstance
state_machine_count: 0
graph_count:     3 (AnimGraph, SetReference, EventGraph)
variable_count:  3
interfaces:      PC_01_AnimationLayerInterface_Overlay_C
```

**역할**: 모든 Overlay 포즈 ABP의 기반 클래스. `PC_01_AnimationLayerInterface_Overlay_C` 인터페이스를 구현.

---

## 3. PC_OverlayLayerBlending

```
asset_path:      /Game/Art/Character/PC/PC_01/OverlaySystem/PC_OverlayLayerBlending
skeleton:        PC_01_Body_001_Skeleton
parent_class:    SBActorAnimInstance
state_machine_count: 0
graph_count:     3 (AnimGraph, UpdateLayerValues, EventGraph)
variable_count:  11
```

### 변수 목록 (커브 기반 블렌딩 제어)

| 변수명 | 타입 | 카테고리 | 설명 |
|--------|------|---------|------|
| Spine_Add | real | CurveValues | 척추 가산 블렌딩 가중치 |
| Head_Add | real | Curve Values | 머리 가산 블렌딩 가중치 |
| Arm_L_Add | real | Curve Values | 왼팔 가산 블렌딩 |
| Arm_R_Add | real | Curve Values | 오른팔 가산 블렌딩 |
| Arm_L_LS | real | Curve Values | 왼팔 LocalSpace 블렌딩 |
| Arm_R_LS | real | Curve Values | 오른팔 LocalSpace 블렌딩 |
| Arm_L_MS | real | Curve Values | 왼팔 MeshSpace 블렌딩 |
| Arm_R_MS | real | Curve Values | 오른팔 MeshSpace 블렌딩 |
| Hand_L | real | Curve Values | 왼손 블렌딩 |
| Hand_R | real | Curve Values | 오른손 블렌딩 |
| AllLayerAlpha | real | 디폴트 | 전체 레이어 알파 |

**특이사항**: 부위별 블렌딩 모드(Add/LocalSpace/MeshSpace)를 커브 값으로 분리 제어.

---

## 4. PC_01_Fist_Normal_Guard_Overlay_ABP

```
asset_path:      /Game/Art/Character/PC/PC_01/OverlaySystem/Poses/Fist_Normal_Guard/PC_01_Fist_Normal_Guard_Overlay_ABP
skeleton:        PC_01_Body_001_Skeleton
parent_class:    PC_01_OverlayPose_Base_C     ← 베이스 클래스 상속
state_machine_count: 0
graph_count:     1 (EventGraph)
variable_count:  0
interfaces:      없음 (부모에서 상속)
```

**구조**: `PC_01_OverlayPose_Base_C`를 상속하는 구체 포즈 ABP.  
변수 없이 오직 포즈 데이터만 제공.

---

## 5. PC_01_ABP에서 OverlaySystem 연결 구조

```
PC_01_ABP (AnimGraph)
  └── LinkedAnimLayer: OverlayPose
        │  (인터페이스: PC_01_AnimationLayerInterface_Overlay_C)
        └── PC_OverlayLayerBlending
              ├── AnimGraph: 커브 기반 부위별 블렌딩
              │     ├── Spine_Add / Head_Add
              │     ├── Arm_L/R_Add, Arm_L/R_LS, Arm_L/R_MS
              │     └── Hand_L/R
              └── PC_01_OverlayPose_Base (인터페이스 구현)
                    └── PC_01_Fist_Normal_Guard_Overlay_ABP (구체 포즈)
```

---

## 6. OverlaySystem 관련 PC_01_ABP 변수

```
OverlayPoseState: byte   ← 현재 오버레이 포즈 상태 (E_OverlayPose enum 값)
OverlayWeight:    real   ← 오버레이 블렌딩 가중치
```

---

## 7. PC_01_AnimationLayerInterface_Overlay (인터페이스 ABP)

```
경로: /Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimationLayerInterface_Overlay
역할: 오버레이 레이어 인터페이스 정의
PC_01_ABP에서 linked_anim_blueprints에 포함됨
```

---

## 8. 참고: Evie OverlaySystem 구조 (PC_01 참고용)

Evie도 동일한 패턴:
- `Evie_ALI_Overlay` — 레이어 인터페이스
- `Evie_ABP_Overlay_Default` — 기본 오버레이 포즈
- `Evie_ABP_Overlay_Feminine` — Stance_Feminin 서브폴더
- `Evie_ABP_Overlay_Injured` — Stance_Injured 서브폴더

---

## 9. 수집 상태

| 항목 | 상태 |
|------|------|
| OverlaySystem ABP 목록 | 완료 |
| PC_01_OverlayPose_Base 구조 | 완료 |
| PC_OverlayLayerBlending 변수 | 완료 |
| PC_01_Fist_Normal_Guard_Overlay_ABP | 완료 |
| PC_01_Overlays ChooserTable | 미수집 (인덱싱 미완료, 88-89% 단계에서 실패) |
| E_OverlayPose enum 값 목록 | 미수집 (ChooserTable 검색 경로 없음) |
