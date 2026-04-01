# UAF (Unreal Animation Framework) 종합 가이드

> UE 5.7 기준 | 최종 업데이트: 2026-03-28

UAF는 Epic Games의 차세대 애니메이션 프레임워크로, 기존 Animation Blueprint(ABP)를 대체합니다.
이 가이드는 초보자도 따라할 수 있도록 단계별로 구성되어 있습니다.

---

## 목차

| 장 | 제목 | 내용 |
|----|------|------|
| [01](./01_UAF_OVERVIEW.md) | UAF 개요 | UAF란 무엇인가, ABP와의 차이, 현재 상태 |
| [02](./02_PLUGIN_SETUP.md) | 플러그인 설정 | 필수/선택 플러그인 활성화 |
| [03](./03_CORE_ASSETS.md) | 핵심 에셋 이해 | Workspace, System, Animation Graph, Shared Variables |
| [04](./04_STEP_BY_STEP_SETUP.md) | 단계별 셋업 | 에셋 생성부터 캐릭터 적용까지 |
| [05](./05_SYSTEM_EVENTGRAPH.md) | System EventGraph | Initialize/PrePhysics 노드 구성 |
| [06](./06_ANIMATION_GRAPH.md) | Animation Graph | Chooser + Motion Matching 연동 |
| [07](./07_DATA_INTERFACE.md) | Data Interface & Bindings | 변수 바인딩, 스레드 안전 데이터 교환 |
| [08](./08_MOVER_INTEGRATION.md) | Mover 2.0 연동 | Mover + UAF + Motion Matching |
| [09](./09_ARCHITECTURE.md) | 기술 아키텍처 | Trait 시스템, RigVM, 메모리 구조 |
| [10](./10_TROUBLESHOOTING.md) | 문제 해결 & 주의사항 | 알려진 이슈, 크래시 방지 |
| [A](./APPENDIX_RESOURCES.md) | 참고 자료 | 공식 문서, 튜토리얼, 커뮤니티 링크 |

---

## 핵심 참고 자료

| 자료 | 링크 | 설명 |
|------|------|------|
| UAF 공식 FAQ | [Epic Developer Community](https://dev.epicgames.com/community/learning/knowledge-base/nWWx/unreal-engine-unreal-animation-framework-uaf-faq) | Epic 공식 FAQ |
| David Martinez 가이드 | [farravid.github.io](https://farravid.github.io/posts/How-to-setup-Mover-2.0-+-Unreal-Animation-Framework-(UAF)-+-Motion-Matching-in-5.7/) | Mover+UAF+MM 실전 셋업 (스크린샷 포함) |
| RemRemRemRe 아키텍처 | [remremremre.github.io](https://remremremre.github.io/posts/My-understanding-of-Unreal-Animation-Framework-in-5.6/) | UAF 내부 구조 기술 분석 |
| 60분 튜토리얼 | [Epic Developer Community](https://dev.epicgames.com/community/learning/tutorials/98mz/unreal-engine-your-first-unofficial-60-minutes-inside-uaf) | 커뮤니티 입문 튜토리얼 |
| Witcher 4 UAF 발표 | [Unreal Fest Orlando 2025](https://dev.epicgames.com/community/learning/talks-and-demos/RmO5/unreal-animation-framework-in-the-witcher-4-unreal-engine-5-tech-demo-unreal-fest-orlando-2025) | CD PROJEKT RED의 UAF 활용 사례 |
