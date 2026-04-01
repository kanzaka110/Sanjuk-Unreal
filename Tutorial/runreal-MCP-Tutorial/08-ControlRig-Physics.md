# 08. Control Rig & Physics

> Control Rig, IK Rig, Physics Asset, IK Retargeter를 Python으로 다루는 방법

## Control Rig

### Control Rig 에셋 정보 조회

```python
import unreal
import json

cr = unreal.load_asset('/Game/Rigs/CR_Character')
if cr:
    info = {
        'name': cr.get_name(),
        'class': cr.get_class().get_name(),
    }
    print(json.dumps(info, indent=2))
```

### 시퀀서에서 Control Rig 키프레임 작업

Control Rig은 주로 **시퀀서(Level Sequence)** 컨텍스트에서 Python으로 조작합니다:

```python
import unreal

level_seq = unreal.load_asset('/Game/Cinematics/MySequence')
if level_seq:
    bindings = level_seq.get_bindings()
    for binding in bindings:
        tracks = binding.get_tracks()
        for track in tracks:
            track_name = track.get_class().get_name()
            print(f'Track: {track_name}')
            if 'ControlRig' in track_name:
                sections = track.get_sections()
                for section in sections:
                    print(f'  Section: {section.get_class().get_name()}')
```

> **참고**: Control Rig 그래프 노드 자체를 Python으로 편집하는 것은 매우 제한적입니다. 노드 추가/와이어링이 필요하면 **Monolith MCP**를 사용하세요. Epic 공식 문서: [Python Scripting for Control Rig](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-scripting-for-animating-with-control-rig-in-unreal-engine)

---

## IK Rig

### IK Rig 에셋 조회

```python
import unreal
import json

registry = unreal.AssetRegistryHelpers.get_asset_registry()
ar_filter = unreal.ARFilter(
    class_names=['IKRigDefinition'],
    package_paths=['/Game/'],
    recursive_paths=True
)
assets = registry.get_assets(ar_filter)

result = []
for ad in assets:
    result.append({
        'name': str(ad.asset_name),
        'path': str(ad.package_name)
    })

print(json.dumps(result, indent=2))
```

---

## IK Retargeter (리타게팅)

Epic이 Python API를 공식 지원하는 영역입니다. UE 5.2+ 문서 참고.

### Retargeter 생성 및 설정

```python
import unreal

source_rig = unreal.load_asset('/Game/Rigs/IKR_Mixamo')
target_rig = unreal.load_asset('/Game/Rigs/IKR_Mannequin')
retargeter = unreal.load_asset('/Game/Rigs/RTG_MixamoToMannequin')

if retargeter:
    controller = unreal.IKRetargeterController.get_controller(retargeter)

    controller.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, source_rig)
    controller.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, target_rig)

    print('Retargeter configured')
```

### 리타겟 체인 설정 조회

```python
import unreal
import json

retargeter = unreal.load_asset('/Game/Rigs/RTG_MixamoToMannequin')
if retargeter:
    controller = unreal.IKRetargeterController.get_controller(retargeter)
    chains = controller.get_all_chain_settings()

    result = []
    for chain in chains:
        result.append({
            'target_chain': str(chain.target_chain),
        })

    print(json.dumps(result, indent=2))
```

### 배치 리타게팅 실행

```python
import unreal
import json

source_path = '/Game/Mixamo/Animations/'
output_path = '/Game/Characters/Retargeted/'

editor_util = unreal.EditorAssetLibrary
all_assets = editor_util.list_assets(source_path, recursive=True)

registry = unreal.AssetRegistryHelpers.get_asset_registry()
count = 0
for asset_path in all_assets:
    asset_data = registry.get_asset_by_object_path(asset_path)
    class_name = str(asset_data.asset_class_path.asset_name)
    if class_name == 'AnimSequence':
        count += 1
        print(f'Found AnimSequence: {asset_data.asset_name}')

print(f'Total AnimSequences to retarget: {count}')
print(f'Use Editor UI or Monolith for batch retargeting execution')
```

