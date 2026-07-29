# UE 모션 증거 검수 staging — H1

> 정렬 검증만 통과했다. AI 검수 전 결론·운영 truth·에셋 수정으로 승격 금지.

## 가설
- 1프레임 이웃 클립 선택이 덜컥 원인이다.

## 타임라인 정렬 — CURRENT_MEASUREMENT
|영상 프레임|시각(s)|시각 관찰|ANIM_REC f|clip|sms|delta|
|---:|---:|---|---:|---|---|---:|
|0|0.0|이동 루프|1000|Jog_F|1|0.0|
|1|0.033333|시각적 덜컥|1002|Jog_L|1|0.0|
|2|0.066667|이동 루프 복귀|1004|Jog_F|1|0.0|

## 현재 에셋 실측 — CURRENT_MEASUREMENT
```json
{
  "animation_blueprint": {
    "asset": "/Game/PC01/PC_01_ABP",
    "compile_status": "synthetic-readonly-fixture"
  },
  "capture_method": "ue_readonly_dump",
  "captured_at": "2026-07-29T09:11:00+09:00",
  "chooser_rows": [
    {
      "asset": "/Game/PC01/GroundMoving",
      "row": "LockOn-Left"
    }
  ],
  "pose_search_databases": [
    {
      "asset": "/Game/PC01/PSD_GroundMoving",
      "continuing_pose_cost_bias": -0.01
    }
  ],
  "project_revision": "synthetic-readonly-fixture",
  "schema_version": 1
}
```

## 반박
- 영상 덜컥이 카메라 움직임일 수 있다.
- 로그 clip 필드가 최종 포즈를 뜻하지 않을 수 있다.

## 메모리 충돌
- 아래는 `HISTORICAL_NOTE`이며 현재 실측보다 자동 승격하지 않는다.
- 과거에도 경계각에서 1프레임 플리커가 있었다. — source_ref=`historical-note-fixture`

## 빠진 후보
- 포스트 프로세스 애니메이션 블루프린트
- 루트 모션 보정

## 단일변수 체크
- 변수: `ContinuingPoseCostBias`
- 기준값: `-0.01`
- 후보값: `-0.1`
- 실제 적용·관찰: 미실행. 회사 PC에서 한 변수만 바꿔 재수집 필요.

## 종합 판정
- `HOLD_HERMES_REVIEW` — 정렬은 PASS지만 AI 반박·실기기 비교 전 결론 금지.

## provenance
```json
{
  "anim_rec": {
    "bytes": 228,
    "record_count": 3,
    "sha256": "67848e245fe7832893b3a78f3f976b3c2b2737098a2c6cb342293dc09542cb79"
  },
  "asset_dump": {
    "bytes": 421,
    "captured_at": "2026-07-29T09:11:00+09:00",
    "evidence_class": "CURRENT_MEASUREMENT",
    "sha256": "3037f77b7dca3d8da4974dd42294910fd1a45c83089c63b4045b0d93ef758ac1"
  },
  "mapping": {
    "anim_frames_per_video_frame": 2.0,
    "video_fps": 30.0
  },
  "review_request": {
    "bytes": 680,
    "sha256": "fd1d08e98f050049f18d1a2faff27556541dd9b1c00d9cabed43f6eff8a43b67"
  },
  "video": {
    "bytes": 1662,
    "captured_at": "2026-07-29T09:10:00+09:00",
    "probe": {
      "duration_s": 0.1,
      "fps": 30.0,
      "frame_count": 3,
      "method": "ffprobe-readonly",
      "r_fps": 30.0
    },
    "sha256": "12d6202b6ec7bf0a2e3030220bda594f8ce4fd4f9209e7cb589e9f0da23f142b"
  }
}
```
