# Motion Matching & GASP

> 2026-04-12 브리핑 | [목차로 돌아가기](00_INDEX.md)

---

## GASP 5.7 업데이트 (변경 없음)

- **400개 신규 애니메이션** 추가
- **Mover Plugin** (Experimental) — CharacterMovementComponent 후속
  - Simple Spring Walking Mode: 스프링 기반 속도/회전
  - Smooth Walking Mode: 세밀한 튜닝용
  - 슬라이드 메카닉: 경사면 기반 속도 변화
- 롤백 네트워킹 지원 (Network Prediction / Chaos Networked Physics)

## Motion Matching 생태계

| 프로젝트 | 설명 |
|----------|------|
| [GASPALS](https://github.com/PolygonHive/GASPALS) | GASP + ALS Layering 통합 |
| [GASPALS Mover Demo](https://www.patreon.com/posts/gaspals-mover-5-151397021) | Mover Plugin 데모 (Patreon) |
| [LocoMotion Matching](https://www.fab.com/listings/87d53674-265e-41ca-8634-5d782ed4abf0) | Fab 마켓플레이스 — 복제 지원 로코모션 |
| [Motion Symphony 2](https://github.com/Animation-Uprising/MoSymph2.0-Example-Project) | 모션 매칭 + 포즈 매칭 도구 |

## TA 액션
- GASPALS Mover Demo 분석 → ALS 레이어링 + Mover 조합 학습
- 5.8에서 Mover 정식화 대비 — 기존 CMC 의존 코드 점검

## 소스
- [GASP 5.7 Tech Blog](https://www.unrealengine.com/tech-blog/explore-the-updates-to-the-game-animation-sample-project-in-ue-5-7)
- [Motion Matching 공식 문서](https://dev.epicgames.com/documentation/en-us/unreal-engine/motion-matching-in-unreal-engine)
- [GASP 5.7 커뮤니티 튜토리얼](https://dev.epicgames.com/community/learning/tutorials/x1dz/unreal-engine-exploring-game-animation-sample-project-gasp-in-ue5-7)
- [80.lv GASP 5.7](https://80.lv/articles/game-animation-sample-project-updated-for-unreal-engine-5-7)
