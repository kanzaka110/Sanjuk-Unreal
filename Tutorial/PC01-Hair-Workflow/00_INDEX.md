# PC_01_Hair_01 신규 제작 워크플로우

Maya 원본 XGen 씬에서부터 UE5 Groom Asset + SB2 커스텀 Physics(SBStableRodsSystem)까지 PC_01_Hair_01을 완전히 새로 만드는 절차.

## 전제

| 항목 | 값 |
|---|---|
| 대상 캐릭터 | PC_01 (Evie) |
| 출력 에셋 | `/Game/Art/Character/PC/PC_01/Equipment/Hair/PC_01_Hair_01/PC_01_Hair_01` |
| Binding 타깃 | `CH_P_01_Head_001` (SkeletalMesh) |
| Physics Asset | `Evie_Body_PhysicsAsset` |
| 솔버 | `CustomSolver` → `/Game/Art/TA/Groom/SBStableRodsSystem` (CosseratRods 파생) |
| 그룹 수 | 5 (Hero / Size8 / Sim OFF / Size4 / 굵은) |
| Maya | 2023 (`shiftup.MOD` 모듈 로드) |
| 사내 툴 | Groom Hair Manager v1.0.1+ (TA 장석호) |
| MCP | Maya MCP (50007) + Monolith (9316) |

## 단계 구성

| # | 문서 | Phase | 위치 |
|---|---|---|---|
| 01 | [Preparation](01-Preparation.md) | Maya 환경 + 원본 씬 수령 + UE 백업 | Maya/UE |
| 02 | [XGen Conversion](02-XGen-Conversion.md) | Description → Interactive → Cache 라운드트립 | Maya |
| 03 | [Guide Curves](03-Guide-Curves.md) | xgGuide → Curve, 5그룹 매핑 | Maya |
| 04 | [Groom Hair Manager](04-Groom-Hair-Manager.md) | Component Table → Alembic export | Maya |
| 05 | [Maya MCP Verify](05-Maya-MCP-Verify.md) | dump_groom_metadata 검증 | Claude Code |
| 06 | [UE Import](06-UE-Import.md) | GroomAsset + Binding + Material | UE |
| 07 | [Physics Tuning](07-Physics-Tuning.md) | SBStableRodsSystem 5그룹 라이브값 이식 | UE |
| 08 | [PIE Validation](08-PIE-Validation.md) | PIE + HighResShot + 잔존 이슈 체크 | UE/PIE |
| **09** | **[Automation](09-Automation.md)** | **Maya Phase 02~05 자동화 (MCP 툴 4종 + spec.json)** | **Maya/MCP** |

> 02~05 를 자동화하려면 09편 우선. 수동 절차는 그대로 02~04 따라가도 됨.

## 산출물

```
Maya:
  Documents/maya/projects/PC_01_Hair/scenes/PC_01_Hair_v2_export.ma
  Documents/maya/projects/PC_01_Hair/cache/PC_01_Hair_v2.abc

UE (P4 staging):
  /Game/Art/Character/PC/PC_01/Equipment/Hair/PC_01_Hair_01/
    PC_01_Hair_01.uasset            ← 신규 본
    PC_01_Hair_01_Binding.uasset    ← 재바인딩 필요
    PC_01_Hair_01_v1_backup.uasset  ← 작업 전 자동 백업 (이 가이드의 산물)

자동화 자산 (09편):
  scripts/maya/pc01_hair_v2_spec.json        ← 5그룹 매핑 spec
  scripts/maya/maya_send.py                  ← commandPort fallback
  C:/Dev/MayaMCP/src/mayatools/thirdparty/   ← MCP 툴 4종
    groom_inspect_sfup.py
    groom_convert_xgen.py
    groom_curves_from_guides.py
    groom_apply_spec.py

dumps/:
  hair01_pre_rebuild_<TIMESTAMP>.json        ← 작업 전 라이브 dump
  hair01_post_rebuild_<TIMESTAMP>.json       ← 검증용 dump
  maya_groom_verify_pc01_hair_v2.json        ← Maya 측 alembic_attrs verify
```

## 핵심 함정 (반드시 확인)

| 함정 | 위치 | 비고 |
|---|---|---|
| `groom_guide` vs `groom_guides` 단수/복수 | Maya export 어트리뷰트 | SB2 사내 툴은 단수, Epic 스키마는 복수. UE 인식 여부 05편에서 검증 |
| `LocalBone='root'` 유지 필수 | UE GroomComponent | `head`로 바꾸면 PC_01은 튐 ([[project-pc01-hair01-params]]) |
| `bLocalSimulation=True` 유지 필수 | UE GroomComponent | False 시 헤어 너무 튐 |
| Grp 4 Gravity=-1 버그 | Maya 어트리뷰트 / UE 그룹 | Original 잔존 버그. 신규본 -981 강제 |
| Binding 내부 경로 `/Game/ART/` 대문자 | UE Binding | 스크립트 매칭 시 대소문자 주의 |
| Monolith `//Game/...` 이중 슬래시 | MCP 호출 | Editor fatal crash. 단일 슬래시 강제 |
| PythonScriptPlugin 비활성 | SB2 | `monolith.scripting.execute_script(python)` 차단. runreal 또는 수동 |

## 백업 정책

1. **작업 전:** 현재 PC_01_Hair_01 5그룹 파라미터 JSON dump (`scripts/dump_pc01_hair_params.py`)
2. **작업 전:** UE에서 `PC_01_Hair_01.uasset` → `PC_01_Hair_01_v1_backup.uasset` 복사 (P4 add)
3. **Maya 변환 전:** 원본 XGen 씬을 `_pre_convert` suffix로 별도 저장
4. **각 Phase 종료:** 진행 노트를 `Briefing/2026-MM-DD_pc01-hair-rebuild.md`에 1줄 갱신

## 참고 자료

- [Confluence — Groom Hair Manager](https://shiftupcorp.atlassian.net/wiki/spaces/SB2/pages/285638786/Groom+Hair+Manager) (TA 장석호)
- [Confluence — SHIFT UP TOOL](https://shiftupcorp.atlassian.net/wiki/spaces/SB2/pages/285409479)
- [UE5.7 Using Alembic for Grooms](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-alembic-for-grooms-in-unreal-engine)
- [UE5.7 XGen Guidelines](https://dev.epicgames.com/documentation/en-us/unreal-engine/xgen-guidelines-for-hair-creation-in-unreal-engine)
- 메모리: `project_sb2_groom_hair_manager.md`, `project_pc01_hair01_params.md`, `reference_groom_physics_params.md`
- 사내 툴 본체: `\\10.220.70.11\eve\ART_Backup\EVE_ANI_FACE\SB2_Facial_Project\scripts\maya_script\shiftupTool\script\sfupTools\Groom_Hair_Manager\`
