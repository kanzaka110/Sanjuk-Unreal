# UpdateWallHandIK 리팩터 플랜 (2026-07-07)

대상: `/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP` → 함수 `UpdateWallHandIK`
백업: `backup_UpdateWallHandIK_20260707_163909.json` (283노드 / 444엣지)

## 현황
- 283노드 = CallFunction 162 + **Knot 98(손대지 않음)** + BreakStruct 9 + VarGet 7 + VarSet 3 + Select 2 + Entry 1 + Cast 1
- 반복 팬아웃: Select Float 43 / Break Vector 2D 18 / Select Vector 7 / Select Name 4
- SetWallHandData(96)·SetWallHandFront(86) 서브트리가 **75노드 공유** = 공유 DAG (트리 분리 불가)

## 실행 경로
Monolith에 Collapse 액션 없음 → ①에디터 네이티브(안전) 또는 ②Monolith 재구축(위험, P4 revert 이력).

## 리팩터 A — bRight struct-select 치환 (실감량 ~25노드, 핵심)
`GetConfig.RWall`(Break_5) / `GetConfig.LWall`(Break_6) 를 필드별로 23번 SelectFloat 하는 것을
**구조체 단위로 한 번 Select → 한 번 Break** 로 치환.

교체 전:
- Break_5(RWall) + Break_6(LWall) + 23×SelectFloat(bRight) [+ 관련 Break Vector 2D 중복]

교체 후:
- `Select<SWallHandSideConfig>(bRight, RWall, LWall)` 1개
- `Break SWallHandSideConfig` 1개 → 스칼라 7필드 직결
- 선택된 config의 V2D 필드만 Break Vector 2D (중복 R/L 제거)

대상 SelectFloat 23 노드ID:
CF_1, 30, 31, 32, 63, 64, 99, 101, 126, 127, 130, 132, 134, 138, 140, 142, 144, 149, 151, 156, 158, 160, 162
직접 스칼라 7: IKStrength, AttachStartDist, AttachFullDist, TurnReleaseSpeed, TurnBlockHold, SpineLeanMaxDeg, ElbowAngleDeg

유지(치환 불가): 정면-오버레이 AND게이트 14개 (Front vs Side 타입 상이) —
CF_89,131,133,135,139,141,143,145,150,152,157,159,161,163

## 리팩터 B — 코멘트 박스 구획 (안전, 추가 전용)
메인 그래프 구역 라벨 (Collapse 스캐폴드 겸용):
1. 속도 평활 (VInterp → Set WallHandSmoothVel)
2. 벽 트레이스 R/L/정면 (3× Sphere Trace)
3. 측면 설정 R/L 해결 (bRight 블록) ← 리팩터 A 영역
4. 정면 오버레이 병합 (AND 게이트 14)
5. 팔로우/소켓 Z (FollowBaseZ)
6. 최종 Set (Config/Data/Front/Data)

## 검증
각 변경 후: compile_blueprint → 에러 0 확인 → PIE 벽짚기 R/L/정면 동작 실측 → 이상시 P4 revert.
