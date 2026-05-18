---
name: SB2 MetaHuman for Maya 작업 절차 (Confluence 캐시)
description: Epic 공식 MetaHuman for Maya 플러그인 - Maya 2022~2025 + UE 5.6 DCC Export 기반. SB2 RnD 워크플로우 정리.
type: project
originSessionId: ebb9a6d8-e675-4b83-840f-614d45867951
---
Confluence 페이지 v7 캐시 (2026-05-07 동기화). 페이지: https://shiftupcorp.atlassian.net/wiki/spaces/SB2/pages/637960334/MH_MetaHuman_for_Maya

**Why:** Epic 공식 MetaHuman for Maya 플러그인의 도구 3종 중 하나가 Groom Exporter — 사내 Groom Hair Manager 와 같은 일을 함. PC_01/NPC 헤어 export 시간 문제 디버깅 시 대안으로 검토 가능. 또한 MetaHuman 얼굴 수정 워크플로우 (Expression Editor + DNA 갱신) 가 SB2 RnD 결과로 정리되어 있음.

**How to apply:** MetaHuman 캐릭터 페이셜/그룸 작업 시 이 메모를 참고. 첨부 `MetaHuman_for_Maya_RnD.docx` 에는 작업 중 해결한 이슈와 테스트 내용 추가. 페이지 자체는 절차 위주이고 docx 가 트러블슈팅.

## Epic 플러그인 3 도구

1. **Character Assembler** — UE 에서 DCC Export 로 내보낸 MetaHuman 자산을 Maya 에서 리깅·텍스처된 애니메이션 가능 캐릭터로 조립
2. **Groom Exporter** — 레거시 XGen Description 으로 만든 MetaHuman 호환 헤어를 UE 로 export. **사내 Groom Hair Manager 와 기능 중복**
3. **Expression Editor** — 얼굴 표정 수정 (joint delta / blend shape / pseudo-human)

## 기술 세부사항

- Maya **2022~2025**
- UE **5.6** + **DCC Export 파이프라인** 필수 (헤드 DNA / 바디 DNA / 텍스처 파일 사전 export 전제)
- 1.5GB 디스크

## 설치 (4 단계)

1. Fab 에서 MetaHuman for Maya 라이브러리에 추가 (https://www.fab.com/ko/listings/9e3bf55e-d4c3-44fc-a3d4-ec4cb772ec29)
2. Epic Games Launcher → Fab Library → UE 5.6 에 설치
3. `C:\Program Files\Epic Games\UE_5.6\Engine\Plugins\Marketplace\MetaHumanForMaya_5.6\Content` 의 `MetaHumanForMaya.msi` 실행
4. Maya 에 플러그인 등록 (Plug-in Manager)

## 사용 — Edit Expression 워크플로우 (Sculpt Mesh 방식)

1. Expression 노드 선택 → **Edit Selected Expression**
2. `sculpt_head_lod0_mesh` 선택 → isolate → Maya 내장 Sculpt 툴로 수정 (또는 외부 export/import)
3. 우측 하단 **ML Joint Matching** 클릭 → 셰입에 맞는 Joint Delta + blend shape 자동 적용
4. **Edit Expression** 버튼 다시 눌러 모드 종료
5. **Update DNA** — 수정 내용을 DNA 에 반영

## Unreal Setup (DNA 갱신 전략)

**핵심 전략**: 단순 DNA 업데이트만으로는 Blendshape 가 갱신 안 됨 → 리그 제거 후 DNA 레퍼런스로 Head 재생성 → Skeletal Mesh 재생성.

1. MetaHuman Character 에셋 → **Remove Rig** (필수, 이거 안 하면 수정 불가)
2. **Head > Conform > Import DNA** → DNA 파일 선택 → Import. DNA 의 Mesh / Expression (rig logic / blendshape) 모두 자동 생성

## 결과 / 남은 과제

- 서드파티 툴이 하던 기능 대부분 포함, 더 정밀한 디테일 교정 가능
- Performance Capture 결과: 실제 인물 vs 메타휴먼 표정 차이는 Expression 수정으로 축소 가능 (시간 소요)
- **과제 1**: 다수 Shape 를 Expression 에 일괄 적용하는 ML 기반 자동화 필요 (현재는 일일이 등록)
- **과제 2**: 위 1 을 바탕으로 전체 제작 파이프라인 최적화
- **과제 3**: Body DNA / 파이프라인 RnD

## SB2 Groom Hair Manager 와의 관계

| 항목 | SHIFTUP Groom Hair Manager | Epic Groom Exporter |
|---|---|---|
| 위치 | 사내 NAS (`\\10.220.70.11\eve\...\sfupTools\Groom_Hair_Manager`) + standalone fork (`E:\Maya\maya_script\Groom_Hair_Manager`) | UE 5.6 + Maya 2022~2025 플러그인 |
| 입력 | XGen Legacy Description | "MetaHuman-compatible grooms created with legacy XGen Descriptions" |
| 출력 | `.abc` (groom_group_id, groom_root_uv, groom_guide / groom_guides) | `.abc` (Epic 표준 스키마) |
| UE 호환 | 5.5~5.7 (사내 검증), `groom_guide` 단수 잠재 이슈 | UE 5.6 공식 |

→ PC_01/NPC 헤어 export 시간 문제가 사내 툴 코드 자체 이슈가 아니라 데이터 양/씬 상태 때문이면, Epic 플러그인을 검증해서 비교하는 것도 의미 있음. 단 SB2 가 UE 5.7.4 커스텀 빌드라 UE 5.6 전제인 이 플러그인이 그대로 동작할지는 미확인.

## 첨부

- `MetaHuman_for_Maya_RnD.docx` (작업 진행 중 해결한 이슈 + 테스트 내용 — 페이지 본문엔 미포함)
- 다운로드: `https://shiftupcorp.atlassian.net/wiki/download/attachments/637960334/MetaHuman_for_Maya_RnD.docx`
