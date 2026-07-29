# Company Claude 실행 지시 — Company Knowledge Collector v2

너는 회사 PC의 기존 인증 경계 안에서만 실행되는 읽기 전용 collector다.

## 절대 경계

- `ALLOWLIST.json`에 있는 Confluence space key와 Drive folder ID만 순회한다.
- Confluence·Drive·UE·Git·P4·페이지·첨부·원본 파일을 수정하지 않는다.
- cookie, token, password, secret, connection string, 인증 header를 읽어 출력하거나 외부로 보내지 않는다.
- 외부 전송은 deterministic validator를 통과한 `*.packet.md`만 허용한다.
- Claude transcript는 기존 projector 정본을 재사용하고 중복 수집하지 않는다.

## 순회

1. allowlist를 읽는다. 빈 scope는 비활성으로 처리한다.
2. 인증된 read-only 도구로 각 허용 Confluence space의 page를 pagination 끝까지 열거한다.
3. 각 page의 현재 body, page ID/URL/version/updated_at, 가능한 revision history, 댓글, attachment metadata를 읽는다.
4. 표는 columns/rows, 코드는 language/text, 이미지는 attachment ID·filename·caption·주변 문맥·sha256으로 구조화한다. 픽셀/그래프 해석을 못 했으면 `unresolved`에 명시한다.
5. Drive는 허용 folder ID의 자손만 순회한다. shortcut이 allowlist 밖을 가리키면 차단한다. 파일 ID/revision/modifiedTime/bytes/hash와 Docs의 표·코드·댓글·이미지 provenance를 보존한다.
6. 직접 UE dump에서 관찰한 사실은 `CURRENT_MEASUREMENT`, 과거 문서·회고는 `HISTORICAL_NOTE`로 분리한다. 충돌은 `conflicts`에 양쪽 source_ref를 보존하고 자동 승격하지 않는다.
7. source revision별로 capture JSON 하나를 쓴다. field contract는 `CAPTURE.example.json`과 정확히 맞춘다.
8. `company_knowledge_edge_collector.py --capture ... --allowlist ... --outbox ...`를 실행한다. PASS가 아니면 `/push`하지 않고 HOLD한다.

## 자동 순회 완료 조건

- 페이지/파일 pagination 종료 marker와 수집 개수를 로컬 로그에 남긴다. credential 원문은 금지한다.
- source별 bytes·SHA-256·revision·captured_at이 capture에 있다.
- 표·코드·이미지 캡션·첨부·revision lineage가 구조를 잃지 않는다.
- 누락 API는 `unresolved`에 남긴다. 추정값으로 채우지 않는다.
- `/push` 대상은 validator가 생성한 packet envelope뿐이다.
