# 언리얼 엔진 애니메이션 기술 동향 리포트 (2025-2026 초)

> 작성일: 2026-04-06  
> 대상 버전: UE 5.5 ~ 5.7 (릴리스) / 5.8 (프리뷰/로드맵)

---

## 목차

1. [AnimNext / UAF (Unreal Animation Framework)](#1-animnext--uaf-unreal-animation-framework)
2. [Motion Matching & PoseSearch](#2-motion-matching--posesearch)
3. [MetaHuman Animator](#3-metahuman-animator)
4. [Chaos Cloth / Physics](#4-chaos-cloth--physics)
5. [AI 기반 애니메이션](#5-ai-기반-애니메이션)
6. [MCP (Model Context Protocol) for UE](#6-mcp-model-context-protocol-for-ue)
7. [Control Rig / IK](#7-control-rig--ik)
8. [Verse / UEFN 애니메이션](#8-verse--uefn-애니메이션)
9. [커뮤니티 도구 & 플러그인](#9-커뮤니티-도구--플러그인)
10. [종합 정리 & 전망](#10-종합-정리--전망)

---

## 1. AnimNext / UAF (Unreal Animation Framework)

### 개요
UAF(Unreal Animation Framework)는 기존 **Animation Blueprint(ABP)**를 대체할 차세대 애니메이션 시스템이다. 내부적으로 "AnimNext"라고 불리며, Epic이 UE 5.2부터 플러그인 형태로 실험해온 장기 프로젝트이다.

### 현재 상태: Experimental (UE 5.5~5.7)
- UE 5.5~5.7에서 **Experimental 플러그인**으로 포함
- `Module`과 `AnimationGraph` 두 가지 논리적 컨테이너로 구성
- RigVM 위에서 동작하며 **멀티스레드 실행** 지원
- ABP의 AnimGraph 노드를 통해 UAF 그래프를 기존 ABP 안에 임베드 가능 (점진적 전환)

### 5.8 로드맵
- **5.8에서 Game Animation Sample Project의 캐릭터 하나를 UAF로 완전 구성 예정**
- 여전히 Experimental이지만, 커뮤니티가 실전 경험을 쌓을 수 있는 수준까지 안정화 목표
- ABP와의 공존 기간을 거쳐 장기적으로 ABP를 대체

### 커뮤니티 반응
- 포럼에서 활발한 탐색 스레드 존재 ([UAF Explorations](https://forums.unrealengine.com/t/uaf-anim-next-explorations/2649236))
- Mover 2.0 + UAF + Motion Matching 조합 셋업 가이드가 커뮤니티에서 공유됨
- "ABP 대비 성능 향상이 기대되지만, 아직 프로덕션에 쓰기엔 이르다"는 평가가 주류

### 관련 링크
- [UAF FAQ (Epic Developer Community)](https://dev.epicgames.com/community/learning/knowledge-base/nWWx/unreal-engine-unreal-animation-framework-uaf-faq)
- [AnimNext API 문서 (UE 5.7)](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Animation/AnimNext)
- [Mover 2.0 + UAF + Motion Matching 셋업 가이드](https://farravid.github.io/posts/How-to-setup-Mover-2.0-+-Unreal-Animation-Framework-(UAF)-+-Motion-Matching-in-5.7/)

---

## 2. Motion Matching & PoseSearch

### 개요
Motion Matching은 런타임에 애니메이션 데이터베이스에서 최적의 포즈를 검색하여 캐릭터 동작을 합성하는 시스템이다. UE5에서는 **PoseSearch** 플러그인으로 구현되어 있다.

### 최신 발전 (UE 5.6~5.7)
- **Chooser + PoseSearch Column (Experimental)**: Chooser 시스템에 PoseSearch 컬럼이 추가되어 Motion Matching과 Chooser가 더 긴밀하게 통합됨
- **Game Animation Sample Project (GASP) 5.7 업데이트**:
  - 새로운 **Mover 플러그인** 추가 (Experimental)
  - 갱신된 로코모션 데이터셋 + **400개 신규 애니메이션**
  - 슬라이드 기능, Smart Object 셋업, 로코모션 스타일 추가
- **멀티 캐릭터 Motion Matching**: 로드맵에 포함 — Motion Matching으로 제어되는 캐릭터 간 상호작용 지원 예정

### 서드파티 도구
- **RDR System**: ALS Refactored + GASP Motion Matching을 결합한 C++ 전용 프로젝트 (무료 공개)
- **Motorica Motion Factory**: AI 생성 애니메이션 데이터셋을 Motion Matching용으로 자동 구성 (아래 AI 섹션에서 상세)

### 커뮤니티 반응
- Motion Matching이 점차 "표준 로코모션 방식"으로 자리잡는 추세
- GASP 프로젝트가 공식 레퍼런스로 활용도가 높음
- 5.7.4에서 일부 호환성 이슈 보고 ([포럼 스레드](https://forums.unrealengine.com/t/motion-matching-on-5-7-4/2711258))

### 관련 링크
- [Motion Matching 공식 문서 (UE 5.7)](https://dev.epicgames.com/documentation/en-us/unreal-engine/motion-matching-in-unreal-engine)
- [GASP 5.7 업데이트 블로그](https://www.unrealengine.com/en-US/tech-blog/explore-the-updates-to-the-game-animation-sample-project-in-ue-5-7)
- [RDR System (80.lv)](https://80.lv/articles/free-c-system-that-combines-als-gasp-motion-matching-for-unreal-engine-5)

---

## 3. MetaHuman Animator

### 개요
MetaHuman은 Epic의 고품질 디지털 휴먼 프레임워크이며, MetaHuman Animator는 비디오/오디오 입력으로부터 페이셜 애니메이션을 생성하는 도구이다.

### 주요 업데이트

#### UE 5.6 (2025년 6월)
- **Early Access 졸업** → 정식 릴리스
- MetaHuman Creator가 **엔진 내 직접 편집** 가능 (DCC 왕복 불필요)
- **라이선스 변경**: Unity, Godot, Maya, Houdini, Blender 등 타 엔진/소프트웨어에서 MetaHuman 캐릭터와 애니메이션 사용 허용
- MetaHuman Animator가 **웹캠 등 모노 카메라**도 지원 (기존 스테레오 HMC/iPhone만 지원)
- **MetaHuman for Houdini**: Character Rig HDA로 Houdini 내 리깅/텍스처 캐릭터 조립

#### UE 5.7 (2025년 11월~12월)
- **프로시저럴 그루밍**: 간편한 헤어 생성
- **아트 디렉팅 헤어 애니메이션**: 스켈레탈 메시 워크플로로 키프레임 애니메이션과 리지드바디 시뮬레이션 블렌딩 (예: 포니테일이 어깨 위에 놓이는 히어로 포즈)
- **Live Link Face**: iPad / Android 외부 카메라 연동 실시간 페이셜 캡처
- 스크립터블 생성 오퍼레이션 추가

#### MetaHuman 판매 허용 (2025년)
- 이제 MetaHuman 캐릭터를 **상업적으로 판매** 가능
- Fab 마켓플레이스에서 MetaHuman 에셋 거래 가능

### 커뮤니티 반응
- "폰 한 대로 실감나는 페이셜 애니메이션을 만들 수 있다"는 평가
- 라이선스 개방이 크게 호평받음
- 인디~AAA 모두에서 도입 확대

### 관련 링크
- [MetaHuman 5.7 릴리스 노트](https://dev.epicgames.com/documentation/en-us/metahuman/metahuman-5-7-release-notes)
- [MetaHuman 공식 사이트](https://www.metahuman.com/?lang=en-US)
- [MetaHuman Creator, Unity/Godot 사용 허용 (CG Channel)](https://www.cgchannel.com/2025/06/you-can-now-sell-metahumans-or-use-them-in-unity-or-godot/)
- [MetaHuman for Houdini (CG Channel)](https://www.cgchannel.com/2025/08/this-free-add-on-turns-metahumans-into-rigged-houdini-characters/)

---

## 4. Chaos Cloth / Physics

### 개요
Chaos Cloth는 언리얼 엔진의 파티클 기반 의류 시뮬레이션 시스템이다. Chaos Physics 프레임워크의 일부로, 실시간 의류 물리를 제공한다.

### 현재 상태: Production-Ready (2025~)
- 2025년 기준 **프로덕션 레디** 상태
- Chaos Cloth Panel 노드 에디터 (UE 5.3+)로 비파괴적 클로스 오서링
- **다중 의류 레이어** (재킷, 망토 등) 성능 및 정확도 개선
- **프리베이크 유체 시뮬레이션** 추가

### ML 클로스 시뮬레이션
- **머신러닝 기반 클로스 시뮬레이션**: 학습된 데이터셋으로 오프라인 시뮬레이션 수준의 피델리티를 실시간 구현
- 기존 물리 기반 모델보다 높은 충실도

### Control Rig Physics (UE 5.6, Experimental)
- 캐릭터 리그에 **프로시저럴 피직스** 추가 가능
- 리얼리즘과 역동적 움직임 강화

### 커뮤니티 반응
- Unreal Fest Orlando 2025에서 "Chaos Cloth Demystified" 세션 발표
- 아티스트 친화적 워크플로가 호평
- MCP 서버 중 ChiR24/Unreal_mcp만 Chaos Cloth 지원 (유일)

### 관련 링크
- [Chaos Character Physics 학습 경로](https://dev.epicgames.com/community/learning/paths/QX/unreal-engine-welcome-to-chaos-character-physics)
- [Chaos Cloth Tool 개요](https://dev.epicgames.com/community/learning/tutorials/OPM3/unreal-engine-chaos-cloth-tool-overview)
- [Chaos Cloth Demystified (Unreal Fest 2025)](https://forums.unrealengine.com/t/talks-and-demos-chaos-cloth-demystified-a-practical-guide-for-artists-unreal-fest-orlando-2025/2674007)

---

## 5. AI 기반 애니메이션

### 5.1 ML Deformer
- **프레임워크 상태**: Beta → 안정화 진행 중
- 머신러닝으로 스킨 캐릭터의 메시 변형을 근사하여 **근육/살/의류 시뮬레이션** 수준의 실시간 디포메이션 구현
- Neural Morph Model, Vertex Delta Model 등 다수 NN 모델 타입 지원
- 해부학적 데이터(3D/4D/MRI)에서 파생된 트레이닝 가능
- [ML Deformer 문서 (UE 5.7)](https://dev.epicgames.com/documentation/en-us/unreal-engine/ml-deformer-framework-in-unreal-engine)

### 5.2 Neural Network Engine (NNE)
- Experimental → **Beta** 승격
- 런타임 + 에디터 내에서 사전 학습된 NN 모델 로딩/실행
- 애니메이션, 렌더링, 물리 등 다양한 유즈케이스

### 5.3 Motorica AI
- 스톡홀름 기반 제너레이티브 애니메이션 AI 회사
- **2025년 6월 시드 펀딩 500만 유로** (Angular Ventures 리드)
- **Motion Factory**: AI로 Motion Matching용 애니메이션 데이터셋 즉시 생성
  - AAA 스튜디오에서 프로덕션에 활용 중
  - **기존 워크플로 대비 200배 속도, 99% 시간 절감** 보고
- UE5, Unity, Maya, Blender, Cinema 4D 호환
- Epic Developer Community에 공식 튜토리얼 존재
- [Motorica 공식 사이트](https://www.motorica.com)
- [Motorica AI 튜토리얼 (Epic)](https://dev.epicgames.com/community/learning/tutorials/8X66/motorica-ai-tutorial-generative-animation-in-unreal-engine-i-icvr)

### 5.4 Cascadeur
- AI 보조 키프레임 애니메이션 소프트웨어 (물리 기반)
- **AutoPosing**: 뉴럴 네트워크 기반 스마트 리그 — 컨트롤 포인트 이동 시 나머지 신체를 AI가 자동 배치
- **AI Inbetweening** (2025.1~2025.3): 걷기/달리기 등 모션 스타일 셀렉터
- 사족보행(Quadruped) 지원 추가 (2025.3)
- **Cascadeur 2026.1 (2026년 4월 9일 출시 예정)**:
  - **Unreal Engine Live Link 플러그인** 탑재 — Epic MegaGrant $50,000 지원
  - 수동 내보내기 없이 실시간 스트리밍
- [Cascadeur 공식 사이트](https://cascadeur.com)
- [Cascadeur UE Live Link (CG Channel)](https://www.cgchannel.com/2025/09/cascadeur-to-get-dedicated-unreal-engine-live-link-plugin/)

### 5.5 DeepMotion
- 웹 기반 AI 모션 캡처 플랫폼
- 비디오 → 3D 애니메이션 변환 (AI 기반)
- **MetaHuman 호환**: 비디오 업로드로 MetaHuman 구동
- UE5 자동 리타기팅 지원
- Motion Smoothing, Root Joint at Origin 등 UE 연동 기능 강화
- [DeepMotion x UE5](https://www.deepmotion.com/companion-tools/unreal-engine)

### 5.6 에디터 내 AI 어시스턴트 (UE 5.7 신규)
- UE 5.7에서 **에디터 내 AI 어시스턴트** 도입
- 실시간 도움, C++ 코드 생성, 단계별 안내
- 튜토리얼/문서/샘플 프로젝트를 한곳에서 접근

---

## 6. MCP (Model Context Protocol) for UE

### 개요
MCP는 AI 에이전트(Claude, Cursor 등)가 언리얼 에디터를 자연어로 제어할 수 있게 하는 프로토콜이다. Epic 공식이 아닌 **커뮤니티 주도** 프로젝트들이다.

### 주요 MCP 서버 현황

#### Monolith (v0.12.0+)
- **가장 포괄적인 UE MCP 플러그인**
- 1,125 액션 / 15 모듈 (최신) — 또는 443 액션 / 10 모듈 (초기 공개 기준)
- **애니메이션 모듈**: 시퀀스, 몽타주, 블렌드스페이스, ABP 그래프 작성, PoseSearch, Control Rig, Physics Assets, IK Rigs, 리타기터, 스켈레톤 관리
- C++ 네이티브 소스 인덱스, 자동 업데이터 내장
- Windows 전용 (Mac/Linux 예정)
- Claude Code, Cursor 등 MCP 호환 클라이언트와 연동
- HTTP 모드 (localhost:9316) 지원
- [GitHub: Monolith](https://github.com/tumourlove/monolith)

#### runreal/unreal-mcp
- **Python Remote Execution** 기반 — 별도 UE 플러그인 설치 불필요
- 20개 도구 노출
- UE5.4+ / Node.js 필요
- 에셋 관리, 씬 조작, 콘솔 명령, 프로젝트 정보 조회
- 커스텀 Python 스크립트로 확장 용이
- [GitHub: runreal/unreal-mcp](https://github.com/runreal/unreal-mcp)

#### chongdashu/unreal-mcp
- Claude Desktop, Cursor, Windsurf용
- Remote Control API 기반
- EXPERIMENTAL 상태
- [GitHub: chongdashu/unreal-mcp](https://github.com/chongdashu/unreal-mcp)

#### ChiR24/Unreal_mcp
- C++ Automation Bridge 플러그인 + TypeScript 서버
- **Chaos Cloth 유일 지원**
- [GitHub: ChiR24/Unreal_mcp](https://github.com/ChiR24/Unreal_mcp)

#### 기타
- Docker 공식 이미지: `mcp/unreal-engine-mcp-server`
- flopperam/unreal-engine-mcp: 건축/구조물 특화
- GenOrca/unreal-mcp: Python + C++ 커스텀 도구 개발

### 공식 지원 여부
- **Epic Games는 아직 공식 MCP를 제공하지 않음**
- 모든 MCP 서버는 커뮤니티/서드파티 프로젝트
- 에디터 내 AI 어시스턴트(UE 5.7)는 MCP와 별개의 공식 AI 연동

### 추천 조합 (애니메이션 특화)
```
Monolith (메인, 1125 액션 / 15 모듈)
+ runreal/unreal-mcp (Python 확장/UAF 대비)
+ ChiR24/Unreal_mcp (Cloth 시뮬레이션, Chaos Cloth 유일 지원)
```

---

## 7. Control Rig / IK

### 최신 기능 (UE 5.6~5.7)

#### UE 5.6: 엔진 퍼스트 리깅 혁신
- **인에디터 모프 타겟 생성/스컬프팅**: 스켈레탈 메시 에디터에서 빌트인 모델링 도구로 블렌드 셰이프 편집
- **Control Rig Physics (Experimental)**: 프로시저럴 피직스를 캐릭터 리그에 추가
- Motion Trails 완전 재설계: 뷰포트에서 아크/스페이싱 직접 편집
- Tween Tools 대폭 강화: 핫키 간접 제어, Overshoot 모드, Time Offset 슬라이더
- Curve Editor 리디자인: 키프레임 애니메이션 속도/성능 향상
- **Epic "Rigging in UE 5.6 Workshop"** 무료 공개: 5일간 초대 전용 → 전체 사용자 개방
  - FK/IK, 스플라인, 디포머, 블렌드 셰이프, Control Rig Physics, Python 도구 커버

#### UE 5.7: 워크플로 최적화
- **리팩토링된 Animation Mode**: 도구 최소화 패널, 뷰포트 공간 확보
- 통합 Constraint UX: Space + Constraints + Snapper를 단일 인터페이스로
- IK Retargeter, Selection Set 기능 강화
- Full Body IK 시스템 완전 문서화

### 서드파티 도구
- **mGear 5.0 + UEGear 1.0** (정식 릴리스, 베타 졸업)
  - Maya의 mGear 리그 → UE Blueprint 기반 Control Rig 변환
  - 노드 그래프 에디터로 UE 5.4+ 내에서 리그 생성
- **Power IK**: Control Rig과 통합 가능한 IK 솔루션

### 관련 링크
- [Control Rig 문서 (UE 5.7)](https://dev.epicgames.com/documentation/en-us/unreal-engine/control-rig-in-unreal-engine)
- [IK Rig 문서 (UE 5.7)](https://dev.epicgames.com/documentation/en-us/unreal-engine/ik-rig-in-unreal-engine)
- [Full Body IK 문서](https://dev.epicgames.com/documentation/en-us/unreal-engine/control-rig-full-body-ik-in-unreal-engine)
- [Rigging Workshop (Epic)](https://digitalproduction.com/2025/12/08/rigging-for-all-epic-opens-ue-5-6-workshop/)
- [mGear/UEGear 1.0 릴리스](https://digitalproduction.com/2025/05/22/rig-it-like-its-free-mgear-5-0-and-uegear-1-0/)

---

## 8. Verse / UEFN 애니메이션

### 개요
UEFN(Unreal Editor for Fortnite)은 포트나이트 내 게임/경험을 제작하는 도구이며, **Verse**는 그 전용 프로그래밍 언어이다.

### 애니메이션 관련 기능
- Blender, Maya 등 외부 DCC에서 제작한 3D 모델/애니메이션 임포트 가능
- UE의 렌더링, 라이팅, VFX, 애니메이션, 월드빌딩 도구 사용
- Verse로 게임 로직, 플레이어 인터랙션, 오브젝트 조작 스크립팅

### 2025~2026 업데이트
- **UEFN v39.50 (2026년 2월 19일)**:
  - **Verse Physics API**: 물리 오브젝트 조작 가능
  - 모바일 프리뷰 테스팅
  - 인아일랜드 트랜잭션 (인게임 아이템 판매)
- **크리에이터 이코노미**: Epic이 $3.2억+ 크리에이터 수익 분배, 상위 크리에이터 월 $50K~$100K+
- 애니메이션 이징 유틸리티, 디버깅 도구 등 커뮤니티 Verse 코드 번들 활발

### 한계
- UEFN은 풀 UE5 대비 기능 제한 (AnimNext/UAF 미지원)
- 커스텀 C++ 플러그인 불가
- 애니메이션 시스템은 UE 메인라인 대비 뒤처짐

### 관련 링크
- [UEFN 공식 페이지](https://www.unrealengine.com/en-US/uses/uefn-unreal-editor-for-fortnite)
- [State of Unreal 2025 포트나이트 크리에이터 하이라이트](https://www.fortnite.com/news/state-of-unreal-2025-highlights-for-fortnite-creators)

---

## 9. 커뮤니티 도구 & 플러그인

### 마켓플레이스 변화
- 2024년 Unreal Marketplace + ArtStation + Sketchfab → **Fab** 통합
- 소스코드 포함 플러그인 다수, 커스텀 확장 가능

### 주요 애니메이션 플러그인

| 이름 | 분류 | 가격 | 비고 |
|------|------|------|------|
| **Odyssey** | 2D 애니메이션 | 무료 | 프레임별 드로잉/스토리보드, Fab에서 무료 배포 |
| **Ozone (Kitestring)** | 캐릭터 디포메이션 | 유료 | 영화 품질 실시간 디포메이션 |
| **Motion Animations** | 모션 라이브러리 | 유료 | 코드 플러그인, Fab 마켓플레이스 |
| **Rig It Right** | MetaHuman 리깅 | 무료 | MetaHuman 애니메이션 도구 |
| **RDR System** | 로코모션 | 무료 | ALS + GASP Motion Matching 통합, C++ |
| **Motorica 플러그인** | AI 애니메이션 | 무료 | 제너레이티브 AI 애니메이션, UE 임포터 |

### 인기 학습 리소스
- Epic 공식 "Game Animation Sample Project" (무료, 매 버전 업데이트)
- Agora Studio 애니메이션 샘플 프로젝트 (Epic 추천)
- Epic "Rigging in UE 5.6 Workshop" (무료 공개)
- Motorica "Motion Matching Made Simple" 시리즈 (3편)

### 관련 링크
- [Fab 마켓플레이스 가이드 (Vagon)](https://vagon.io/blog/best-marketplaces-for-unreal-engine-assets-and-plugins)
- [애니메이션 파이프라인 플러그인 (Epic 블로그)](https://www.unrealengine.com/en-US/blog/boost-your-unreal-engine-animation-production-pipeline-with-these-plugins)
- [Odyssey 무료 배포 발표](https://www.unrealengine.com/en-US/news/odyssey-2d-animation-plugin-is-now-free-on-fab)

---

## 10. 종합 정리 & 전망

### 버전별 애니메이션 핵심 변화 요약

| 버전 | 출시 | 핵심 애니메이션 변화 |
|------|------|---------------------|
| **5.5** | 2024 | AnimNext 초기 실험, PoseSearch 안정화, NNE 실험적 |
| **5.6** | 2025.06 | **역대 최대 애니메이션 툴 업데이트** — Motion Trails, Tween, 인에디터 리깅, MetaHuman 정식, Control Rig Physics |
| **5.7** | 2025.11 | Animation Mode 리팩토링, Mover 플러그인, 헤어 애니메이션, GASP 400 애니메이션, AI 어시스턴트 |
| **5.8** (예정) | 2026 후반? | **UAF 실전 데뷰**, 멀티캐릭터 Motion Matching |

### 5대 트렌드

1. **엔진 퍼스트 애니메이션**: DCC 왕복 최소화, 엔진 내에서 리깅/애니메이팅/스컬프팅 완결
2. **AI/ML의 프로덕션 침투**: ML Deformer, Motorica, Cascadeur, DeepMotion 등 AI 도구가 AAA 파이프라인에 실전 투입
3. **MCP를 통한 AI-UE 연동**: 공식은 아직 없지만 Monolith 등 커뮤니티 MCP가 빠르게 성장, 애니메이션 자동화 가능성 확대
4. **UAF로의 점진적 전환**: ABP 대체 차세대 시스템이 서서히 모습을 드러냄, 5.8이 분수령
5. **MetaHuman 에코시스템 개방**: 타 엔진/DCC 지원, 상업적 판매 허용으로 산업 전반 확산

### 권장 액션 (TA 관점)

- **지금 학습**: UE 5.6/5.7 인에디터 리깅 워크숍, Motion Matching (GASP), Control Rig Physics
- **실험 시작**: UAF (5.7 Experimental 플러그인), Motorica 플러그인, Cascadeur Live Link (2026.1)
- **모니터링**: UAF 5.8 프리뷰, 멀티캐릭터 Motion Matching, MCP 생태계 발전
- **MCP 환경 유지**: Monolith + runreal 조합으로 AI 자동화 파이프라인 구축 지속

---

> 이 리포트는 2026년 4월 기준 웹 검색 결과를 기반으로 작성되었으며, Epic의 로드맵은 변경될 수 있습니다.

## Sources

### 공식 Epic / Unreal Engine
- [UE 5.7 릴리스 노트](https://www.unrealengine.com/en-US/news/unreal-engine-5-7-is-now-available)
- [UE 5.6 릴리스](https://www.unrealengine.com/en-US/news/unreal-engine-5-6-is-now-available)
- [State of Unreal 2025 발표](https://www.unrealengine.com/en-US/news/all-the-big-news-and-announcements-from-the-state-of-unreal-2025)
- [GASP 5.7 업데이트](https://www.unrealengine.com/en-US/tech-blog/explore-the-updates-to-the-game-animation-sample-project-in-ue-5-7)
- [UAF FAQ](https://dev.epicgames.com/community/learning/knowledge-base/nWWx/unreal-engine-unreal-animation-framework-uaf-faq)
- [Motion Matching 문서](https://dev.epicgames.com/documentation/en-us/unreal-engine/motion-matching-in-unreal-engine)
- [ML Deformer 문서](https://dev.epicgames.com/documentation/en-us/unreal-engine/ml-deformer-framework-in-unreal-engine)
- [Control Rig 문서](https://dev.epicgames.com/documentation/en-us/unreal-engine/control-rig-in-unreal-engine)
- [MetaHuman 5.7 릴리스 노트](https://dev.epicgames.com/documentation/en-us/metahuman/metahuman-5-7-release-notes)
- [Agora Studio 애니메이션 샘플](https://www.unrealengine.com/en-US/news/explore-agora-studios-new-animation-sample-projects-for-unreal-engine)
- [Future of Animation 이벤트](https://www.unrealengine.com/en-US/events/future-of-animation)

### 미디어 / 분석
- [AWN: UE 5.6 애니메이터 신기능](https://www.awn.com/news/unreal-engine-56-brings-exciting-new-features-animators)
- [AWN: UE 5.7 릴리스](https://www.awn.com/news/unreal-engine-57-now-available)
- [CG Channel: UE 5.6 신기능](https://www.cgchannel.com/2025/01/see-the-new-features-due-in-unreal-engine-5-6-and-beyond/)
- [CG Channel: MetaHuman 판매 허용](https://www.cgchannel.com/2025/06/you-can-now-sell-metahumans-or-use-them-in-unity-or-godot/)
- [PC Gamer: MetaHuman Animator](https://www.pcgamer.com/hardware/unreals-metahuman-animator-can-generate-surprisingly-lifelike-animation-with-just-your-phone-and-its-now-integrated-directly-into-unreal-engine-5-6/)
- [Puget Systems: UE 5.6 분석](https://www.pugetsystems.com/blog/2025/06/19/unreal-engine-5-6-faster-open-worlds-smoother-animation-better-icvfx/)
- [80.lv: GASP 5.7 업데이트](https://80.lv/articles/game-animation-sample-project-updated-for-unreal-engine-5-7)
- [Digital Production: Rigging Workshop](https://digitalproduction.com/2025/12/08/rigging-for-all-epic-opens-ue-5-6-workshop/)
- [Digital Production: mGear/UEGear](https://digitalproduction.com/2025/05/22/rig-it-like-its-free-mgear-5-0-and-uegear-1-0/)
- [Digital Production: Cascadeur](https://digitalproduction.com/2026/02/18/cascadeur-on-physics-ai-and-control/)

### AI / ML 애니메이션
- [Motorica 공식](https://www.motorica.com)
- [Motorica 펀딩 발표 (AWN)](https://www.awn.com/news/motorica-raises-over-5m-generative-ai-expansion-scaling)
- [Cascadeur 공식](https://cascadeur.com)
- [Cascadeur UE Live Link (CG Channel)](https://www.cgchannel.com/2025/09/cascadeur-to-get-dedicated-unreal-engine-live-link-plugin/)
- [DeepMotion x UE5](https://www.deepmotion.com/companion-tools/unreal-engine)

### MCP 프로젝트
- [Monolith GitHub](https://github.com/tumourlove/monolith)
- [runreal/unreal-mcp GitHub](https://github.com/runreal/unreal-mcp)
- [chongdashu/unreal-mcp GitHub](https://github.com/chongdashu/unreal-mcp)
- [ChiR24/Unreal_mcp GitHub](https://github.com/ChiR24/Unreal_mcp)

### 커뮤니티
- [UAF Explorations 포럼](https://forums.unrealengine.com/t/uaf-anim-next-explorations/2649236)
- [Motion Matching 5.7.4 포럼](https://forums.unrealengine.com/t/motion-matching-on-5-7-4/2711258)
- [Chaos Cloth Demystified (Unreal Fest 2025)](https://forums.unrealengine.com/t/talks-and-demos-chaos-cloth-demystified-a-practical-guide-for-artists-unreal-fest-orlando-2025/2674007)
- [Mover 2.0 + UAF + Motion Matching 가이드](https://farravid.github.io/posts/How-to-setup-Mover-2.0-+-Unreal-Animation-Framework-(UAF)-+-Motion-Matching-in-5.7/)
- [RDR System (ALS + GASP)](https://80.lv/articles/free-c-system-that-combines-als-gasp-motion-matching-for-unreal-engine-5)
