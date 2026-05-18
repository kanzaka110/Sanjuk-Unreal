---
name: UE 5.7 Groom PhysicsAsset 슬롯 위치 + 우선순위
description: GroomAsset/Binding엔 PhysAsset 필드 없음. UGroomComponent.PhysicsAsset 단일 슬롯이 우선, 비면 SkelMesh PhysAsset로 fallback.
type: reference
originSessionId: 33c8c3f0-53ef-45b1-8b23-2a8242724e7c
---
# UE 5.7 Groom PhysicsAsset 슬롯 위치

## 결론

**UE 5.7에서 Groom의 PhysicsAsset 슬롯은 `UGroomComponent.PhysicsAsset` 단 한 곳**. GroomAsset(.uasset)과 GroomBindingAsset(.uasset)에는 PhysicsAsset 필드가 없음.

## 슬롯 매핑

| 슬롯 | 존재? | 소스 |
|---|---|---|
| `GroomAsset.uasset` | **없음** | `cache/ue57_groom/GroomAsset.h` (PhysicsAsset 필드 0건) |
| `GroomBindingAsset.uasset` | **없음** | `cache/ue57_groom/GroomBindingAsset.h` (PhysicsAsset 필드 0건) |
| `UGroomComponent.PhysicsAsset` | **있음** | `cache/ue57_groom/GroomComponent.h` L53-55 — `TObjectPtr<UPhysicsAsset>`, Category="Simulation" |
| `UGroomComponent.CollisionComponents[]` | 수동 추가 | `GroomComponent.h` L57-58 — `AddCollisionComponent(SkelMeshComp)` 호출 |
| `SkeletalMeshComponent.PhysicsAsset` | 자동 fallback | `NiagaraDataInterfacePhysicsAsset.cpp` L709-723 |

## 우선순위 (Niagara DI가 PhysAsset 찾는 순서)

`NiagaraDataInterfacePhysicsAsset.cpp` L699-727 + `GroomComponent.cpp` L3699-3713 (UE 5.7):

1. **`GroomComponent.PhysicsAsset`** — Details > Simulation > Physics Asset 슬롯 (**최우선**)
2. `GroomComponent.CollisionComponents[*].PhysicsAsset` — BP에서 `AddCollisionComponent`로 등록
3. (1)/(2) 비면 → attach된 SkelMeshComp의 `PhysicsAsset` 자동 fallback
4. 다 없으면 Niagara DI `DefaultSource` (보통 None)

## How to apply

진단 시:
1. **SkelMesh PhysAsset만 보고 "캡슐 부재"라고 단정 금지.** 먼저 `UGroomComponent.PhysicsAsset` 슬롯 확인
2. BP의 GroomComponent 덤프 → `physics_asset` 필드가 None이면 fallback, 값 있으면 그게 1순위
3. Python: `obj.get_editor_property("physics_asset")`로 추출

## PC_01 실측 (2026-04-29)

- `PC_01_BP_Sanjuk` Hair_GEN_VARIABLE.physics_asset = `Evie_Body_PhysicsAsset`
- PC_01 SkelMesh `CH_P_01_Head_001` PhysAsset에 head 캡슐 없어도 무관 — Groom 슬롯이 우선
- 들림 이슈 → 해결됨

## 덤프 스크립트

`scripts/dump_pc01_groom_component_physasset.py` — SubobjectDataSubsystem으로 BP의 모든 SCS 노드 순회 후 GroomComponent의 physics_asset/binding_asset/groom_asset 출력.

5.7 API 함정:
- `cls_name == "GroomComponent"` 비교 안 됨 (SBCharacterGroomComponent 같은 서브클래스). `"GroomComponent" in cls_name` 사용
- `is_a` 메소드 5.7 Python에 없음 — 문자열 매칭만 안전
- `bp.simple_construction_script` 직접 접근 5.7에서 차단 → `unreal.SubobjectDataSubsystem` + `k2_gather_subobject_data_for_blueprint(bp)` 사용
- `SubobjectDataBlueprintFunctionLibrary.get_object(data)` (deprecated 경고 나오지만 작동)

## 관련

- `reference_groom_physics_params.md` — 파라미터 단일 진실원
- `feedback_project_collision_requires_physassets_review.md` — 들림 이슈 케이스
