# SB2 LocoTransit 스탠스 커브 채널 추가 — 구현 가이드

작성일: 2026-04-16  
문제: 이동 중 180° 회전 시 Fist_Battle 스탠스가 일반 걷기로 잠깐 바뀌었다 복귀  
원인: `PSS_SM_LocoTransitions`에 스탠스 구분 채널 없음 → MM이 스탠스 무시하고 최저 비용 포즈 선택

---

## 전체 흐름

```
[1단계] 커브 이름 확인
[2단계] Fist_Battle Transit 애니메이션에 커브 굽기
[3단계] PSS_SM_LocoTransitions에 Curve 채널 추가
[4단계] ABP BlueprintThreadSafeUpdateAnimation에서 커브 값 공급
[5단계] PSD_GroundMovingTransit / PSD_GroundIdleTransit 리빌드
[6단계] 검증
```

---

## 1단계: 커브 이름 확인

`PSS_SM_LocoLoops`가 `PoseSearchFeatureChannel_Curve (cardinality=1)`만 사용함.  
이 커브 이름이 스탠스 구분에 쓰이는 기준값 → **LocoTransitions에 동일 커브 추가할 것.**

**에디터에서 확인:**
```
Content Browser → /Game/Art/Character/PC/PC_01/MotionMatching/PSS/PSS_SM_LocoLoops
→ Channels[0]: PoseSearchFeatureChannel_Curve
→ CurveName 확인 (예: "LocomotionStance", "AnimStance", "GaitMode" 등)
```

> 이하 가이드에서는 커브 이름을 **`LocomotionStance`** 로 표기.  
> 실제 이름으로 교체할 것.

---

## 2단계: Fist_Battle Transit 애니메이션에 커브 굽기

### 커브 값 정의

| 스탠스 | LocomotionStance 커브 값 |
|--------|-------------------------|
| 일반 (Normal) | 0.0 |
| Fist_Battle | 1.0 |

> LocoLoops 애니메이션에서 이미 사용 중인 값을 그대로 따를 것.

### 적용 대상 애니메이션 (PSD_GroundMovingTransit의 Fist_Battle 시퀀스)

`PSD_GroundMovingTransit`을 열어 Fist_Battle 포함 시퀀스 전체 확인.  
아래는 예상 목록 (실제 DB에서 필터로 "Fist_Battle" 검색):

```
P_Player_Fist_Battle_*_Start_*
P_Player_Fist_Battle_Pivot_*
P_Player_Fist_Battle_Stop_*
... (DB에서 직접 확인)
```

### Python 스크립트로 일괄 커브 추가 (로컬 PC에서 실행)

```python
# scripts/add_stance_curve_to_fist_battle.py
# 실행 위치: 로컬 PC, runreal 또는 UE Python 콘솔

import unreal

CURVE_NAME = "LocomotionStance"   # ← 1단계에서 확인한 실제 이름으로 교체
STANCE_VALUE = 1.0                # Fist_Battle 값

# PSD_GroundMovingTransit 열어서 Fist_Battle 시퀀스 목록 수동 지정
# 또는 아래처럼 에셋 이름으로 필터링
ASSET_PATH = "/Game/Art/Character/PC/PC_01/MotionMatching/Animation/"

asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
all_anim_assets = asset_registry.get_assets_by_path(ASSET_PATH, recursive=True)

controller = unreal.AnimSequenceEditorSubsystem()

for asset_data in all_anim_assets:
    if "Fist_Battle" not in str(asset_data.asset_name):
        continue
    if asset_data.asset_class_path.asset_name != "AnimSequence":
        continue

    anim_seq = asset_data.get_asset()
    if not anim_seq:
        continue

    # 커브 추가 또는 덮어쓰기
    curve_id = unreal.SmartName()
    curve_id.curve_name = CURVE_NAME

    # 커브가 없으면 추가
    if not anim_seq.find_curve_identifier(CURVE_NAME, unreal.RawCurveTrackTypes.RCT_FLOAT):
        unreal.AnimationLibrary.add_curve(anim_seq, CURVE_NAME)

    # 전체 구간을 stance 값으로 굽기
    length = anim_seq.get_play_length()
    unreal.AnimationLibrary.add_float_curve_key(anim_seq, CURVE_NAME, 0.0, STANCE_VALUE)
    unreal.AnimationLibrary.add_float_curve_key(anim_seq, CURVE_NAME, length, STANCE_VALUE)

    print(f"[OK] {asset_data.asset_name}")

print("완료")
```

**일반 스탠스 애니메이션에도 커브가 없으면 0.0으로 추가** (MM 쿼리 시 기본값 0 → 매칭됨):
```python
# 일반 Transit 애니메이션: LocomotionStance = 0.0 으로 동일하게 처리
# (없으면 MM이 쿼리 커브 기본값 0과 차이가 커져 비용 왜곡 가능)
```

