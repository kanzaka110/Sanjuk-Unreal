# runreal/unreal-mcp 완전 가이드

> UE5 에디터를 AI로 제어하는 가장 가벼운 방법 - 플러그인 설치 없이 Python Remote Execution으로 연결

## 이 튜토리얼은 누구를 위한 건가요?

- UE5를 사용하는 애니메이터/테크니컬 아티스트
- Claude Code나 Cursor 같은 AI 도구로 UE5를 자동화하고 싶은 분
- C++ 플러그인 빌드 없이 바로 MCP를 사용하고 싶은 분

## 목차

| 번호 | 제목 | 내용 |
|------|------|------|
| 01 | [runreal이란?](01-What-Is-runreal.md) | 개요, 아키텍처, 다른 MCP와의 차이점 |
| 02 | [설치 가이드](02-Installation.md) | Node.js 설치부터 MCP 연결까지 |
| 03 | [UE5 에디터 설정](03-UE5-Editor-Setup.md) | Python 플러그인 활성화, Remote Execution 설정 |
| 04 | [Claude Code 연결](04-Connect-Claude-Code.md) | settings.json 설정, 연결 확인, 트러블슈팅 |
| 05 | [기본 도구 사용법](05-Basic-Tools.md) | 19개 MCP 도구 완전 가이드 |
| 06 | [Python 스크립팅 기초](06-Python-Scripting-Basics.md) | editor_run_python으로 UE5 제어하기 |
| 07 | [애니메이션 워크플로우](07-Animation-Workflow.md) | AnimSequence, Montage, BlendSpace, ABP |
| 08 | [Control Rig & Physics](08-ControlRig-Physics.md) | Control Rig, IK Rig, Physics Asset, Retargeting |
| 09 | [실전 자동화 레시피](09-Automation-Recipes.md) | 배치 이름변경, 에셋 스캔, 머티리얼 생성 등 |
| 10 | [Monolith와 함께 쓰기](10-With-Monolith.md) | 동시 설정, 역할 분배, 하이브리드 전략 |
| 11 | [트러블슈팅](11-Troubleshooting.md) | 자주 겪는 문제와 해결법 |
| 12 | [참고자료](12-References.md) | 공식 문서, 커뮤니티, Python API 레퍼런스 |

## 프로젝트 정보

| 항목 | 내용 |
|------|------|
| **GitHub** | https://github.com/runreal/unreal-mcp |
| **npm** | https://www.npmjs.com/package/@runreal/unreal-mcp |
| **버전** | 0.1.4 (2026-04 기준) |
| **라이선스** | MIT (무료) |
| **UE 요구사항** | 5.4 이상 |
| **외부 의존성** | Node.js 18+ |
| **개발사** | RUNREAL (runreal.dev) |

## 핵심 장점

1. **플러그인 설치 불필요** - UE 내장 Python Remote Execution만 사용
2. **P4/Git에 영향 없음** - 프로젝트 파일 수정 제로
3. **Python API 전체 접근** - `editor_run_python`으로 UE Python API 무제한 사용
4. **설치 30초** - `npx @runreal/unreal-mcp` 한 줄이면 끝
5. **UAF 대비 최적** - UAF Python API 공개 시 별도 업데이트 없이 즉시 활용
