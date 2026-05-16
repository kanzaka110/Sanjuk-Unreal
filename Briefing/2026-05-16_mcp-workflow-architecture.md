# 2026-05-16 — MCP-First Workflow Architecture

## 목표

PC_01 ABP / SB2 작업에서 **Monolith MCP를 최대한 활용**할 수 있는 5층 워크플로우 구조 정착. 어제 평가에서 식별된 leak (1,226 액션 중 ~50개만 사용 / 워크플로우 분리 / 에이전트 미정착) 해소.

성공 지표:
- 작업 시간 30~50% 단축 (수정 → PIE → 검증 자동화로)
- 미사용 액션 카탈로그 → 매월 재평가
- 모든 ABP 작업이 백업 → 적용 → 검증 사이클을 자동으로 돌게

---

## 5-Layer Architecture

```
┌────────────────────────────────────────────────────────────┐
│ ① 발견층 (Discovery)                                         │
│   monolith.discover() → .claude/state/action_catalog.json  │
│   ├─ 1,226 액션 자동 카탈로그                                │
│   ├─ 모듈별 분류 (Animation 115 / BP 88 / LogicDriver 66...)│
│   └─ 미사용 액션 강조 (사용 빈도와 비교)                       │
├────────────────────────────────────────────────────────────┤
│ ② 추상화층 (Abstraction)                                     │
│   scripts/lib/monolith_helpers.py                          │
│   ├─ name-based node lookup (hardcoded ID 제거)             │
│   ├─ Bulk operation wrappers                                │
│   ├─ retry / error 패턴 표준화                              │
│   └─ backup-apply-verify 데코레이터                          │
├────────────────────────────────────────────────────────────┤
│ ③ 작업층 (Operations) — 이미 정착됨                           │
│   scripts/{build_,wire_,inspect_,analyze_,restore_,dump_}* │
│   네이밍 컨벤션 그대로 유지                                   │
├────────────────────────────────────────────────────────────┤
│ ④ 자동화층 (Automation)                                       │
│   scripts/workflows/<scenario>.py                           │
│   "수정 → compile → save → PIE 시작 → N초 녹화 → 로그 파싱  │
│    → 결과 리포트" 한 명령으로                                 │
├────────────────────────────────────────────────────────────┤
│ ⑤ 위임층 (Delegation)                                         │
│   .claude/agents/ 정착 + .claude/rules/agent-triggers.md   │
│   "ABP 분석 시 무조건 inspector 먼저" 같은 자동 패턴            │
└────────────────────────────────────────────────────────────┘
```

---

## 디렉토리 구조 (목표)

```
Sanjuk-Unreal/
├── scripts/
│   ├── lib/                                     # ② 추상화층 (신규)
│   │   ├── __init__.py
│   │   ├── monolith_client.py                   # rpc(), discover()
│   │   ├── node_lookup.py                       # name-based lookup
│   │   ├── bulk_ops.py                          # build_*_from_spec wrappers
│   │   └── workflow_decorators.py               # @backup_apply_verify
│   ├── workflows/                               # ④ 자동화층 (신규)
│   │   ├── apply_and_verify.py                  # 수정→PIE→로그→리포트
│   │   ├── diagnose_noise.py                    # C1/C2/D1 시나리오 자동
│   │   ├── full_recovery.py                     # TRACK-A + TRACK-B 한 번에
│   │   └── transition_function_setup.py         # Phase 4.A~F 통합
│   ├── discover_monolith_actions.py             # ① 발견층 (신규, MVP-1)
│   └── (기존 작업층 그대로 — 119개 스크립트)
├── .claude/
│   ├── state/                                   # ① 발견층 결과 (신규)
│   │   ├── action_catalog.json                  # discover 결과 (자동 생성)
│   │   ├── action_usage.json                    # 호출 빈도 (선택, 후순위)
│   │   ├── unused_actions.md                    # 미사용 액션 리포트
│   │   └── catalog_history/                     # 월별 스냅샷
│   ├── rules/
│   │   └── agent-triggers.md                    # ⑤ 위임층 (신규)
│   └── agents/ (기존)
└── (기타 그대로)
```

---

## MVP 4단계 (1주일)

### MVP-1: Discovery 스크립트 (Day 1, 1~2시간)

