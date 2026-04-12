# 핵심 요약 & 트렌드

> 2026-04-12 브리핑 | [목차로 돌아가기](00_INDEX.md)

---

## 한줄 요약

**AI 애니메이션 도구(Rokoko, Cascadeur, JALI)의 UE5 직결 파이프라인이 급속 성숙 중이며, UAF 5.8 실전 데뷔와 Mover Plugin 정식화가 2026 하반기 최대 분수령.**

---

## 5대 트렌드

### 1. 🆕 AI 모캡/애니메이션 도구의 무료화 + UE5 직결
- **Rokoko Create**: 무료 풀바디 애니메이션 생성 도구 출시 (2026.04)
- **Cascadeur 2026.1**: Root Motion + AutoPosing AI, UE5 Live Link 플러그인 (유료 구독)
- **JALI**: NAB 2026에서 실시간 페이셜 애니메이션 시연 — Heart & Mask 시스템으로 감정 블렌딩
- 이전 대비: Cascadeur Live Link가 4/9 → 4/12 사이 정식 출시 확인

### 2. GASP 5.7 + Mover Plugin 안착
- 400개 신규 애니메이션 추가
- Mover Plugin (Experimental) — CharacterMovementComponent 후속
- Simple Spring / Smooth Walking 두 가지 이동 모드
- 슬라이드 메카닉 추가 (경사면 기반 속도 변화)
- 변경 없음: 4/6 브리핑 대비 추가 업데이트 없음

### 3. UAF/AnimNext — 5.8 실전 데뷔 준비
- 5.8에서 GASP 캐릭터 1개를 UAF로 완전 구성 예정
- Control Rig + UAF 통합 진행 (절차적 노드 이동)
- 🆕 커뮤니티 실습 가이드 등장: "Mover 2.0 + UAF + Motion Matching in 5.7" (David Martinez)
- 변경 없음: 5.8 로드맵은 4/6과 동일

### 4. MCP 생태계 확장
- Monolith: 443 액션 → 최신 fork에서 지속 업데이트 중
- 🆕 StraySpark: 207+ AI 도구, Epic 포럼에 공식 소개
- ChiR24/Unreal_mcp: Cloth 시뮬레이션 지원 유지
- Docker 이미지 배포 시작 (mcp/unreal-engine-mcp-server)

### 5. 엔진 내 애니메이션 도구 성숙
- Odyssey: 무료 2D 애니메이션 플러그인 (Fab 배포)
- MetaHuman Animation Tool v1.4: UE 5.7 호환 (2026.03)
- Gnomon Workshop: Technical Animation for Games 5시간 코스 출시 (2026.04)
- Indie Games Week (4/13-17): MetaHuman 워크플로우 세션 예정

---

## 긴급도별 분류

| 긴급도 | 항목 |
|--------|------|
| **지금 행동** | Rokoko Create 무료 테스트, Cascadeur 2026.1 Live Link 테스트, Indie Games Week 참가 준비 |
| **이번 분기** | UAF 5.7 실험 (David Martinez 가이드 참조), GASP 5.7 Mover Plugin 분석, StraySpark MCP 평가 |
| **모니터링** | UAF 5.8 프리뷰, Mover Plugin 정식화, Epic 공식 MCP 동향 |

## 소스
- [Rokoko Create 무료 출시](https://www.cgchannel.com/2026/04/rokoko-create-generates-full-body-animations-for-free/) — 2026.04, 무제한 무료 애니메이션 생성
- [Cascadeur 2026.1](https://www.cgchannel.com/2026/04/nekki-releases-cascadeur-2026-1/) — 2026.04, Root Motion + UE5 Live Link
- [JALI NAB 2026](https://www.shootonline.com/spw/jali-research-real-time-facial-animation-powers-iels-live-animation-production-workflow-at-nab-2026/) — 실시간 페이셜
- [GASP 5.7 업데이트](https://www.unrealengine.com/tech-blog/explore-the-updates-to-the-game-animation-sample-project-in-ue-5-7) — Mover Plugin, 400 애니메이션
- [UAF FAQ](https://dev.epicgames.com/community/learning/knowledge-base/nWWx/unreal-engine-unreal-animation-framework-uaf-faq) — 5.8 로드맵
- [Mover 2.0 + UAF 가이드](https://farravid.github.io/posts/How-to-setup-Mover-2.0-+-Unreal-Animation-Framework-(UAF)-+-Motion-Matching-in-5.7/) — David Martinez
- [StraySpark MCP](https://forums.unrealengine.com/t/strayspark-unreal-mcp-server-200-ai-tools-for-ue5-editor-automation-via-mcp/2707474) — 207+ AI 도구
- [Gnomon TA 코스](https://www.cgchannel.com/2026/04/tutorial-introduction-to-technical-animation-for-games/) — 2026.04, 5시간
- [Indie Games Week](https://www.unrealengine.com/events/indie-games-week-2026) — 4/13-17, MetaHuman 세션
