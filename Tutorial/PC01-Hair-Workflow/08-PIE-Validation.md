# 08. PIE Validation — 실제 인게임 검증 + 잔존 이슈 체크 + Hermes 옵션

UE 에디터/PIE에서 신규 헤어가 실제로 의도대로 거동하는지 시각·로그·스크린샷으로 확정.

## 1. PIE 진입

### 1.1 시작점

테스트 레벨: `/Game/Maps/PC_01_AnimTest` 또는 `/Game/Maps/_Sandbox` (TA 셋업 기준).

PIE 실행 전 콘솔 명령 사전 등록:

```
~ (콘솔 토글)
r.HairStrands.DebugMode 0
stat unit
```

### 1.2 PIE Play

`Alt+P` 또는 Toolbar의 Play 버튼.

처음 진입 시 1초 정도 헤어 settle 대기 (시뮬 안정화). 즉시 결론 내리지 말 것.

## 2. 시각 검증

### 2.1 정적 자세 (Idle)

PC_01이 Idle 상태에서 헤어가:
- [ ] 두피에서 자연스럽게 늘어짐 (떨어지는 모양)
- [ ] strand 5그룹 모두 보임 (Hero/Size8/Size4 두께 차이)
- [ ] **Grp 4 뒷머리가 자연스럽게 떨어짐** (Gravity=-981 적용 확인)
- [ ] 떨림/덜덜림 없음 (잔존 이슈일 수 있음 — 4절)
- [ ] 어깨/등 관통 없음
- [ ] 얼굴 클립핑 없음

### 2.2 이동 (Walk/Jog/Sprint)

WASD로 이동하면서:
- [ ] 가속 시 헤어가 뒤로 흩날림 (Inertia 반응)
- [ ] 정지 시 settle (0.3~0.5s) 자연스러움
- [ ] 회전(좌/우) 시 좌우 흔들림
- [ ] **텔레포트(빠른 점프/순간이동) 시 튐 없음** ← 잔존 이슈 후보

### 2.3 전투 (Attack/Evade)

전투 액션 시:
- [ ] 회피 회전 시 헤어가 자연스럽게 따라옴
- [ ] 빠른 모션에서 strand 발사 / 관통 없음
- [ ] 무기 / 어깨 캡슐과의 충돌 자연스러움

### 2.4 r.HairStrands.DebugMode

콘솔 명령으로 시뮬 가이드/Strands 시각화:

| 모드 | 표시 |
|---|---|
| `r.HairStrands.DebugMode 0` | 일반 렌더 |
| `r.HairStrands.DebugMode 6` | Guides + Strands 시뮬 상태 |
| `r.HairStrands.DebugMode 12` | Physics constraints (캡슐 충돌 포함) |

`DebugMode 6`에서:
- [ ] Guide Curve가 의도한 위치에 있음
- [ ] **시뮬 가이드 개수 > 0** (그룹 0/1/3/4) ← 가장 중요

`DebugMode 12`에서:
- [ ] Evie_Body_PhysicsAsset의 캡슐이 head/shoulder/torso 위치에 있음
- [ ] 헤어 strand가 캡슐을 관통하지 않음

## 3. 스크린샷 + 자동 비교

### 3.1 HighResShot 캡처

```
~ (콘솔)
HighResShot 1920x1080
```

저장 위치: `<Project>/Saved/Screenshots/Windows/`

권장 캡처 컷:
1. Idle 정면
2. Idle 후면 (뒷머리)
3. Idle 측면
4. Sprint 진행 중 (헤어 흩날림)
5. Evade 회전 중
6. r.HairStrands.DebugMode 6 (Guide 시각화)

### 3.2 자동화 (Monolith)

```python
# Claude Code에서
editor_query("run_console_command", command="HighResShot 1920x1080")
# Saved/Screenshots/ 자동 감지 + Read로 AI multimodal 검증
```

참조: `reference_visual_verification.md` — screenshot.py 파이프라인.

### 3.3 v1 vs v2 비교

가능하면 v1_backup (01편 백업본)을 Binding 한 번 다시 가리키게 해서 동일 컷 캡처 → 두 컷 시각 비교. 룩이 일치하면 신규본 OK.

## 4. 잔존 이슈 체크리스트

07편 6절에서 식별한 잔존 이슈를 PIE에서 검증:

### 4.1 뒷머리 (Grp 4) 덜덜림

| 처방 | 결과 |
|---|---|
| Grp 4 ProjectCollision = False | (PIE 재진입 후 확인) |
| Grp 4 BendDamping 0.005 → 0.010 | |
| Grp 4 AirDrag 0.020 → 0.030 | |

