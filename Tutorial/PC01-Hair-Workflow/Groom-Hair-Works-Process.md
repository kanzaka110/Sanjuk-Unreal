# Groom Hair Works Process (SB2 공식 SOP)

> XGen Groom 을 UE5 Groom Asset 임포트용 Alembic 으로 정리·Export 하는 **사내 표준 작업 절차**.
> 원본: [Confluence — Groom Hair Works Process](https://shiftupcorp.atlassian.net/wiki/spaces/SB2/pages/1608908814/Groom+Hair+Works+Process) (작성자: 채승호 / SB2)
> 이 문서는 원본을 오타 수정 + 구조화한 정리본. 스크린샷은 원본 페이지 참조.

---

## 한눈에 보기

| 단계 | 작업 | 핵심 |
|---|---|---|
| 0 | 준비·확인 | Maya Data + `.xgen` 같은 폴더 / Description 존재 확인 |
| 1 | Description → **Interactive Description** | `Generate > Convert to Interactive Groom…` (창 **공란**으로 Convert) |
| 2 | Interactive Description → **splineDescription** | Cache **Export → 다시 Import** 라운드트립 |
| 3 | splineDescription **그룹 해제** | Groom Hair Manager → `Edit > Split Spline in Description Group` |
| 4 | splineDescription **그룹 재정리** | 시뮬 부위별로 그룹화 (**시뮬 OFF 부위도 별도 그룹**) |
| 5 | **Guide Curve 생성** | 그룹별 시뮬 컨트롤러. **과다 선택 금지** (= 인게임 strand) |
| 6 | **Export** | Groom Hair Manager 로 그룹 + hair 등록 후 Export |

### 메뉴 경로 빠른 참조

| 작업 | 경로 |
|---|---|
| Interactive 변환 | `Generate > Convert to Interactive Groom…` |
| Cache Export | `Generate > Cache > Export Cache` |
| 그룹 해제(Split) | `Groom Hair Manager > Edit > Split Spline in Description Group` |
| 최종 Export | `Groom Hair Manager > Export` |

---

## 0. 시작 전 준비 및 확인

- **Maya Data 와 `[FileName].xgen` 데이터는 같은 폴더 안에 배치**
  - ⚠ 경로가 어긋나면 Description 은 보여도 strand 가 안 들어옴 (`${PROJECT}` 미해석).
- 모델링 팀에서 온 Maya Data 안에 **Description 이 들어가 있는지 확인**.

## 1. Description → Interactive Description 변환

1. Description 선택 → `Generate > Convert to Interactive Groom…` 선택
2. `Convert to Interactive Groom…` 창에서 **공란으로 Convert** 선택
3. **Interactive Description** 이 생성된 것을 확인

> 📷 *원본 스크린샷: 변환 메뉴 / 변환 창 / 생성 결과*

## 2. Interactive Description → splineDescription 변환

Interactive Description 을 Cache 로 Export 한 후 **다시 Import** 해야 한다.

1. 생성된 Interactive Description 선택 → `Generate > Cache > Export Cache` 선택
2. 해당 옵션들을 활성화한 후 Export
   - ✅ 정상 Export 시 `[FileName].abc` 데이터 생성 확인
3. Export 된 `[FileName].abc` 를 다시 Import
4. ✅ 정상 Import 시 **splineDescription** 이 들어와 있는 것 확인

> 📷 *원본 스크린샷: Export Cache 옵션 / Import / splineDescription 결과*

## 3. splineDescription 그룹 해제

1. Groom Hair Manager Script 를 연 후 splineDescription 을 **모두 선택 → Group 해제**
   - `Groom Hair Manager > Edit > Split Spline in Description Group`
2. splineDescription 하위의 Curve 가 그룹 해제되어 **각 개체별로 분리**된 것을 확인

> 📷 *원본 스크린샷: Split 메뉴 / 분리된 Curve*

## 4. splineDescription 그룹 재정리

- 엔진으로 가져갔을 때 **헤어 시뮬레이션 값을 다르게 주고 싶은 부위별**로 splineDescription Group 을 재정리한다.
- ⚠ **시뮬레이션이 적용 안 될 부분도 꼭 별도 Group 으로 정리**해야 한다.

> 📷 *원본 스크린샷: 부위별 그룹 트리*

## 5. Guide Curve 생성

- 각 Group 별로 **시뮬레이션 컨트롤러로 쓰일 Guide Curve** 를 만들어 주어야 한다.
- ⚠ **여기서 선택되는 Guide Curve 가 실제 인게임 strand 가 되므로 너무 많이 선택하면 안 된다.**
- 생성된 Guide Curve 들도 splineDescription 들처럼 **Group 정리**를 해준다.

> 📷 *원본 스크린샷: Guide Curve 생성 / 그룹 정리*

## 6. Export

- Groom Hair Manager 를 사용해 Export 진행한다.
  - 생성한 **각 그룹별로 등록 + hair 등록** 후 익스포트 진행한다.

> 📷 *원본 스크린샷: Groom Hair Manager Export 화면*

---

## 부록 — 자주 막히는 지점

- **5단계 "Curves from Guides: no guides selected" 경고**
  XGen 가이드(`xgGuide`)가 **선택돼 있어야** 동작한다. 분리된 스플라인 커브
  (`...SplineGrp*_Curve_*`, shape = `nurbsCurve`)는 가이드가 아니므로 선택해도 걸러진다.
  → 명령은 현재 Maya 선택에서 **가이드 shape 만** 필터링(`xgmSelectedGuides`)하므로,
  실제 `xgGuide` 가이드를 먼저 선택할 것. (순서 문제 아님 = 선택 대상 문제)

## 관련 문서

- 상세 가이드(자동화 포함): [00_INDEX](00_INDEX.md) — PC01-Hair-Workflow 10편
- 사내 툴 명세: 메모리 `project_sb2_groom_hair_manager.md`
- 라이브 파라미터: 메모리 `project_pc01_hair01_params.md`
