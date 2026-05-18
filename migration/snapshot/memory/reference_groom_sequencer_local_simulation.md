---
name: Groom 시뮬 시퀀서 테스트 시 bLocalSimulation 함정
description: UE 5.7 Groom 기본 bLocalSimulation=true는 시퀀서 평행이동을 reference frame에 흡수해 헤어가 안 흔들리게 함. 시네마틱은 false 권장.
type: reference
originSessionId: 37384c1c-fae6-46a1-a434-331200afafc8
---
# UE 5.7 Groom — 시퀀서에서 캐릭터 이동이 헤어에 안 먹는 함정

소스: `cache/ue57_groom/GroomAssetPhysics.h:382-398` `FHairSimulationSetup`

## 핵심

**`bLocalSimulation = true`** (UE 5.7 Groom 기본, 게임용)
- 시뮬 reference frame = LocalBone (보통 root) 좌표계
- 캐릭터 root가 (0,0,0) → (1000,0,0)으로 이동하면 reference frame도 같이 이동
- 헤어는 reference frame 대비 "정지" → 외력 = 0 → 안 흔들림
- **회전(angular)은 LocalBone 본 자체 회전이면 일부 살아남음. 평행이동(linear)은 거의 100% 흡수**

**`bLocalSimulation = false`** (시네마틱 정공)
- 시뮬 reference frame = 월드 좌표계
- 캐릭터 이동 시 헤어 가닥은 관성으로 잠시 머무름 → 캐릭터-헤어 위치 차이 = 외력 → 출렁임 ✅

## 진단 1순위 — "시퀀서로 캐릭터 움직이는데 헤어가 안 흔들려"

5초 확인: 캐릭터 BP > GroomComponent > Details > **Simulation Setup** > **Local Simulation** 체크 해제(false)

증상별 매핑:
- "이동값만 안 먹음, 회전은 어느 정도 됨" → bLocalSimulation 거의 확정
- "이동/회전 둘 다 약함" → LinearVelocityScale/AngularVelocityScale도 함께 점검
- "갑자기 흔들림 끊김" → TeleportDistance < 캐릭터 한 프레임 이동량 → reset 발생

## 보조 노브 점검 순서

| 우선 | 파라미터 | 권장 (시퀀서) | UE 5.7 기본 |
|---|---|---|---|
| 1 | bLocalSimulation | **false** | true |
| 2 | LinearVelocityScale | 1.0 (Min/Max 0~1) | 1.0 |
| 3 | AngularVelocityScale | 1.0 (사용자가 모션 최대화 시) | 1.0 (UE 권장은 0.7) |
| 4 | TeleportDistance | 200~500 cm | 50 cm |
| 5 | AirDrag | ≤ 0.05 | 0.1 |
| 6 | BendDamping / StretchDamping | ≤ 0.005 | 0.001 |
| 7 | SubSteps / IterationCount | 과수렴 시 외력 흡수 — 16/40 정도 | 5/5 |

## 시퀀서 키프레임 측면

- **Auto/Cubic 보간**: 매끄러워서 instantaneous velocity 작아짐 → 외력 작음
- **Linear 또는 키 간격 좁힘**: 더 큰 velocity → 더 큰 외력
- 캐릭터 트랜스폼 트랙 키 인터폴레이션 모드 점검 가치 있음

## 함정 / 반례

- **bLocalSimulation=false + 시퀀스 컷 점프**(예: 5초 시점에 캐릭터 위치 워프)에서 헤어가 폭주 가능. → TeleportDistance 충분히 크게 + 컷 직전 PreRoll 0.5초로 안정화
- **LocalSim=false 전환 후 BendStiffness가 너무 낮으면** 헤어 형태 유지 약해질 수 있음
- **Spawnable 시퀀서 액터**는 시퀀스 시작에 새로 spawn → 시뮬 0초 시작 → 워밍업 부족. PreRoll 또는 Possessable로 전환

## How to apply

시퀀서로 헤어 시뮬 테스트 시:
1. 1순위로 LocalSimulation 토글
2. 그래도 부족하면 위 표 순서대로 점검
3. NPC_001 같은 GroomComponent-side 진단 시 `dump_npc001_hair.py` 보강해 SimulationSetup 5필드(`b_local_simulation`, `local_bone`, `linear_velocity_scale`, `angular_velocity_scale`, `teleport_distance`) 떠야 정확
