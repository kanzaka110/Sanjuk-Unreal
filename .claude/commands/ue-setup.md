# 새 UE 프로젝트 초기 세팅 자동화

새 UE 프로젝트를 MCP 작업 환경에 연결하는 셋업 명령어.

## 입력

필수:
- 프로젝트 이름
- UE 버전 (5.5 / 5.6 / 5.7)
- 프로젝트 경로 (기본: `C:/Users/ohmil/OneDrive/문서/Unreal Projects/{프로젝트명}`)

## 실행 순서

### 1단계: 프로젝트 존재 확인

```bash
ls "{프로젝트경로}/{프로젝트명}.uproject"
```

존재하지 않으면 에러 + UE에서 프로젝트 먼저 생성하라고 안내.

### 2단계: 플러그인 설치 안내

**Monolith (UE 5.7 필수):**
1. Fab에서 Monolith 다운로드 → Plugins/Monolith에 설치
2. .uproject에 플러그인 활성화 확인
3. 에디터 재시작 → 포트 9316 확인

**UnrealClaude (선택):**
1. GitHub에서 릴리스 다운로드
2. Plugins/UnrealClaude에 설치
3. 에디터 재시작 → 포트 3000 확인

### 3단계: MCP 설정 업데이트

`.mcp.json`에 새 프로젝트용 경로 반영 필요 시 안내.
(현재 설정이 MonolithTest 고정이므로 프로젝트별 분기가 필요한지 확인)

### 4단계: CLAUDE.md 업데이트

CLAUDE.md의 UE5 프로젝트 섹션에 새 프로젝트 추가:
- 프로젝트명, UE 버전, 경로
- 설치된 플러그인 목록

### 5단계: 연결 검증

1. `/ue-status` 실행하여 MCP 연결 확인
2. Monolith에서 새 프로젝트의 에셋 조회 테스트
3. 성공 시 메모리에 프로젝트 정보 저장

### 6단계: 최종 체크리스트

- [ ] .uproject 확인
- [ ] Monolith 플러그인 설치 및 연결
- [ ] UnrealClaude 설치 (선택)
- [ ] MCP 설정 반영
- [ ] CLAUDE.md 업데이트
- [ ] 연결 테스트 통과
