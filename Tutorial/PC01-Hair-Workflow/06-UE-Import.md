# 06. UE Import — GroomAsset + Binding + Material 재연결

abc 파일을 UE 5.7로 임포트하고 BP_Sanjuk가 가리키는 Binding을 신규본으로 갈아끼운다.

## 1. P4 체크아웃

작업 대상 파일 사전 체크아웃 (UE 에디터 또는 P4V):

```
/Game/Art/Character/PC/PC_01/Equipment/Hair/PC_01_Hair_01/
  PC_01_Hair_01.uasset                ← 갈아끼울 본체
  PC_01_Hair_01_Binding.uasset        ← 재생성 필요
  
(읽기만, 체크아웃 불필요)
/Game/Art/Character/PC/PC_01/Blueprint/
  PC_01_BP_Sanjuk.uasset              ← 슬롯 재연결 시에만 체크아웃
```

⚠ `save_asset`은 P4 체크아웃 안 된 파일에선 실패함.

## 2. Groom Asset Import

### 2.1 Import 다이얼로그

Content Browser에서 `/Game/Art/Character/PC/PC_01/Equipment/Hair/PC_01_Hair_01/` 으로 이동 → `Import` 버튼:

| 옵션 | 값 |
|---|---|
| File | `C:/Users/SHIFTUP/Documents/maya/projects/PC_01_Hair/cache/PC_01_Hair_v2.abc` |
| Type | Groom |

`Groom Import Options` 창:

| 옵션 | 값 | 비고 |
|---|---|---|
| Conversion Settings | `Maya` (기본) | Z-up, 단위 cm |
| Convert (Scale) | `1.0` | Maya 단위가 cm면 그대로 |
| Override Skeletal Mesh | (체크 해제) | Binding은 별도 |
| Group Settings — Per-group Override | (체크) | 5그룹 개별 설정 가능 |

`Import` 클릭.

### 2.2 임포트 결과

```
PC_01_Hair_01.uasset (덮어쓰기 또는 신규)
```

기존 동명 자산이 있으면 다이얼로그 → `Replace`. 01편에서 백업해놓은 `_v1_backup`이 있으니 안전.

### 2.3 1차 검증

GroomAsset 더블클릭 → Editor 열림. 확인:

| 항목 | 기대 |
|---|---|
| HairGroupsInfo 개수 | **5** |
| GroupID 0~4 모두 보임 | ✅ |
| 각 그룹 Strands.NumCurves | > 0 |
| 각 그룹 Guides.NumGuides | > 0 (group 2 Sim OFF 제외) |
| Strands/Cards/Mesh LOD | 자동 채워짐 |

**🚨 Guides.NumGuides=0이면 05편 단수/복수 함정 발생.** 그땐 06편 중단, Maya로 복귀해서 abc 헤더 또는 사내 툴 패치.

## 3. Binding Asset 재생성

기존 `PC_01_Hair_01_Binding`은 옛 groom을 가리키고 있을 가능성. 새 GroomAsset에 맞춰 재바인딩.

### 3.1 신규 Binding 생성

Content Browser → 우클릭 → `Animation > Groom > Groom Binding`:

| 옵션 | 값 |
|---|---|
| Source Skeletal Mesh | (비움) |
| Target Skeletal Mesh | `CH_P_01_Head_001` |
| Source Groom Asset | (비움) |
| Target Groom Asset | `PC_01_Hair_01` (방금 import한 본) |
| Binding Type | `Skinning` |
| NumInterpolationPoints | 100 (기본) |

이름: 기존 `PC_01_Hair_01_Binding` **덮어쓰기** (Save Asset As → 동명 선택).

### 3.2 Build

Binding Editor → `Build` 클릭. 진행 후 Build Log에:

```
[GroomBinding] Build complete for PC_01_Hair_01_Binding (5 groups)
```

오류 없이 통과해야 함.

### 3.3 검증

Binding Asset 더블클릭 → Editor 표시:

| 항목 | 기대 |
|---|---|
| Target SkeletalMesh | `CH_P_01_Head_001` |
| Target GroomAsset | `PC_01_Hair_01` (신규) |
| Group Count | 5 |
| BindingType | `Skinning` |

## 4. Material 연결

`PC_01_Hair_Material` (MIC of `MA_Groomhair`)는 기존 그대로 사용. 신규 GroomAsset의 각 그룹에 슬롯 할당:

GroomAsset Editor → `Material Slots` 패널:

| Slot Index | Material |
|---|---|
| 0 (Hero) | `PC_01_Hair_Material` |
| 1 (Size8) | `PC_01_Hair_Material` |
| 2 (SimOFF) | `PC_01_Hair_Material` |
| 3 (Size4) | `PC_01_Hair_Material` |
| 4 (Thick) | `PC_01_Hair_Material` |

전부 같은 머티리얼 (PC_01은 단일 헤어 룩). 그룹별 룩이 달라지면 MIC 추가 생성 후 별도 슬롯.

## 5. BP_Sanjuk 슬롯 확인 (수정 없음)

`PC_01_BP_Sanjuk` → Hair_GEN_VARIABLE (SBCharacterGroomComponent):

| 슬롯 | 값 | 작업 |
|---|---|---|
| groom_asset | `PC_01_Hair_Sanjuk` (legacy) | 그대로 둠 |
| binding_asset | `PC_01_Hair_01_Binding` | **그대로 — 재바인딩으로 자동 갱신** |
| physics_asset | `Evie_Body_PhysicsAsset` | 그대로 |

→ Binding이 새 groom을 가리키므로 BP 변경 없이 신규 헤어 적용. PIE에서 즉시 검증 가능.

### 5.1 만약 BP가 groom_asset을 직접 참조한다면

`groom_asset` 필드를 `PC_01_Hair_01`로 변경 필요. 변경 절차:
1. BP 체크아웃
2. Components 패널 → Hair_GEN_VARIABLE 선택
3. Details → Groom → `Groom Asset` → 신규 `PC_01_Hair_01` 드래그
4. Compile + Save

⚠ Sanjuk legacy 슬롯도 빌드 dependency가 있을 수 있으므로 함부로 비우지 않음.

## 6. P4 add + 저장

신규 생성 파일:

```
PC_01_Hair_01.uasset                    ← Modified (replaced)
PC_01_Hair_01_Binding.uasset            ← Modified (rebuilt)
PC_01_Hair_01_v1_backup.uasset          ← Added (01편 백업)
PC_01_Hair_01_Binding_v1_backup.uasset  ← Added (01편 백업)
```

UE 에디터 `Save All` → P4 변경리스트에 추가. **이 시점에 Submit은 보류** — 07편 Physics 튜닝 후 한꺼번에.

## 7. 체크포인트

- [ ] abc Import → GroomAsset 생성, 5그룹 모두 보임
- [ ] **Guides.NumGuides > 0** (그룹 2 제외) ← ⚠ 가장 중요
- [ ] Binding 재생성 + Build 성공
- [ ] Material 슬롯 5개 모두 연결
- [ ] BP_Sanjuk PIE 진입 시 헤어 보임 (1차 시각 확인)
- [ ] P4 staging 추가 (Submit 아직)

OK면 → [07 Physics Tuning](07-Physics-Tuning.md)
