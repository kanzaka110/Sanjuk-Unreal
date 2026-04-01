# 07. 애니메이션 워크플로우

> `editor_run_python`을 사용하여 애니메이션 에셋을 생성하고 관리하는 방법

## AnimSequence 작업

### 애니메이션 정보 조회

```python
import unreal
import json

anim = unreal.load_asset('/Game/Animations/Walk_Fwd')
if anim:
    info = {
        'name': anim.get_name(),
        'length_sec': anim.get_play_length(),
        'num_frames': anim.number_of_frames,
        'frame_rate': str(anim.get_sampling_frame_rate()),
        'has_root_motion': anim.get_editor_property('enable_root_motion'),
        'rate_scale': anim.get_editor_property('rate_scale'),
        'skeleton': anim.get_skeleton().get_name() if anim.get_skeleton() else 'None'
    }
    print(json.dumps(info, indent=2))
```

### 애니메이션 속성 수정

```python
import unreal

anim = unreal.load_asset('/Game/Animations/Walk_Fwd')

anim.set_editor_property('rate_scale', 1.5)
anim.set_editor_property('enable_root_motion', True)
anim.set_editor_property('force_root_lock', False)
anim.set_editor_property('loop', True)

unreal.EditorAssetLibrary.save_asset('/Game/Animations/Walk_Fwd')
print('Animation properties updated')
```

### 프로젝트 전체 애니메이션 스캔

```python
import unreal
import json

registry = unreal.AssetRegistryHelpers.get_asset_registry()
ar_filter = unreal.ARFilter(
    class_names=['AnimSequence'],
    package_paths=['/Game/'],
    recursive_paths=True
)
assets = registry.get_assets(ar_filter)

result = []
for ad in assets:
    anim = unreal.load_asset(str(ad.package_name))
    if anim:
        result.append({
            'name': str(ad.asset_name),
            'path': str(ad.package_name),
            'length': anim.get_play_length(),
            'frames': anim.number_of_frames,
            'root_motion': anim.get_editor_property('enable_root_motion')
        })

print(json.dumps(result, indent=2))
```

---

## AnimMontage 작업

### 몽타주 생성

```python
import unreal

factory = unreal.AnimMontageFactory()
skeleton = unreal.load_asset('/Game/Characters/SK_Mannequin_Skeleton')
factory.set_editor_property('target_skeleton', skeleton)

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
montage = asset_tools.create_asset(
    'AM_Attack',
    '/Game/Animations/Montages',
    unreal.AnimMontage,
    factory
)

if montage:
    unreal.EditorAssetLibrary.save_asset('/Game/Animations/Montages/AM_Attack')
    print('Montage created: AM_Attack')
```

### 몽타주 정보 조회

```python
import unreal
import json

montage = unreal.load_asset('/Game/Animations/Montages/AM_Attack')
if montage:
    info = {
        'name': montage.get_name(),
        'length': montage.get_play_length(),
        'skeleton': montage.get_skeleton().get_name() if montage.get_skeleton() else 'None',
        'num_sections': len(montage.get_editor_property('composite_sections'))
    }
    print(json.dumps(info, indent=2))
```

---

## BlendSpace 작업

### 1D BlendSpace 생성

```python
import unreal

skeleton = unreal.load_asset('/Game/Characters/SK_Mannequin_Skeleton')

factory = unreal.BlendSpaceFactory1D()
factory.set_editor_property('target_skeleton', skeleton)

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
bs = asset_tools.create_asset(
    'BS_Speed',
    '/Game/Animations/BlendSpaces',
    unreal.BlendSpace1D,
    factory
)

if bs:
    unreal.EditorAssetLibrary.save_asset('/Game/Animations/BlendSpaces/BS_Speed')
    print('1D BlendSpace created: BS_Speed')
```

### 2D BlendSpace 생성

```python
import unreal

skeleton = unreal.load_asset('/Game/Characters/SK_Mannequin_Skeleton')

factory = unreal.BlendSpaceFactory()
factory.set_editor_property('target_skeleton', skeleton)

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
bs = asset_tools.create_asset(
    'BS_Locomotion2D',
    '/Game/Animations/BlendSpaces',
    unreal.BlendSpace,
    factory
)

if bs:
    unreal.EditorAssetLibrary.save_asset('/Game/Animations/BlendSpaces/BS_Locomotion2D')
    print('2D BlendSpace created: BS_Locomotion2D')
```

