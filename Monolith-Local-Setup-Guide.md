# Monolith MCP 로컬 전용 설치 가이드

> 회사 Perforce에 올리지 않고 내 PC에서만 Monolith UE5 플러그인을 사용하는 방법

## 추천: 엔진 레벨 설치 (프로젝트 파일 무수정)

### Epic Launcher 설치 엔진인 경우

```
C:\Program Files\Epic Games\UE_5.7\Engine\Plugins\Marketplace\Monolith\
```

- 에디터 자동 인식, `Edit > Plugins`에서 활성화만 하면 됨
- 같은 엔진 쓰는 다른 프로젝트에서도 자동 사용 가능
- P4 워크스페이스에 아예 잡히지 않음

### 엔진도 P4 소스 빌드로 공유하는 경우

엔진 폴더도 P4 워크스페이스에 포함되어 있으면, 완전 독립 경로에 설치:

```
C:\MyLocalPlugins\Monolith\
```

인식시키는 방법 3가지 (택 1):

#### 방법 A: 환경변수 (파일 수정 제로, 가장 깨끗)

```bash
set UE_ADDITIONAL_PLUGIN_DIRS=C:\MyLocalPlugins
```

- 프로젝트/엔진 파일 어느 쪽도 수정 없음
- 시스템 환경변수에 등록하면 영구 적용

#### 방법 B: DefaultEngine.ini

```ini
; 본인 PC의 DefaultEngine.ini (로컬 전용, P4 체크아웃 안 함)
[/Script/Engine.Engine]
+AdditionalPluginDirectories=C:/MyLocalPlugins
```

#### 방법 C: .p4ignore (프로젝트 Plugins/ 폴더에 넣는 경우)

```
Plugins/Monolith/...
```

```bash
p4 set P4IGNORE=.p4ignore
```

---

## MCP 서버 설정 (항상 로컬 전용)

Claude Code MCP 설정은 원래 개인 PC에만 존재하므로 별도 조치 불필요:

```jsonc
// ~/.claude.json 또는 ~/.claude/settings.json
{
  "mcpServers": {
    "monolith": {
      "url": "http://localhost:8080"
    }
  }
}
```

---

## 주의사항

- `.uproject`에 Monolith 플러그인 의존성이 자동 추가되는지 확인 필요 (추가되면 팀 빌드 깨짐)
- Monolith는 순수 C++ 내장 HTTP 서버 → Python/Node.js 불필요
- Editor-only 플러그인인지 확인 (런타임 빌드 미포함이어야 안전)

---

## 추천 MCP 조합 (애니메이션 특화)

| MCP | 역할 | 비고 |
|-----|------|------|
| **Monolith** | 메인 | 115 애니메이션 액션, Control Rig, PoseSearch, Physics Asset |
| **runreal/unreal-mcp** | Python 확장/UAF 대비 | 플러그인 불필요, UE Python API 전체 접근 |
| **ChiR24/Unreal_mcp** | Cloth 시뮬레이션 | Chaos Cloth 바인딩 유일 지원 |

---

## UE5 MCP 전체 비교 (2026-04 조사 기준)

| 프로젝트 | Stars | 액션/도구 | 애니메이션 | UAF 대응 | 가격 |
|---------|-------|----------|----------|---------|------|
| **Monolith** | 32 | 815 액션 | 최고 (115) | 최고 | 무료 |
| **chongdashu/unreal-mcp** | 1,673 | BP/Actor 중심 | 없음 | 낮음 | 무료 |
| **flopperam/unreal-engine-mcp** | 716 | 40+ 도구 | 높음 | 중간 | 무료 |
| **kvick-games/UnrealMCP** | 553 | 씬 조작 | 기본 | 낮음 | 무료 |
| **ChiR24/Unreal_mcp** | 435 | 36 도구 | Cloth 포함 | 중간 | 무료 |
| **ClaudusBridge** (Fab) | N/A | 483+ 도구 | 높음 | 중간 | 유료 |
| **StraySpark** | N/A | 305 도구 | 중간 | 중간 | $29~$99 |
| **VibeUE** | - | 931 메소드 | 높음 | 중간 | 무료 |
| **runreal/unreal-mcp** | 92 | Python API | 간접 | 높음 | 무료 |
