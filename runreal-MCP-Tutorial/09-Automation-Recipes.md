# 09. 실전 자동화 레시피

> 실무에서 바로 쓸 수 있는 Python 자동화 스크립트 모음

## 레시피 1: 에셋 배치 이름변경

Mixamo에서 가져온 애니메이션의 프리픽스를 일괄 변경:

```python
import unreal

editor_util = unreal.EditorAssetLibrary
registry = unreal.AssetRegistryHelpers.get_asset_registry()

target_path = '/Game/Animations/'
all_assets = editor_util.list_assets(target_path, recursive=True)

rename_rules = {
    'mixamo_': 'AS_',
    'Anim_': 'AS_',
    'anim_': 'AS_',
    'Montage_': 'AM_',
}

renamed = 0
for asset_path in all_assets:
    asset_data = registry.get_asset_by_object_path(asset_path)
    name = str(asset_data.asset_name)
    new_name = name

    for old_prefix, new_prefix in rename_rules.items():
        if new_name.startswith(old_prefix):
            new_name = new_prefix + new_name[len(old_prefix):]
            break

    if new_name != name:
        old_full = str(asset_path)
        new_full = old_full.rsplit('/', 1)[0] + '/' + new_name
        success = editor_util.rename_asset(old_full, new_full)
        if success:
            renamed += 1
            print(f'{name} -> {new_name}')

print(f'Renamed: {renamed} assets')
```

---

## 레시피 2: 프로젝트 애니메이션 보고서

프로젝트의 모든 애니메이션 관련 에셋 현황을 한눈에:

```python
import unreal
import json

editor_util = unreal.EditorAssetLibrary
registry = unreal.AssetRegistryHelpers.get_asset_registry()
all_assets = editor_util.list_assets('/Game/', recursive=True)

categories = {
    'AnimSequence': 0,
    'AnimMontage': 0,
    'BlendSpace': 0,
    'BlendSpace1D': 0,
    'AnimBlueprint': 0,
    'Skeleton': 0,
    'SkeletalMesh': 0,
    'PhysicsAsset': 0,
    'IKRigDefinition': 0,
    'IKRetargeter': 0,
    'ControlRigBlueprint': 0,
    'Material': 0,
    'MaterialInstanceConstant': 0,
    'StaticMesh': 0,
}

for asset_path in all_assets:
    asset_data = registry.get_asset_by_object_path(asset_path)
    class_name = str(asset_data.asset_class_path.asset_name)
    if class_name in categories:
        categories[class_name] += 1

report = {
    'total_assets': len(all_assets),
    'by_type': categories
}

print(json.dumps(report, indent=2))
```

---

## 레시피 3: 머티리얼 인스턴스 배치 생성

마스터 머티리얼에서 색상 변형을 자동 생성:

```python
import unreal

master_mat = unreal.load_asset('/Game/Materials/M_Character_Master')
if not master_mat:
    print('Master material not found')
else:
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

    variants = {
        'MI_Char_Red':    unreal.LinearColor(1.0, 0.0, 0.0, 1.0),
        'MI_Char_Blue':   unreal.LinearColor(0.0, 0.0, 1.0, 1.0),
        'MI_Char_Green':  unreal.LinearColor(0.0, 1.0, 0.0, 1.0),
        'MI_Char_Gold':   unreal.LinearColor(1.0, 0.84, 0.0, 1.0),
        'MI_Char_Purple': unreal.LinearColor(0.5, 0.0, 0.5, 1.0),
    }

    for name, color in variants.items():
        factory = unreal.MaterialInstanceConstantFactoryNew()
        factory.set_editor_property('initial_parent', master_mat)

        mi = asset_tools.create_asset(
            name,
            '/Game/Materials/Characters',
            unreal.MaterialInstanceConstant,
            factory
        )

        if mi:
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
                mi, 'BaseColor', color
            )
            unreal.EditorAssetLibrary.save_asset(f'/Game/Materials/Characters/{name}')
            print(f'Created: {name}')

    print(f'Done: {len(variants)} material instances created')
```

---

## 레시피 4: 미사용 에셋 찾기

참조가 없는 에셋을 찾아 정리 후보 목록 생성:

