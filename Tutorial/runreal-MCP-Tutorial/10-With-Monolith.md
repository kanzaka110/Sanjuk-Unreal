# 10. Monolith와 함께 쓰기

> runreal과 Monolith를 동시에 사용하여 각각의 강점을 살리는 하이브리드 전략

## 왜 둘 다 쓰나요?

| 영역 | Monolith이 더 나은 이유 | runreal이 더 나은 이유 |
|------|----------------------|---------------------|
| AnimBlueprint 그래프 편집 | 전용 노드 와이어링 도구 | Python API로 불가능 |
| BlendSpace 생성 | 샘플 포인트 포함 원클릭 | 가능하지만 더 번거로움 |
| Control Rig 그래프 | 전용 그래프 조작 도구 | 매우 제한적 |
| PoseSearch/Motion Matching | **유일하게 지원** | 지원 없음 |
| 에셋 배치 이름변경 | 전용 도구 없음 | **Python으로 자유자재** |
| 커스텀 자동화 | C++ 빌드 필요 | **Python 스크립트만** |
| FBX 배치 임포트 | 전용 도구 없음 | **Python으로 바로** |
| 프로젝트 분석/보고서 | 에셋 검색은 가능 | **JSON 출력으로 상세** |
| 플러그인 설치 | C++ 플러그인 필요 | **설치 불필요** |
| UE 5.4~5.6 | 5.7 필수 | **5.4부터 지원** |

## 동시 설정 방법

### settings.local.json

```jsonc
// ~/.claude/settings.local.json
{
  "mcpServers": {
    "monolith": {
      "url": "http://localhost:8080"
    },
    "unreal-mcp": {
      "command": "npx",
      "args": ["-y", "@runreal/unreal-mcp"]
    }
  }
}
```

### CLI로 추가

```bash
claude mcp add unreal-mcp -- npx -y @runreal/unreal-mcp
claude mcp add monolith --url http://localhost:8080
```

## 역할 분배 가이드

### Monolith에게 맡기세요

- AnimBlueprint 스테이트 머신 생성
- AnimBlueprint에 노드 추가/연결
- Control Rig 그래프 편집
- PoseSearch 스키마/DB 설정
- BlendSpace 생성 + 샘플 포인트 추가
- Montage 섹션/슬롯 설정
- Niagara VFX 생성
- GAS (Gameplay Ability System)

### runreal에게 맡기세요

- 에셋 검색/목록/정보 조회
- 에셋 배치 이름변경
- FBX 배치 임포트
- 머티리얼 인스턴스 배치 생성
- 프로젝트 보고서/분석
- 미사용 에셋 찾기
- 레벨 액터 일괄 조작
- 커스텀 자동화 스크립트
- 시퀀서 키프레임 작업

### 협업 시나리오 예시

```
1단계 (runreal): "프로젝트의 모든 AnimSequence 목록을 알려줘"
    → editor_run_python으로 에셋 스캔

2단계 (Monolith): "Walk/Run/Idle을 사용하는 Locomotion BlendSpace를 만들어줘"
    → Monolith의 전용 BlendSpace 도구 사용

3단계 (Monolith): "ABP_Character에 Locomotion StateMachine을 추가하고 BlendSpace를 연결해줘"
    → Monolith의 ABP 그래프 편집 도구 사용

4단계 (runreal): "Characters 폴더의 모든 SkeletalMesh에 Physics Asset이 할당되어 있는지 확인해줘"
    → editor_run_python으로 배치 검증
```

## 컨텍스트 윈도우 관리

MCP 서버를 많이 등록하면 컨텍스트 윈도우를 소비합니다.

### 권장 사항

- UE 작업할 때는 **불필요한 MCP 서버를 비활성화** (Gmail, Notion 등)
- Monolith + runreal 두 개 정도가 적절
- ChiR24 (Cloth 전용)은 필요할 때만 활성화

### MCP 서버 토글 방법

Claude Code에서:
```
/mcp
```
MCP 관리 화면에서 개별 서버를 켜고 끌 수 있습니다.

## UAF 대비 전략

| 시기 | 전략 |
|------|------|
| **지금** (UAF Experimental) | Monolith(ABP/ControlRig) + runreal(Python 자동화) |
| **UE 5.8** (UAF 샘플 포함) | runreal의 `editor_run_python`으로 UAF Python API 실험 |
| **UE 5.9+** (UAF Production) | Monolith UAF 모듈 추가 기대 + runreal로 커스텀 확장 |

runreal은 UAF Python API가 공개되는 순간 **별도 업데이트 없이** 바로 활용할 수 있는 유일한 MCP입니다.

## 다음 단계

[11. 트러블슈팅](11-Troubleshooting.md)으로 이동하세요.
