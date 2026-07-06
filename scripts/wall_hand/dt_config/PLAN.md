# Wall Hand IK DataTable화 계획 (2026-07-06)

승인 스코프: 요청 3개(강도/시점/커브) + 추천 5개(접근오프셋·이격·정면폭·속도별오프셋·턴차단). 커브 = 진짜 CurveFloat.

## 신규 에셋 (폴더: /Game/Art/Character/PC/PC_01/Blueprint/WallHandIK/)

| 에셋 | 타입 | 생성 수단 |
|---|---|---|
| S_WallHandIKConfig | UserDefinedStruct | Monolith create_user_defined_struct |
| DT_WallHandIK | DataTable (row=위 구조체) | Monolith create_data_table + add_data_table_row("Default") |
| C_WallHandAttach | CurveFloat | py 콘솔(AssetTools) — 키 (0,0)(1,1) 시딩 시도 |
| C_WallHandRelease | CurveFloat | 〃 |

## S_WallHandIKConfig 필드 (현행 등가 기본값)

| 필드 | 기본값 | 현행 위치 |
|---|---|---|
| IKStrengthMax | 1.0 | (신규 — 하드코딩 1.0) |
| AttachStartDist | 60.0 | BP CF_21/CF_0 InRangeA |
| AttachFullDist | 45.0 | BP CF_21 InRangeB |
| FrontFullDist | 10.0 | BP CF_0 InRangeB |
| AttachDuration | 0.55 | (환산: FInterp 3→12 가속 등가) |
| ReleaseDuration | 0.65 | (환산: FInterp 4.5 등가, 저속) |
| ReleaseDurationFast | 0.4 | (환산: FInterp 8 등가, 질주 450+) |
| TurnReleaseDuration | 0.12 | (환산: FInterp 28 등가) |
| AttachCurve | C_WallHandAttach | (신규) |
| ReleaseCurve | C_WallHandRelease | (신규) |
| ApproachOffsetDist | 20.0 | ABP var WHApproachDist |
| StandoffR | 4.0 | BP CF_101.A |
| StandoffL | 2.0 | BP CF_101.B |
| FrontHandHalfWidth | 12.4 | BP CF_26.B / CF_40.B |
| FrontHandHeight | 12.4 | BP CF_34.Z(−) / CF_41.Z(+) — 부호는 그래프서 |
| FrontStandoff | 2.5 | BP CF_77.B |
| FwdOffsetJog | 5.0 | BP CF_1 (±) |
| FwdOffsetRun | 20.0 | BP CF_30 (±) |
| FwdOffsetSprint | 60.0 | BP CF_64 (±) |
| HeightOffsetRun | −5.0 | BP CF_32 (양측 동일) |
| HeightOffsetSprint | −10.0 | BP CF_31 (양측 동일) |
| TurnBlockHold | 0.8 | ABP IsWallHandAllowed CF_17.A |

## 배선

**PC_01_BP UpdateWallHandIK**: 함수 head에 GetDataTableRow(DT, "Default") exec 스플라이스 → Break S_WallHandIKConfig → 소비 핀 직결(변수 불요). ± 부호는 Multiply(−1) 노드 추가. 대상 핀 = 위 표의 BP 칸 전부.

**PC_01_ABP SetSmoothedWallHandAlpha** (전 경로 매 프레임 호출 — 유일 read 지점):
1. head에 GetDataTableRow 스플라이스 → Break
2. Set WHApproachDist / Set WHTurnBlockHold(신규 var — IsWallHandAllowed CF_17.A가 참조)
3. **커브 리팩터**: 신규 var `WHBlendT`(0..1 진행도)
   - 목표 T = 기존 알파램프 타겟(WallHandAlphaTarget, 거리 기반 0..1)
   - WHBlendT ← MoveTowards(WHBlendT, targetT, dt/Duration) — Duration: 상승=AttachDuration / 하강=(턴블록? TurnReleaseDuration : MapRange(Speed2D,100→450, ReleaseDuration→ReleaseDurationFast))
   - WallHandAlpha = (상승? AttachCurve : ReleaseCurve).GetFloatValue(WHBlendT)  ← pure 호출
   - 내부 수학(접근오프셋/엔게이지)은 계속 WallHandAlpha(0..1) 사용
4. **강도 적용은 CR 핸드오프에서만**: 신규 var `WHAlphaScaled = WallHandAlpha × IKStrengthMax` → GetWallHandState의 Alpha 출력을 WHAlphaScaled로 교체 (내부 수학 불변 — 강도<1이어도 접근오프셋 영구잔류 버그 없음)
5. 구 FInterpTo 체인(CF_16 MapRange 3→12, CF_6 4.5→8, CF_8 Select 28) 제거

**중간 반전(붙다 떼기) 처리**: Attach/Release 커브 양 끝 (0,0)(1,1) 고정 전제. 반전 시 커브 차이만큼 미세 점프 가능 → 잔여 시 post FInterpTo(20) 필터 추가 검토 (1차는 미적용).

## 리스크 / 미검증
- K2Node_GetDataTableRow를 Monolith add_node가 지원하는지 미검증 → 안 되면 사용자 수동 노드 2개 + 내가 배선
- CurveFloat 키 시딩 py API 미검증 → 안 되면 사용자가 커브 에디터서 (0,0)(1,1) 수동 2키
- P4: 신규 에셋 4개 add — save 시 체크아웃 모달 리스크는 신규 add라 낮음
- UpdateVariables(348노드)는 건드리지 않음 — read 지점을 alpha 함수 내부로 한정
