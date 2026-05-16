# 에이전트 자동 트리거 룰

사용자 요청 패턴별로 어떤 에이전트를 자동 호출할지 명시. 5/16 MCP-First Workflow Architecture의 ⑤ 위임층(Delegation).

## 원칙

1. **Inspector 먼저, Tuner 나중** — 진단 없이 처방 금지
2. **연쇄 호출 가능** — Inspector → 결과 본 후 Tuner 자동 호출
3. **사용자가 명시적으로 거부할 수 있음** — "에이전트 안 쓰고 직접 해" 같은 지시 우선

## 트리거 표

### AnimBP 작업 (animbp-inspector / animbp-tuner)

| 사용자 요청 패턴 | 자동 호출 | 인풋 |
|----------------|---------|------|
| "ABP 변수가 어떻게 동작" / "왜 이런 값" / "어떻게 변하나" | **animbp-inspector** | 그래프명 + 변수명 또는 노드 ID |
| "ABP 분석해줘" / "현재 상태 어때" | **animbp-inspector** | 자산 경로 + 그래프명 |
| "이 노드 동작 진단" / "FootPlacement 왜 이래" | **animbp-inspector** | 노드 클래스 + 자산 경로 |
| "값 바꿔줘" / "이 변수 X로 설정" | **animbp-tuner** (Inspector 결과 후) | 처방 spec |
| "처방 적용해줘" / "방금 제안 적용" | **animbp-tuner** | Inspector 보고서 참조 |
| "transition 함수 만들어줘" / "GetTransitionState 빌드" | Inspector → Tuner 연쇄 | Phase 명시 |

### Simulation 작업 (sim-inspector / sim-tuner)

| 사용자 요청 패턴 | 자동 호출 | 인풋 |
|----------------|---------|------|
| "Groom 떨려" / "헤어가 뻣뻣해" / "헤어 시뮬 진단" | **sim-inspector** | Groom 자산 경로 |
| "옷 관통" / "Cloth 떨림" / "Chaos Cloth 진단" | **sim-inspector** | Cloth 자산 |
| "Physics Asset 검증" / "캡슐 콜리전 확인" | **sim-inspector** | PhysicsAsset 경로 |
| "Gravity Scale -981로" / "Damping 0.05로" / "이 파라미터 X" | **sim-tuner** (Inspector 결과 후) | 파라미터 spec |

### MCP / 워크플로우 작업 (직접 처리)

| 사용자 요청 패턴 | 처리 | 비고 |
|----------------|------|------|
| "discover 돌려줘" / "신규 액션 알려줘" | 직접 실행 `scripts/discover_monolith_actions.py` | 에이전트 X |
| "워크플로우 자동화" / "한 번에 돌려줘" | 직접 `scripts/workflows/apply_and_verify.py` | 에이전트 X |
| "복구해줘" / "ABP 복원" | 직접 `scripts/restore_*.py` 또는 의사결정 트리 | 복구 마스터 플랜 참조 |
| "리와인드 로그 재구현" | 직접 step1~6 시퀀스 | rewind-recorder 가이드 참조 |

## 연쇄 호출 패턴

### 패턴 A: 진단만
```
사용자: "PC_01 ABP의 Sprint 트랜지션 어떻게 되어있어?"
→ animbp-inspector 호출 (UpdateVariables + Sprint 관련 변수 dump)
→ 결과 보고
```

### 패턴 B: 진단 → 처방 (Inspector → Tuner)
```
사용자: "Sprint→Battle 시 turn 끼어드는 거 잡아줘"
→ animbp-inspector (현재 게이트 상태 진단)
→ Inspector 결과로 처방 도출
→ animbp-tuner (게이트 확장 적용)
→ apply_and_verify (PIE 검증)
→ 최종 보고
```

### 패턴 C: 직접 처리 (에이전트 우회)
```
사용자: "monolith.discover() 돌려서 미사용 액션 알려줘"
→ 직접 scripts/discover_monolith_actions.py 실행
→ 결과 보고
```

## Inspector 호출 시 컨텍스트 주입 필수

서브에이전트는 CLAUDE.md / 메모리 / 룰을 자동 상속받지 못함. 호출 시 다음을 명시 포함:

- **자산 경로**: `/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP`
- **현재 작업 컨텍스트**: 어떤 진단/처방을 위한 호출인지
- **관련 변수/노드**: 알려진 ID 또는 이름
- **이전 작업 참조**: 관련 Briefing 문서 경로

## Tuner 호출 시 필수 사전조건

1. **Inspector 보고서가 반드시 선행** — Tuner 단독 호출 금지 (정의에도 명시)
2. **dry-run 옵션 명시** — 처방 spec에 어떤 변경이 일어날지 사전 출력
3. **백업 자동 생성 확인** — `@backup_apply_verify` 데코레이터 또는 명시적 dump

## 모니터링 / 갱신

- 에이전트 호출 빈도가 0이면 트리거 룰 부적합 → 패턴 보강
- 에이전트가 부적절한 답을 내면 인풋 컨텍스트 부족 → 주입 명세 보강
- 새 작업 도메인 (예: Niagara) 추가 시 새 에이전트 정의 + 트리거 표 추가

## 환경 제약

- 서브에이전트는 Monolith 직접 호출 불가 (메인 에이전트만 가능)
- Inspector는 dump/grep/read 만, Tuner는 메인이 호출하는 RPC 결과를 받아 처리
- GCP 환경에서는 Monolith 안 돌아감 — Inspector도 메모리/문서 기반 일반 답만 가능
