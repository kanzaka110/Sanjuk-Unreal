# 부록 B: 참고 자료

[← 이전: 용어 사전](./APPENDIX_A_GLOSSARY.md) | [목차](./00_INDEX.md)

---

## 공식 문서

| 리소스 | URL | 내용 |
|--------|-----|------|
| UAF FAQ | dev.epicgames.com/community/learning/knowledge-base/nWWx | 공식 FAQ, 로드맵 |
| UAF API 문서 | dev.epicgames.com/documentation/en-us/unreal-engine/API/PluginIndex/UAF | C++ API 레퍼런스 |
| AnimNext Blueprint API | dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Animation/AnimNext | BP 노드 레퍼런스 |
| Game Animation Sample 5.7 | unrealengine.com/en-US/tech-blog/explore-the-updates-to-the-game-animation-sample-project-in-ue-5-7 | 공식 샘플 프로젝트 업데이트 |

## Epic 발표

| 리소스 | 내용 |
|--------|------|
| Unreal Fest 2024: Next-Gen Animation Tools | UE 5.4 기준 AnimNext 소개, 설계 철학 |
| GDC 2024 Animation Talks | Motion Matching + Chooser 통합 |
| UE 5.7 Release Notes | UAF 리브랜딩, MM 노드 추가 |

## 커뮤니티 가이드

| 리소스 | 저자 | 내용 |
|--------|------|------|
| My Understanding of UAF in 5.6 | RemRemRemRe | TraitStack, Module, 내부 구조 심층 분석 (중국어/영어) |
| How to setup Mover 2.0 + UAF + MM in 5.7 | David Martinez (farravid) | 실습 가이드, Mover + UAF 통합 |
| UAF (Anim Next) Explorations | Epic Forums 스레드 | 커뮤니티 실험 및 토론 |
| AnimNext Plugin Discussion | Epic Forums 스레드 | 초기 플러그인 발견 및 토론 |

## 관련 플러그인 문서

| 플러그인 | 용도 | 문서 위치 |
|---------|------|----------|
| **PoseSearch** | Motion Matching | Engine/Plugins/Animation/PoseSearch |
| **Chooser** | 조건 기반 에셋 선택 | Engine/Plugins/Chooser |
| **BlendStack** | 블렌드 스택 | Engine/Plugins/Animation/BlendStack |
| **AnimationWarping** | 애니메이션 워핑 | Engine/Plugins/Animation/AnimationWarping |
| **MotionWarping** | 모션 워핑 | Engine/Plugins/Animation/MotionWarping |
| **Mover** | 차세대 캐릭터 무브먼트 | Engine/Plugins/Mover |

## 소스 코드 참조 (엔진 내)

UAF의 소스 코드를 직접 확인하고 싶을 때:

```
Engine/Plugins/Experimental/AnimNext/
├── AnimNext/                    ← 코어 런타임
│   ├── Source/
│   │   ├── AnimNext/
│   │   │   ├── Public/
│   │   │   │   ├── TraitStack.h
│   │   │   │   ├── Trait.h
│   │   │   │   ├── Module.h
│   │   │   │   └── ...
│   │   │   └── Private/
│   │   └── AnimNextEditor/      ← 에디터 전용
│   └── AnimNext.uplugin
│
├── AnimNextAnimGraph/           ← 애니메이션 그래프
│   └── Source/
│       ├── AnimNextAnimGraph/
│       └── AnimNextAnimGraphEditor/
│
└── AnimNextUncookedOnly/        ← 에디터 전용 도구
```

## 학습 순서 추천

### 초보자

1. **먼저**: Game Animation Sample 프로젝트 다운로드 및 분석
2. **그 다음**: David Martinez의 Mover + UAF 가이드 따라하기
3. **심화**: RemRemRemRe의 내부 구조 분석 읽기
4. **실습**: 이 가이드를 따라 자체 프로젝트에서 변환

### 숙련자

1. **소스 코드**: Engine/Plugins/Experimental/AnimNext/ 직접 읽기
2. **API 문서**: UAF C++ API 레퍼런스 확인
3. **커뮤니티**: Epic Forums UAF 스레드 참여
4. **실습**: 커스텀 Trait 개발

---

## 이 가이드의 한계

1. **UE 5.7 기준**: UE 5.8 이후 API가 변경될 수 있음
2. **UAF는 Experimental**: 이 가이드의 내용이 향후 변경될 수 있음
3. **공식 마이그레이션 도구 없음**: 모든 변환은 수동 작업
4. **프로젝트 특화**: SandboxCharacter_CMC_ABP 기준으로 작성됨
5. **커뮤니티 기반 정보 포함**: 일부 내용은 커뮤니티 리서치 기반

### 업데이트 시기

다음 상황에서 이 가이드를 업데이트해야 합니다:
- UE 5.8 출시 시 (첫 공식 데모 포함)
- UAF API에 Breaking Change가 있을 때
- 공식 마이그레이션 가이드가 출시될 때
- 프로젝트의 ABP 구조가 변경될 때

---

*가이드 작성일: 2026-03-28*
*UE 버전: 5.7*
*UAF 상태: Experimental*

---

[← 이전: 용어 사전](./APPENDIX_A_GLOSSARY.md) | [목차](./00_INDEX.md)
