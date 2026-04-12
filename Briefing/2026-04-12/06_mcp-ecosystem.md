# 🆕 MCP 생태계 & AI-UE 연동

> 2026-04-12 브리핑 | [목차로 돌아가기](00_INDEX.md)

---

## MCP 서버 현황 (2026.04)

| 서버 | 액션 수 | 특징 | 상태 |
|------|---------|------|------|
| **Monolith** | 443+ | BP, Material, Animation, Niagara, UI 등 10 모듈 | 우리 주력 |
| 🆕 **StraySpark** | 207+ | AI 도구, Epic 포럼 공식 소개 | 신규 경쟁자 |
| **ChiR24/Unreal_mcp** | — | Cloth 시뮬레이션 유일 지원 | 유지 |
| **chongdashu/unreal-mcp** | — | Cursor/Windsurf/Claude Desktop | 범용 |
| **flopperam/unreal-engine-mcp** | — | 자연어 3D 월드 빌딩 | 특수 |
| **kvick-games/UnrealMCP** | — | AI 에이전트 UE 제어 | 범용 |

## 🆕 주요 변화

### StraySpark 등장
- Epic Developer Community 포럼에 공식 스레드 개설
- 207+ AI 도구로 UE5 에디터 자동화
- Monolith의 실질적 경쟁자 → 비교 분석 필요

### Docker 배포
- `mcp/unreal-engine-mcp-server` Docker 이미지 공개
- 컨테이너 기반 MCP 서버 배포 가능 → CI/CD 파이프라인 통합 잠재력

### Monolith 커뮤니티
- 원본(tumourlove) 외 다수 fork 활발
- 443 액션, 10 모듈 (우리는 v0.12.0, 1125 액션 / 16 모듈 버전 사용)

## TA 액션
- StraySpark 207+ 도구 목록 확인 → Monolith과 기능 비교
- Docker 배포 방식 → GCP에서의 MCP 서버 운영 가능성 검토

## 소스
- [Monolith GitHub](https://github.com/tumourlove/monolith) — 443 액션, 10 모듈
- [StraySpark 포럼](https://forums.unrealengine.com/t/strayspark-unreal-mcp-server-200-ai-tools-for-ue5-editor-automation-via-mcp/2707474)
- [Docker MCP](https://hub.docker.com/r/mcp/unreal-engine-mcp-server)
- [MCP Deep Dive](https://skywork.ai/skypage/en/A-Deep-Dive-into-the-UE5-MCP-Server-Bridging-AI-and-Unreal-Engine/1972113994962538496)
