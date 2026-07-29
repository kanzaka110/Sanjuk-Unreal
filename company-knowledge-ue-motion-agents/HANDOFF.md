# Company Knowledge v2 + UE Motion Evidence handoff

## 결론

- P0 v2 deterministic edge collector, 기존 v1 packet 연결, Hermes review staging: `PASS_LOCAL`.
- P1 실영상·ANIM_REC·현재 에셋 dump 정렬기: `PASS_LOCAL_ALIGNMENT`.
- 운영 truth 자동 promotion: 금지. `auto_apply=false`.

## 회사 PC 배치

### Company Knowledge

`company_pc/`만 회사 PC로 옮긴다. 회사 Claude에 `COMPANY_CLAUDE_V2_PROMPT.md`를 주고 `ALLOWLIST.json`을 승인된 Confluence space·Drive folder ID로만 채운다. Drive folder ID는 현재 빈 배열이라 fail-closed다.

성공 경로:

```text
py company_knowledge_edge_collector.py --capture <capture.json> --allowlist ALLOWLIST.json --outbox <outbox>
py company_knowledge_packet.py validate <outbox packet files>
```

`/push` 대상은 validator가 생성한 packet envelope뿐이다. cookie·token·session·capture 원본은 보내지 않는다.

### UE Motion Evidence

`ue_motion_company_pc/`를 사용한다. 실제 MP4, video manifest, ANIM_REC, 현재 초우저 행·포즈 검색 데이터베이스·애니메이션 블루프린트 dump, 시작·끝 anchor 2개가 모두 있어야 한다.

```text
py ue_motion_evidence_pipeline.py --video <mp4> --video-manifest <json> --anim-rec <log> --asset-dump <json> --review-request <json> --output <staging.md>
```

정렬 성공도 verdict=`HOLD_HERMES_REVIEW`다. `REVIEW_AGENT_PROMPT.md` 형식의 AI 검수 후에만 가설 판정한다.

## Hermes 서버

`hermes_server/`의 watcher·stager는 packet append-only store 뒤에 review staging을 만든다. 기존 케이스 기술 위키는 자동 수정하지 않는다.

## 검증 증거

- `evidence/focused-regression.txt`: 18/18 PASS.
- `evidence/company-edge-collect.json`: sample capture packet 생성 PASS.
- `evidence/packet-validate.txt`: packet validate PASS.
- `evidence/watcher-stage.txt`: import·staging PASS, promotion HOLD.
- `evidence/motion/pipeline-result.json`: 실제 synthetic 30fps MP4 정렬 PASS, verdict HOLD.

## 외부 HOLD

1. 회사 PC의 승인된 Drive folder ID가 아직 고정되지 않았다.
2. 회사 인증 Confluence·Drive를 통한 실제 v2 자동 순회 E2E는 회사 PC에서 실행해야 한다.
3. 실제 승호 영상·ANIM_REC·현재 에셋 dump가 없어 P1 실제 가설 판정은 HOLD다.
4. 이미지 픽셀·그래프·댓글·revision API가 회사 인증 도구에서 미노출이면 `unresolved`로 남기며 완전 수집이라 선언하지 않는다.
