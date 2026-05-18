---
name: Monolith 인덱싱 — 최초 1회 비용 후 안전
description: SB2 Monolith 인덱싱. 최초 풀 인덱스는 메모리 부하 있음(DDC 컴파일 연쇄). 완료 후 재시작은 인크리멘털 3초, 안전.
type: feedback
originSessionId: c0b37efc-71b6-4348-a2e2-afba5093f18e
---
SB2에서 Monolith 인덱싱을 **최초 1회만 조심**. 이후엔 안전.

**Why:**
- 최초 풀 인덱스: 795,609 에셋 처리 중 DDC 콜드 컴파일 연쇄 트리거 → `BEWARE: AssetCompile` 수천건, 메모리 1.1GB 요구 vs 가용 742MB → PC 프리즈 (2026-04-16, 2026-04-20 두 번 경험)
- 최초 인덱싱 자체는 247초에 완료됨. 죽는 건 그 **직후** DDC 압박.
- **인덱싱 완료 이후 재시작:** 인크리멘털 3초, DDC 캐시 히트, `BEWARE` 0건 (2026-04-20 확증)

**How to apply:**
- 인덱스 DB 없는 상태에서 처음 인덱싱 활성화할 때:
  1. 다른 앱 다 끄고 RAM 최대 확보
  2. 에디터 열고 기다림 (인덱싱 + DDC 병행 구간이 4~5분 위험 구간)
  3. 완료되면 `LogMonolithIndex: [성공] ... Indexing completed successfully` 확인
  4. PC 꺼지거나 멈춰도 DB는 디스크에 남음 — 재시작하면 인크리멘털로 복구
- 한 번 완료된 DB가 있으면 재인덱싱 없음:
  - `Existing index found — deferring incremental catch-up` 로그 확인
  - `bIndexEnabled=True` 유지해도 무방
- 혹시 DB가 손상된 경우만 재빌드 필요:
  - `sqlite3 ProjectIndex.db "PRAGMA integrity_check;"` 로 확인
  - 손상 시 DB 삭제 후 재인덱싱 (이번엔 DDC 이미 캐시되어 있어 훨씬 안전)

**이전 기록 수정:** "SB2에서 인덱싱 절대 금지"는 **부정확**. 최초 1회 비용만 감수하면 이후 안전. 795,609 에셋 검색 + `project.search` 사용 가치 있음.
