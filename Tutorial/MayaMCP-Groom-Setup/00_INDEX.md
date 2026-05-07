# MayaMCP + Groom 데이터 수집 셋업 가이드

SB2 PC_01 / NPC 그룸(XGen Legacy + Interactive Groom)을 Claude Code에서 자연어로 조사·덤프하기 위한 환경 구성 기록.

## 환경 (2026-05-07 시점)

| 항목 | 값 |
|---|---|
| Maya | 2023 (`C:\Program Files\Autodesk\Maya2023`) |
| MayaMCP 본체 | `C:\Dev\MayaMCP` (PatrickPalmer/MayaMCP, v0.2.0) |
| MCP 서버 venv | `C:\Dev\MayaMCP\.venv` (Python 3.11.9) |
| Maya commandPort | 50007 (`Documents/maya/2023/scripts/userSetup.py`로 자동) |
| Sanjuk-Unreal `.mcp.json` | `maya` 항목 등록 완료 |

## 동작 검증 절차

1. **Maya 2023 실행**
   - 시작 시 Script Editor에 `[MayaMCP] Command port 50007 opened` 워닝 출력 확인
   - 출력 안 나오면 Script Editor에서 수동 실행:
     ```mel
     commandPort -name ":50007" -sourceType "mel" -echoOutput false;
     ```

2. **Claude Code 재기동**
   - `C:\Dev\Sanjuk-Unreal`에서 Claude Code 새 세션
   - `/mcp` 입력 → `maya` 서버가 listed + connected 확인

3. **첫 호출 (Maya 보안 팝업)**
   - 자연어로 `씬에 있는 카메라 목록 보여줘` 같이 요청
   - Maya에서 "Allow All" 클릭 (세션 시작마다 1회)

4. **Groom 메타데이터 덤프**
   - 자연어: `현재 씬의 그룸 메타데이터 dump해줘` (또는 직접 `dump_groom_metadata` 툴 호출)
   - 응답 dict의 키:
     - `xgen_legacy[]` — collection / description / bound geometry
     - `interactive_groom[]` — xgmSplineDescription / 바운드 메시 / density
     - `alembic_attrs[]` — `groom_root_uv` / `groom_group_id` / `groom_guides` 노출된 노드
     - `errors[]` — XGen 플러그인 미로드 등 경고

## 추가된 파일

| 경로 | 용도 |
|---|---|
| `C:\Dev\MayaMCP\src\mayatools\thirdparty\dump_groom_metadata.py` | 그룸 dump 툴 (XGen Legacy + Interactive 둘 다) |
| `Documents\maya\2023\scripts\userSetup.py` | commandPort 50007 자동 오픈 |
| `Sanjuk-Unreal\.mcp.json` 의 `maya` 항목 | Claude Code MCP 등록 |

## UE Groom Asset과 매핑하는 핵심 attribute

UE 5.7 Groom Importer가 Alembic에서 읽는 Epic 스키마 (모두 옵셔널):

| 속성 | 타입 | 의미 | 권장 |
|---|---|---|---|
| `groom_guides` | int | 1이면 가이드 커브 (시뮬 대상) | 시뮬 사용 시 필수 |
| `groom_root_uv` | Vec2 | 스칼프 메시 UV 좌표 | 권장 (없으면 spherical 자동) |
| `groom_group_id` | int | 그룹 ID (머티리얼/시뮬 슬롯) | 다중 그룹 시 필수 |
| `groom_guide_id` | int | 가이드 ID (구 명칭) | UE4 호환용 |
| `groom_width`, `groom_color` | float / Vec3 | 굵기, 색상 | 선택 |

PC_01 Sanjuk 5그룹 케이스는 `groom_group_id 0~4`로 분리된 상태로 들어와 있을 가능성이 높음. dump 결과의 `alembic_attrs`로 어느 노드가 그룹 ID를 들고 있는지 확인 가능.

## 다음 단계 (TODO)

- [ ] PC_01 헤어 작업한 Maya 씬을 열고 dump_groom_metadata 호출 → JSON 저장
- [ ] UE Groom Asset(이미 SB2/Content/Hair 아래 있음) 덤프와 대조 스크립트 작성
- [ ] XGen Legacy → Alembic export 자동화 툴 (`export_groom_alembic.py`) 추가
- [ ] Interactive Groom의 가이드 커브만 추출하는 툴 추가 (`extract_guide_curves.py`)

## 참고

- [PatrickPalmer/MayaMCP](https://github.com/PatrickPalmer/MayaMCP)
- [UE 5.7 Using Alembic for Grooms](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-alembic-for-grooms-in-unreal-engine)
- [XGen Guidelines for Hair Creation in UE5](https://dev.epicgames.com/documentation/en-us/unreal-engine/xgen-guidelines-for-hair-creation-in-unreal-engine)
- 메모리 `reference_groom_physics_params.md` (UE 5.7 Groom Physics)
- 메모리 `project_pc01_hair_gravity_bug.md` (Sanjuk 5그룹 튜닝 상태)