**파일:** `scripts/discover_monolith_actions.py`

**기능:**
1. `monolith.discover()` 호출 → 전체 액션 리스트
2. 각 도메인별 `<domain>_query` action 메서드 추출 (animation_query, blueprint_query 등)
3. 모듈별 액션 카운트 출력
4. `.claude/state/action_catalog.json` 저장
5. (선택) 사용 추적 데이터 (`action_usage.json`) 와 비교 → 미사용 액션 리포트

**출력 예시:**
```
Total actions: 1,226
Modules:
  Animation:        115 (사용 12 / 미사용 103)
  Blueprint:         88 (사용 8 / 미사용 80)
  MonolithMesh:    242 (사용 0 / 미사용 242)
  ...
[ATTENTION] 도메인 미사용 액션 중 추천:
  - blueprint_query.build_graph_from_spec  ← 우리 restore_update_variables 대체
  - animation_query.trace_state_machine    ← [ANIM_REC] 보완
  - chooser_query.add_column               ← Phase 4.D 단순화
```

### MVP-2: Helper 라이브러리 (Day 2-3, 4~6시간)

**파일:** `scripts/lib/`

**핵심:**

```python
# monolith_client.py — 모든 rpc 호출 표준화
def rpc(action: str, params: dict, retries: int = 3, silent: bool = False) -> ...

# node_lookup.py — ID hardcoding 제거
def find_node_by_variable(graph_data, var_name) -> node_id
def find_node_by_function(graph_data, fn_name, fn_class=None) -> node_id
def find_var_get(graph_data, var_name) -> node_id  # K2Node_VariableGet 전용

# bulk_ops.py — 65 wire 한 번에
def bulk_connect(asset, graph, wires: list[Wire]) -> dict[ok|fail]
def build_format_text(asset, graph, format_str, position) -> node_id  # FT 패턴

# workflow_decorators.py
@backup_apply_verify(graph='UpdateVariables', tag='sprint_start')
def my_modification(): ...
# → 자동 dump_pre, 작업, compile, save, dump_post, diff
```

**효과:** 향후 모든 작업 코드량 30~40% 감소 + 깨질 위험 ↓.

### MVP-3: PIE 자동화 워크플로우 (Day 4, 3~4시간)

**파일:** `scripts/workflows/apply_and_verify.py`

**시그니처:**
```python
def apply_and_verify(
    apply_fn: Callable,
    pie_seconds: float = 5.0,
    log_filter: str = "[ANIM_REC]",
    expected_changes: dict = None,
) -> VerifyReport
```

**흐름:**
1. apply_fn 실행 (사용자 수정 함수)
2. compile_blueprint → error_count 0 확인
3. save_asset
4. `editor_console_command("ce StartPIE")` 자동 호출
5. `time.sleep(pie_seconds)` 동안 PIE 동작
6. `editor_console_command("StopPIE")` (또는 시간 만료)
7. SB2_2.log 에서 `[ANIM_REC]` 라인 추출 → 슬라이스
8. expected_changes 와 비교 → 보고서 생성
9. 결과 → `.claude/state/last_verify_report.json`

**효과:** 매 변경마다 5~10초로 검증. 현재는 수동 5~10분.

### MVP-4: Agent Triggers (Day 5, 2시간)

**파일:** `.claude/rules/agent-triggers.md`

**내용:**
```markdown
# 에이전트 자동 트리거 룰

| 사용자 요청 패턴 | 자동 호출 에이전트 | 인풋 |
|----------------|----------------|------|
| "ABP 변수가 어떻게 동작" / "왜 이런 값" | animbp-inspector | 그래프명 + 노드 |
| "처방 적용해줘" / "이 값 X로" | animbp-tuner (Inspector 결과 후) | 처방 spec |
| "Groom 떨려" / "옷 관통" | sim-inspector | asset path |
| "discover" / "신규 액션 알려줘" | (직접 — discover_monolith_actions.py) | — |
```

→ Claude가 자동으로 패턴 매칭. 사용자가 매번 "에이전트 호출해줘" 안 해도 됨.

---

## 작업 흐름 예시 (Before / After)

### Before (현재 — 5/13 FT 통합 작업)

