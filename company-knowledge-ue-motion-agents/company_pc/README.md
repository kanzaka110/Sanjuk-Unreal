# Company Knowledge Agent v2

## 상태

- v1 packet transport·append-only receiver는 그대로 유지한다.
- v2는 회사 PC의 인증된 읽기 도구가 만든 구조화 capture를 fail-closed 검증해 v1 packet outbox로 연결한다.
- Hermes 수신 후 기존 기술 위키를 자동 수정하지 않고 `Company-Knowledge-Staging/<group_id>/`에 검토 staging만 만든다.
- `auto_apply=false`, promotion=`HOLD_HUMAN_REVIEW` 고정이다.

## 실행 경계

- 회사 PC에서만 원본을 읽는다. Confluence·Drive·UE·Git·P4는 읽기 전용이다.
- 회사 인증 cookie·token·session은 JSON·로그·packet·`/push`에 넣지 않는다.
- allowlist 밖 source는 접근·수집하지 않는다. Drive allowlist가 빈 배열이면 Drive 수집은 차단된다.
- 기존 Claude transcript projector는 재사용하고 중복 순회하지 않는다.

## 회사 PC 실행

1. `ALLOWLIST.json`을 승인된 공간·폴더 ID로만 채운다.
2. 회사 Claude에 `COMPANY_CLAUDE_V2_PROMPT.md`를 제공해 source별 capture JSON을 생성한다.
3. source마다 실행한다.

```text
py company_knowledge_edge_collector.py ^
  --capture captures\source.json ^
  --allowlist ALLOWLIST.json ^
  --outbox outbox
```

성공 marker: JSON의 `status=PASS`, `scrub_status=PASS`, `packet_count>=1`.

4. 기존 `/push`로 `outbox/*.packet.md`만 전달한다. capture 원본·credential·회사 인증 세션은 전달하지 않는다.

## Hermes 수신

`company_knowledge_packet_watch.py`가 packet을 append-only store로 검증한 뒤 `company_knowledge_case_stager.py`를 호출한다. staging은 provenance·revision·conflict·원문 body를 보존하지만 운영 truth가 아니다.

## 완료/차단

- 로컬 구현·focused test: PASS.
- 기존 실제 Confluence page 1608679894의 **v2 canonical packet store 재수집**: 회사 PC 실행 전 HOLD.
- 이미지 픽셀·그래프·댓글·revision API가 인증 도구에 노출되지 않으면 `UNRESOLVED`로 기록하며 완전수집이라 주장하지 않는다.
