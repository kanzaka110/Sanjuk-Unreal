# WallHandIK 덤프 스냅샷 — 2026-07-02 (작업 재개 기준점)

Monolith v0.20.3 (pid 36668) 라이브 에디터에서 덤프. 에셋 4개 디스크/메모리 상태.

## 파일

| 파일 | 내용 |
|------|------|
| `cr_dump.txt` | PC_01_CtrlRig_WallHandIK 전체 (멤버변수 9 + 노드/핀디폴트/링크, 663줄). 생성=`../dump_wallhand_cr.py` (py 콘솔 우회) |
| `bp_UpdateWallHandIK.json` | PC_01_BP UpdateWallHandIK 그래프 (165노드) |
| `abp_SetWallHandData.json` | ABP setter (35노드) — VInterpTo 우손 타겟 |
| `abp_SetWallHandFront.json` | ABP setter (12노드) — VInterpTo 좌손 타겟 |
| `abp_SetSmoothedWallHandAlpha.json` | alpha FInterpTo (14노드) |
| `abp_Get*.json` ×5 | 게터 5개 (TargetWorld/AlphaValue/Right/Front/TargetL) |
| `layer_EventGraph.json` | AnimLayer_IK EventGraph (53노드) — ABP→레이어 읽기체인 |
| `layer_IK.json` | AnimLayer_IK IK 애님그래프 (100노드) — CR_4/LayeredBoneBlend |
| `*_variables.json` | 변수 전체 (ABP 186 / 레이어 26 / BP 20) |
| `abp_info.json`, `layer_info.json` | 그래프 목록/컴파일 상태 |

## 6/30 메모리 대비 실측 대조 (✅실측 2026-07-02)

**일치 (디스크에 살아있음):**
- 좌우 비대칭 fix: 레이어 `CF_23.Z ← CF_20.Z` raw 직결, CF_22 FInterpTo orphan ✓
- CR weight 스무딩: `WInterpR`/`WInterpL` (AlphaInterp) 존재 ✓
- 정면 폭 노브 `CF_76.B=17.5` / 벽 이격 `CF_77.B=2.5` ✓
- cross 오프셋 우 `CF_94.B=(0,15,15)` / 좌 `CF_54.B=(0,-15,15)` (부호 미러) ✓
- 측면 standoff `CF_101 A=2.0/B=2.0`, 측면 오프셋 SelectFloat `CF_63=3.0/0`·`CF_64=60/-60` ✓
- alpha 램프 `CF_21` 60→45 ✓
- spine-Z 체인 존재 — 단 ID 변경: GetSocketLocation(pelvis)=**CF_96**, Dot(0,0,1)=**CF_97** (메모리의 CF_39/40 아님)
- SetWallHandData 파라미터 클린 6개 (메모리의 dupe 5개 **없음** — 정리된 상태)

**드리프트 (메모리와 불일치 — 재개 시 확인 필요):**
1. 🔴 **속도스케일 InterpSpeed 미배선**: `SetWallHandData.InBlendSpeed`·`SetWallHandFront.InBlendSpeed` 둘 다 **비연결 디폴트 15.0**. 메모리의 CF_57 VSizeXY→CF_58 MapRangeClamped(0→400, 15→4) 체인이 BP에 **없음** (VSizeXY 노드 미존재). 함수 내부 InterpSpeed←InBlendSpeed 파라미터 배선은 정상 → **BP 쪽 공급 체인만 소실/미저장**. 사용자 "좋아" 확인했던 기능이라 P4 revert 또는 미저장 가능성.
2. ⚠ **BP 노드 ID 전면 재배열**: 메모리의 CF_39~43(spine-Z)·CF_57/58·CF_65 등은 현재 없고 CF_96/97/103/104 등 신규 ID 존재. **메모리 기록 노드 ID로 직접 편집 금지 — 이 덤프가 ground truth.**

## 상태
- ABP compile_status=UpToDate. WallHand 변수: ABP 14개(WHPrev*/WHBlend* 미사용 잔존 포함), 레이어 6개, BP 1개.
- **BP `WallHandSmoothVel`(메모리 미기록 신규)**: 트레이스 전방 리드용 속도 스무딩 — 함수 첫 exec에서 `VInterpTo(Current=자기값, Target=CF_59, dt=0.0167 상수, speed 12)`→Set→`CF_27.A`(velocity lead). InterpSpeed 스케일 기능과 무관.
- 신규 ID 체인: `CF_103 GetActorLocation→CF_104 BreakVector.Z→CF_98.B` (spine-Z의 rootZ 공급 — 메모리의 CF_34.Z 대체).
- 미해결 과제(메모리): 손바닥 정면 flush(CR 에디터+bDrawDebug 시각 튜닝 필요), 측면 정면 오발동(facing 게이트 롤백 상태).
