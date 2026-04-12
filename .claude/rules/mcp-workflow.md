# MCP 워크플로우 규칙

## 도구 우선순위 (반드시 준수)

1. **Monolith** (localhost:9316) — 에디터 제어 전체. 항상 최우선 시도
2. **UnrealClaude** (localhost:3000) — UE5 API 문서 컨텍스트, C++ 참조용
3. **runreal** (stdio) — Python 스크립트 자동화, 배치 작업

## Monolith 모듈 (v0.12.0, 1,125 액션)

| 모듈 | 액션 수 | 용도 |
|------|---------|------|
| Animation | 115 | AnimSequence, Montage, BlendSpace, ABP, State Machine |
| Blueprint | 88 | 그래프 편집, 변수, 리플리케이션 |
| Material | 57 | 머티리얼 함수, 파라미터 |
| Niagara | 96 | 파티클, 이미터, 다이나믹 인풋 |
| MonolithMesh | 242 | 레벨 디자인, 공간 쿼리, 프로시저럴 지오메트리 |
| MonolithGAS | 130 | 어빌리티, 어트리뷰트, 게임플레이 이펙트 |
| MonolithAI | 229 | BT, Blackboard, StateTree, EQS, Perception |
| MonolithUI | 42 | 위젯 블루프린트, UI 템플릿 |
| MonolithLogicDriver | 66 | 상태 머신 생성/제어 |

## 액션 패턴

```
# 조회: list → inspect 순서
animation_query("list_sequences", ...)
animation_query("inspect_abp", ...)

# 생성: create → configure
animation_query("create_montage", ...)
animation_query("add_notify", ...)

# 벌크 생성: JSON spec 활용
build_behavior_tree_from_spec(spec_json)
build_state_tree_from_spec(spec_json)
```

## 실패 처리 순서

1. Monolith 연결 실패 → UE 에디터 실행 확인 → `/recover`
2. 액션 실패 → 에셋 경로 확인 (Copy Reference) → 재시도
3. 인덱싱 미완료 → "LogMonolith" 로그 확인 → 대기 후 재시도
4. Monolith 불가 시 → runreal Python 스크립트로 폴백
5. MCP 전체 불가 시 → 문서/가이드 기반 수동 안내

## 작업 전 필수 확인

- `/doctor`로 MCP 전체 상태 점검 (첫 작업 시)
- Monolith 포트 9316 응답 확인 (PreToolUse 훅이 자동 수행)
- 에셋 경로는 항상 에디터에서 Copy Reference로 정확한 경로 취득
