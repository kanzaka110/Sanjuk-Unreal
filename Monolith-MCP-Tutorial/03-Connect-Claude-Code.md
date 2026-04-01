# 3. Claude Code 연결

## 3.1 연결 방법

### Step 1: UE 에디터가 실행 중인지 확인

Output Log에 다음 메시지가 있어야 합니다:
```
LogMonolith: Monolith MCP server listening on port 9316
```

### Step 2: Claude Code 실행

**프로젝트 폴더에서** Claude Code를 실행합니다:

```bash
# 프로젝트 루트로 이동
cd "C:\Users\ohmil\OneDrive\문서\Unreal Projects\MonolithTest"

# Claude Code 실행
claude
```

> 💡 Claude Code는 현재 디렉토리의 `.mcp.json`을 **자동 감지**합니다.
> 반드시 `.mcp.json`이 있는 폴더에서 실행하세요!

### Step 3: 연결 확인

Claude Code에서 다음을 입력하세요:

```
Monolith 서버에 연결되어 있니? monolith_discover를 호출해서 확인해줘.
```

정상이면 10개 모듈과 443개 액션 목록이 출력됩니다.

## 3.2 수동 연결 테스트

터미널에서 직접 확인할 수도 있습니다:

```bash
# MCP 서버에 도구 목록 요청
curl -X POST http://localhost:9316/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### 정상 응답 예시

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {"name": "monolith_discover", "description": "..."},
      {"name": "animation_query", "description": "..."},
      {"name": "blueprint_query", "description": "..."},
      ...
    ]
  }
}
```

### 실패 시 (connection refused)

```
curl: (7) Failed to connect to localhost port 9316: Connection refused
```

→ [트러블슈팅 가이드](09-Troubleshooting.md) 참조

## 3.3 Monolith 도구 구조 이해하기

Monolith는 **13개 MCP 도구**로 **443개 액션**을 제어합니다:

```
monolith_discover()          ← 전체 액션 목록 조회
├── animation_query(action, params)   ← 애니메이션 (115 액션)
├── blueprint_query(action, params)   ← 블루프린트
├── material_query(action, params)    ← 머티리얼
├── niagara_query(action, params)     ← 나이아가라 VFX
├── editor_query(action, params)      ← 에디터 기능
├── config_query(action, params)      ← 프로젝트 설정
├── search_query(action, params)      ← 프로젝트 검색
├── source_query(action, params)      ← C++ 소스 분석
├── ui_query(action, params)          ← UMG/위젯
└── core_query(action, params)        ← 핵심 유틸리티
```

### 사용 패턴

AI에게 자연어로 요청하면 됩니다. 내부적으로는 이렇게 동작합니다:

```
사용자: "ThirdPerson 캐릭터의 AnimBP에 Idle 스테이트를 추가해줘"
    ↓
Claude Code: animation_query("add_state", {"abp": "/Game/...", "name": "Idle"})
    ↓
Monolith → UE 에디터에서 실행
    ↓
결과 반환
```

하지만 이 내부 동작을 알 필요는 없습니다. **자연어로 요청하면 AI가 알아서 적절한 액션을 선택**합니다.

## 체크리스트

- [ ] UE 에디터 실행 중 (port 9316 리스닝)
- [ ] 프로젝트 폴더에서 Claude Code 실행
- [ ] `monolith_discover` 호출 성공
- [ ] (선택) curl로 수동 테스트 성공

---
[← 이전: Monolith 설치](02-Installation.md) | [다음: 기본 사용법 →](04-Basic-Usage.md)
