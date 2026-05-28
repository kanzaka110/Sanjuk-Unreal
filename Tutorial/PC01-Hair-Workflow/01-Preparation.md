# 01. Preparation — Maya 환경 + 원본 씬 수령 + UE 백업

## 1. Maya 환경 확인

### 1.1 모듈 로드 검증

Maya 2023 실행 후 Script Editor에 다음 출력 확인:

```
// shiftup.MOD : loaded
// MayaMCP   : Command port 50007 opened
```

출력이 없으면:

```mel
// shiftup.MOD 수동 로드
loadModule -load "C:/Users/SHIFTUP/Documents/maya/2023/modules/shiftup.MOD";

// commandPort 수동 오픈
commandPort -name ":50007" -sourceType "mel" -echoOutput false;
```

### 1.2 메뉴 확인

상단 메뉴에 `SHIFTUP` 메뉴가 보여야 함. `SHIFTUP > Character Settings > Groom Hair Manager` 클릭 시 UI가 떠야 정상.

UI가 안 뜨면 사내 NAS 마운트 확인:
```
\\10.220.70.11\eve\ART_Backup\EVE_ANI_FACE\SB2_Facial_Project\scripts\maya_script\shiftupTool\script\sfupTools\Groom_Hair_Manager\
```

### 1.3 XGen 플러그인 로드

`Windows > Settings/Preferences > Plug-in Manager`에서:
- `xgenToolkit.mll` — Loaded + Auto load 체크
- `AbcExport.mll`, `AbcImport.mll` — Loaded + Auto load 체크

미로드 시 Groom Hair Manager의 Validation에서 desc_sources를 못 잡음.

## 2. 원본 XGen 씬 수령

### 2.1 요청 채널

TA 장석호 (`@장석호` Slack 또는 사내 NAS 직접 접근) → PC_01 헤어 원본 Maya 씬 1식 수령:

```
필요 파일:
  PC_01_Hair_v<n>.ma          ← 메인 씬
  PC_01_Hair_v<n>.xgen        ← XGen Description
  scalp_mesh / xgGuide / xgmGuide 노드 포함
  collections/                ← XGen collection 디렉토리
  
선택:
  reference Body mesh         ← UV/scalp 검증용
```

### 2.2 작업 폴더 셋업

```
Documents/maya/projects/PC_01_Hair/
├── scenes/
│   ├── PC_01_Hair_v2_source.ma         ← 수령본 (read-only)
│   ├── PC_01_Hair_v2_pre_convert.ma    ← 변환 전 백업 (02편 직전)
│   └── PC_01_Hair_v2_export.ma         ← 최종 export 직전
├── cache/
│   └── (Interactive Description abc / 가이드 abc / 최종 Groom abc)
├── data/
│   └── xgen/
└── workspace.mel
```

수령 직후 `_source.ma`는 **read-only 속성**으로 잠금 (실수로 변형 방지).

## 3. UE 측 백업

### 3.1 라이브 파라미터 dump

```powershell
# Claude Code에서
py scripts/dump_pc01_hair_params.py
```

산출물:
- `dumps/hair01_pre_rebuild_20260528.json` — 현재 5그룹 전체 파라미터
- `dumps/hair01_pre_rebuild_groomcomponent_20260528.json` — BP_Sanjuk Hair_GEN_VARIABLE CDO

dump 스크립트가 없으면 Monolith로 직접:

```
animation_query("get_groom_asset_info",
  asset_path="/Game/Art/Character/PC/PC_01/Equipment/Hair/PC_01_Hair_01/PC_01_Hair_01",
  include_groups=True)
```

⚠ 경로 단일 슬래시 강제. `//Game/...` 시 editor fatal crash.

### 3.2 에셋 복사 백업

UE Content Browser에서 P4 체크아웃 후:

```
PC_01_Hair_01.uasset       → PC_01_Hair_01_v1_backup.uasset   (Duplicate)
PC_01_Hair_01_Binding.uasset → PC_01_Hair_01_Binding_v1_backup.uasset
```

⚠ P4 Submit 전. 신규본이 검증 통과해야 v1_backup 제거 가능.

### 3.3 BP_Sanjuk CDO 노트

`PC_01_BP_Sanjuk`의 `Hair_GEN_VARIABLE` (SBCharacterGroomComponent)의 다음 필드는 새 에셋이 들어와도 유지:

| 필드 | 값 | 비고 |
|---|---|---|
| bLocalSimulation | True | False 금지 |
| LocalBone | "root" | "head" 금지 |
| LinearVelocityScale | 1.0 | 최댓값 |
| AngularVelocityScale | 1.0 | 최댓값 |
| TeleportDistance | 50 | |
| WindScale | 0.4 | SB2 커스텀 필드 |
| PhysicsAsset | Evie_Body_PhysicsAsset | 06편에서 재연결 |

신규 에셋 임포트 후 Binding만 새 것으로 갈아끼우면 위 필드는 자동 보존.

## 4. 체크포인트

다음 편(02 XGen Conversion)으로 넘어가기 전 확인:

- [ ] Maya 2023 + shiftup.MOD + MayaMCP 정상
- [ ] `SHIFTUP > Groom Hair Manager` UI 실행 성공
- [ ] XGen/AbcExport/AbcImport 플러그인 Loaded
- [ ] 원본 씬 수령 + `_source.ma` read-only 잠금
- [ ] 작업 폴더 트리 생성
- [ ] UE 라이브 dump JSON 저장 (작업 전 베이스라인)
- [ ] UE `_v1_backup.uasset` 2개 생성

모두 OK면 → [02 XGen Conversion](02-XGen-Conversion.md)
