# MCP 생태계 & AI-UE 연동

> 2026-04-06 브리핑 | [목차로 돌아가기](00_INDEX.md)

---

## 현황

MCP(Model Context Protocol)는 AI 에이전트(Claude, Cursor 등)가 UE 에디터를 자연어로 제어하는 프로토콜. **Epic 공식 MCP는 아직 없으며**, 모두 커뮤니티/서드파티 프로젝트.

---

## 주요 MCP 서버 비교

| 서버 | 액션 수 | 특징 | 플러그인 필요 | 애니메이션 지원 |
|------|---------|------|--------------|----------------|
| **Monolith v0.12.0** | 1,125 / 15모듈 | 가장 포괄적, HTTP 모드 | O (엔진 설치) | 시퀀스, 몽타주, ABP, Control Rig, PoseSearch 등 |
| **runreal/unreal-mcp** | 20 | Python Remote Exec, 플러그인 불필요 | X | 커스텀 스크립트로 확장 |
| **ChiR24/Unreal_mcp** | - | C++ Bridge + TS 서버 | O | **Chaos Cloth 유일 지원** |
| **chongdashu/unreal-mcp** | - | Remote Control API | X | Experimental |

---

## 추천 조합 (애니메이션 특화)

```
Monolith (메인, 1125 액션 / 15 모듈)
+ runreal/unreal-mcp (Python 확장 / UAF 대비)
+ ChiR24/Unreal_mcp (Cloth 시뮬레이션)
```

---

## 기타 MCP 프로젝트

- **Docker 공식 이미지**: `mcp/unreal-engine-mcp-server`
- **flopperam/unreal-engine-mcp**: 건축/구조물 특화
- **GenOrca/unreal-mcp**: Python + C++ 커스텀 도구

---

## 공식 AI 연동 (MCP 외)

- UE 5.7 **에디터 내 AI 어시스턴트**: 코드 생성, 단계별 안내 (MCP와 별개)

---

## TA 액션

- [ ] Monolith + runreal 조합 유지 및 최신 버전 추적
- [ ] Epic 공식 MCP 발표 모니터링
- [ ] ChiR24 MCP로 Chaos Cloth 자동화 테스트

---

## 참고 링크

- [Monolith GitHub](https://github.com/tumourlove/monolith)
- [runreal/unreal-mcp GitHub](https://github.com/runreal/unreal-mcp)
- [ChiR24/Unreal_mcp GitHub](https://github.com/ChiR24/Unreal_mcp)
