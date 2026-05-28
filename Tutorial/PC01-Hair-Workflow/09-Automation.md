# 09. Automation — Maya Phase 02~05 자동화

UI 클릭 절차(02 XGen Convert / 03 Curve 변환 / 04 Groom Hair Manager / 05 Verify)를 spec.json + 4개 MCP 툴로 일괄 실행.

## 1. 아키텍처

```
┌──────────────────────────────────────────────────────────────┐
│  Claude Code                                                 │
│    ↓ 자연어 호출 (또는 직접 mcp__maya__* 호출)               │
│  MayaMCP (stdio)                                             │
│    ↓ commandPort 50007                                       │
│  Maya 2023                                                   │
│    ↓ MEL/Python                                              │
│  XGen / sfupTools.Groom_Hair_Manager / AbcExport             │
│    ↓                                                          │
│  cache/PC_01_Hair_v2.abc                                     │
└──────────────────────────────────────────────────────────────┘
```

## 2. 신규 MCP 툴 4종

각 툴은 `C:/Dev/MayaMCP/src/mayatools/thirdparty/` 에 .py 파일로 추가됨.
**MayaMCP 서버 재기동 후 등록됨** (Claude Code 새 세션).

| MCP 도구 | Phase | 역할 |
|---|---|---|
| `mcp__maya__groom_inspect_sfup()` | 0 (사전) | shiftup.MOD 사내 모듈 import + 함수 시그니처 enumerate. **최초 1회 필수.** |
| `mcp__maya__groom_convert_xgen(dry_run)` | 02 | XGen → Interactive → Cache round-trip |
| `mcp__maya__groom_curves_from_guides(dry_run)` | 03 | xgGuide → Curve 일괄 + 긴 커브 rebuild |
| `mcp__maya__groom_apply_spec(spec_json_path, dry_run)` | 04 + 05 | spec.json → 사내 백엔드 호출 + Export + dump verify |

기존 도구도 그대로 사용:
- `mcp__maya__dump_groom_metadata(verbose=True)` (05편 verify)

## 3. spec.json

`scripts/maya/pc01_hair_v2_spec.json` 템플릿 제공.

핵심 필드:

```json
{
  "asset_id": "PC_01_Hair_v2",
  "output_abc": "C:/.../cache/PC_01_Hair_v2.abc",
  "scalp_mesh": "scalp_mesh",
  "scalp_uv_set": "map1",
  "xgen": { "convert_to_interactive": true, ... },
  "guide_curves": { "source": "xgGuide", ... },
  "groups": [
    { "group_id": 0, "new_desc_name": "Hero",
      "desc_sources": ["desc_grp0_hero_cache"],
      "guide_sources": ["GuideCrv_grp0_hero"] },
    ...
  ],
  "validation": { ... },
  "post_export_verify": { "run_dump_groom_metadata": true, ... }
}
```

NPC/다른 캐릭터에 재사용 시 이 파일을 복사 + asset_id / 노드명 갱신.

## 4. 사용 순서

### 4.1 0회차 — 사내 모듈 시그니처 검증 (필수)

```
mcp__maya__groom_inspect_sfup()
```

기대 응답 (시뮬레이션):

```json
{
  "module_path": "//10.220.70.11/eve/.../Groom_Hair_Manager/utils.py",
  "available_modules": ["sfupTools.Groom_Hair_Manager.utils", "...main"],
  "functions": {
    "sfupTools.Groom_Hair_Manager.utils": [
      "prepare_export(spec)",
      "duplicate_raw_sources(spec)",
      "create_groups(spec)",
      "set_attributes(spec)",
      "export_alembic(spec)",
      ...
    ]
  },
  "errors": []
}
```

> errors 가 비어있고 `prepare_export` 또는 단계별 함수 6종 중 하나 이상 보이면 OK.
> errors 가 있으면 shiftup.MOD 미로드 또는 NAS 미마운트. 01편 Preparation 1.2절로 복귀.

