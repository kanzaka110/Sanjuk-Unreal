# [Maya] Groom Hair Works Process (SB2 공식 SOP)

> XGen Groom 을 UE5 Groom Asset 임포트용 Alembic 으로 정리·Export 하는 사내 표준 작업 절차 (언리얼 작업 직전까지).
> 원본: [Confluence — Maya Groom Hair Works Process](https://shiftupcorp.atlassian.net/wiki/spaces/SB2/pages/1608908814/Maya+Groom+Hair+Works+Process) (작성자: 채승호 / SB2). 스크린샷은 원본 참조.
> `🔎 실측` 표시 = 2026-06 Evie(PC_01) 헤어 실작업에서 확인·보강한 항목.

---

## 한눈에 보기

| 단계 | 작업 | 핵심 |
|---|---|---|
| 0 | xgen 사전 작업 | workspace.mel + Set Project 로 프로젝트 인식 |
| 1 | Description → **Interactive Description** | `Generate > Convert to Interactive Groom…` (창 공란 Convert) |
| 2 | Interactive → **splineDescription** | Cache Export → 다시 Import 라운드트립 |
| 3 | splineDescription **그룹 해제** | GHM `Edit > Split Spline in Description Group` |
| 4 | splineDescription **그룹 재정리** | 시뮬 부위별 그룹화 (시뮬 OFF 부위도 별도 그룹) |
| 5 | **Guide Curve 생성** | 그룹별 시뮬 컨트롤러 = 인게임 strand. 적게 고를 것 |
| 6 | **Export** | GHM Component Table 등록 후 .abc export |
| 7 | **Card Hair 별도 Export** | 카드용 부분만 단일 그룹 .abc 로 한 번 더 |
| 8 | UE Import | [별도 문서](https://shiftupcorp.atlassian.net/wiki/spaces/SB2/pages/1608810847) |

### 시작 전 준비
- Maya 파일과 `[FileName].xgen` 은 같은 폴더에. 경로가 어긋나거나 네이밍이 전달받은 것에서 바뀌면 Description 은 보여도 strand 가 안 들어온다.
- 받은 Maya 파일에 Description 이 들어있는지 확인.
- 작업은 `SHIFT UP > Groom Hair Manager`(GHM) 툴로. UI 설명은 [Groom Hair Manager](https://shiftupcorp.atlassian.net/wiki/spaces/SB2/pages/285638786) 문서.

---

## 0. xgen 을 정상적으로 불러오기 위한 사전 작업

`[File]:경로` 안에 `workspace.mel` 이 있어야 해당 경로가 프로젝트로 인식된다.

1. File → Project Window
2. New → Location 을 `[File]:경로`, Current Project `[Folder]:이름`
3. Accept → Maya 가 `workspace.mel` + 하위 폴더(scenes, sourceimages…) 자동 생성
4. 기존 파일을 만들어진 폴더로 이동 (xgen 폴더 겹친다고 뜨면 덮어쓰기)

이후 `File → Set Project` 로 그 폴더를 Set → Maya data 를 열면 xgen 이 들어와 있다.

> **🔎 실측 — 자주 막히는 2가지**
> 1. 메모장으로 workspace.mel 을 만들면 `workspace.mel.txt` 로 저장돼 인식 안 됨. 확장자(.mel) 확인.
> 2. `.xgen` 파일 안에 옛 절대경로(`xgProjectPath`)가 박혀 있으면, 폴더 옮기고 Set Project 해도 Description 은 보이는데 **strand 가 0**. → `.xgen` 안의 경로를 현재 위치로 수정.

## 1. Description → Interactive Description

1. Description 선택 → `Generate > Convert to Interactive Groom…`
2. 변환 창은 **비운 채로** Convert → Interactive Description 생성 확인

Legacy XGen 은 밀도맵으로 절차적 생성이라 커브로 못 빼낸다. Interactive 로 바꿔야 가닥이 실제 스플라인이 돼 캐시·추출이 된다. 창을 비우고 Convert 하면 원본 밀도·모양 그대로 넘어온다.

## 2. Interactive Description → splineDescription (Cache 라운드트립)

GHM 은 캐시로 다시 불러온 Interactive Description 만 인식한다. 한 번 Cache Export → 다시 Import.

1. Interactive Description 선택 → `Generate > Cache > Export Cache`
2. **Current Frame**, **Write Final Width** 체크 후 Export → `[FileName].abc`. Write Final Width 빼먹으면 UE 에서 굵기가 기본값으로 잡혀 모양이 달라지니 꼭 체크.
3. 방금 구운 `.abc` 를 다시 Import → splineDescription 들어온 것 확인

## 3. splineDescription 그룹 해제

1. GHM Script 에서 splineDescription 전부 선택 → `Edit > Split Spline in Description Group`
2. 하위 Curve 들이 개체별로 분리된 것 확인

캐시를 다시 불러오면 여러 가닥이 한 transform 밑에 묶여 들어올 때가 있는데, group_id 는 커브(transform) 단위로 붙어서 묶인 채 두면 그룹 매핑이 꼬인다. 미리 개체별로 쪼개둔다.

## 4. splineDescription 그룹 재정리

엔진에서 시뮬 값을 다르게 줄 부위별로 그룹을 다시 묶는다. 앞머리·뒷머리·잔머리는 길이·움직임이 달라 같은 값으로 안 맞기 때문. **시뮬 안 거는 부분도 꼭 따로 그룹으로 빼둬야** UE 에서 그 그룹만 시뮬을 끌 수 있다.

그룹은 부위로 알아보기 쉽게 이름을 붙인다(앞머리·뒷머리·잔머리·시뮬OFF). 이름 공백·중복은 export 전 Validation 이 잡아준다.

> **🔎 실측 — 그룹명 일관성**
> strand 그룹명과 5번에서 만들 guide 그룹명을 **똑같이** 맞춰둘 것 (예: `Back_Hair` ↔ `Back_Hair_GuideCrv`). Component Table 등록은 수동이라 자동 매핑은 아니지만, 이름이 어긋나거나 오타가 있으면(`BackHair` / `Sub_Hiar` 등) 등록할 때 엉뚱한 그룹을 고르기 쉽다.

## 5. Guide Curve 생성

그룹마다 시뮬 컨트롤러로 쓸 Guide Curve 를 만든다. UE 는 가닥을 전부 시뮬 못 하니 그룹 대표 커브(Guide)만 시뮬하는데, SB2 에선 여기서 고른 Guide 가 **인게임 strand 로도 쓰인다**. 개수가 곧 움직임 디테일이자 비용이라, **그룹 모양을 대표할 만큼만 적게 고르는 게 포인트.**

1. Guide 로 쓸 **xgGuide 를 선택**한 뒤 Curve 로 생성 (`Generate > Curves from Guides`)

> **🔎 실측 — "no guides selected" 경고**
> 쪼개놓은 spline curve(`…SplineGrp*_Curve_*`, nurbsCurve)가 아니라 **xgGuide** 를 골라야 한다. Curve 로 분리된 가닥은 가이드로 안 잡힌다. (순서 문제 아님 = 선택 대상 문제)

만든 Guide Curve 도 그룹으로 정리하고, 모양을 해당 머리 중앙쪽으로 다듬으면 더 좋다. 가이드 커브가 너무 길면(CV 많으면) UE 임포터 한계로 잘릴 수 있으니 GHM `Edit > Auto Rebuild Long Name Curves` 로 CV 수를 줄인다.

## 6. Export

1. Outliner 에서 scalp_mesh 선택 → `Set Mesh`
2. `Reload UV Set` → 쓸 UV Set 선택
3. `Add New Component Set` 으로 그룹 수만큼 행 추가 → 각 행 우클릭으로 `desc_sources` / `guide_sources` 등록 (시뮬 OFF 그룹은 guide 비움)
4. `Table Validation` 으로 공백(빨강)·중복(노랑) 확인
5. `Export Groom Hair` → .abc

Scalp Mesh 는 root_uv 계산 기준. 커브 뿌리 위치를 두피 UV 로 환산해 박아두고, UE 바인딩 때 같은 UV Set 으로 위치를 맞춘다. export 하면 `groom_group_id` / `groom_guide` / `groom_root_uv` 가 abc 에 들어간다.

## 7. Card Hair 별도 Export

Card Hair 부분만 별도로 엔진에서 Card 로 베이킹해야 해서 더미 데이터가 필요. GHM 으로 **Card Hair 부분만 따로 한 번 더 Export** 한다.

> **🔎 실측 — 왜 Card Hair 만 따로 빼는가**
> UE 헤어 카드 생성기(HairCardGenerator, Experimental)는 **여러 그룹이 든 그룸에서 카드 베이킹이 실패**한다 — `IndexError: index N is out of bounds for axis 0 with size 1` (physics width 배열이 그룹 수와 안 맞아서). 그래서 Card Hair 는 **반드시 단일 그룹 .abc 로 따로** 내보내야 UE 카드 베이킹이 정상 동작한다 (단일 그룹이면 group 0 만 처리되어 에러 없음).
> (우회) 합친 그룸에서 굳이 하려면 카드 생성 다이얼로그의 **"Use group asset strand width" 체크 해제**로 에러는 피할 수 있으나, 별도 export 가 정석.

## 8. 이후 — UE Import

여기까지가 Maya 작업. 나온 .abc 를 UE 에 넣는다. UE5 Import 작업은 [별도 문서](https://shiftupcorp.atlassian.net/wiki/spaces/SB2/pages/1608810847) 참조.

> **UE 쪽 실측 메모 (UE 문서로 이관 권장)**
> - **좌우 미러**: 그룸이 좌우 반전돼 임포트되면 UE Groom import Conversion **Scale 좌우축 -1** (Maya RH→UE LH 핸디드니스. 그룸 커브는 winding 없어 반사가 남음). 옵션 변경하려면 `Reimport With New File…` 로 다이얼로그 띄워야 함(F5 Reimport 는 기존 설정 재사용).
> - **카드 품질/컬러**: 아틀라스 4096, # 카드/트라이앵글로 최적화 조절. 컬러는 카드 머티리얼을 strand 머티리얼(Melanin/Redness)에 맞춰야 함(베이크 텍스처 기반이라 따로 놂).
> - **GPU 시뮬은 카드로 안 줄어듦**: 카드는 렌더만 절감. Niagara 시뮬은 `EnableSimulation` / 가이드 수 / SubSteps×IterationCount 로 줄임.

## 관련 문서

- 상세 가이드(자동화 포함): [00_INDEX](00_INDEX.md) — PC01-Hair-Workflow 10편
- 사내 툴 명세: 메모리 `project_sb2_groom_hair_manager.md`
- 카드 파이프라인: 메모리 `reference_sb2_groom_card_pipeline.md`
- 라이브 파라미터: 메모리 `project_pc01_hair01_params.md`
