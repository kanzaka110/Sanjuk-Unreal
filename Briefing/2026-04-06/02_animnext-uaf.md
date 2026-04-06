# AnimNext / UAF (Unreal Animation Framework)

> 2026-04-06 브리핑 | [목차로 돌아가기](00_INDEX.md)

---

## 무엇인가

ABP(Animation Blueprint)를 대체할 **차세대 애니메이션 시스템**. Epic이 UE 5.2부터 "AnimNext"라는 이름으로 실험해온 장기 프로젝트.

---

## 현재 상태: Experimental (UE 5.5~5.7)

- `Module`과 `AnimationGraph` 두 가지 논리적 컨테이너로 구성
- RigVM 위에서 동작, **멀티스레드 실행** 지원
- ABP의 AnimGraph 노드를 통해 UAF 그래프를 기존 ABP 안에 임베드 가능 (점진적 전환)

---

## 5.8 로드맵 (핵심)

- **GASP 캐릭터 1개를 UAF로 완전 구성 예정**
- 여전히 Experimental이지만, 커뮤니티가 실전 경험을 쌓을 수 있는 수준까지 안정화
- ABP와의 공존 기간을 거쳐 장기적으로 ABP를 대체

---

## 커뮤니티 현황

- UE 포럼에 [UAF Explorations](https://forums.unrealengine.com/t/uaf-anim-next-explorations/2649236) 활발한 탐색 스레드
- [Mover 2.0 + UAF + Motion Matching 셋업 가이드](https://farravid.github.io/posts/How-to-setup-Mover-2.0-+-Unreal-Animation-Framework-(UAF)-+-Motion-Matching-in-5.7/) 공유됨
- 평가: "성능 향상 기대되지만, 아직 프로덕션에는 이르다"

---

## MCP 지원

- **Monolith**: AnimNext 직접 지원 없음 (ABP 그래프 작성은 지원)
- **runreal**: 커스텀 Python 스크립트로 UAF 실험 가능

---

## TA 액션

- [ ] UE 5.7에서 UAF 플러그인 활성화 후 GASP 캐릭터로 실험 시작
- [ ] Mover 2.0 + UAF + Motion Matching 조합 셋업 테스트
- [ ] 5.8 프리뷰 출시 시 UAF 완전 구성 캐릭터 분석

---

## 참고 링크

- [UAF FAQ (Epic)](https://dev.epicgames.com/community/learning/knowledge-base/nWWx/unreal-engine-unreal-animation-framework-uaf-faq)
- [AnimNext API 문서 (UE 5.7)](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Animation/AnimNext)
