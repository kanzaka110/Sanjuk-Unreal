# UE 작업별 에이전트 선택 규칙

UE5 작업 유형에 따라 최적의 에이전트를 자동 선택한다.

## 에이전트 매핑

| 작업 유형 | 에이전트 | 용도 |
|---------|---------|------|
| UE C++ 코드 작성 | `cpp-build-resolver` → `cpp-reviewer` | 빌드 에러 해결 + 코드 리뷰 |
| 블루프린트 아키텍처 | `architect` | 모듈 구조, 플러그인 의존성 설계 |
| 애니메이션 ABP 설계 | `planner` → `architect` | State Machine, TraitStack 설계 |
| MCP 서버 문제 | `build-error-resolver` | 연결/설정 오류 해결 |
| Python 자동화 (runreal) | `python-reviewer` | runreal 스크립트 리뷰 |
| 보안 (시크릿, API키) | `security-reviewer` | 노출된 시크릿 감지 |
| 문서/가이드 작성 | `doc-updater` | 튜토리얼, README 업데이트 |
| 성능 최적화 | `code-reviewer` | 프로파일링 결과 기반 리뷰 |

## UE C++ 작업 시 필수 체인

1. **코드 작성** → 직접 또는 `general-purpose` 에이전트
2. **빌드 검증** → `cpp-build-resolver` (실패 시 자동)
3. **코드 리뷰** → `cpp-reviewer` (UE 코딩 컨벤션 적용)
4. **보안 검사** → `security-reviewer` (API 키, 하드코딩 체크)

## 병렬 실행 가능한 조합

- `cpp-reviewer` + `security-reviewer` — 코드 리뷰와 보안 동시 검사
- `architect` + `Explore` — 설계 검토와 기존 코드 탐색 동시 수행
- `planner` + `docs-lookup` — 구현 계획 수립과 API 문서 조회 동시 수행

## 에이전트 사용 시 주의사항

- UE 도메인 컨텍스트(룰, CLAUDE.md)는 서브에이전트에 자동 주입되지 않음
- 에이전트 프롬프트에 UE 관련 컨텍스트를 명시적으로 포함할 것
- Monolith 액션은 메인 에이전트에서만 실행 (서브에이전트에서 MCP 직접 호출 불가)
