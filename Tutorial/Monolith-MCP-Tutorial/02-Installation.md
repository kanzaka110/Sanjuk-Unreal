# 2. Monolith 설치

## 2.1 플러그인 다운로드

### 방법 A: Git Clone (권장)

프로젝트 폴더로 이동하여 Plugins 폴더에 클론합니다:

```bash
# 프로젝트 폴더로 이동 (예시)
cd "C:\Users\ohmil\OneDrive\문서\Unreal Projects\MonolithTest"

# Plugins 폴더 생성 (없으면)
mkdir -p Plugins

# Monolith 클론
cd Plugins
git clone https://github.com/tumourlove/monolith.git Monolith
```

### 방법 B: ZIP 다운로드

1. https://github.com/tumourlove/monolith/releases 접속
2. 최신 릴리스 (v0.10.0) 의 `Monolith-v0.10.0.zip` 다운로드
3. 압축 해제
4. `YourProject/Plugins/Monolith/` 경로에 배치

### 설치 확인

설치 후 폴더 구조가 이렇게 되어야 합니다:

```
MonolithTest/
├── Content/
├── Config/
├── Plugins/
│   └── Monolith/           ← 여기!
│       ├── Monolith.uplugin
│       ├── Source/
│       ├── Skills/
│       ├── Binaries/       ← 프리컴파일 DLL (ZIP 다운로드 시)
│       └── ...
├── MonolithTest.uproject
└── .mcp.json               ← 다음 단계에서 생성
```

> 💡 `Monolith.uplugin` 파일이 `Plugins/Monolith/` 바로 아래에 있어야 합니다.
> `Plugins/Monolith/monolith/` 처럼 이중 폴더가 되지 않도록 주의하세요.

## 2.2 MCP 설정 파일 생성

프로젝트 **루트** 폴더 (`.uproject` 파일이 있는 곳)에 `.mcp.json` 파일을 만듭니다.

### Claude Code용 설정

```json
{
  "mcpServers": {
    "monolith": {
      "type": "http",
      "url": "http://localhost:9316/mcp"
    }
  }
}
```

### Cursor / Cline용 설정

```json
{
  "mcpServers": {
    "monolith": {
      "type": "streamableHttp",
      "url": "http://localhost:9316/mcp"
    }
  }
}
```

> ⚠️ **중요!** Claude Code는 `"http"`, Cursor/Cline은 `"streamableHttp"` — 이것을 틀리면 연결이 안 됩니다!

### 파일 생성 명령어

```bash
# 프로젝트 루트로 이동
cd "C:\Users\ohmil\OneDrive\문서\Unreal Projects\MonolithTest"

# Claude Code용 .mcp.json 생성
cat > .mcp.json << 'EOF'
{
  "mcpServers": {
    "monolith": {
      "type": "http",
      "url": "http://localhost:9316/mcp"
    }
  }
}
EOF
```

## 2.3 Claude Code 스킬 설치 (선택사항)

Monolith에 내장된 스킬을 설치하면, Claude Code가 애니메이션 작업 시 자동으로 최적의 명령을 사용합니다:

```bash
# Monolith 스킬을 Claude Code에 복사
cp -r Plugins/Monolith/Skills/* ~/.claude/skills/
```

설치되는 스킬:
- `unreal-animation` — Montage, ABP State Machine, BlendSpace 워크플로우
- `unreal-blueprints` — Blueprint 그래프 조작
- `unreal-materials` — Material 에디터
- 그 외 6개 도메인 스킬

## 2.4 Unreal Editor 실행

1. `.uproject` 파일을 더블클릭하여 UE 5.7 에디터 실행
2. 첫 실행 시 **자동 인덱싱** 시작 (30~60초)
3. **Output Log** 확인 방법:
   - 메뉴: `Window → Developer Tools → Output Log`
   - 필터에 `LogMonolith` 입력
4. 다음 메시지가 나오면 성공:

```
LogMonolith: Monolith MCP server listening on port 9316
```

### 플러그인이 안 보이는 경우

1. `Edit → Plugins` 메뉴
2. 검색창에 `Monolith` 입력
3. 체크박스 활성화
4. 에디터 재시작

## 체크리스트

- [ ] Monolith가 `Plugins/Monolith/`에 설치됨
- [ ] `.mcp.json` 파일이 프로젝트 루트에 생성됨
- [ ] (선택) Claude Code 스킬이 복사됨
- [ ] UE 에디터에서 `LogMonolith: ... listening on port 9316` 확인됨

---
[← 이전: 사전 준비](01-Prerequisites.md) | [다음: Claude Code 연결 →](03-Connect-Claude-Code.md)
