# Monolith MCP Tutorial - UE5 애니메이션을 AI로 제어하기

> 이 튜토리얼은 Unreal Engine 5.7에서 Monolith MCP 플러그인을 사용하여
> Claude Code로 애니메이션 에셋을 자연어로 제어하는 방법을 초보자도 따라할 수 있도록 안내합니다.

## 목차

1. [사전 준비](01-Prerequisites.md) - 필요한 소프트웨어 설치
2. [Monolith 설치](02-Installation.md) - 플러그인 다운로드 및 프로젝트 설정
3. [Claude Code 연결](03-Connect-Claude-Code.md) - MCP 서버 연결 및 검증
4. [기본 사용법](04-Basic-Usage.md) - 첫 번째 AI 명령어 실행
5. [애니메이션 워크플로우](05-Animation-Workflow.md) - AnimSequence, Montage, BlendSpace
6. [Animation Blueprint](06-Animation-Blueprint.md) - State Machine, 트랜지션, 노드 연결
7. [Control Rig](07-Control-Rig.md) - 리그 조작, 노드 와이어링
8. [실전 예제](08-Practical-Examples.md) - 캐릭터 로코모션 세팅 자동화
9. [트러블슈팅](09-Troubleshooting.md) - 자주 발생하는 문제와 해결법
10. [참고 자료](10-References.md) - 공식 문서, 커뮤니티, 관련 프로젝트

## 환경 요구사항

| 항목 | 요구사항 |
|------|---------|
| Unreal Engine | **5.7 이상** |
| OS | Windows (Mac/Linux 미지원) |
| AI 클라이언트 | Claude Code, Cursor, 또는 MCP 호환 클라이언트 |
| Python | 3.10+ (선택 - C++ 소스 인덱싱 시) |

## 현재 프로젝트 상태

| 프로젝트 | UE 버전 | Monolith 호환 |
|----------|---------|---------------|
| MetaHumans | 5.6 | ❌ 5.7 업그레이드 필요 |
| MetaHumans_5_5 | 5.5 | ❌ 5.7 업그레이드 필요 |
| SlayAnimationSample | 5.6 | ❌ 5.7 업그레이드 필요 |

> ⚠️ 현재 프로젝트들은 UE 5.5~5.6이므로, 5.7로 업그레이드하거나 새 5.7 프로젝트를 만들어야 합니다.
