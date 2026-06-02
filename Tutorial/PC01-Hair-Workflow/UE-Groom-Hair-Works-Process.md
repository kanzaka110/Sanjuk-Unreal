# [UE5] Groom Hair Works Process (SB2 공식 SOP)

> Maya 에서 export 한 `.abc` 를 UE 로 가져와 캐릭터에 붙이고 시뮬까지 돌리는 과정.
> 원본: [Confluence — UE5 Groom Hair Works Process](https://shiftupcorp.atlassian.net/wiki/spaces/SB2/pages/1608810847/UE5+Groom+Hair+Works+Process) (작성자: 채승호 / SB2). 스크린샷은 원본 참조.
> Maya 쪽은 [Maya Groom Hair Works Process](Groom-Hair-Works-Process.md). `🔎 실측` = 2026-06 Evie(PC_01) 작업에서 확인·보강.

---

## 1. Groom Asset Import

Content Browser 에서 `.abc` import → GroomAsset 생성. Import 창 Conversion:
- **회전 (X=270, Y=0, Z=180)**
- **스케일 (X=-1, Y=1, Z=1)** ← 좌우 미러 보정

> **🔎 실측 — 왜 Scale X=-1 / 카드가 깨질 때**
> - Maya(오른손) → UE(왼손) 변환 시 그룸 커브는 winding 이 없어 좌우 반사가 남아 미러로 들어온다. **Scale 좌우축 -1** 로 상쇄.
> - 이미 import 한 에셋 Conversion 변경은 **우클릭 → `Reimport With New File…`** (같은 .abc 다시 선택)으로 옵션 창을 띄워야 함. F5 Reimport 는 기존 설정 재사용.
> - ⚠ 음수 스케일은 이후 **카드 베이킹 지오메트리를 깨뜨릴 수** 있다(찢어지는 메시). 심하면 7절 #카드↓·트라이앵글↑, 또는 미러를 Maya 에서 처리하고 UE 는 정상 스케일(X=1)로.

## 2. Import 후 확인

GroomAsset 더블클릭 → 그룹 점검:
- 그룹 수(HairGroupsInfo)가 Maya 와 같은지
- 각 그룹 strand 수 > 0
- 각 그룹 **NumGuides > 0** (시뮬 OFF 그룹은 0 OK)

> 시뮬 줄 그룹인데 **NumGuides=0** 이면 Maya 가이드 선택/어트리뷰트 오류 → Maya Guide Curve 단계부터 다시. (사내 툴 `groom_guide` 단수 vs Epic `groom_guides` 복수 차이도 의심 — 메모리 `project_sb2_groom_hair_manager`)

## 3. Binding 생성

Content Browser 우클릭 → `Animation > Groom > Groom Binding`:
- Target Skeletal Mesh: 붙일 캐릭터 머리 메시
- Target Groom Asset: import 한 GroomAsset
- **Binding Type: Skinning**

Build. **Maya root_uv 계산에 쓴 UV Set 과 같은 UV 기준**이어야 뿌리 위치가 맞는다. 헤어 갈아끼울 땐 Binding 도 새 GroomAsset 기준으로 다시 만든다(옛 groom 가리킬 수 있음).

## 4. 캐릭터에 붙이기

캐릭터 BP 의 Groom 컴포넌트에 지정 (※ SB2 는 `SBCharacterGroomComponent` 가능 — 컴포넌트명 확인):
- Groom Asset / Binding Asset / Physics Asset(관통 막기) / Material(그룹별 슬롯)

## 5. Physics 설정

각 그룹 Physics 섹션에서 솔버·파라미터. SB2 는 표준 솔버 대신 커스텀 **SBStableRodsSystem**(CosseratRods 파생) — 그룹마다 NiagaraSolver=CustomSolver, CustomSystem=SBStableRodsSystem. 디테일 값은 PC_01_Hair_01 참고.

> **🔎 실측 — 덜덜림(jitter) 잡는 순서 (PC_01 우선순위, 메모리 `feedback_groom_jitter_real_causes`)**
> 1. **ProjectStretch = False** (전 그룹) — 빠른 이동·회전·프레임드랍 폭발성 길이보정이 튐/덜덜 1순위 원인. 먼저 이것만 끄고 테스트.
> 2. **BendDamping 0.015~0.018** — 너무 낮으면(0.003~0.005) underdamped 덜덜. swing 살리려면 0.020 이하.
> 3. **Head 본 캡슐** 확인 — 없으면 strand 머리 통과 후 강한 push-out 진동. 캡슐 전까진 ProjectCollision=False.
> 4. 빠른 그룹 **SubSteps 8~16**. **IterationCount 는 jitter 용의자 아님**.

### Groom 값 요약 (UE5.7 GroomAssetPhysics.h 기준)

값 하나만 보지 말고 2~3개 조합으로 판단.

| 분류 | 값 | 핵심 |
|---|---|---|
| 솔버 | SubSteps / IterationCount | 빠른모션 안정 / 제약 엄격도. **둘의 곱 = 시뮬 비용** |
| 외력 | GravityVector.Z(-981) / AirDrag(0.1) | 처짐·복원 / 공기저항(올리면 빨리 멈춤). ※ -1·0 은 버그 |
| Bend | BendStiffness(0.01) / BendDamping(0.001) | 빳빳함 / 진동감쇠(너무 낮으면 덜덜) |
| Stretch | StretchStiffness(헤어 100~1000) / **ProjectStretch** | 길이유지 / **False 권장**(True 면 튐) |
| Collision | CollisionRadius / **ProjectCollision** | 관통방지 / head 캡슐 없으면 False |
| Strands | StrandsSize / Density / Thickness | 디테일·질량·굵기 |

**Component (SB2)**: bLocalSimulation=True / **LocalBone=head**(예민, 소수점 튜닝 필요 — 옛 "root" 폐기) / Linear·AngularVelocityScale(1.0, 낮추면 반응↓) / TeleportDistance(50) / WindScale.

## 6. SB2 시뮬 주의

- **bLocalSimulation = True** (False 면 심하게 튐)
- **LocalBone = head** — head 는 움직임에 매우 예민, root 는 둔감. head 라 소수점까지 디테일 튜닝 필요.
- Linear/Angular VelocityScale, TeleportDistance, WindScale 은 캐릭터별 튜닝값.

## 7. Card Import / 카드 생성

1. Card Hair 도 Hair 와 같이 Import → GroomAsset 열고 Hair GroomAsset 의 MI/스트랜드 정보 통일
2. Card → `Add Card Asset` → 그룹 인덱스 = Hair Group Index → **헤어 카드 생성**
3. 생성창: 아틀라스(**4096 or 2048** 권장, 클수록 디테일↑) / #카드 / #텍스처 / #트라이앵글 / Max Flyaway
   - **카드 수 많으면 메시 깨짐** → #카드↓ 또는 트라이앵글↑

> **🔎 실측 — 카드 베이킹은 단일 그룹 그룸에서**
> 여러 그룹이 든 그룸에서 헤어 카드 생성 → `IndexError: index N is out of bounds for axis 0 with size 1` (physics width 배열이 그룹 수와 불일치) 실패. **Card Hair 는 Maya 에서 별도 .abc 로 빼서** 단독 import 후 베이킹. (우회: 생성 다이얼로그 "Use group asset strand width" 체크 해제. 단 별도 export 가 정석.)

## 8. Card 적용

1. Hair GroomAsset 열고 `Add Card Asset` → 만든 메시·텍스처 넣기, Group Index 지정
2. LOD 창에서 해당 Group ID 에:
   - **Geometry Type : Cards**
   - **Binding Type : Skinning**
   - **Simulation : Disable**

> **🔎 실측 — 카드+가닥 동시 표시 / 색 매칭**
> - **동시 표시는 그룹 단위**로 갈린다 — 카드 줄 그룹만 Geometry Type=Cards, 나머지 Strands. 한 그룹 안 가닥↔카드는 LOD 교체라 동시 불가. (헤어 카드 생성은 기본이 그룸 전체 LOD 단위 → 그룹별 Geometry Type 으로 분리해야 동시 렌더)
> - **카드 색이 가닥과 다르게(붉/주황) 뜨면** 머티리얼 문제. 가닥=헤어 셰이딩(Melanin/Redness 런타임), 카드=베이크 텍스처+별도 머티리얼. 카드 머티리얼 색을 가닥 머티리얼에 맞춘다.

## 9. 렌더링 부하 / 시뮬 비용

카드는 **렌더링**만 줄이고 **시뮬(Niagara GPU)**은 안 줄인다. 시뮬은 EnableSimulation·가이드 수·SubSteps×IterationCount 로 줄인다(카드 그룹은 Simulation=Disable 이라 시뮬 0).

부하 측정 (헤어가 뷰포트/PIE 에 실제 렌더 중이어야 함):
- `stat unit` GPU ms → `r.HairStrands.Enable 0/1` 토글 차이 = 헤어 총 렌더 비용
- `ProfileGPU` 패스별 ms (HairStrandsVoxelize / Raster / HairCardsAndMeshes / Composition)
- `r.HairStrands.Strands 0` / `.Cards 0` 가닥 vs 카드, `r.HairStrands.Simulation 0` 시뮬 vs 렌더 분리

> 토글로 끈 뒤 머리가 사라지면 서브 토글을 다시 1 로 (`Enable 1` 만으론 안 됨). CVar 설정은 출력이 없는 게 정상이고, 측정은 stat/ProfileGPU 가 한다.

## 관련 문서

- Maya 쪽: [Maya Groom Hair Works Process](Groom-Hair-Works-Process.md)
- 상세: [06-UE-Import](06-UE-Import.md) / [07-Physics-Tuning](07-Physics-Tuning.md) / [08-PIE-Validation](08-PIE-Validation.md)
- 메모리: `project_pc01_hair01_params` / `reference_groom_physics_params` / `feedback_groom_jitter_real_causes` / `reference_sb2_groom_card_pipeline`
