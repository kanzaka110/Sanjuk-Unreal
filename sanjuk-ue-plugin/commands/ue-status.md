---
name: ue-status
description: UE 에디터 + MCP 빠른 상태 조회
---

# UE 에디터 + MCP 빠른 상태 조회

/doctor보다 가벼운 빠른 상태 확인 명령어. 현재 에디터와 MCP 연결 상태를 한눈에 파악.

## 실행 순서

### 1단계: MCP 연결 상태 (병렬 실행)

세 서버 모두 동시에 확인:

```bash
# UnrealClaude
curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 http://localhost:3000

# runreal
which npx 2>/dev/null && echo "OK" || echo "MISSING"
```

**Monolith는 `monolith_status` 액션으로 실측** (단순 포트 응답이 아니라 버전/액션수/프로젝트 확인):
- MCP 노출 세션: `monolith_status()`
- 미노출 세션: `curl -s -X POST http://localhost:9316/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"monolith_status","arguments":{}}}'`
- 반환: `version` / `total_actions` / `namespaces` / `project_name` / `server_running`

### 2단계: Monolith 상세 (연결 성공 시만)

`monolith_status` 응답으로 헬스 판정:
1. `server_running == true` 확인
2. `total_actions` 기대치(≈1232) 비교 → 현저히 적으면 부분 로드/인덱싱 미완 의심
3. `project_name == "SB2"` 확인 (엉뚱한 프로젝트 연결 감지)
4. ⚠ `monolith_discover` 전체 호출로 모듈 enumerate 하지 말 것 (토큰 폭발) — status 요약으로 충분

### 3단계: 한 줄 요약 출력

```
🟢 Monolith v0.20.2 (1232액션/26네임스페이스, SB2) | 🟢 UnrealClaude | 🟢 runreal — 모든 MCP 정상
```

또는

```
🟢 Monolith (16모듈) | 🔴 UnrealClaude | 🟢 runreal — UnrealClaude 연결 실패, /recover 실행 권장
```

상태 코드:
- 🟢 정상 연결
- 🟡 응답 느림 (>2초)
- 🔴 연결 실패

**참고:** 전체 진단이 필요하면 `/doctor` 사용
