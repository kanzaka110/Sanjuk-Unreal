# MCP 헬스체크 — 전체 환경 진단

모든 MCP 서버와 작업 환경을 단계별로 점검하는 진단 명령어.

## 실행 순서

### 1단계: MCP 서버 상태 점검

각 MCP 서버에 대해 라이프사이클 단계별로 확인:

**Monolith (localhost:9316)** — 최우선
1. 연결 테스트: `curl -s -o /dev/null -w "%{http_code}" http://localhost:9316/mcp` 실행
2. 응답 코드 200이면 ✅, 아니면 ❌ + 실패 단계 기록
3. 연결 성공 시: Monolith 도구 목록 확인 (MCP 도구 호출 가능 여부)

**UnrealClaude Bridge (localhost:3000)** — 보조
1. 연결 테스트: `curl -s -o /dev/null -w "%{http_code}" http://localhost:3000` 실행
2. 브릿지 노드 프로세스 확인: `tasklist | grep -i node` (Windows)
3. 응답 상태 기록

**runreal (stdio)** — 확장
1. `npx -y @runreal/unreal-mcp --help` 실행 가능 여부 확인
2. Python 의존성 확인

### 2단계: UE5 프로젝트 상태

1. MonolithTest 프로젝트 경로 존재 확인:
   `ls "C:/Users/ohmil/OneDrive/문서/Unreal Projects/MonolithTest/MonolithTest.uproject"`
2. Monolith 플러그인 설치 확인:
   `ls "C:/Users/ohmil/OneDrive/문서/Unreal Projects/MonolithTest/Plugins/Monolith"`
3. UnrealClaude 플러그인 설치 확인:
   `ls "C:/Users/ohmil/OneDrive/문서/Unreal Projects/MonolithTest/Plugins/UnrealClaude"`

### 3단계: Git 및 동기화 상태

1. `git status` — 로컬 변경사항
2. `git log HEAD..origin/master --oneline` — 원격 대비 상태 (fetch 먼저)
3. 현재 브랜치 확인

### 4단계: 메모리 시스템 상태

1. `~/.claude/projects/C--dev-Sanjuk-Unreal/memory/MEMORY.md` 존재 확인
2. 메모리 파일 개수 및 마지막 수정일 확인

### 5단계: 결과 리포트

모든 점검 결과를 단일 테이블로 출력:

| 구분 | 항목 | 상태 | 실패 단계 |
|------|------|------|-----------|
| MCP | Monolith (9316) | ✅/❌ | — |
| MCP | UnrealClaude (3000) | ✅/❌ | — |
| MCP | runreal (stdio) | ✅/❌ | — |
| UE5 | MonolithTest 프로젝트 | ✅/❌ | — |
| UE5 | Monolith 플러그인 | ✅/❌ | — |
| UE5 | UnrealClaude 플러그인 | ✅/❌ | — |
| Git | 로컬 상태 | clean/dirty | — |
| Git | 원격 동기화 | 최신/N커밋 뒤처짐 | — |
| 메모리 | 파일 수 | N개 | — |

### 6단계: 권장 조치

❌ 항목이 있으면 각각에 대해 복구 방법 제시:
- MCP 실패 → `/recover` 명령어 안내
- Git 뒤처짐 → `/pull` 명령어 안내
- 플러그인 누락 → 설치 가이드 링크

**모두 ✅이면:** "모든 시스템 정상 — 작업 준비 완료" 출력
