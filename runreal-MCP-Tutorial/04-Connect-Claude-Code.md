# 04. Claude Code 연결

> runreal MCP 서버를 Claude Code에 등록하여 AI가 UE5 에디터를 제어할 수 있게 합니다.

## 방법 1: CLI 명령어로 추가 (가장 간단)

```bash
claude mcp add unreal-mcp -- npx -y @runreal/unreal-mcp
```

이 한 줄이면 끝입니다. `~/.claude/settings.local.json`에 자동 추가됩니다.

## 방법 2: 설정 파일 직접 편집

### 사용자 전역 설정 (모든 프로젝트에 적용)

파일: `~/.claude/settings.local.json`

```jsonc
{
  "mcpServers": {
    "unreal-mcp": {
      "command": "npx",
      "args": ["-y", "@runreal/unreal-mcp"]
    }
  }
}
```

### 프로젝트 전용 설정 (현재 프로젝트만)

파일: `{프로젝트루트}/.mcp.json`

```jsonc
{
  "mcpServers": {
    "unreal-mcp": {
      "command": "npx",
      "args": ["-y", "@runreal/unreal-mcp"]
    }
  }
}
```

### 글로벌 설치를 사용하는 경우

npx 대신 직접 실행:

```jsonc
{
  "mcpServers": {
    "unreal-mcp": {
      "command": "node",
      "args": ["C:/Users/{사용자}/AppData/Roaming/npm/node_modules/@runreal/unreal-mcp/dist/bin.js"]
    }
  }
}
```

## 방법 3: Cursor에서 사용

파일: `.cursor/mcp.json` 또는 Cursor Settings > MCP

```jsonc
{
  "mcpServers": {
    "unreal-mcp": {
      "command": "npx",
      "args": ["-y", "@runreal/unreal-mcp"]
    }
  }
}
```

## 방법 4: Claude Desktop에서 사용

파일: `%APPDATA%\Claude\claude_desktop_config.json`

```jsonc
{
  "mcpServers": {
    "unreal": {
      "command": "npx",
      "args": ["-y", "@runreal/unreal-mcp"]
    }
  }
}
```

## 연결 확인

### 1단계: UE5 에디터가 켜져 있는지 확인

에디터가 실행 중이고 Remote Execution이 활성화되어 있어야 합니다.

### 2단계: Claude Code에서 테스트

Claude Code를 열고 다음과 같이 물어보세요:

```
"현재 UE 프로젝트 정보를 알려줘"
```

정상이면 Claude가 `editor_project_info` 도구를 호출하고, 프로젝트 이름/엔진 버전/에셋 수 등을 반환합니다.

### 3단계: 등록된 MCP 서버 확인

```bash
claude mcp list
```

`unreal-mcp`가 목록에 보이면 등록 성공입니다.

## 연결 순서 (중요!)

```
1. UE5 에디터를 먼저 실행
2. Project Settings에서 Remote Execution 확인
3. Claude Code 실행 (MCP 서버가 자동 시작됨)
4. Claude에게 UE 관련 질문/명령
```

> **순서가 중요합니다!** MCP 서버는 시작할 때 UE 에디터를 찾습니다. 에디터가 나중에 켜지면 MCP 서버를 재시작해야 합니다.

## MCP 서버 재시작 방법

Claude Code에서:
```
/mcp
```
MCP 관리 화면에서 `unreal-mcp`를 재시작할 수 있습니다.

또는 Claude Code 자체를 재시작합니다.

## 다음 단계

연결이 되었으면 [05. 기본 도구 사용법](05-Basic-Tools.md)으로 이동하세요.
