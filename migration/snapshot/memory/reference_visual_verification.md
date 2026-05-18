---
name: visual-verification
description: "scripts/screenshot.py + MonolithClient.screenshot. editor.run_console_command(\"HighResShot WxH\") → Saved/Screenshots 자동 감지 → AI multimodal Read. [[feedback-visual-mesh-over-anim-rec]] \"시각이 진짜 기준\" 원칙 자동화."
metadata: 
  node_type: memory
  type: reference
  originSessionId: ea3be7a5-d8f0-4249-af75-76ddb6a92c3d
---

ABP 변경 후 시각 검증 자동화. 사용자 호소가 "ANIM_REC 수치는 맞는데 mesh 가 이상하다" 일 때 (메모리 [[feedback-visual-mesh-over-anim-rec]]) AI 가 직접 PNG 를 multimodal 로 분석.

**Why:** 2026-05-18 검증. `editor.capture_scene_preview` 는 niagara/material 전용 (animation_blueprint 거부됨). `editor.run_console_command("HighResShot 1920x1080")` 는 정상 → `<project>/Saved/Screenshots/WindowsEditor/HighresScreenshot####.png` 생성 → AI 가 Read 로 visual 입력. PIE 또는 에디터 viewport 모두 동일 메커니즘.

## 단일 캡처

```bash
py scripts/screenshot.py --label transit-after --copy dumps/screenshots
```
결과:
- 원본: `E:\Perforce\SB2\...\Saved\Screenshots\WindowsEditor\HighresScreenshot00001.png`
- 복사: `dumps/screenshots/20260518_123055_transit-after.png`
- AI: `Read dumps/screenshots/20260518_123055_transit-after.png` → 이미지 분석

## before/after 묶음

```bash
py scripts/screenshot.py --before-after istransition --copy dumps/screenshots
# 1) before 캡처
# 2) Enter 대기 — 사용자가 변경/PIE 시작/Pose 변환 등 수행
# 3) Enter → after 캡처
```
결과:
- `..._istransition_before.png` + `..._istransition_after.png`
- AI 가 두 PNG 비교

## MonolithClient API

```python
from monolith_helpers import MonolithClient

cli = MonolithClient(asset)
result = cli.screenshot(
    resolution=(1920, 1080),
    label="transit-after",
    copy_to="dumps/screenshots",
)
# result: {captured_path, copied_to, elapsed_seconds, command_result}
```

## 워크플로우 통합 (Tuner 후 검증)

```
/inspect-abp → 처방
  ↓
py scripts/abp_backup.py backup <asset> <label>
  ↓
py scripts/screenshot.py --label <label>_before --copy dumps/screenshots
  ↓
/tune-abp → 변경 적용
  ↓
사용자 PIE 시작 (또는 그대로 viewport)
  ↓
py scripts/screenshot.py --label <label>_after --copy dumps/screenshots
  ↓
AI 가 before/after Read → 시각 변화 보고
  ↓
사용자 호소와 매칭 / 차이 분석
```

## 한계
- **PIE 가 안 돌면 빈 레벨/하늘만 캡처** — PC_01 캐릭터 검증은 PIE 필수
- 캡처 폴링 ~5초 (HighResShot 가 디스크에 PNG 쓰기까지 대기)
- viewport 카메라 자동 set 불가 (BugItGo 는 PIE 전용, 에디터에서 exit_code=1) — Editor viewport 카메라 이동은 Python plugin 필요 ([[feedback-sb2-python-plugin-disabled]] 차단)
- **대신 카메라 변동 자동 감지** (2026-05-18 추가):
  - 캡처 시 `editor.get_viewport_info` 동시 dump → PNG 옆 `<name>.camera.json` 저장
  - `MonolithClient.compare_camera(before_meta, after_meta, tol=1.0)` → drift_location_cm / drift_rotation_deg / drift_fov_deg / moved bool + warning
  - `screenshot.py --before-after` 가 후처리로 자동 비교 + "카메라 이동 영향" 경고
  - moved=true 면 mesh 차이가 진짜 변경인지 카메라 이동 영향인지 명시
- 캡처 명령 자체는 `editor.run_console_command` 라 임의 console 명령 가능:
  - `show Collision` / `show Bones` / `show Bounds` 등을 캡처 직전 호출하면 디버그 시각화 포함

## 응용 패턴
- 슬로프 진단: `show Collision` + HighResShot → PC_01 FootPlacement 정렬 확인
- Transition 호소: PIE 시작 → before HighResShot → Transition 발동 → after HighResShot
- Groom 비교: Grp 파라미터 변경 전후 캡처

관련 메모리: [[feedback-visual-mesh-over-anim-rec]], [[reference-abp-backup-system]], [[reference-monolith-animgraph-editing-limits]].
