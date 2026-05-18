---
name: SB2 로컬 Maya MCP + Groom 데이터 수집 환경
description: PC_01/NPC 그룸을 Claude Code에서 자연어로 조사하기 위한 PatrickPalmer/MayaMCP 셋업 상태와 경로
type: project
originSessionId: ebb9a6d8-e675-4b83-840f-614d45867951
---
2026-05-07 셋업 완료. PC_01 Sanjuk 5그룹 헤어 / NPC 그룸 메타데이터를 Maya 쪽에서 직접 dump하기 위해 PatrickPalmer/MayaMCP를 로컬에 설치.

**Why:** UE Groom Asset 튜닝(reference_groom_physics_params.md, project_pc01_hair_gravity_bug.md) 작업 중 Maya 원본 씬의 group_id / root_uv / guide curve 구성을 알아야 UE 측 그룹과 1:1 매핑이 가능. xGen2UE 같은 export 스크립트만으로는 round-trip 진단이 어려움.

**How to apply:** Maya 씬 분석/그룸 데이터 dump 요청이 오면 이 환경을 사용. 새 세션에서는 ① Maya 2023 실행 → ② commandPort 50007이 userSetup.py로 자동 오픈됐는지 확인 → ③ Claude Code 재기동 → ④ /mcp로 maya 서버 연결 확인 후 dump_groom_metadata 호출.

## 경로

| 항목 | 경로 |
|---|---|
| MayaMCP 본체 | `C:\Dev\MayaMCP` (PatrickPalmer/MayaMCP v0.2.0) |
| MCP 서버 venv | `C:\Dev\MayaMCP\.venv` (Python 3.11.9, mcp 1.27.0) |
| 그룸 dump 툴 | `C:\Dev\MayaMCP\src\mayatools\thirdparty\dump_groom_metadata.py` |
| Maya 자동 시작 스크립트 | `C:\Users\SHIFTUP\Documents\maya\2023\scripts\userSetup.py` |
| `.mcp.json` 등록 | `C:\Dev\Sanjuk-Unreal\.mcp.json`의 `maya` 항목 |
| 가이드 문서 | `C:\Dev\Sanjuk-Unreal\Tutorial\MayaMCP-Groom-Setup\00_INDEX.md` |

## MayaMCP 동작 방식 (요약)

- Maya 내부 플러그인 설치 불필요. Maya가 commandPort 50007 (MEL)을 열어두면 외부 venv의 MCP 서버가 거기에 Python 코드를 MEL python(...) 래핑으로 전송.
- thirdparty/ 폴더에 `def 함수명(...)` 한 개짜리 .py를 떨구면 자동으로 MCP 툴로 등록 (파일명 == 함수명 필수, MCP 서버 재기동 필요).
- 첫 호출 시 Maya가 보안 팝업 → "Allow All" 클릭해야 세션 동안 통신 가능.

## dump_groom_metadata 반환 스키마

```
{
  "xgen_legacy": [{collection, description, bound_geometry, ...}],
  "interactive_groom": [{description_shape, transform, bound_mesh, density, ...}],
  "alembic_attrs": [{node, attrs: ["groom_root_uv", "groom_group_id", ...]}],
  "errors": ["xgenm module not available ..." 등]
}
```

XGen 플러그인 미로드 시 `xgen_legacy`는 비고 errors에 메시지 들어감. Interactive Groom 전용 씬이면 정상.

## 미완 / 다음 작업

- 실제 PC_01 Maya 씬 열어 dump 결과 확보 후 UE Groom Asset 슬롯과 매핑 검증.
- export_groom_alembic.py / extract_guide_curves.py 추가 예정.
