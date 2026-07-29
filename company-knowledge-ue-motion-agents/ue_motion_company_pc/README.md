# UE Motion Evidence Agent

## 목적

30fps 실영상의 시각 관찰과 ANIM_REC 필드, 현재 초우저 행·포즈 검색 데이터베이스·애니메이션 블루프린트 dump를 같은 타임라인으로 맞춘다.

## Fail-closed 입력

- 실제 MP4와 bytes·SHA-256 manifest
- `ffprobe`로 확인되는 constant 30fps
- `[ANIM_REC]` 로그(`f`, `sms`, `clip` 필수)
- 영상 프레임↔ANIM_REC 프레임 시작·끝 anchor 정확히 2개
- `ue_readonly_dump`로 만든 현재 에셋 dump
- 가설 정확히 1개, 반박 최대 3개, 단일변수 체크 1개

하나라도 없으면 `HOLD`. 시간축을 추정하지 않는다.

## 실행

```text
py ue_motion_evidence_pipeline.py ^
  --video capture.mp4 ^
  --video-manifest video_manifest.json ^
  --anim-rec SB2.log ^
  --asset-dump asset_dump.json ^
  --review-request review_request.json ^
  --output motion_review_staging.md
```

성공해도 verdict는 `HOLD_HERMES_REVIEW`다. 정렬 PASS와 가설 판정은 분리한다. Hermes/회사 Claude가 `REVIEW_AGENT_PROMPT.md` 형식으로 검수한 뒤에만 종합 판정을 낸다.

## 현재 상태

- synthetic real-MP4 vertical slice·fail-closed 회귀: PASS.
- 승호의 실제 영상·ANIM_REC·현재 에셋 dump: 미제공이므로 실제 케이스 판정은 HOLD.
