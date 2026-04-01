# 06. Python 스크립팅 기초

> `editor_run_python`은 runreal의 가장 강력한 도구입니다. UE5의 전체 Python API에 접근할 수 있습니다.

## 핵심 규칙

1. **반드시 `import unreal`로 시작**
2. **주석 금지** - `#`이나 `"""` 주석을 넣으면 에러 발생
3. **결과는 `print()`로 출력** - stdout이 MCP 서버로 반환됨
4. **JSON으로 출력하면 AI가 파싱하기 좋음**

```python
import unreal
import json
result = {"engine_version": str(unreal.SystemLibrary.get_engine_version())}
print(json.dumps(result))
```

## 자주 쓰는 UE Python 모듈

| 모듈 | 용도 |
|------|------|
| `unreal.EditorAssetLibrary` | 에셋 로드/저장/삭제/이름변경/목록 |
| `unreal.AssetToolsHelpers.get_asset_tools()` | 에셋 생성/임포트 |
| `unreal.AssetRegistryHelpers.get_asset_registry()` | 에셋 검색/필터링 |
| `unreal.EditorActorSubsystem` | 액터 스폰/조회/삭제 |
| `unreal.EditorLevelLibrary` | 뷰포트 카메라, 월드 접근 |
| `unreal.MaterialEditingLibrary` | 머티리얼 노드/파라미터 편집 |
| `unreal.EditorLoadingAndSavingUtils` | 레벨 열기/저장 |
| `unreal.GameplayStatics` | 런타임 유틸리티 |

## 패턴 1: 에셋 목록 조회

```python
import unreal
import json

editor_util = unreal.EditorAssetLibrary
assets = editor_util.list_assets('/Game/Characters/', recursive=True, include_folder=False)

result = []
for path in assets:
    result.append(str(path))

print(json.dumps(result, indent=2))
```

## 패턴 2: 특정 클래스 에셋 검색

```python
import unreal
import json

registry = unreal.AssetRegistryHelpers.get_asset_registry()
ar_filter = unreal.ARFilter(
    class_names=['AnimSequence'],
    package_paths=['/Game/Animations'],
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

## 패턴 3: 에셋 로드 및 속성 조회

```python
import unreal
import json

anim = unreal.load_asset('/Game/Animations/Walk_Fwd')
if anim:
    info = {
        'name': anim.get_name(),
        'length': anim.get_play_length(),
        'num_frames': anim.number_of_frames,
        'frame_rate': str(anim.get_sampling_frame_rate()),
        'skeleton': str(anim.get_skeleton().get_name()) if anim.get_skeleton() else 'None'
    }
    print(json.dumps(info, indent=2))
else:
    print(json.dumps({'error': 'Asset not found'}))
```

## 패턴 4: 에셋 생성

```python
import unreal

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

new_mat = asset_tools.create_asset(
    asset_name='M_TestMaterial',
    package_path='/Game/Materials',
    asset_class=unreal.Material,
    factory=unreal.MaterialFactoryNew()
)

if new_mat:
    unreal.EditorAssetLibrary.save_asset('/Game/Materials/M_TestMaterial')
    print('Created: /Game/Materials/M_TestMaterial')
else:
    print('Failed to create material')
```

## 패턴 5: 액터 스폰

```python
import unreal

subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

actor = subsystem.spawn_actor_from_class(
    unreal.StaticMeshActor,
    unreal.Vector(0, 0, 100),
    unreal.Rotator(0, 0, 0)
)

mesh_comp = actor.static_mesh_component
mesh_comp.set_static_mesh(
    unreal.load_asset('/Engine/BasicShapes/Cube')
)

actor.set_actor_label('MyCube')
actor.set_actor_scale3d(unreal.Vector(2, 2, 2))

print(f'Spawned: {actor.get_actor_label()}')
```

## 패턴 6: 선택된 액터 작업

```python
import unreal
import json

subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
selected = subsystem.get_selected_level_actors()

result = []
for actor in selected:
    loc = actor.get_actor_location()
    result.append({
        'name': actor.get_actor_label(),
        'class': actor.get_class().get_name(),
        'location': {'x': loc.x, 'y': loc.y, 'z': loc.z}
    })

print(json.dumps(result, indent=2))
```

## 패턴 7: FBX 임포트

```python
import unreal

task = unreal.AssetImportTask()
task.set_editor_property('filename', 'C:/Models/character.fbx')
task.set_editor_property('destination_path', '/Game/Imported')
task.set_editor_property('automated', True)
task.set_editor_property('save', True)

fbx_options = unreal.FbxImportUI()
fbx_options.set_editor_property('import_mesh', True)
fbx_options.set_editor_property('import_animations', True)
fbx_options.set_editor_property('import_as_skeletal', True)

task.set_editor_property('options', fbx_options)

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
asset_tools.import_asset_tasks([task])

print('Import complete')
```

## 패턴 8: 진행률 표시 (대량 작업)

```python
import unreal

items = list(range(100))

with unreal.ScopedSlowTask(len(items), 'Processing...') as slow_task:
    slow_task.make_dialog(True)
    for i, item in enumerate(items):
        if slow_task.should_cancel():
            break
        slow_task.enter_progress_frame(1, f'Item {i+1}/{len(items)}')
        pass

print('Done')
```

## 에러 처리 패턴

```python
import unreal
import json

try:
    asset = unreal.load_asset('/Game/Some/Asset')
    if not asset:
        print(json.dumps({'success': False, 'error': 'Asset not found'}))
    else:
        print(json.dumps({'success': True, 'name': asset.get_name()}))
except Exception as e:
    print(json.dumps({'success': False, 'error': str(e)}))
```

## 다음 단계

기본 Python 패턴을 익혔으면 [07. 애니메이션 워크플로우](07-Animation-Workflow.md)로 이동하세요.