함수 시그니처가 spec dict 안 받으면 (예: `prepare_export(table, scalp, uv, output)` 식) → `groom_apply_spec.py` 7절의 호출부를 시그니처에 맞게 수정 필요. 이 가이드 작성 시점엔 spec dict 통일 인터페이스 가정.

### 4.2 Phase 02 — XGen Conversion

```
mcp__maya__groom_convert_xgen(dry_run=True)
```

응답의 `plan` 리스트에 발사될 MEL 명령 확인. 의도와 맞으면 실제 실행:

```
mcp__maya__groom_convert_xgen(dry_run=False, save_pre_convert_scene=True)
```

산출:
- `<scene>_pre_convert.ma` 백업
- 새 xgmSplineDescription 노드들 (Interactive)
- `cache/desc/*.abc` per description
- 원본 desc → `_ORIG_DO_NOT_USE` 그룹으로 격리

⚠ SB2 환경에서 `xgmInteractiveBaseFromGroom` / `xgmSplineCache` MEL 시그니처가 다르면 errors 에 잡힘. 그 경우 사내 TA에게 정확한 procedure 명 확인 → `groom_convert_xgen.py` 패치.

### 4.3 Phase 03 — Guide Curves

```
mcp__maya__groom_curves_from_guides(dry_run=True)
```

응답 확인 후:

```
mcp__maya__groom_curves_from_guides(dry_run=False, rebuild_long_curves=True)
```

산출:
- 새 NURBS curves (xgGuide와 동일 world position)
- 긴 커브 (spans+degree > 252) → spans=32 로 rebuild
- 그룹 매핑은 사람이 수동 정리 (시각 판단)

⚠ Curve 모양 정돈 (TwinTail 중심 배치 등)은 자동화 안 됨. 한 번 정돈한 .ma 를 보존하면 재사용 가능.

### 4.4 그룹 매핑 + spec.json 갱신 (수동)

자동화 안 됨. 사람이 Outliner 보면서:
1. 새 curves 를 그룹별로 묶기 (`group -n "GuideCrv_grp0_hero" ...`)
2. desc cache 노드 이름을 `desc_grp0_hero_cache` 등으로 rename
3. `spec.json` 의 `desc_sources` / `guide_sources` 에 정확한 노드명 기입

(향후 개선) `scripts/maya/build_spec_from_scene.py` 로 자동 추출 가능. 첫 1회만 사람 손.

### 4.5 Phase 04 + 05 — Apply Spec + Verify

```
mcp__maya__groom_apply_spec(
  spec_json_path="C:/Dev/Sanjuk-Unreal/scripts/maya/pc01_hair_v2_spec.json",
  dry_run=True
)
```

응답에서 `plan` 리스트 + `backend` (sfupTools / abcexport_fallback / dry_run) 확인:

| backend | 의미 | 대처 |
|---|---|---|
| `sfupTools` | 사내 백엔드 사용 ✅ | OK, dry_run=False 로 실행 |
| `abcexport_fallback` | 사내 백엔드 미발견 | groom_inspect_sfup 으로 재확인 |
| `dry_run` | 실행 안 함 | dry_run=False 로 재호출 |

실제 실행:

```
mcp__maya__groom_apply_spec(
  spec_json_path="...",
  dry_run=False
)
```

산출:
- `PC_01_Hair_v2.abc` (output_abc 경로)
- `dumps/maya_groom_verify_pc01_hair_v2.json` (post-verify dump)

응답의 `errors` 가 비어있으면 OK. Phase 06 (UE Import) 로 진행.

## 5. Fallback — MayaMCP 미가용 시

MayaMCP 서버가 안 떠 있거나 새 툴이 등록 안 됐을 때, commandPort 50007 직접 호출:

```powershell
# inspect
py scripts/maya/maya_send.py py "from mayatools.thirdparty.groom_inspect_sfup import groom_inspect_sfup; import json; print(json.dumps(groom_inspect_sfup()))"

# apply (dry_run)
py scripts/maya/maya_send.py py "from mayatools.thirdparty.groom_apply_spec import groom_apply_spec; import json; print(json.dumps(groom_apply_spec('C:/Dev/Sanjuk-Unreal/scripts/maya/pc01_hair_v2_spec.json', dry_run=True)))"
```

