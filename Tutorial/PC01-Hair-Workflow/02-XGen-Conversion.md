# 02. XGen Conversion — Description → Interactive → Cache 라운드트립

Groom Hair Manager는 **Cache로 Import된 Interactive Description**만 desc_sources로 잡는다. 원본 XGen Description은 직접 못 쓰므로 라운드트립 필수.

> 출처: [Confluence — Groom Hair Manager](https://shiftupcorp.atlassian.net/wiki/spaces/SB2/pages/285638786/Groom+Hair+Manager) "사용 전 준비" 1번.

## 1. Description → Interactive Description 변환

### 1.1 변환 직전 백업

```mel
file -rename "C:/Users/SHIFTUP/Documents/maya/projects/PC_01_Hair/scenes/PC_01_Hair_v2_pre_convert.ma";
file -save;
```

### 1.2 Convert 실행

1. Outliner에서 원본 XGen Description (collection 하위 `description1`, `description2`, ...) 선택
2. **XGen Window** → 우측 Description 패널 → 우클릭 → `Convert to Interactive Groom`
3. 진행 다이얼로그 → `Convert`
4. 변환 완료 후 Outliner에 `xgmSplineDescription_<name>` 노드 생성 확인

### 1.3 검증

```mel
// Interactive Description 노드 수
ls -type "xgmSplineDescription";
// 원본 description 개수와 일치해야 함
```

전부 변환된 게 아니면 원본 desc 중 빈 것/오류 desc가 있는 것. XGen 패널에서 빨간 표시 확인.

## 2. Cache Export

Interactive Description → Cache(.abc)로 굽기.

### 2.1 옵션 설정

XGen Interactive Groom 윈도우 → File → `Generate Cache`:

| 옵션 | 값 |
|---|---|
| Frame Range | **Current Frame** ✅ |
| Format | Alembic |
| File | `Documents/maya/projects/PC_01_Hair/cache/<desc>_cache.abc` |
| Write Final Width | **체크 ✅** |
| Use Mesh Topology | 체크 (옵션) |
| Per-Strand Attrs | (그대로) |

> ⚠ Confluence 가이드 인용: "Current Frame 체크 / Write Final Width 체크". 두 옵션 누락 시 width 정보 손실 → UE에서 strand 굵기가 fallback 값으로 잡힘.

### 2.2 Export 실행

`Export` 클릭. 진행 후 Script Editor에 다음 출력:

```
// Result: Cache exported to .../cache/<desc>_cache.abc
```

각 Interactive Description마다 1개씩 abc 산출. 원본 desc 개수만큼 반복.

## 3. Cache Import (다시 불러오기)

방금 export한 abc를 다시 **씬 안으로 import**. 이게 Groom Hair Manager가 인식하는 형태.

### 3.1 Import 절차

XGen Interactive Groom 윈도우 → File → `Import Cache`:

| 옵션 | 값 |
|---|---|
| File | 방금 export한 `<desc>_cache.abc` |
| Bound Geometry | scalp_mesh (선택) |
| Create New Description | 체크 |

`Import` 클릭.

### 3.2 검증

```mel
// Cache로 import된 Interactive Description 확인
ls -type "xgmSplineDescription";
```

원본 Interactive Description + Cache import된 Interactive Description 둘 다 보임 (개수 2배).

**Cache import된 노드의 이름 패턴**: `xgmSplineDescription_<orig>_cache_n` 또는 `xgmSplineDescription_n` (자동 suffix).

### 3.3 원본 정리 (옵션 권장)

작업 편의를 위해 원본 Interactive Description은 별도 그룹으로 격리:

```mel
group -n "_ORIG_DO_NOT_USE" `ls -type "xgmSplineDescription" -tail 5`;
// 또는 outliner에서 수동 그룹화
```

Cache import된 desc만 노출시켜야 4편 Groom Hair Manager에서 desc_sources 선택할 때 혼동 없음.

## 4. 추가 그룹 정리

Confluence "+추가로" 섹션 — 이후 작업의 편의성을 위해 그룹으로 정리.

권장 트리 구조 (PC_01 5그룹 케이스 가정):

```
PC_01_Hair_v2_root
├── _ORIG_DO_NOT_USE       (격리)
├── descriptions/
│   ├── desc_grp0_hero_cache
│   ├── desc_grp1_size8_cache
│   ├── desc_grp2_simoff_cache
│   ├── desc_grp3_size4_cache
│   └── desc_grp4_thick_cache
├── scalp_mesh
└── xgGuides/              (다음 편)
```

`group_id 0~4` 사전 매핑은 03편 Guide Curves에서 확정.

## 5. 체크포인트

- [ ] 원본 `_pre_convert.ma` 백업 저장
- [ ] 모든 XGen Description → Interactive Description 변환 완료
- [ ] 각 Interactive Description → .abc cache export (Current Frame + Write Final Width)
- [ ] export한 abc를 다시 씬으로 import
- [ ] Cache import된 desc만 작업용으로 노출, 원본은 격리
- [ ] 5그룹 desc 트리 정리

OK면 → [03 Guide Curves](03-Guide-Curves.md)
