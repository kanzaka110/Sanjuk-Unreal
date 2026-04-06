# Motion Matching & PoseSearch

> 2026-04-06 브리핑 | [목차로 돌아가기](00_INDEX.md)

---

## 무엇인가

런타임에 애니메이션 데이터베이스에서 최적의 포즈를 검색하여 캐릭터 동작을 합성하는 시스템. UE5에서는 **PoseSearch** 플러그인으로 구현.

---

## 최신 발전 (UE 5.6~5.7)

### Chooser + PoseSearch Column (Experimental)
- Chooser 시스템에 PoseSearch 컬럼 추가
- Motion Matching과 Chooser가 더 긴밀하게 통합

### GASP 5.7 업데이트
- 새로운 **Mover 플러그인** 추가 (Experimental)
- **400개 신규 애니메이션** 포함 갱신된 로코모션 데이터셋
- 슬라이드 기능, Smart Object 셋업, 로코모션 스타일 추가

### 로드맵
- **멀티 캐릭터 Motion Matching**: Motion Matching으로 제어되는 캐릭터 간 상호작용 지원 예정

---

## 서드파티 도구

| 도구 | 설명 | 가격 |
|------|------|------|
| **RDR System** | ALS Refactored + GASP Motion Matching 결합 (C++) | 무료 |
| **Motorica Motion Factory** | AI 생성 데이터셋을 Motion Matching용으로 자동 구성 | 무료 |

---

## 커뮤니티 반응

- Motion Matching이 점차 **"표준 로코모션 방식"**으로 자리잡는 추세
- GASP 프로젝트가 공식 레퍼런스로 활용도 높음
- 5.7.4에서 일부 호환성 이슈 보고됨

---

## TA 액션

- [ ] GASP 5.7 프로젝트 다운로드 후 신규 애니메이션 분석
- [ ] RDR System 평가 (ALS + Motion Matching 통합 레퍼런스)
- [ ] Motorica Motion Factory로 커스텀 데이터셋 생성 테스트

---

## 참고 링크

- [Motion Matching 공식 문서 (UE 5.7)](https://dev.epicgames.com/documentation/en-us/unreal-engine/motion-matching-in-unreal-engine)
- [GASP 5.7 업데이트 블로그](https://www.unrealengine.com/en-US/tech-blog/explore-the-updates-to-the-game-animation-sample-project-in-ue-5-7)
- [RDR System (80.lv)](https://80.lv/articles/free-c-system-that-combines-als-gasp-motion-matching-for-unreal-engine-5)
