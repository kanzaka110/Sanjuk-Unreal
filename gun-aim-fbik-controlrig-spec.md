# PC_01 Gun 모드 조준 정밀화 — 전용 FBIK Control Rig 빌드 스펙

작성 2026-06-15. AimOffset(coarse) 위에 얹는 정밀 보정 CR. `PC_01_CtrlRig_LookAt` 재사용 안 함 — **전용** `PC_01_CtrlRig_GunAim` 신규.

## 목표
AimOffset은 상체를 "대략" 조준 방향으로 돌리는 BlendSpace라 총구가 조준선과 정확히 안 맞는다(피치 극단·근거리 시차). 그 위에 Control Rig 포스트 보정으로 **척추(spine_01~03) + 왼팔(드론 장착)**을 풀어 **총구가 조준선 라인트레이스 히트지점을 정확히 향하게** 만든다. 일정 각 초과 시 보정을 클램프하고 캐릭터 turn-in-place가 넘겨받는다.

## 확정 사항
- 드론 장착 = **왼손**. 솔브 체인 `upperarm_l → lowerarm_l → hand_l`, 무기 본 `lowerarm_weapon_02_l`.
- 조준 타겟 = **화면중앙 라인트레이스 히트지점**(월드).
- 보정 범위 = **척추 + 왼팔**.
- 게이트 = IsAiming(StancePhase==2).

## 스켈레톤 (실측)
- 척추: `spine_01→02→03→04→05`. 보정 분산은 spine_01/02/03 권장.
- 왼팔: `clavicle_l → upperarm_l → lowerarm_l → hand_l` (+twist/corrective).
- 무기 본: `lowerarm_weapon_02_l` (총구/조준 기준 후보. 드론이 별도 소켓이면 그 transform으로 교체).

## CR 입력 변수 (ABP에서 주입)
| 변수 | 타입 | 의미 |
|------|------|------|
| `AimTargetWorld` | FVector | 화면중앙 라인트레이스 히트 월드좌표 (BP가 매프레임 계산) |
| `Alpha` | float 0~1 | 보정 강도 = IsAiming 스무딩(진입/해제 ~0.15s 블렌드) |
| `MaxYawDeg` | float | 좌우 클램프(예 50°). 초과분은 솔브 안 함 → turn-in-place |
| `MaxPitchDeg` | float | 상하 클램프(예 45°) |
| `MuzzleBone` | FName(상수) | 기본 `lowerarm_weapon_02_l` |

## Forwards Solve 로직 (RigVM, CR 에디터에서 작성)
1. **Early-out**: `Alpha <= 0` 이면 솔브 스킵(입력 포즈 그대로). 성능.
2. **조준 델타 계산**: 기준점(spine_03 또는 muzzle 위치)에서 `AimTargetWorld`로의 방향 → 현재 상체 forward와의 yaw/pitch 차(residual). AimOffset이 이미 대부분 처리했으므로 여기선 **잔차만** 보정.
3. **Yaw/Pitch 클램프**: residual을 `±MaxYawDeg / ±MaxPitchDeg`로 clamp. 클램프된 초과분은 버림(turn-in-place 담당).
4. **척추 분산 Aim**: clamp된 보정각을 spine_01/02/03에 분산 적용(가중 예 0.2/0.3/0.5). Aim(Aim Item) 또는 가산 회전. `Alpha`로 블렌드.
5. **왼팔 IK**: `upperarm_l→lowerarm_l→hand_l` Two-Bone IK(또는 Basic IK):
   - 목표: `MuzzleBone`(`lowerarm_weapon_02_l`)의 forward 축이 `AimTargetWorld`를 향하도록.
   - 방식: ① hand/weapon을 타겟으로 Aim 회전 → ② Two-Bone IK로 팔꿈치 자연스럽게 유지(pole vector = 안정적 팔꿈치 방향). `Alpha` 블렌드.
6. **블렌드**: 모든 보정은 입력 포즈 ↔ 솔브 포즈를 `Alpha`로 보간(스냅 방지).
7. **클램프 동반**: 솔브가 한계각 초과를 요구하면 4·5단계가 clamp된 각까지만 적용.

## ABP 통합 (Monolith로 가능 — 제가 처리)
1. **새 변수** `AimTargetWorld`(FVector), `GunAimAlpha`(float).
   - `GunAimAlpha` = IsAiming을 FInterpTo(0↔1, ~0.15s)로 스무딩.
   - `AimTargetWorld` ← BP가 set(아래 BP측).
2. **CR 노드 배치**: `PC_01_AnimLayer_IK`(IK 레이어)에서 **AimOffset 출력 뒤**에 Control Rig 노드(`PC_01_CtrlRig_GunAim`) 삽입. 풋클램프 CR과 같은 패턴. 입력 핀에 `AimTargetWorld`/`GunAimAlpha`/Max* 배선.
   - 대안: SkeletalMesh post-process CR로. (IK 레이어 방식이 ABP 변수 배선 쉬움)

## BP측 — 조준 타겟 라인트레이스 (사용자/제가 BP 그래프로)
PC_01_BP(또는 카메라/컨트롤러)에서 매프레임:
1. 카메라 위치 + 카메라 forward(화면중앙)로 LineTrace, MaxDist(예 10000).
2. 히트 시 `HitLocation`, 미스 시 `CamLoc + Fwd*MaxDist` → `AimTargetWorld`.
3. AnimInstance(`PC_01_ABP`)에 set (스레드세이프 변수).
- 시차 보정: 카메라-총구 위치차 때문에 "카메라 방향"이 아닌 "히트지점"을 향해야 총구가 조준선에 맞음.

