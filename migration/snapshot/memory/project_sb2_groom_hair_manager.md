---
name: SB2 사내 Groom Hair Manager 툴 구조
description: shiftup.MOD가 가리키는 사내 Maya 그룸 export 툴의 구성과 부여 어트리뷰트, UE 스키마와의 차이점
type: project
originSessionId: ebb9a6d8-e675-4b83-840f-614d45867951
---
SB2 사내 NAS Maya 툴 모듈 (TA 장석호) — XGen Interactive Groom Description을 UE5 Groom Asset 임포트용 Alembic으로 정리·export.

**Why:** PC_01/NPC 헤어 모든 abc는 이 툴이 찍어낸 결과물. UE Groom Asset에 들어 있는 group_id / root_uv / 가이드 커브의 출처를 추적할 때 이 툴 산출 어트리뷰트 명세가 ground truth.

**How to apply:** SB2 헤어 abc/Groom Asset의 어트리뷰트가 의심스러우면 이 메모를 먼저 본다. dump_groom_metadata 결과의 alembic_attrs 컬럼은 이 툴이 부여하는 어트리뷰트 명과 1:1 매칭되어야 한다.

## 경로

| 항목 | 위치 |
|---|---|
| 모듈 등록 | `C:\Users\SHIFTUP\Documents\maya\2023\modules\shiftup.MOD` |
| 본체 | `\\10.220.70.11\eve\ART_Backup\EVE_ANI_FACE\SB2_Facial_Project\scripts\maya_script\shiftupTool\script\sfupTools\Groom_Hair_Manager\` |
| 진입점 | Maya 메뉴 SHIFTUP → Character Settings → Groom Hair Manager |
| 버전 | 1.0.1 (2025-12-16, Split Spline 추가) |
| 백업 | `_backup/2025-12-16/` (2025-08-28자), `_backup/main - 복사본.py` (2024-09-09) |

## UI Component Table 컬럼

`table_id (hidden) | group_id | new_desc_name | desc_sources | count | guide_sources | count | del`

각 row가 하나의 그룹. `desc_sources`는 XGen Description (Width/WidthTaper/WidthTaperStart 어트리뷰트로 식별), `guide_sources`는 가이드 커브 그룹.

## Export 파이프라인 (utils.prepare_export)

1. `duplicate_raw_sources` → `Temp_export_group_<UUID8>` 안에 desc/guide 복제
2. `create_groups` → `{desc}_SplineGrp_{gid}`, `{desc}_GuideCrv_{gid}` 빈 transform
3. `parent_all_curves` → guide는 shape relative reparent (월드 보존)
4. `rename_desc_and_move_spline_groups` → 사용자 desc 이름 적용 후 SplineGrp을 desc 하위로
5. **Set Attributes** (핵심)
6. `AbcExport -worldSpace -dataFormat ogawa -attr groom_root_uv -attr groom_group_id -attr groom_guide -uvWrite -root <temp> -file <path>`

## 부여 어트리뷰트 (UE 스키마 비교)

### Spline Group (Description per group)
- `groom_group_id` (short)
- `riCurves` (bool=1)
- `groom_guide_AbcGeomScope` (string='con')
- `groom_root_uv` (vectorArray of (u,v,0)) + `_AbcGeomScope`='uni' + `_AbcType`='vector2'

### Curve Guide
- `groom_group_id` (short)
- **`groom_guide` (short=1)** — ⚠ 단수형. Epic 공식 문서는 `groom_guides`(복수). 인식 여부 미검증.
- `riCurves` (bool=1)
- `groom_guide_AbcGeomScope` (string='con')

## groom_root_uv 산정 방식

각 nurbsCurve shape의 `cv[0]` world position → `MFnMesh.getUVAtPoint(MSpace.kWorld, uv_set)`로 closest UV → `(u, v, 0)` 벡터. AbcType='vector2'로 마킹해 z=0 무시.

## Edit 메뉴 두 유틸

- **Split Spline in Description Group** — multi-shape transform을 shape별 transform으로 분리. batch_size=50, world matrix 보존. (그룹 ID 매핑 깨짐 방지)
- **Auto Rebuild Long Name Curves** — `spans+degree>255`인 커브를 target_spans(기본 32)로 rebuildCurve. UE Groom 임포터의 CV 한계 워크어라운드.

## 잠재 이슈 / 의심 포인트

- **`groom_guide` vs `groom_guides`** 단수/복수 차이. UE Groom 임포터 소스(`Engine/Plugins/Runtime/HairStrands/Source/HairStrandsCore/Private/GroomBuilder.cpp` 등)에서 어느 쪽을 인식하는지 미확인. PC_01 Sanjuk 5그룹 헤어 시뮬 거동 이상의 후보 원인 중 하나로 후속 검증 가치 있음.
- 가이드가 인식 안 되면 abc 안에 guide curve가 있어도 UE Groom Asset이 시뮬 가이드 0개로 잡힘.
