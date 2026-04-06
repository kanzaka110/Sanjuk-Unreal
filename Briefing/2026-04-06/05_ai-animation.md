# AI 기반 애니메이션 도구

> 2026-04-06 브리핑 | [목차로 돌아가기](00_INDEX.md)

---

## 엔진 내장 AI/ML

### ML Deformer (Beta)
- 머신러닝으로 실시간 근육/살/의류 디포메이션 구현
- Neural Morph Model, Vertex Delta Model 등 다수 NN 모델 지원
- 해부학적 데이터(3D/4D/MRI)에서 트레이닝 가능
- [공식 문서 (UE 5.7)](https://dev.epicgames.com/documentation/en-us/unreal-engine/ml-deformer-framework-in-unreal-engine)

### Neural Network Engine — NNE (Beta)
- Experimental → Beta 승격
- 런타임 + 에디터 내 사전 학습 NN 모델 로딩/실행
- 애니메이션, 렌더링, 물리 등 다양한 유즈케이스

### 에디터 내 AI 어시스턴트 (UE 5.7 신규)
- 실시간 도움, C++ 코드 생성, 단계별 안내
- 튜토리얼/문서/샘플 프로젝트를 한곳에서 접근

---

## 서드파티 AI 도구

### Motorica AI — 제너레이티브 애니메이션
- 2025년 6월 시드 펀딩 **500만 유로** (Angular Ventures)
- **Motion Factory**: AI로 Motion Matching용 데이터셋 즉시 생성
- AAA 스튜디오 실전 투입, **기존 대비 200배 속도, 99% 시간 절감**
- UE5, Unity, Maya, Blender, Cinema 4D 호환
- [공식 사이트](https://www.motorica.com) | [Epic 튜토리얼](https://dev.epicgames.com/community/learning/tutorials/8X66/motorica-ai-tutorial-generative-animation-in-unreal-engine-i-icvr)

### Cascadeur — AI 키프레임 애니메이션
- **AutoPosing**: 뉴럴 네트워크 기반 스마트 리그 (포인트 이동 → AI 자동 배치)
- **AI Inbetweening**: 걷기/달리기 모션 스타일 셀렉터
- 사족보행(Quadruped) 지원 추가
- **Cascadeur 2026.1 (2026년 4월 9일 출시)**:
  - **UE Live Link 플러그인** 탑재 (Epic MegaGrant $50K 지원)
  - 수동 내보내기 없이 실시간 스트리밍
- [공식 사이트](https://cascadeur.com)

### DeepMotion — 웹 AI 모캡
- 비디오 → 3D 애니메이션 변환
- MetaHuman 호환, UE5 자동 리타기팅
- [UE5 연동](https://www.deepmotion.com/companion-tools/unreal-engine)

---

## 도구별 비교

| 도구 | 유형 | UE 연동 | 가격 | 성숙도 |
|------|------|---------|------|--------|
| ML Deformer | 디포메이션 | 엔진 내장 | 무료 | Beta |
| NNE | NN 런타임 | 엔진 내장 | 무료 | Beta |
| Motorica | 모션 생성 | 플러그인 | 무료 | 프로덕션 |
| Cascadeur | 키프레임 | Live Link (4/9~) | 무료/유료 | 프로덕션 |
| DeepMotion | AI 모캡 | 리타기팅 | 무료/유료 | 프로덕션 |

---

## TA 액션

- [ ] **즉시**: Cascadeur 2026.1 출시(4/9) 후 Live Link 플러그인 테스트
- [ ] Motorica Motion Factory로 커스텀 로코모션 데이터셋 생성 실험
- [ ] ML Deformer로 근육 시뮬레이션 퀄리티 vs 성능 벤치마크
- [ ] DeepMotion 웹 AI 모캡 → MetaHuman 파이프라인 검증
