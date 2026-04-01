# 05. 기본 도구 사용법

> runreal이 제공하는 19개 MCP 도구를 카테고리별로 정리합니다.

## 도구 전체 목록

### 경로 설정 (4개)

| 도구 | 설명 | 사용 예시 |
|------|------|----------|
| `set_unreal_engine_path` | UE 엔진 경로 설정 | `C:/Program Files/Epic Games/UE_5.7` |
| `get_unreal_engine_path` | 현재 엔진 경로 조회 | - |
| `set_unreal_project_path` | 프로젝트 경로 설정 | `C:/Projects/MyGame` |
| `get_unreal_project_path` | 현재 프로젝트 경로 조회 | - |

**사용 시점**: 처음 연결할 때 한 번 설정하면 됩니다. AI에게 "프로젝트 경로 설정해줘"라고 하면 됩니다.

---

### 에셋 관리 (6개)

#### `editor_list_assets`
- `/Game` 폴더 하위의 모든 에셋 목록 반환
- 파라미터 없음

```
프롬프트: "프로젝트의 모든 에셋을 보여줘"
```

#### `editor_search_assets`
- 이름이나 경로로 에셋 검색 (최대 50개)
- 파라미터: `search_term` (필수), `asset_class` (선택)

```
프롬프트: "Walk이라는 이름의 AnimSequence를 찾아줘"
→ search_term: "Walk", asset_class: "AnimSequence"
```

#### `editor_get_asset_info`
- 특정 에셋의 상세 정보 (LOD 포함)
- 파라미터: `asset_path`

```
프롬프트: "/Game/Characters/SK_Mannequin 에셋 정보 알려줘"
```

#### `editor_get_asset_references`
- 에셋이 참조하는/참조받는 관계 조회
- 파라미터: `asset_path`

```
프롬프트: "이 머티리얼을 어디서 사용하고 있는지 알려줘"
```

#### `editor_export_asset`
- 에셋을 텍스트/바이너리로 내보내기
- 파라미터: `asset_path`

#### `editor_validate_assets`
- 에셋 유효성 검증 (최대 100개)
- 파라미터: `asset_paths` (선택, 없으면 전체)

```
프롬프트: "애니메이션 폴더의 에셋을 검증해줘"
```

---

### 프로젝트/맵 정보 (3개)

#### `editor_project_info`
- 프로젝트 상세 정보 반환
- 반환: 프로젝트 이름, 엔진 버전, 총 에셋 수, 입력 액션, 게임 모드 등

```
프롬프트: "현재 프로젝트 정보를 알려줘"
```

#### `editor_get_map_info`
- 현재 열린 맵의 정보
- 반환: 액터 수, 라이팅 정보, 스트리밍 레벨

```
프롬프트: "현재 맵에 대해 알려줘"
```

#### `editor_get_world_outliner`
- 월드 아웃라이너의 모든 액터 목록
- 반환: 이름, 위치, 회전, 스케일, 컴포넌트 목록

```
프롬프트: "레벨의 모든 액터를 나열해줘"
```

---

### 오브젝트 생성/수정/삭제 (3개)

#### `editor_create_object`
월드에 새 액터 생성

| 파라미터 | 필수 | 설명 |
|---------|:----:|------|
| `object_class` | O | 액터 클래스 |
| `object_name` | O | 이름 |
| `location` | X | {x, y, z} |
| `rotation` | X | {pitch, yaw, roll} |
| `scale` | X | {x, y, z} |
| `properties` | X | 추가 속성 |

**지원 클래스**:
- `StaticMeshActor` - 스태틱 메시 (이름에 sphere/cylinder/cone/plane 포함 시 자동 매핑)
- `SkeletalMeshActor` - 스켈레탈 메시
- `DirectionalLight`, `PointLight`, `SpotLight` - 라이트
- `Camera` / `CameraActor` - 카메라
- `Pawn`, `Character`, `PlayerStart`
- Blueprint 클래스 경로도 지원 (예: `/Game/Blueprints/BP_Enemy.BP_Enemy_C`)

```
프롬프트: "레벨 중앙에 PointLight를 하나 만들어줘"
프롬프트: "좌표 (100, 200, 0)에 큐브를 놓아줘"
```

#### `editor_update_object`
기존 액터 수정

| 파라미터 | 필수 | 설명 |
|---------|:----:|------|
| `actor_name` | O | 수정할 액터 이름 |
| `location` | X | 새 위치 |
| `rotation` | X | 새 회전 |
| `scale` | X | 새 스케일 |
| `properties` | X | 속성 변경 |
| `new_name` | X | 이름 변경 |

```
프롬프트: "MyCube를 위치 (0, 0, 500)으로 옮기고 스케일을 2배로 키워줘"
```

#### `editor_delete_object`
액터 삭제 (단일/다중)

| 파라미터 | 필수 | 설명 |
|---------|:----:|------|
| `actor_names` | O | 삭제할 액터 이름 (콤마 구분 가능) |

```
프롬프트: "TempCube와 TempSphere를 삭제해줘"
```

---

### 카메라/비주얼 (2개)

#### `editor_take_screenshot`
- 에디터 뷰포트 스크린샷 촬영
- 640x520 PNG, base64로 반환
- **주의**: UE 에디터 윈도우가 포커스 상태여야 함

```
프롬프트: "현재 뷰포트를 스크린샷 찍어줘"
```

#### `editor_move_camera`
- 뷰포트 카메라 이동

| 파라미터 | 필수 | 설명 |
|---------|:----:|------|
| `location` | O | {x, y, z} |
| `rotation` | O | {pitch, yaw, roll} |

```
프롬프트: "카메라를 위에서 아래로 내려다보는 뷰로 옮겨줘"
```

---

### Python 실행 (1개) - 가장 강력한 도구!

#### `editor_run_python`
UE 에디터 내에서 **임의의 Python 코드**를 실행

| 파라미터 | 필수 | 설명 |
|---------|:----:|------|
| `code` | O | Python 코드 문자열 |

**규칙**:
- 반드시 `import unreal`을 포함해야 함
- **주석 사용 금지** (Remote Execution 프로토콜 제한)
- 결과는 `print()`로 출력

```
프롬프트: "모든 StaticMeshActor를 50유닛 위로 올려줘"
→ AI가 Python 코드를 생성하여 editor_run_python으로 실행
```

이 도구 하나로 UE Python API의 모든 기능에 접근할 수 있습니다. 자세한 활용법은 [06. Python 스크립팅 기초](06-Python-Scripting-Basics.md)를 참고하세요.

---

### 콘솔 명령 (1개)

#### `editor_console_command`
- UE 콘솔 명령 실행
- 파라미터: `command`

```
프롬프트: "stat fps 콘솔 명령을 실행해줘"
프롬프트: "가비지 콜렉션을 실행해줘" → obj gc
```

---

### MCP 리소스 (1개)

| 리소스 | URI | 설명 |
|--------|-----|------|
| `docs` | `docs://unreal_python` | UE Python API 문서 링크 |

## 다음 단계

기본 도구를 익혔으면 [06. Python 스크립팅 기초](06-Python-Scripting-Basics.md)로 이동하세요.