```python
import unreal
import json

editor_util = unreal.EditorAssetLibrary
registry = unreal.AssetRegistryHelpers.get_asset_registry()

search_path = '/Game/Materials/'
all_assets = editor_util.list_assets(search_path, recursive=True)

unreferenced = []
for asset_path in all_assets[:100]:
    deps = registry.get_referencers(unreal.Name(str(asset_path)))
    if len(deps) == 0:
        asset_data = registry.get_asset_by_object_path(asset_path)
        unreferenced.append({
            'name': str(asset_data.asset_name),
            'path': str(asset_path),
            'class': str(asset_data.asset_class_path.asset_name)
        })

print(json.dumps({'unreferenced_count': len(unreferenced), 'assets': unreferenced}, indent=2))
```

---

## 레시피 5: 레벨 액터 정리

특정 태그나 패턴의 액터를 일괄 삭제:

```python
import unreal

subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
all_actors = subsystem.get_all_level_actors()

prefix = 'Temp_'
to_delete = []
for actor in all_actors:
    label = actor.get_actor_label()
    if label.startswith(prefix):
        to_delete.append(actor)

for actor in to_delete:
    label = actor.get_actor_label()
    subsystem.destroy_actor(actor)
    print(f'Deleted: {label}')

print(f'Total deleted: {len(to_delete)}')
```

---

## 레시피 6: SkeletalMesh 정보 일괄 조회

모든 캐릭터 메시의 LOD, 본 수, 머티리얼 정보:

```python
import unreal
import json

registry = unreal.AssetRegistryHelpers.get_asset_registry()
ar_filter = unreal.ARFilter(
    class_names=['SkeletalMesh'],
    package_paths=['/Game/Characters'],
    recursive_paths=True
)
assets = registry.get_assets(ar_filter)

result = []
for ad in assets:
    mesh = unreal.load_asset(str(ad.package_name))
    if mesh:
        lod_info = mesh.get_editor_property('lod_info')
        materials = mesh.get_editor_property('materials')
        phys = mesh.get_editor_property('physics_asset')

        result.append({
            'name': str(ad.asset_name),
            'lod_count': len(lod_info),
            'material_count': len(materials),
            'has_physics_asset': phys is not None,
            'physics_asset': phys.get_name() if phys else 'None'
        })

print(json.dumps(result, indent=2))
```

---

## 레시피 7: FBX 배치 임포트

폴더의 모든 FBX를 자동 임포트:

```python
import unreal
import os

source_folder = 'C:/Export/Animations'
dest_path = '/Game/Imported/Animations'
skeleton_path = '/Game/Characters/SK_Mannequin_Skeleton'

skeleton = unreal.load_asset(skeleton_path)
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

fbx_files = [f for f in os.listdir(source_folder) if f.endswith('.fbx')]
imported = 0

for fbx_file in fbx_files:
    full_path = os.path.join(source_folder, fbx_file).replace('\\', '/')

    task = unreal.AssetImportTask()
    task.set_editor_property('filename', full_path)
    task.set_editor_property('destination_path', dest_path)
    task.set_editor_property('automated', True)
    task.set_editor_property('save', True)
    task.set_editor_property('replace_existing', False)

    fbx_options = unreal.FbxImportUI()
    fbx_options.set_editor_property('import_mesh', False)
    fbx_options.set_editor_property('import_animations', True)
    fbx_options.set_editor_property('skeleton', skeleton)
    fbx_options.anim_sequence_import_data.set_editor_property('import_bone_tracks', True)

    task.set_editor_property('options', fbx_options)
    asset_tools.import_asset_tasks([task])
    imported += 1
    print(f'Imported: {fbx_file}')

print(f'Total imported: {imported}/{len(fbx_files)}')
```

## Claude에게 이렇게 요청하세요

```
"Animations 폴더의 모든 에셋 이름에서 mixamo_ 프리픽스를 AS_로 바꿔줘"

"프로젝트의 애니메이션 에셋 현황 보고서를 만들어줘"

"M_Character_Master를 부모로 하는 빨강/파랑/녹색 머티리얼 인스턴스를 만들어줘"

"C:/Export/Animations 폴더의 FBX 파일들을 전부 임포트해줘"
```

## 다음 단계

[10. Monolith와 함께 쓰기](10-With-Monolith.md)로 이동하세요.