> **팁**: 실제 배치 리타게팅 실행은 에디터 UI의 Batch Export/Retarget 기능이나 Monolith MCP가 더 안정적입니다. Python으로는 대상 목록 파악과 설정까지만 하고, 실행은 에디터 UI를 권장합니다.

---

## Physics Asset

### Physics Asset 정보 조회

```python
import unreal
import json

phys_asset = unreal.load_asset('/Game/Characters/PA_Character')
if phys_asset:
    bodies = phys_asset.get_editor_property('skeletal_body_setups')
    constraints = phys_asset.get_editor_property('constraint_setups')

    body_info = []
    for body in bodies:
        bone_name = str(body.get_editor_property('bone_name'))
        body_info.append(bone_name)

    info = {
        'name': phys_asset.get_name(),
        'num_bodies': len(bodies),
        'num_constraints': len(constraints),
        'bones': body_info
    }

    print(json.dumps(info, indent=2))
```

### SkeletalMesh에 Physics Asset 할당

```python
import unreal

skel_mesh = unreal.load_asset('/Game/Characters/SK_Character')
phys_asset = unreal.load_asset('/Game/Characters/PA_Character')

if skel_mesh and phys_asset:
    skel_mesh.set_editor_property('physics_asset', phys_asset)
    unreal.EditorAssetLibrary.save_asset('/Game/Characters/SK_Character')
    print('Physics Asset assigned')
```

### 여러 캐릭터에 Physics Asset 일괄 할당

```python
import unreal

assignments = {
    '/Game/Characters/Warrior/SK_Warrior': '/Game/Characters/Warrior/PA_Warrior',
    '/Game/Characters/Mage/SK_Mage': '/Game/Characters/Mage/PA_Mage',
    '/Game/Characters/Archer/SK_Archer': '/Game/Characters/Archer/PA_Archer',
}

count = 0
for mesh_path, phys_path in assignments.items():
    mesh = unreal.load_asset(mesh_path)
    phys = unreal.load_asset(phys_path)

    if mesh and phys:
        mesh.set_editor_property('physics_asset', phys)
        unreal.EditorAssetLibrary.save_asset(mesh_path, only_if_is_dirty=True)
        count += 1
        print(f'Assigned: {mesh_path}')
    else:
        print(f'Failed: {mesh_path} or {phys_path} not found')

print(f'Total assigned: {count}')
```

---

## Cloth 시뮬레이션

> **현재 한계**: Cloth 시뮬레이션 (Chaos Cloth)의 Python API는 매우 제한적입니다. 에셋 생성과 설정은 에디터 UI에서 하는 것이 현실적입니다.

할 수 있는 것:

```python
import unreal
import json

registry = unreal.AssetRegistryHelpers.get_asset_registry()
ar_filter = unreal.ARFilter(
    class_names=['ClothingAssetCommon'],
    package_paths=['/Game/'],
    recursive_paths=True
)
assets = registry.get_assets(ar_filter)

result = []
for ad in assets:
    result.append({
        'name': str(ad.asset_name),
        'path': str(ad.package_name)
    })

print(json.dumps(result, indent=2))
```

Cloth 시뮬레이션 에셋의 세부 설정이 필요하면 **ChiR24/Unreal_mcp** (Chaos Cloth 지원)을 추천합니다.

## Claude에게 이렇게 요청하세요

```
"프로젝트의 모든 IK Rig 에셋을 찾아줘"

"SK_Character에 PA_Character Physics Asset을 할당해줘"

"RTG_MixamoToMannequin 리타게터의 체인 설정을 보여줘"

"Mixamo/Animations 폴더에 리타게팅 대상 애니메이션이 몇 개인지 알려줘"
```

## 다음 단계

[09. 실전 자동화 레시피](09-Automation-Recipes.md)로 이동하세요.
