# PC_01 벽 짚기 손 IK — 2026-06-30 작업 스크립트

전환 블렌드 폴리싱 + 측면 오프셋/spine-Z 신규 + 좌/우 비대칭 해결. 전부 Monolith HTTP(`localhost:9316`)로 BP/ABP/CR 편집. 대상 에셋:
- BP `PC_01_BP:UpdateWallHandIK`
- ABP `PC_01_ABP` (`SetWallHandData`/`SetWallHandFront`/`SetSmoothedWallHandAlpha`)
- AnimLayer `PC_01_AnimLayer_IK`
- CR `PC_01_CtrlRig_WallHandIK`

## 핵심 발견 (재발 방지)
- **좌/우 비대칭의 진짜 원인** = `PC_01_AnimLayer_IK` EventGraph에서 **오른손 타겟(WallHandTarget) Z에만** `FInterpTo(speed 3)`가 걸려 이중 스무딩 → 오른손만 느리게/뭉개져 올라옴. 왼손(WallHandTargetL)은 직결. → `01_*` 로 우회(CF_23.Z ← CF_20.Z raw). **교훈: ABP/CR 배선 대칭인데 좌/우 동작 다르면 AnimLayer per-side set 경로의 숨은 interp를 의심.**
- 진단 핵심: "타겟은 좌우 동일(tgtR==tgtL)인데 손만 한쪽 lag" → 타겟↔손 사이(CR/AnimLayer)에 추가 스무딩. 팬-거리 지표 불신, 타겟 vs 손 동시 로깅이 답.
- Monolith는 **enum Select 핀 자동확장 불가** → WalkMode별 값은 에디터에서 Select 직접 생성. `set_function_params`는 append(중복 파라미터 주의).
- 릴리즈 stretch: 느린 alpha 릴리즈(speed 3) 중 질주로 몸이 멀어지면 손이 월드 벽점 잡고 늘어났다 스냅(~47cm). → `08_*` gap 비례 릴리즈 속도(`3 + |alpha−target|×12`)로 질주 자동 가속.

## 스크립트 순서
- `01` 좌/우 비대칭 해결 (AnimLayer 오른손 Z FInterpTo 우회) — **이번 세션 핵심 픽스**
- `02` CR weight 스무딩 (SelR/SelL → WInterpR/L AlphaInterp 8/8)
- `03` CR 릴리즈 ease (WInterp Decreasing 8→4)
- `04a/b` 측면 손 위치 오프셋 (벽면-상대 벡터, 좌/우 bRight 선택, CF_84.B 가산)
- `05a/b` spine/pelvis-Z 반응 (손 Z += scale×(소켓Z−rootZ−RestC))
- `06a/b` InBlendSpeed 파라미터 + velocity 속도스케일 (MapRange)
- `07` 적응형 타이머 제거 (catch-up 스냅 유발 → 단일 상수로)
- `08` 릴리즈 gap 비례 속도 (질주 stretch 해결, SetSmoothedWallHandAlpha)
- `_diag_logger.py` PIE 슬레이트-틱 로거 (타겟/손/alpha/속도 캡처)

상세는 메모리 `project_pc01_wall_hand_ik.md` 6/30 섹션.