## 클램프 ↔ turn-in-place 연계
- `MaxYawDeg`(~50°) 초과 = 상체만으론 못 조준 → 캐릭터가 돌아야 함. 이건 별도 "원거리 회전 임계각"(SBCharacter C++, SB2-6081 동형) 작업과 맞물림. CR은 클램프까지만, 회전은 캐릭터측.

## 왜 전용(LookAt 재사용 안 함)
- gun 전용 튜닝 격리, 기존 LookAt CR(타 용도) 간섭 없음, 독립 on/off.

## 구현 분담
- ✅ Monolith로 제가: 새 변수, GunAimAlpha 스무딩, CR 노드 배선/게이팅, BP 라인트레이스 그래프(가능 범위).
- ⚠ CR 에디터 수동(제가 단계 안내): `PC_01_CtrlRig_GunAim` RigVM 솔버(2~6단계). Monolith는 RigVM from-scratch 불가.
- 에셋 생성: CR 에디터에서 `PC_01_Body_001_Skeleton` 우클릭 → Create → Control Rig, 이름 `PC_01_CtrlRig_GunAim` (또는 Monolith 생성 가능 시 제가).

## 클린 빌드 (6/15 채택) — 내장 `Aim` 노드 기반 (LookAt 복사 대신)
조준=회전 정렬이라 내장 `Aim` 노드가 FBIK(위치 IK)보다 정확·간결. LookAt 32노드 → Aim 2노드.
- 변수 재사용: AimTargetWorld, EnableLookAt, Weight.
- **v1**: Forwards Solve에서 `Aim` 노드 2개. ①Item=spine_03, Primary.Target=AimTargetWorld(Kind=Location), Primary.Axis=spine forward, Weight=0.5. ②Item=lowerarm_weapon_02_l, 총구 forward, Weight=1.0. Execute: Begin→Aim→Aim. 프리뷰에서 축/방향 검증.
- **v2**: 각 Weight를 Select(EnableLookAt ? w : 0)로 게이트.
- **v3**: 게이트 Weight를 Interpolate로 스무딩(팝 방지) + 과회전은 캐릭터 turn-in-place 위임.
- 분담: 노드배치=CR에디터(add_node 크래시), 검증/값튜닝=Monolith(set_pin_default/set_variable_defaults/export_graph/remove_node 안전확인).
- ⚠ LookAt 함수는 비웠음(사용자). 이 클린 버전은 Forwards Solve에 직접 Aim 노드(별도 LookAt 함수 불필요).

## (구) RigVM 빌드 가이드 — SB2 AimBoneMath 패턴 (CR 에디터)
에셋: `/Game/Art/Character/PC/PC_01/Body/PC_01_Body_001/Rig/PC_01_GunModeAim_CtrlRig`
기존 `PC_01_CtrlRig_LookAt::LookAt` 함수에서 추출한 SB2 표준 패턴을 그대로 차용(재사용 아님, 패턴 복제).

### SB2 LookAt 1-본 패턴 (참고 원형)
```
Get Transform(Bone, global)
  → AimBoneMath (Aim Math: bone forward → Location 타겟)
  → To Euler → Clamp(Pitch/Yaw/Roll) → From Euler   [각도 제한]
  → AlphaInterp / Interpolate (Weight·Enable 블렌드)  [스무딩]
  → Set Transform(Bone, global)
+ If(EnableLookAt) 게이트, InterpSpeed(Start/End)로 진입/해제 부드럽게
```

### CR 변수 (Variables 패널에 생성, ABP가 핀으로 주입)
- `AimTargetWorld` (Vector) — 조준 타겟(=AimBoneMath Location)
- `Alpha` (Float) — 전체 강도(ABP GunAimAlpha)
- `Clamp_Yaw` `Clamp_Pitch` (Float) — 한계각(예 50/45)
- (척추 분산 가중치는 그래프 상수로)

### Forwards Solve 구성 (위 1-본 그룹을 본별로 반복)
순서 = 부모→자식 (회전 누적 자연스럽게):
1. **spine_01** : AimBoneMath(forward→AimTargetWorld) → Clamp → AlphaInterp(Alpha×0.2) → Set. 
2. **spine_02** : 〃 (Alpha×0.3)
3. **spine_03** : 〃 (Alpha×0.5)
4. **lowerarm_weapon_02_l** (총구 본) : AimBoneMath(총구 forward축 → AimTargetWorld) → Clamp → AlphaInterp(Alpha×1.0) → Set. ← 총구 정밀 정렬 핵심.
   - (선택) 팔이 부자연스러우면 `upperarm_l→lowerarm_l→hand_l` Two Bone IK 추가로 팔꿈치 보정.
- **축 주의**: AimBoneMath의 Primary(Aim) 축 = 각 본의 forward(스켈레톤 기준 확인 필요), Secondary(Up) = 안정 up. TA가 본 축 보고 설정.
- **Alpha=0 분기**: If(Alpha>0)로 전체 솔브 스킵(성능) 또는 AlphaInterp가 0 처리.

### 빌드 순서 권장
먼저 **spine_03 + lowerarm_weapon_02_l 2개만** 만들어 PIE 확인(최소 동작) → 됐으면 spine_01/02 분산 추가 → 클램프·Alpha 튜닝.

## 검증 (PIE)
- 조준선을 적/벽 여러 지점에 → 총구가 정확히 조준선 향하는지.
- 진입/해제 시 스냅 없는지(Alpha 블렌드).
- 한계각 초과 시 과회전 없이 클램프 + 캐릭터 턴으로 넘어가는지.
- 이동 중 조준 품질(척추 분산이 걷기와 충돌 안 하는지).
