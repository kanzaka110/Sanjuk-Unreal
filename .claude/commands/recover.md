# 복구 — 알려진 실패 시나리오 자동 복구

MCP 서버 장애, UE5 빌드 실패 등 알려진 문제를 자동으로 진단하고 복구하는 명령어.

## 실행 순서

### 1단계: 현재 상태 진단

아래 항목을 병렬로 점검하여 실패 시나리오를 식별:

1. MCP 서버 연결: `curl -s -o /dev/null -w "%{http_code}" http://localhost:9316/mcp`
2. MCP 서버 연결: `curl -s -o /dev/null -w "%{http_code}" http://localhost:3000`
3. Git 상태: `git status` + `git fetch origin`
4. UE5 에디터 프로세스: `tasklist | grep -i UnrealEditor` (Windows)

### 2단계: 실패 시나리오별 복구 레시피 실행

감지된 문제에 대해 아래 레시피를 **순서대로** 실행:

---

#### 레시피 A: Monolith MCP 연결 실패 (포트 9316)

**증상:** curl 응답 없음 또는 connection refused
**원인 분류:**
- UE5 에디터가 꺼져 있음
- Monolith 플러그인이 로드되지 않음
- 포트 충돌

**복구 단계:**
1. UE5 에디터 프로세스 확인: `tasklist | grep -i UnrealEditor`
2. 에디터가 꺼져 있으면 → 사용자에게 "UE5 에디터를 열고 MonolithTest 프로젝트를 로드하세요" 안내
3. 에디터가 켜져 있으면 → 포트 확인: `netstat -an | grep 9316`
   - 포트 사용 중이 아니면 → "에디터 Output Log에서 Monolith 플러그인 로드 상태를 확인하세요"
   - 포트 사용 중이면 → "Monolith 서버가 실행 중이지만 응답하지 않음. 에디터를 재시작하세요"
4. 복구 후 재점검: curl로 연결 재확인

---

#### 레시피 B: UnrealClaude Bridge 연결 실패 (포트 3000)

**증상:** curl 응답 없음
**원인 분류:**
- Node 프로세스 미실행
- 브릿지 스크립트 경로 오류
- UE5 에디터 미실행

**복구 단계:**
1. Node 프로세스 확인: `tasklist | grep -i node`
2. Node 미실행 → 브릿지 수동 시작 시도:
   ```
   node "C:/Users/ohmil/OneDrive/문서/Unreal Projects/MonolithTest/Plugins/UnrealClaude/Resources/mcp-bridge/index.js"
   ```
3. 스크립트 파일 존재 확인 → 없으면 "UnrealClaude 플러그인 재설치 필요" 안내
4. 복구 후 재점검

---

#### 레시피 C: Git Stale Branch (원격보다 뒤처짐)

**증상:** `git log HEAD..origin/master`에 커밋이 있음
**복구 단계:**
1. 로컬 변경사항 확인
2. 변경사항 없으면 → `git pull origin master`
3. 변경사항 있으면 → 사용자에게 선택지 제시:
   - `git stash && git pull && git stash pop`
   - 먼저 커밋 후 pull

---

#### 레시피 D: Git 충돌 상태

**증상:** `git status`에 "both modified" 또는 "Unmerged" 표시
**복구 단계:**
1. 충돌 파일 목록 표시
2. 각 파일의 충돌 내용 표시
3. 사용자에게 해결 방안 제시 (ours/theirs/수동)

---

#### 레시피 E: UE5 셰이더 컴파일 지연/실패

**증상:** 에디터 응답 없음, Monolith 타임아웃
**복구 단계:**
1. DerivedDataCache 삭제 안내:
   `rm -rf "C:/Users/ohmil/OneDrive/문서/Unreal Projects/MonolithTest/DerivedDataCache"`
2. Saved/ShaderDebugInfo 삭제 안내
3. 에디터 재시작 안내

---

### 3단계: 결과 리포트

| 시나리오 | 상태 | 조치 |
|---------|------|------|
| Monolith MCP | ✅ 정상 / 🔧 복구됨 / ❌ 수동 필요 | 상세 |
| UnrealClaude | ✅ 정상 / 🔧 복구됨 / ❌ 수동 필요 | 상세 |
| Git 동기화 | ✅ 최신 / 🔧 풀 완료 / ❌ 충돌 | 상세 |
| UE5 상태 | ✅ 정상 / ❌ 점검 필요 | 상세 |

### 4단계: 에스컬레이션

자동 복구 실패 시:
- 구체적인 에러 메시지와 로그 표시
- 수동 복구 단계를 번호 목록으로 제시
- 관련 문서 링크 안내 (Monolith-Local-Setup-Guide.md 등)
