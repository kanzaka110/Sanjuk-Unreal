---
name: Monolith 부분 인덱싱 조사 대기
description: 2026-04-20 예정 — Monolith v0.12.0에서 모듈 단위/경로 단위 인덱싱 제어 가능 여부 확인
type: project
originSessionId: 39f100c7-5cb2-4d29-8ac3-476cb7351b2e
---
Monolith 인덱싱 시 메모리 피크가 크다는 이슈 → 사용자 타이밍에 맞춰 부분 인덱싱하는 방법 조사 예정.

**Why:** MetaHumans 포함 UE 프로젝트에서 초기 인덱싱 메모리 부하가 12~18GB까지 올라감. 작업 맥락(애니메이션만)에 불필요한 모듈(Niagara/GAS/AI/UI)까지 전체 로드되는 구조가 원인 의심.

**How to apply (내일 체크):**
- Monolith 설정 파일 위치 확인: `.uplugin`, `Config/*.ini`, `MonolithSettings.ini` (플러그인 경로 `MonolithTest/Plugins/Monolith/`)
- 확인 포인트:
  1. **모듈 개별 enable/disable** 가능한지 (16개 모듈 중 Animation/Blueprint만 켜기)
  2. **경로 화이트리스트/블랙리스트** 지원 여부 (MetaHumans/Quixel 제외)
  3. **지연 로딩(lazy module load)** API 존재 여부 (`load_module("MonolithAI")` 같은 런타임 제어)
  4. AssetRegistry 스캔 범위 커스터마이징 지점
- 대안 검토: 애니메이션 전용 경량 UE 프로젝트 분리 운영
- 오늘 대화에서 제시한 4가지 접근 (모듈 토글 / 경로 필터 / lazy load / 프로젝트 분할) 중 실제 지원되는 것 매칭
