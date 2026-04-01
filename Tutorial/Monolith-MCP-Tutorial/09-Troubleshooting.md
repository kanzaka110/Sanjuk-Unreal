# 9. 트러블슈팅

## 가장 흔한 문제들

### 문제 1: "Connection refused" - MCP 서버에 연결할 수 없음

**증상:**
```
curl: (7) Failed to connect to localhost port 9316: Connection refused
```

**원인 & 해결:**

| 원인 | 해결 방법 |
|------|----------|
| UE 에디터가 실행 안 됨 | 에디터 실행 후 다시 시도 |
| Monolith 플러그인 비활성화 | Edit → Plugins → Monolith 활성화 → 재시작 |
| 포트 충돌 | Editor Preferences에서 포트 변경 후 `.mcp.json`도 수정 |
| 방화벽 차단 | Windows 방화벽에서 port 9316 허용 |

**확인 방법:**
```bash
# 포트가 열려 있는지 확인
netstat -an | findstr 9316

# Output Log 확인
# UE 에디터 → Window → Developer Tools → Output Log
# 필터: LogMonolith
```

### 문제 2: Claude Code가 Monolith 도구를 인식 못 함

**증상:** "monolith_discover를 모릅니다" 같은 응답

**체크리스트:**
1. `.mcp.json` 파일이 **프로젝트 루트**에 있는지 확인
2. Claude Code를 `.mcp.json`이 있는 **같은 폴더에서** 실행했는지 확인
3. `.mcp.json`의 `type`이 `"http"` 인지 확인 (Claude Code용)

```bash
# .mcp.json 위치 확인
ls -la .mcp.json

# 내용 확인
cat .mcp.json
```

**해결:**
```bash
# Claude Code 재시작
exit  # 현재 세션 종료
claude  # 다시 실행
```

### 문제 3: Transport type 불일치

**증상:** 연결은 되지만 응답이 없거나 에러

**원인:** Claude Code와 Cursor의 transport type이 다름

```json
// Claude Code → "http" 사용
{"type": "http", "url": "http://localhost:9316/mcp"}

// Cursor/Cline → "streamableHttp" 사용
{"type": "streamableHttp", "url": "http://localhost:9316/mcp"}
```

### 문제 4: 에셋을 찾을 수 없음

**증상:** "에셋을 찾을 수 없습니다" 에러

**해결:**
1. Content Browser에서 에셋 우클릭 → **Copy Reference**
2. 복사된 경로를 AI에게 전달
3. 경로 형식: `/Game/Characters/Animations/Idle_Anim`

```
❌ "Idle 애니메이션을 수정해줘"
✅ "/Game/Characters/Animations/Idle_Anim 을 수정해줘"
```

### 문제 5: Blueprint 전용 프로젝트에서 "빌드 실패"

**증상:** 에디터 실행 시 컴파일 에러

**해결:**
- GitHub Releases에서 **ZIP 다운로드** (프리컴파일 DLL 포함)
- Git clone이 아닌 릴리스 ZIP 사용

### 문제 6: 인덱싱이 완료되지 않음

**증상:** 도구는 연결되지만 에셋 검색이 안 됨

**해결:**
1. Output Log에서 인덱싱 진행 상태 확인
2. 대규모 프로젝트는 인덱싱에 2~3분 소요
3. "LogMonolith: Indexing complete" 메시지 대기

### 문제 7: 자동 업데이트 문제

**Monolith 수동 업데이트:**
```bash
cd YourProject/Plugins/Monolith
git pull origin main
# 에디터 재시작
```

**자동 업데이트 비활성화:**
- Editor Preferences → Monolith → Auto-Update → Off

## 로그 확인 방법

```
1. UE 에디터 → Window → Developer Tools → Output Log
2. 필터에 "LogMonolith" 입력
3. 에러 메시지 확인

주요 로그 메시지:
- "Monolith MCP server listening on port 9316" → 정상
- "Failed to bind port 9316" → 포트 충돌
- "Indexing complete" → 인덱싱 완료
- "Plugin loaded successfully" → 플러그인 로드 성공
```

## 도움 받기

- **GitHub Issues**: https://github.com/tumourlove/monolith/issues
- **GitHub Wiki FAQ**: https://github.com/tumourlove/monolith/wiki/FAQ

---
[← 이전: 실전 예제](08-Practical-Examples.md) | [다음: 참고 자료 →](10-References.md)
