[COMPANY-KNOWLEDGE-PACKET v1]
manifest: {"captured_at":"2026-07-29T09:00:00+09:00","group_bytes":1763,"group_id":"ckg_20260729_confluence_1608679894_015eb53ee428","group_sha256":"015eb53ee4286bd8ec32676b38279a40cb573b976b8a8ad658f53c31f752e299","packet_id":"ckp_20260729_confluence_1608679894_015eb53ee428_p001","part_bytes":1763,"part_count":1,"part_index":1,"part_sha256":"015eb53ee4286bd8ec32676b38279a40cb573b976b8a8ad658f53c31f752e299","read_only":true,"redaction_count":1,"schema_version":1,"source_id":"1608679894","source_kind":"confluence","source_title":"샘플 페이지","source_updated_at":"2026-05-29T10:35:04+09:00","source_url":"https://shiftupcorp.atlassian.net/wiki/spaces/SB2/pages/1608679894/example","source_version":"8","status":"PASS"}
--- CONTENT BEGIN ---
## [SOURCE]
- source kind: `confluence`
- source ID: `1608679894`
- title: 샘플 페이지
- URL: https://shiftupcorp.atlassian.net/wiki/spaces/SB2/pages/1608679894/example
- version: `8`
- updated at: `2026-05-29T10:35:04+09:00`
- captured at: `2026-07-29T09:00:00+09:00`
- capture mode: `read-only`
- capture method: `confluence_mcp`

## [CONTENT]
## 샘플 섹션
| 변수 | 값 |
| --- | --- |
| ContinuingPoseCostBias | -0.01 |
```text
[ANIM_REC] f=1002 clip=Jog_L
```
- image attachment_id: `att-sample`
- filename: `sample.png`
- caption: 그래프 캡션
- context: 본문 인접 문맥
- attachment `sample.png` (id `att-sample`, type `image/png`, bytes `12`, sha256 `c9da6ac892c00c4a7b8ac147474e39e222d504916a215f69089da97e27386b9d`)

### Revision lineage
- version `8` at `2026-05-29T10:35:04+09:00` by `[REDACTED]`: 샘플 revision

### Evidence-class claims
- evidence_class: `CURRENT_MEASUREMENT`
  - claim: 현재 에셋 dump에서 직접 읽은 값이다.
  - source_ref: `ue-dump-sample`
  - observed_at: `2026-07-29T09:00:00+09:00`
  - artifact_sha256: `658597935154f9327d06d4317d20e26cf76a51a3b5b091ecaa20c77aa624e200`
- evidence_class: `HISTORICAL_NOTE`
  - claim: 과거 노트에 기록된 값이다.
  - source_ref: `historical-row-sample`
  - observed_at: `2026-05-29T10:35:04+09:00`
  - artifact_sha256: `658597935154f9327d06d4317d20e26cf76a51a3b5b091ecaa20c77aa624e200`

## [CONFLICT]
- 현재 실측과 과거 노트는 자동 덮어쓰지 않는다.

## [UNRESOLVED]
- 댓글 API 미노출 여부 확인 필요

## [HERMES-MERGE]
- 샘플 케이스.md

## [EVIDENCE]
- capture method: `confluence_mcp`
- block count: `5`
- revision count: `1`
- claim count: `2`
- credential scrub markers: `1`
- promotion status: `HOLD_HUMAN_REVIEW`
--- CONTENT END ---