---

## 3단계: PSS_SM_LocoTransitions에 Curve 채널 추가

### 에디터 조작

```
Content Browser → PSS_SM_LocoTransitions 더블클릭
→ Channels 배열에 + 클릭
→ PoseSearchFeatureChannel_Curve 선택
→ 설정:
    CurveName:  LocomotionStance   ← 1단계 커브 이름
    Weight:     10.0               ← 아래 가중치 설명 참고
    OriginTime: 0.0                ← 현재 포즈 기준
```

### 가중치 설정 기준

현재 스키마 cardinality = 34 (Group 12 + Trajectory 22)  
`DataPreprocessor = Normalize` 사용 → 전체를 정규화해서 비교

| Weight | 동작 |
|--------|------|
| 1.0 | 포즈 1차원과 동일 중요도 → 스탠스 구분 약함 |
| 5.0 | 중간 → 같은 스탠스를 선호하되 포즈/궤적 압도하지 않음 |
| **10.0** | 권장 시작값 → 스탠스 다르면 사실상 선택 안 됨 |
| 20.0+ | 스탠스를 하드 필터처럼 사용 → 포즈 품질 희생 가능 |

> **10.0으로 시작**, PIE에서 테스트 후 조정.  
> 잘못된 애니메이션이 계속 선택되면 올리고, 포즈 팝이 생기면 낮춤.

---

## 4단계: ABP 쿼리 업데이트

`BlueprintThreadSafeUpdateAnimation` 그래프에서 Motion Matching 노드로 전달하는 **쿼리 트레이스에 커브 값 공급** 확인.

```
PC_01_ABP → BlueprintThreadSafeUpdateAnimation 그래프
→ Motion Matching 노드 또는 BlendStack 노드 선택
→ "Query" 입력 확인
```

### 쿼리에 커브 값 주입 방법

PoseSearchFeatureChannel_Curve는 **런타임 쿼리 시 현재 AnimInstance의 커브 값을 자동으로 읽음**.

따라서 `BlueprintThreadSafeUpdateAnimation`에서:

```
AnimStance 변수(byte) → float 변환 → SetCurveValue("LocomotionStance", value) 호출
```

또는 더 간단하게:

```
PC_01_ABP EventGraph 또는 BlueprintUpdateAnimation:
→ Get AnimStance → Switch on EAnimStance
   → Normal:     Set Curve Value("LocomotionStance", 0.0)
   → FistBattle: Set Curve Value("LocomotionStance", 1.0)
```

> **주의**: `SetCurveValue`는 Game Thread에서만 호출 가능.  
> `BlueprintThreadSafeUpdateAnimation`에서는 직접 호출 불가 → `EventGraph`의 `Event Blueprint Update Animation`에서 호출할 것.

---

## 5단계: DB 리빌드

```
Content Browser → PSD_GroundMovingTransit 우클릭 → Resave
→ 에디터가 자동으로 재인덱싱

PSD_GroundIdleTransit도 동일 (Turn In Place 포함)
```

**스키마 변경 후 반드시 두 DB 모두 리빌드.**  
리빌드 완료는 에디터 Output Log에서 확인:
```
LogPoseSearch: Indexing PSD_GroundMovingTransit... done (211 assets)
```

---

## 6단계: 검증

### PIE 런타임 확인

```
콘솔: showdebug Animation
→ 캐릭터 선택 → Motion Matching 패널 확인
→ 180° 회전 시 선택된 애니메이션 이름 관찰
   ✅ P_Player_Fist_Battle_Pivot_* 선택
   ❌ P_Player_Pivot_* (일반 Walk) 선택 → Weight 올리기
```

### 비용 디버그 확인

```
콘솔: PoserSearch.DebugVisualization 1
→ 현재 선택 포즈와 후보군 시각화
→ Fist_Battle 시퀀스의 비용이 일반 시퀀스보다 낮은지 확인
```

---

## 변경 파일 요약

| 파일 | 변경 내용 |
|------|----------|
| `PSS_SM_LocoTransitions` | Curve 채널 추가 (LocomotionStance, Weight=10) |
| `Fist_Battle Transit 애니메이션 N개` | LocomotionStance 커브 = 1.0 굽기 |
| `일반 Transit 애니메이션 N개` | LocomotionStance 커브 = 0.0 굽기 (선택사항, 권장) |
| `PC_01_ABP EventGraph` | AnimStance → SetCurveValue("LocomotionStance") |
| `PSD_GroundMovingTransit` | 리빌드 |
| `PSD_GroundIdleTransit` | 리빌드 |

---

## 예상 결과

| 전 | 후 |
|----|-----|
| 180° 회전 → 일반 Pivot 재생 (0.2~0.5초) → Fist_Battle 복귀 | 180° 회전 → Fist_Battle Pivot 직접 선택 |
| 스탠스 팝 발생 | 스탠스 유지 |