`maya_send.py` 가 MEL `python("...")` 으로 wrap 해서 Maya 에 전송.

⚠ thirdparty 폴더가 Maya 의 `sys.path` 에 있어야 함. `C:/Dev/MayaMCP/src/` 가 PYTHONPATH 에 등록돼 있으면 OK. 안 되면:

```python
# Maya Script Editor에서 1회
import sys
sys.path.insert(0, "C:/Dev/MayaMCP/src")
```

## 6. 의사결정 트리

```
groom_inspect_sfup() 호출
├── errors=[] AND functions에 prepare_export OR 6단계 함수 발견
│   └── ✅ 자동화 가능 → Phase 02~05 자동
│
├── errors=[] BUT 함수 시그니처가 spec dict 안 받음
│   └── ⚠ groom_apply_spec.py 7절 호출부 패치 후 재시도
│
├── errors에 ImportError (sfupTools 미발견)
│   └── ❌ 01편 Preparation 1.2 (shiftup.MOD 로드) 재확인
│       └── 마운트 안 되면 → 04편 수동 UI 클릭 fallback
│
└── 환경 검증 안 됨
    └── dry_run=True 로 plan 확인 → TA 협업으로 명령 검증
```

## 7. End-to-end 시퀀스 (이상적 케이스)

```
# 0회차 (1회만)
mcp__maya__groom_inspect_sfup()

# Phase 02
mcp__maya__groom_convert_xgen(dry_run=True)   # 확인
mcp__maya__groom_convert_xgen(dry_run=False)  # 실행

# Phase 03 (자동) + 그룹 정리 (수동, ~10분)
mcp__maya__groom_curves_from_guides(dry_run=False)
# Outliner에서 group/rename + scripts/maya/pc01_hair_v2_spec.json 갱신

# Phase 04 + 05
mcp__maya__groom_apply_spec(
  spec_json_path="C:/Dev/Sanjuk-Unreal/scripts/maya/pc01_hair_v2_spec.json",
  dry_run=True
)
mcp__maya__groom_apply_spec(spec_json_path="...", dry_run=False)

# Maya 작업 끝. 이후 06편 UE Import.
```

총 사람 손: ~10~20분 (그룹 정리 + Curve 정돈) vs 수동 풀 절차 ~2시간.

## 8. 자동화 한계 (재명시)

| 항목 | 자동화 X | 이유 |
|---|---|---|
| 원본 XGen 씬 정합성 검증 | 사람 | XGen plugin 의존, 시각 판단 |
| Guide Curve 모양 정돈 | 사람 | 미적 판단 (TwinTail 중심 배치 등) |
| 그룹 매핑 결정 | 사람 | 디자인 의도 (5그룹 분할 기준) |
| spec.json 첫 1회 작성 | 사람 (이후 재사용) | 노드명 매핑 |
| XGen MEL 시그니처 환경 차이 | 사람 | SB2 빌드 검증 필요 시 TA 협업 |
| PIE 시각 판정 | 사람 | 미적 판단 |

## 9. 첫 사용 체크리스트

- [ ] `C:/Dev/MayaMCP/src/mayatools/thirdparty/` 에 4 .py 파일 확인
- [ ] Claude Code 새 세션 시작 (MayaMCP 재기동)
- [ ] `/mcp` 응답에 `maya` connected
- [ ] `mcp__maya__groom_inspect_sfup()` errors=[]
- [ ] `scripts/maya/pc01_hair_v2_spec.json` 수정 (실제 노드명)
- [ ] `dry_run=True` 응답에서 plan 의도 확인
- [ ] `dry_run=False` 실행
- [ ] `dumps/maya_groom_verify_*.json` 생성 + alembic_attrs 5그룹 보임

OK면 → [06 UE Import](06-UE-Import.md) 그대로 진행.
