# 03. Guide Curves — xgGuide → Curve + 5그룹 매핑

Groom Hair Manager는 **Guide Curve 그룹**을 각 desc와 1:1로 페어링해서 abc에 굽는다. UE Groom Asset의 시뮬 가이드가 여기서 나옴.

> 출처: [Confluence — Groom Hair Manager](https://shiftupcorp.atlassian.net/wiki/spaces/SB2/pages/285638786/Groom+Hair+Manager) "사용 전 준비" 2번.

## 1. Guide Curve 개념

- UE5는 strand 전체를 시뮬 안 하고, 대표 **Guide Curve**만 시뮬 → strand에 interpolation 전파
- 한 그룹당 Guide Curve **1개 이상** (0개면 그 그룹은 시뮬 안 됨)
- 출처 옵션:
  - **xgGuide 변환** (권장, XGen에서 이미 가이드를 만들었을 때)
  - Spline Curve 신규 제작 (Maya 표준 NURBS curve)

PC_01은 원본 씬에 xgGuide가 있으므로 변환 사용.

## 2. xgGuide → Curve 변환

### 2.1 선택

Outliner에서 변환할 xgGuide 노드들 선택 (보통 desc별로 묶여 있음):

```mel
// 모든 xgGuide 선택
select -r `ls -type "xgmGuide" -type "xgGuide"`;
```

XGen 패널에서 가이드가 안 보이면 `Display > Guides` 토글 확인.

### 2.2 Curve로 변환

XGen Window → 가이드 우클릭 → `Curve > Curves from Guides`:

- 출력: 각 가이드당 1개 NURBS curve (transform + nurbsCurve shape)
- 생성 위치: 가이드와 동일한 world position
- 이름: `<guide>_curve1`, ... (자동)

### 2.3 검증

```mel
ls -type "nurbsCurve" | wc -l;
// 원본 가이드 개수와 일치해야 함
```

## 3. 5그룹 매핑

PC_01_Hair_01 현재 구성을 그대로 따라 신규본도 5그룹:

| group_id | 명칭 | desc 매칭 | 비고 |
|---|---|---|---|
| 0 | Hero | Size16, 메인 hero strand | BendStiffness 1.0 (강) |
| 1 | Size8 | Size8 보조 | StretchDamping 저감쇠 |
| 2 | SimOFF | EnableSim=False | 가이드 없어도 OK |
| 3 | Size4 | Size4 잔머리 | |
| 4 | 굵은 | Size4 + Thickness 0.5 | 뒷머리 그룹 |

### 3.1 그룹별 Guide Curve 묶음

각 desc가 시뮬 가이드로 쓸 Curve들을 그룹화:

```
PC_01_Hair_v2_root
├── descriptions/
│   ├── desc_grp0_hero_cache
│   ├── ...
├── guides/
│   ├── GuideCrv_grp0_hero/     ← Curve 묶음
│   │   ├── front_left_01
│   │   ├── front_right_01
│   │   └── ...
│   ├── GuideCrv_grp1_size8/
│   ├── (grp2 sim OFF — guides 폴더 없음 OK)
│   ├── GuideCrv_grp3_size4/
│   └── GuideCrv_grp4_thick/
└── scalp_mesh
```

`group_id 2 (SimOFF)`는 가이드 없어도 됨 — Groom Hair Manager Table에서 `guide_sources` 칼럼을 빈칸으로 두면 됨.

### 3.2 Curve 정돈 (권장)

Confluence "+ Guide Curve의 모양을 수정하여 Groom Hair의 중앙으로 배치":

- 각 그룹의 Curve가 해당 strand 묶음의 시각적 중앙을 지나도록 CV 편집
- 예: TwinTail 그룹이면 한 가닥 가이드를 twintail 중심선에 배치

도구:
- `Modify > Snap Together Tool` — 양 끝점 정렬
- `Curve > Rebuild Curve` (spans 16, degree 3) — CV 수 일관화
- 곡선 spans + degree > 255 케이스는 사내 툴의 **Auto Rebuild Long Name Curves**로 일괄 처리 (target_spans=32)

### 3.3 Curve 이름 컨벤션

| 패턴 | 예시 | 이유 |
|---|---|---|
| `<group>_<location>_<idx>` | `grp0_front_01`, `grp4_back_05` | 매칭 직관 |
| 중복 금지 | Validation에서 노란색 검출됨 | Table Validation 통과용 |
| 빈 이름 금지 | Validation에서 빨간색 검출됨 | 동상 |

## 4. Curve CV[0] = 스칼프 부착점

`groom_root_uv` 어트리뷰트는 **Curve의 CV[0] world position → scalp_mesh UV**로 자동 계산됨 (Groom Hair Manager utils.prepare_export).

→ Curve를 만들 때 CV[0]이 반드시 scalp_mesh 표면 위에 있어야 함. 떨어져 있으면 closest UV로 jump.

검증:
```mel
// 모든 가이드 curve의 CV[0]이 mesh와 가까운지
string $curves[] = `ls -type "nurbsCurve" -dag`;
for ($c in $curves) {
    float $cv0[] = `pointPosition -world ($c + ".cv[0]")`;
    print ($c + " CV[0]: " + $cv0[0] + " " + $cv0[1] + " " + $cv0[2] + "\n");
}
```

CV[0]이 모두 두피 메시 표면(±2cm) 안에 있어야 정상.

## 5. Split Spline (멀티 shape 케이스)

한 transform 아래 여러 shape (`nurbsCurveShape0`, `nurbsCurveShape1`...)이 있으면 abc export 시 group_id 매핑이 깨질 수 있음.

사내 툴 `SHIFTUP > Groom Hair Manager > Edit > Split Spline in Description Group` 실행:
- multi-shape transform → shape별 transform으로 분리
- batch_size=50씩 처리
- world matrix 보존

소요 시간: 200 curves 기준 약 30초.

## 6. 체크포인트

- [ ] 모든 xgGuide → Curve 변환 완료
- [ ] 5그룹 매핑 트리 정리 (group_id 0~4)
- [ ] Curve 이름 컨벤션 적용 (빈/중복 0)
- [ ] CV[0] scalp 표면 부착 확인
- [ ] Long curve(spans+degree>255) Rebuild 처리
- [ ] Multi-shape Split Spline 처리

OK면 → [04 Groom Hair Manager](04-Groom-Hair-Manager.md)