```
사용자: "FT 8개를 1개로 통합하고 싶어"
1. 직접 dump 스크립트 작성 (analyze_animrec.py, inspect_animrec_ft.py)
2. 수동 분석 → 65개 wire 매핑 정리 (1시간)
3. step1, step2, step4, step6 스크립트 4개 별도 작성 (2시간)
4. 각각 수동 실행 + 사이사이 PIE 검증 (1시간)
총: 4~5시간
```

### After (MVP 적용 후)

```
사용자: "FT 8개를 1개로 통합해줘"
1. animbp-inspector 자동 호출 (위임층) → graph dump + 와이어 매핑 자동
2. animbp-tuner 호출 → bulk_connect 한 번에 65 wire (추상화층)
3. apply_and_verify가 PIE → [ANIM_REC] 검증 → 리포트 (자동화층)
총: 30분 ~ 1시간
```

---

## 기존 작업과의 통합 / 마이그레이션

기존 119개 스크립트는 **그대로 유지**, 신규 작업부터 lib/ 활용:

| 작업 | 처리 |
|------|------|
| 기존 step1~6 같은 스크립트 | 그대로 유지 (검증된 작업) |
| Phase 4 신규 작업 (transition function) | lib/ + workflows/ 활용 |
| restore_update_variables.py | lib/bulk_ops 로 리팩토링 (선택, ROI 보고) |

마이그레이션 강제 안 함. 신규 작업이 자연스럽게 lib/ 에 의존하면 점진 통합.

---

## 일정

| Day | 작업 | 환경 |
|-----|------|------|
| 1 (오늘) | Briefing 문서 + MVP-1 스켈레톤 작성 | GCP |
| 2 | MVP-1 로컬 PC 첫 실행 → action_catalog.json 생성 → 미사용 액션 리포트 | 로컬 PC |
| 2-3 | MVP-2 lib/ 작성 + 첫 사용 (restore_update_variables.py 일부 리팩) | 로컬 PC |
| 4 | MVP-3 apply_and_verify.py 작성 + 시범 실행 | 로컬 PC |
| 5 | MVP-4 agent-triggers.md 작성 + 자동 호출 패턴 검증 | 로컬 PC |
| 6-7 | 기존 Phase 4 (Transition 함수화) 작업이 새 구조로 진행되는지 검증 | 로컬 PC |

---

## 리스크 + 완화

| 리스크 | 가능성 | 완화 |
|--------|-------|------|
| `monolith.discover()` 같은 메타 액션이 없을 수 있음 | 中 | 첫 호출에서 검증. 없으면 모듈별 수동 enumerate |
| Helper lib 의존성으로 디버깅 어려워짐 | 中 | 첫 단계는 thin wrapper만. 각 함수가 직접 호출 가능 |
| PIE 자동화가 세션마다 다르게 동작 | 高 | apply_and_verify에 dry-run 옵션 + 실패 시 정상적 fallback |
| 에이전트가 자동 호출돼도 동작이 다를 수 있음 | 中 | trigger rule이 "추천"이라고 명시. 사용자가 거부 가능 |

---

## 작성해야 할 신규 파일 (MVP 1주)

| 파일 | Phase | 역할 |
|------|-------|------|
| `scripts/discover_monolith_actions.py` | MVP-1 | 액션 카탈로그 생성 |
| `scripts/lib/monolith_client.py` | MVP-2 | RPC 표준화 |
| `scripts/lib/node_lookup.py` | MVP-2 | name-based lookup |
| `scripts/lib/bulk_ops.py` | MVP-2 | bulk_connect 등 |
| `scripts/lib/workflow_decorators.py` | MVP-2 | @backup_apply_verify |
| `scripts/workflows/apply_and_verify.py` | MVP-3 | PIE 자동화 |
| `.claude/rules/agent-triggers.md` | MVP-4 | 에이전트 자동 트리거 |

> GCP에서 작성 가능: 모두. 단 MVP-1, MVP-3 동작 검증은 로컬 PC 필요.

---

## 환경 제약

- 설계 / 스켈레톤 코드 작성: GCP 가능
- discover() 실행 / PIE 자동화 검증: 로컬 PC + Monolith 동작 상태 필요
- agent-triggers는 Claude Code 클라이언트 동작에 의존 — 로컬/GCP 양쪽에서 검증