---

## AnimBlueprint 작업

### ABP 생성

```python
import unreal

skeleton = unreal.load_asset('/Game/Characters/SK_Mannequin_Skeleton')

factory = unreal.AnimBlueprintFactory()
factory.set_editor_property('target_skeleton', skeleton)

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
abp = asset_tools.create_asset(
    'ABP_Character',
    '/Game/Characters/Animations',
    unreal.AnimBlueprint,
    factory
)

if abp:
    unreal.EditorAssetLibrary.save_asset('/Game/Characters/Animations/ABP_Character')
    print('AnimBlueprint created: ABP_Character')
```

### ABP 정보 조회

```python
import unreal
import json

abp = unreal.load_asset('/Game/Characters/Animations/ABP_Character')
if abp:
    info = {
        'name': abp.get_name(),
        'skeleton': str(abp.get_editor_property('target_skeleton')),
        'preview_mesh': str(abp.get_editor_property('preview_skeletal_mesh'))
    }
    print(json.dumps(info, indent=2))
```

> **한계**: AnimBlueprint의 **내부 그래프 노드** (State Machine, Transition 등)를 Python으로 직접 편집하는 것은 UE Python API의 한계로 **불가능**합니다. 그래프 편집이 필요하면 **Monolith MCP**를 사용하세요.

---

## Skeleton 작업

### 스켈레톤 본 목록 조회

```python
import unreal
import json

skel_mesh = unreal.load_asset('/Game/Characters/SK_Mannequin')
if skel_mesh:
    skeleton = skel_mesh.get_editor_property('skeleton')
    ref_skeleton = skeleton.get_editor_property('reference_skeleton') if skeleton else None

    if ref_skeleton:
        num_bones = ref_skeleton.get_num()
        bones = []
        for i in range(num_bones):
            bones.append(ref_skeleton.get_bone_name(i))
        print(json.dumps({'num_bones': num_bones, 'bones': [str(b) for b in bones]}, indent=2))
```

---

## 에셋 배치 작업 예시

### 모든 애니메이션 루프 설정 일괄 변경

```python
import unreal

registry = unreal.AssetRegistryHelpers.get_asset_registry()
ar_filter = unreal.ARFilter(
    class_names=['AnimSequence'],
    package_paths=['/Game/Animations/Locomotion'],
    recursive_paths=True
)
assets = registry.get_assets(ar_filter)

count = 0
for ad in assets:
    anim = unreal.load_asset(str(ad.package_name))
    if anim:
        anim.set_editor_property('loop', True)
        unreal.EditorAssetLibrary.save_asset(str(ad.package_name), only_if_is_dirty=True)
        count += 1

print(f'Updated {count} animations to loop=True')
```

### 애니메이션 Rate Scale 일괄 조정

```python
import unreal

registry = unreal.AssetRegistryHelpers.get_asset_registry()
ar_filter = unreal.ARFilter(
    class_names=['AnimSequence'],
    package_paths=['/Game/Animations'],
    recursive_paths=True
)
assets = registry.get_assets(ar_filter)

count = 0
for ad in assets:
    anim = unreal.load_asset(str(ad.package_name))
    if anim and anim.get_editor_property('rate_scale') != 1.0:
        print(f'{ad.asset_name}: rate_scale = {anim.get_editor_property("rate_scale")}')
        count += 1

print(f'Found {count} animations with non-default rate_scale')
```

## Claude에게 이렇게 요청하세요

```
"프로젝트의 모든 AnimSequence를 검색해서 루프 설정이 꺼져있는 것만 알려줘"

"Walk_Fwd 애니메이션의 재생 속도를 1.2배로 변경해줘"

"새 AnimMontage를 만들어줘. 이름은 AM_Dodge, 스켈레톤은 SK_Mannequin"

"Locomotion 폴더의 모든 애니메이션에 루트 모션을 활성화해줘"
```

## 다음 단계

[08. Control Rig & Physics](08-ControlRig-Physics.md)로 이동하세요.