세 처방 중 어느 게 효과 있는지 단일 변수로 테스트.

### 4.2 텔레포트 튐

```python
# BP_Sanjuk 또는 PC_01_BP 측 BP
On Teleport:
    Hair_GEN_VARIABLE -> ResetSimulation()
```

BP 추가 후 PIE에서 텔레포트(시네마틱 컷 이동 등) 시 헤어 reset 확인.

### 4.3 WindScale 과반응

GroomComponent.WindScale 0.4 → 0.2 토글 후 외부 바람 환경 (예: 옥상 레벨)에서 비교.

### 4.4 메모리 충돌 해소

07편 2.4절 ProjectCollision (Grp 4): True vs False 차이를 단일 변수로 검증.

→ 결과를 메모리 업데이트:
- `project_pc01_hair01_params.md` 라이브 갱신 (5/28 신규본 dump)
- `project_pc01_hair_gravity_bug.md` 잔존 이슈 절 상태 업데이트

## 5. 로그 검증

### 5.1 LogGroom

PIE 종료 후 `<Project>/Saved/Logs/SB2.log`에서:

```
grep -E "LogGroom|LogHairStrands|LogStableRods" SB2.log
```

기대:
- `LogGroom: Built groom asset PC_01_Hair_01 with 5 groups` (임포트 시)
- `LogHairStrands: Simulation step ok` (런타임)
- `LogStableRods: Constraint solver converged` (SB2 커스텀)

오류 신호:
- `LogGroom: Warning: No guides found in group N` ← 단수/복수 함정
- `LogHairStrands: NaN detected in strand position` ← 시뮬 폭주

### 5.2 stat anim / stat unit

PIE에서 `stat unit`으로 GPU/CPU 시간 확인:
- 임포트 전 baseline 대비 헤어 cost 차이 작아야 정상
- Hero (Grp 0) SubSteps=32 + Iter=100 이 PIE 30fps 유지 가능 범위에 있는지 확인

## 6. P4 Submit (최종)

모든 검증 통과 시:

```
P4 Changelist:
  - PC_01_Hair_01.uasset
  - PC_01_Hair_01_Binding.uasset
  - PC_01_Hair_01_v1_backup.uasset  (롤백 안전망)
  - PC_01_Hair_01_Binding_v1_backup.uasset
```

Description:
```
[PC_01] Hair rebuild from Maya XGen source (v2)
- Maya source via Groom Hair Manager (TA 장석호 tool)
- 5 groups: Hero/Size8/SimOFF/Size4/Thick
- Physics: SBStableRodsSystem (live values from 2026-05-04 baseline)
- v1_backup retained for rollback
- Refs: Tutorial/PC01-Hair-Workflow/
```

## 7. Hermes 교차검증 (Tier 2 옵션)

비가역 P4 Submit 직전, Hermes 비동기 검수 옵션. `ue-accuracy.md` §10 + `commands/evidence.md` 단일 출처.

```
/evidence
```

→ 패킷 생성 → Hermes에 복붙 → 반박/메모리충돌/빠진 후보 회신 → 실측 재검증.

조건:
- v1 vs v2 PIE 컷 차이가 의도와 다른 경우
- 5그룹 중 어느 한 곳이 명백히 더 나빠진 경우
- 사용자 검토 결과가 애매한 경우

→ 그 외(전부 OK)는 Hermes 생략, Submit 진행.

## 8. 메모리 업데이트

작업 종료 시 다음 메모리에 갱신 1줄 + 검증 태그:

| 메모리 | 갱신 |
|---|---|
| `project_pc01_hair01_params.md` | 5/28 신규 라이브 dump 값 ✅ 실측 |
| `project_pc01_hair_gravity_bug.md` | 신규 ren build 종료 + 잔존 이슈 상태 |
| `project_sb2_groom_hair_manager.md` | groom_guide 단수/복수 검증 결과 추가 |
| `MEMORY_PC01.md` PC_01 헤어 섹션 | 5/28 v2 라이브 갱신 1줄 |

## 9. 체크포인트

- [ ] PIE 진입 + 1차 시각 정상
- [ ] r.HairStrands.DebugMode 6 가이드 시각화 정상 (NumGuides>0)
- [ ] HighResShot 6컷 캡처
- [ ] v1 vs v2 비교 OK
- [ ] 잔존 이슈 4종 검증 (덜덜림/텔레포트/Wind/ProjectCollision)
- [ ] LogGroom/LogHairStrands 오류 0
- [ ] stat unit cost 합리적
- [ ] (옵션) Hermes 검수
- [ ] P4 Submit
- [ ] 메모리 4종 갱신

전부 OK면 PC_01_Hair_01 신규 제작 종료. 🎉
