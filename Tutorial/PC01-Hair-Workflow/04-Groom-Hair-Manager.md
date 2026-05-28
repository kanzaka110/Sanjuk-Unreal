# 04. Groom Hair Manager — Component Table + Alembic Export

사내 툴로 desc/guide/scalp_mesh를 한 번에 합쳐 `.abc`로 굽는다. Maya에서 UE로 넘어가는 마지막 Maya 단계.

> 출처: [Confluence — Groom Hair Manager](https://shiftupcorp.atlassian.net/wiki/spaces/SB2/pages/285638786/Groom+Hair+Manager) "사용 방법" 1·3절.

## 1. 툴 실행

`SHIFTUP > Character Settings > Groom Hair Manager` 클릭.

UI 구성:

```
┌────────────────────────────────────────────────────────────┐
│ Component Table                                            │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ id │group_id│ new_desc_name │ desc_sources │ count │   │
│ │    │        │               │ guide_sources│ count │del │
│ └──────────────────────────────────────────────────────┘   │
│ [Add New Component Set]  [Clear Table]                     │
│                                                            │
│ Scalp Mesh:    [____________]  [Set Mesh] [Clear Mesh]     │
│ Scalp UV:      [Dropdown ▼ ]   [Reload UV Set]             │
│                                                            │
│ [Table Validation]                                         │
│ [Export Groom Hair]                                        │
└────────────────────────────────────────────────────────────┘
```

## 2. Scalp Mesh 등록

### 2.1 등록

1. Outliner에서 `scalp_mesh` 선택 (캐릭터 두피 메시. 보통 머리 윗부분 슬라이스)
2. 툴 UI의 `Set Mesh` 클릭
3. `Scalp Mesh` 라벨에 메시 이름 표시 확인

⚠ scalp_mesh가 **frozen transform(0,0,0)** 상태여야 정확함. 회전/이동 적용된 상태에서 export하면 UV 계산은 정상이지만 binding 시 미세 오차 발생 가능.

### 2.2 UV Set 선택

`Reload UV Set` 클릭 → 드롭다운 갱신 → 사용할 UV Set 선택.

PC_01 케이스: `map1` (기본) 또는 `UV_Scalp` (전용) — TA에게 확인.

> 선택한 UV Set이 `groom_root_uv` 계산 기준. UE에서 Binding 시 동일 UV Set 사용해야 매칭됨.

## 3. Component Table 채우기

5그룹이면 5행 추가.

### 3.1 행 추가

`Add New Component Set` 클릭 5회 → 5행 생성.

### 3.2 각 행 입력

| 컬럼 | 입력 방법 | PC_01 예시 |
|---|---|---|
| group_id | 셀 더블클릭 → 정수 입력 | `0`, `1`, `2`, `3`, `4` |
| new_desc_name | 셀 더블클릭 → UE에서 보일 desc 이름 | `Hero`, `Size8`, `SimOFF`, `Size4`, `Thick` |
| desc_sources | 셀 우클릭 → `Add desc_sources` → Outliner에서 desc 선택 | `desc_grp0_hero_cache` |
| count (desc) | 자동 갱신 | (읽기 전용) |
| guide_sources | 셀 우클릭 → `Add guide_sources` → Outliner에서 guide group 또는 curves 선택 | `GuideCrv_grp0_hero` 그룹 |
| count (guide) | 자동 갱신 | (읽기 전용) |
| del | × 버튼 → 행 삭제 | |

### 3.3 PC_01 5행 권장 입력

| group_id | new_desc_name | desc_sources | guide_sources | 비고 |
|---|---|---|---|---|
| 0 | `Hero` | `desc_grp0_hero_cache` | `GuideCrv_grp0_hero` | Size16 |
| 1 | `Size8` | `desc_grp1_size8_cache` | `GuideCrv_grp1_size8` | |
| 2 | `SimOFF` | `desc_grp2_simoff_cache` | (비움) | UE에서 EnableSim=False |
| 3 | `Size4` | `desc_grp3_size4_cache` | `GuideCrv_grp3_size4` | |
| 4 | `Thick` | `desc_grp4_thick_cache` | `GuideCrv_grp4_thick` | 뒷머리 |

## 4. Validation

`Table Validation` 클릭. 결과:

| 색 | 의미 | 조치 |
|---|---|---|
| 빨강 | 공백 셀 | 해당 셀 채움 (또는 행 삭제) |
| 노랑 | 중복 값 (group_id / new_desc_name) | unique하게 변경 |
| (색 없음) | 통과 | Export 가능 |

⚠ group_id 2의 guide_sources 공백은 **정상** (Sim OFF 그룹). 빨강 표시되면 그룹 2 row만 별도 Validation skip 또는 더미 guide 1개 넣은 뒤 UE에서 EnableSim=False 처리.

## 5. Export Groom Hair

### 5.1 Export 직전 씬 저장

```mel
file -rename "C:/Users/SHIFTUP/Documents/maya/projects/PC_01_Hair/scenes/PC_01_Hair_v2_export.ma";
file -save;
```

### 5.2 Export 실행

`Export Groom Hair` 클릭 → 파일 다이얼로그:

```
Save: C:/Users/SHIFTUP/Documents/maya/projects/PC_01_Hair/cache/PC_01_Hair_v2.abc
```

내부 호출 (참고 — 사용자가 직접 칠 일은 없음):

```mel
AbcExport
  -worldSpace
  -dataFormat ogawa
  -attr groom_root_uv
  -attr groom_group_id
  -attr groom_guide          ⚠ 단수형
  -uvWrite
  -root <Temp_export_group_<UUID8>>
  -file <path>.abc;
```

### 5.3 산출물

```
cache/PC_01_Hair_v2.abc        ← UE 임포트할 파일 (메인)
```

`Temp_export_group_<UUID>` 임시 그룹은 export 후 자동 정리.

## 6. 부여 어트리뷰트 (사내 툴 명세)

### Spline Group (per group)

| 어트리뷰트 | 타입 | 값 |
|---|---|---|
| `groom_group_id` | short | 0~4 |
| `riCurves` | bool | 1 |
| `groom_guide_AbcGeomScope` | string | `con` |
| `groom_root_uv` | vectorArray | (u, v, 0) per CV[0] |
| `groom_root_uv_AbcGeomScope` | string | `uni` |
| `groom_root_uv_AbcType` | string | `vector2` |

### Curve Guide

| 어트리뷰트 | 타입 | 값 |
|---|---|---|
| `groom_group_id` | short | 0~4 |
| `groom_guide` ⚠ 단수 | short | 1 |
| `riCurves` | bool | 1 |
| `groom_guide_AbcGeomScope` | string | `con` |

## 7. 핵심 함정 — `groom_guide` 단수 vs `groom_guides` 복수

| 출처 | 어트리뷰트명 |
|---|---|
| SB2 사내 툴 (이 가이드) | `groom_guide` (단수) |
| Epic 공식 스키마 | `groom_guides` (복수) |

UE Groom Importer가 어느 쪽을 인식하는지 미검증. 만약 단수형을 UE가 못 잡으면 UE Asset의 시뮬 가이드가 0개로 들어옴 → 시뮬 안 됨.

**대처:** 다음 편(05 Maya MCP Verify)에서 abc 어트리뷰트 dump → UE Import 후 GroomAsset의 `NumGuides`로 교차 확인. 0이면 사내 툴에 `groom_guides` 복수 옵션 패치 요청 또는 export 후 abc 헤더 수동 패치.

## 8. 체크포인트

- [ ] Scalp Mesh + UV Set 등록 완료
- [ ] Component Table 5행 입력 완료
- [ ] Validation 빨강·노랑 0 (또는 의도된 잔존만)
- [ ] `_export.ma` 씬 저장
- [ ] `PC_01_Hair_v2.abc` 산출
- [ ] abc 파일 크기 합리적 (수 MB ~ 수십 MB)

OK면 → [05 Maya MCP Verify](05-Maya-MCP-Verify.md)
