# AnimNext / UAF 차세대 애니메이션

> 2026-04-12 브리핑 | [목차로 돌아가기](00_INDEX.md)

---

## 현황

UAF(Unreal Animation Framework)는 ABP(Animation Blueprint) 대체 차세대 시스템. 현재 **Experimental** 상태.

### UE 5.7 (현재)
- Choosers + PoseSearch Column 통합으로 Motion Matching과 연계 강화
- 절차적 노드가 Control Rig로 이동 중 → UAF + Control Rig 깊은 통합 기반 마련

### UE 5.8 (예정, 2026 후반)
- **GASP 캐릭터 1개를 UAF로 완전 구성** → 커뮤니티 첫 실전 레퍼런스
- Experimental 유지, 하지만 hands-on 가능한 수준 목표

### 🆕 커뮤니티 가이드
- David Martinez: [Mover 2.0 + UAF + Motion Matching in 5.7](https://farravid.github.io/posts/How-to-setup-Mover-2.0-+-Unreal-Animation-Framework-(UAF)-+-Motion-Matching-in-5.7/) — 실제 셋업 단계별 가이드
- RemRemRemRe: [UAF 이해하기 (5.6)](https://remremremre.github.io/posts/My-understanding-of-Unreal-Animation-Framework-in-5.6/) — 내부 구조 분석

### TA 액션
- 5.7에서 David Martinez 가이드 따라 UAF + Mover + Motion Matching 실험
- ABP → UAF 마이그레이션 전략 수립 시작

## 소스
- [UAF FAQ](https://dev.epicgames.com/community/learning/knowledge-base/nWWx/unreal-engine-unreal-animation-framework-uaf-faq) — 공식 로드맵
- [UAF 포럼 탐구](https://forums.unrealengine.com/t/uaf-anim-next-explorations/2649236) — 커뮤니티 논의
- [GASP 5.7 업데이트](https://www.unrealengine.com/tech-blog/explore-the-updates-to-the-game-animation-sample-project-in-ue-5-7) — Mover + Choosers 통합
