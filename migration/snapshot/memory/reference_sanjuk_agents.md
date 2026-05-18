---
name: Sanjuk-Unreal 전용 서브 에이전트 4종
description: AnimBP / Sim 도메인 × Inspector / Tuner 역할 매트릭스. .claude/agents/ 에 정의.
type: reference
originSessionId: 5c97ced7-4741-424f-8e22-cc55efda4867
---
# Sanjuk-Unreal 프로젝트 전용 에이전트

2026-04-24 신규 추가. 도메인 2개 × 역할 2개 = 4개 에이전트.

## 에이전트 매트릭스

| 도메인 | Inspector (분석/처방) | Tuner (적용/검증) |
|---|---|---|
| **AnimBP** | `animbp-inspector` | `animbp-tuner` |
| **Simulation** | `sim-inspector` | `sim-tuner` |

## 사용 시점

| 트리거 | 호출 에이전트 |
|---|---|
| "현재 값이 뭐야", "왜 이렇게 동작해" (AnimBP) | `animbp-inspector` |
| "헤어가 뻣뻣해", "천이 관통해" (물리) | `sim-inspector` |
| "이 값 X로 바꿔줘" (AnimBP 수정) | `animbp-inspector` → `animbp-tuner` |
| "제안 적용해줘" (물리 수정) | `sim-inspector` → `sim-tuner` |

## 설계 원칙

### Inspector 공통
- 덤프 먼저 (추측 금지) — 기존 `scripts/dump_*.py` 활용
- `cache/ue57*/` 소스와 대조 — ground truth
- `project_*` / `feedback_*` 메모리 조회 필수
- 에셋 수정 안 함 (Tuner 담당)

### Tuner 공통
- Inspector 처방 없으면 거부
- 변경 전/후 덤프로 검증
- 한 번에 한 파라미터씩
- 메모리에 변경 이력 기록
- Git 커밋은 메인이 `/push` 로

## 도메인 특화

### AnimBP
- Monolith HTTP: `animation_query` + `blueprint_query`
- 생성 클래스 `_C` 로드 → CDO 접근 패턴
- PelvisSettings 3프로필 (Default/Move/Prone) 사전 인지
- Move.MaxOffset 변경 금지 (feedback 참조)

### Simulation
- Groom CosseratRods 함정 인지 (GravityPreloading 무시 등)
- Binding 참조 별도 확인 (Groom 튜닝 → 게임 반영 여부)
- ProjectCollision=True 기본 권장 금지
- `cache/ue57_groom/GroomAssetPhysics.h` 레퍼런스

## 제한 사항

- Tuner 의 `set_cdo_property` 가 SB2 커스텀 빌드에서 실제 동작 여부는 **미검증**. 첫 사용 시 작은 변경으로 시험 필요
- Perforce checkout/submit 흐름과의 충돌 가능성 미검증
- 대규모 구조 변경 (노드 추가/삭제 등)은 범위 밖 — 메인 에이전트 또는 수동

## 관련

- 에이전트 정의: `.claude/agents/animbp-inspector.md`, `animbp-tuner.md`, `sim-inspector.md`, `sim-tuner.md`
- Monolith HTTP 패턴: `reference_monolith_http_api.md`
- UE 5.7 소스 캐시: `reference_ue57_source_cache.md`, `reference_groom_physics_params.md`
