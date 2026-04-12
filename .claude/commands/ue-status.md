# UE 에디터 + MCP 빠른 상태 조회

/doctor보다 가벼운 빠른 상태 확인 명령어. 현재 에디터와 MCP 연결 상태를 한눈에 파악.

## 실행 순서

### 1단계: MCP 연결 상태 (병렬 실행)

세 서버 모두 동시에 확인:

```bash
# Monolith
curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 http://localhost:9316/mcp

# UnrealClaude
curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 http://localhost:3000

# runreal
which npx 2>/dev/null && echo "OK" || echo "MISSING"
```

### 2단계: Monolith 상세 (연결 성공 시만)

Monolith가 응답하면 추가 정보 수집:
1. `tools/list` 호출 → 사용 가능한 모듈 수 확인
2. 현재 열린 프로젝트/레벨 정보 (가능 시)

### 3단계: 한 줄 요약 출력

```
🟢 Monolith (16모듈) | 🟢 UnrealClaude | 🟢 runreal — 모든 MCP 정상
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
