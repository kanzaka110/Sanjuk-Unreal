# 05. Maya MCP Verify — dump_groom_metadata 검증

UE에 임포트하기 전, Claude Code에서 Maya 씬과 abc의 메타데이터를 dump해서 어트리뷰트가 의도대로 박혔는지 확인.

## 1. 사전 조건

| 항목 | 확인 |
|---|---|
| Maya 2023 실행 중 | commandPort 50007 열림 |
| MayaMCP 서버 connected | Claude Code `/mcp` → maya: ✅ |
| 04편 export 직후 씬 그대로 | 새로 load 가능 |

## 2. Maya 씬 메타데이터 dump

Claude Code에서:

```
mcp__maya__dump_groom_metadata(verbose=True)
```

응답 구조:

```json
{
  "xgen_legacy": [
    {"collection": "...", "description": "...", "bound_geometry": "scalp_mesh"}
  ],
  "interactive_groom": [
    {"xgmSplineDescription": "...", "bound_mesh": "scalp_mesh", "density": ...}
  ],
  "alembic_attrs": [
    {"node": "<SplineGrp_0>", "attrs": ["groom_group_id=0", "groom_root_uv", "riCurves=1"]},
    {"node": "<GuideCrv_0_n>", "attrs": ["groom_group_id=0", "groom_guide=1", "riCurves=1"]}
  ],
  "errors": []
}
```

## 3. 검증 항목

### 3.1 alembic_attrs 5그룹 모두 보임

```
필터: alembic_attrs[].attrs contains "groom_group_id"
기대: group_id 0,1,2,3,4 모두 발견
```

빠진 group_id가 있으면 → 04편 Component Table 행 누락 또는 desc_sources/guide_sources 미선택. Maya로 돌아가 보강.

### 3.2 groom_guide vs groom_guides

```
필터: alembic_attrs[].attrs contains "groom_guide"
기대: Curve Guide 노드들에 groom_guide=1 (단수)
```

⚠ 06편 UE Import 후 NumGuides=0이면 이 단수/복수가 의심 1순위. 그땐 abc 헤더를 추가로 확인:

```bash
# WSL 또는 git bash에서
python -c "from alembic import Abc; import sys; ..." 
# 또는 cache/ue57의 abc 파서 활용
```

또는 사내 툴 소스에서 `-attr groom_guide` → `-attr groom_guides` 패치 요청.

### 3.3 groom_root_uv 분포

Curve CV[0]이 scalp_mesh 표면에 안 붙어 있으면 root_uv가 클램프됨. 의심 시:

```
alembic_attrs[].attrs에서 groom_root_uv 값 분포 확인
(0,0) 또는 (1,1) 같은 코너로 몰리면 fallback 발생
```

### 3.4 errors[] 빈 배열

XGen 플러그인 미로드, scalp_mesh 미등록 등은 여기에 잡힘. 비어 있어야 정상.

## 4. abc 파일 직접 dump (옵션)

씬 의존성 없이 abc 자체 검증.

### 4.1 Alembic CLI

```powershell
# Maya에 포함된 abcecho 사용
& "C:/Program Files/Autodesk/Maya2023/bin/abcecho.exe" `
    "C:/Users/SHIFTUP/Documents/maya/projects/PC_01_Hair/cache/PC_01_Hair_v2.abc"
```

출력에서 다음 항목 확인:

```
.geom
  groom_group_id [arbGeomParams, short]
  groom_root_uv  [arbGeomParams, V2f]
  groom_guide    [arbGeomParams, short]    ← 단수
  riCurves       [arbGeomParams, bool]
```

### 4.2 alembic 어트리뷰트 그룹별 카운트 스크립트

`scripts/verify_groom_abc.py`(작성 필요):

```python
"""
groom abc 파일의 group_id별 desc/guide 카운트.
사용: py scripts/verify_groom_abc.py <path.abc>
"""
import sys
from alembic import Abc, AbcGeom

path = sys.argv[1]
archive = Abc.IArchive(path)
top = archive.getTop()

# walk: top -> Temp_export_group_XXX -> desc subgroups -> SplineGrp / GuideCrv
def walk(obj, depth=0):
    for i in range(obj.getNumChildren()):
        child = obj.getChild(i)
        name = child.getName()
        prop_keys = list(child.getProperties().getPropertyHeaders()) if hasattr(child.getProperties(), 'getPropertyHeaders') else []
        print("  " * depth + f"- {name} ({type(child).__name__})")
        walk(child, depth + 1)

walk(top)
```

## 5. UE 측 baseline dump

신규 abc로 임포트하기 전에 현재 PC_01_Hair_01의 정확한 라이브 상태도 한 번 더 dump (06편 임포트 후 비교 기준점).

```powershell
py scripts/dump_pc01_hair_params.py
```

산출: `dumps/hair01_baseline_<TIMESTAMP>.json`

01편에서 dump한 `pre_rebuild`와 동일 내용이면 OK (이중 안전망).

## 6. 체크포인트

- [ ] `dump_groom_metadata` 호출 성공
- [ ] errors[] = []
- [ ] alembic_attrs에 group_id 0~4 모두 발견
- [ ] groom_guide=1 어트리뷰트가 Curve Guide 노드들에 박힘
- [ ] groom_root_uv가 (0,0)/(1,1) 코너로 안 몰림
- [ ] (옵션) abcecho 로 abc 파일 어트리뷰트 직접 확인
- [ ] UE baseline dump 추가 저장

OK면 → [06 UE Import](06-UE-Import.md)
