# 12. 참고자료

## 공식 문서

### runreal
| 리소스 | URL |
|--------|-----|
| GitHub | https://github.com/runreal/unreal-mcp |
| npm | https://www.npmjs.com/package/@runreal/unreal-mcp |
| Discord | https://discord.gg/6ZhWVU5W47 |
| Twitter/X | https://x.com/runreal_dev |

### Unreal Engine Python API
| 리소스 | URL |
|--------|-----|
| Python API 레퍼런스 (5.7) | https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api |
| Python 스크립팅 가이드 | https://dev.epicgames.com/documentation/en-us/unreal-engine/scripting-the-unreal-editor-using-python |
| Control Rig Python | https://dev.epicgames.com/documentation/en-us/unreal-engine/python-scripting-for-animating-with-control-rig-in-unreal-engine |
| IK Retargeter Python (5.2+) | https://docs.unrealengine.com/5.2/en-US/using-python-to-create-and-edit-ik-retargeter-assets-in-unreal-engine/ |
| AnimSequence API | https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/AnimSequence |

### UAF (Unreal Animation Framework)
| 리소스 | URL |
|--------|-----|
| UAF FAQ (공식) | https://dev.epicgames.com/community/learning/knowledge-base/nWWx/unreal-engine-unreal-animation-framework-uaf-faq |
| UAF API (5.7) | https://dev.epicgames.com/documentation/en-us/unreal-engine/API/PluginIndex/UAF |
| UAF + Mover 2.0 가이드 | https://farravid.github.io/posts/How-to-setup-Mover-2.0-+-Unreal-Animation-Framework-(UAF)-+-Motion-Matching-in-5.7/ |
| UAF 탐구 포럼 | https://forums.unrealengine.com/t/uaf-anim-next-explorations/2649236 |
| GASP UE 5.7 블로그 | https://www.unrealengine.com/en-US/tech-blog/explore-the-updates-to-the-game-animation-sample-project-in-ue-5-7 |

---

## 관련 MCP 프로젝트

| 프로젝트 | GitHub | 특징 |
|---------|--------|------|
| **Monolith** | https://github.com/tumourlove/monolith | 815 액션, 애니메이션 최강, C++ 네이티브 |
| **chongdashu** | https://github.com/chongdashu/unreal-mcp | 1,673 stars, 가장 인기 |
| **flopperam** | https://github.com/flopperam/unreal-engine-mcp | 716 stars, 다기능 |
| **ChiR24** | https://github.com/ChiR24/Unreal_mcp | 435 stars, Cloth 지원 |
| **kvick-games** | https://github.com/kvick-games/UnrealMCP | 553 stars |
| **VibeUE** | https://www.vibeue.com/ | 에디터 내 AI Chat |
| **ClaudusBridge** | Fab 마켓플레이스 | 483+ 도구, 유료 |
| **StraySpark** | https://www.strayspark.studio/ | 305 도구, UE+Blender+Godot |
| **UnrealClaude** | https://github.com/Natfii/UnrealClaude | Claude Code CLI + UE5.7 문서 |

---

## UE5 Python API 주요 클래스 레퍼런스

### 에셋 관리

| 클래스 | 주요 메서드 |
|--------|-----------|
| `EditorAssetLibrary` | `list_assets()`, `load_asset()`, `save_asset()`, `rename_asset()`, `delete_asset()`, `duplicate_asset()` |
| `AssetToolsHelpers` | `.get_asset_tools()` -> `create_asset()`, `import_asset_tasks()` |
| `AssetRegistryHelpers` | `.get_asset_registry()` -> `get_assets()`, `get_referencers()` |

### 액터/월드

| 클래스 | 주요 메서드 |
|--------|-----------|
| `EditorActorSubsystem` | `spawn_actor_from_class()`, `get_all_level_actors()`, `get_selected_level_actors()`, `destroy_actor()` |
| `EditorLevelLibrary` | `get_editor_world()`, `spawn_actor_from_class()` |
| `GameplayStatics` | `get_all_actors_of_class()` |

### 머티리얼

| 클래스 | 주요 메서드 |
|--------|-----------|
| `MaterialEditingLibrary` | `set_material_instance_scalar_parameter_value()`, `set_material_instance_vector_parameter_value()`, `set_material_instance_texture_parameter_value()`, `create_material_expression()`, `connect_material_expressions()` |

### 애니메이션

| 클래스 | 주요 속성/메서드 |
|--------|----------------|
| `AnimSequence` | `get_play_length()`, `number_of_frames`, `get_sampling_frame_rate()`, `get_skeleton()`, `enable_root_motion`, `rate_scale`, `loop` |
| `AnimMontage` | `get_play_length()`, `composite_sections` |
| `BlendSpace` / `BlendSpace1D` | `add_sample()` |
| `AnimBlueprint` | `target_skeleton`, `preview_skeletal_mesh` |
| `IKRetargeterController` | `set_ik_rig()`, `get_all_chain_settings()` |

### 팩토리 (에셋 생성용)

| 팩토리 | 생성 대상 |
|--------|----------|
| `MaterialFactoryNew` | Material |
| `MaterialInstanceConstantFactoryNew` | MaterialInstanceConstant |
| `AnimBlueprintFactory` | AnimBlueprint |
| `AnimMontageFactory` | AnimMontage |
| `BlendSpaceFactory` | BlendSpace (2D) |
| `BlendSpaceFactory1D` | BlendSpace1D |

---

## Remote Execution 프로토콜 상세

| 항목 | 값 |
|------|------|
| 디스커버리 | UDP Multicast `239.0.0.1:6766` |
| 명령 실행 | TCP `127.0.0.1:6776` |
| 메시지 형식 | JSON (`magic: "ue_python"`) |
| 실행 모드 | `ExecuteFile` (다중 줄) / `EvaluateStatement` (단일 식) |
| 최대 재시도 | 3회 (2초 → 3초 → 4.5초 지수 백오프) |
| 스크린샷 해상도 | 640x520 (고정) |

---

## 이 튜토리얼 시리즈

| 파일 | 내용 |
|------|------|
| [README.md](README.md) | 목차 및 개요 |
| [01-What-Is-runreal.md](01-What-Is-runreal.md) | 개요, 아키텍처, 비교 |
| [02-Installation.md](02-Installation.md) | 설치 가이드 |
| [03-UE5-Editor-Setup.md](03-UE5-Editor-Setup.md) | UE5 에디터 설정 |
| [04-Connect-Claude-Code.md](04-Connect-Claude-Code.md) | Claude Code 연결 |
| [05-Basic-Tools.md](05-Basic-Tools.md) | 19개 도구 완전 가이드 |
| [06-Python-Scripting-Basics.md](06-Python-Scripting-Basics.md) | Python 스크립팅 기초 |
| [07-Animation-Workflow.md](07-Animation-Workflow.md) | 애니메이션 워크플로우 |
| [08-ControlRig-Physics.md](08-ControlRig-Physics.md) | Control Rig & Physics |
| [09-Automation-Recipes.md](09-Automation-Recipes.md) | 실전 자동화 레시피 |
| [10-With-Monolith.md](10-With-Monolith.md) | Monolith 동시 사용 |
| [11-Troubleshooting.md](11-Troubleshooting.md) | 트러블슈팅 |
| [12-References.md](12-References.md) | 참고자료 (이 파일) |
