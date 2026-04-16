# SB2 플러그인 목록

**수집 날짜:** 2026-04-16  
**엔진:** UE 5.7.4 (SHIFTUP licensee 커스텀 빌드)  
**프로젝트 경로:** `E:/Perforce/SB2/Workspace/Internal/SB2/`  
**엔진 경로:** `E:/Perforce/SB2/Workspace/Internal/Engine/`

---

## 1. SB2 프로젝트 커스텀 플러그인 (Plugins/ 폴더)

> `SB2/Plugins/` 하위에 직접 존재하는 플러그인. 표준 UE에 없는 서드파티 + SHIFTUP 자체 개발 포함.

### 1-1. SHIFTUP 자체 개발 (SB Team / SHIFTUP)

| 플러그인 이름 | 버전 | 활성화 | 카테고리 | 설명 | 모듈 |
|---|---|---|---|---|---|
| **SBAnimation** | 1.0 | O | Animation | SB 커스텀 애니메이션 노드 및 컨트롤러 | SBAnimationRuntime, SBAnimationEditor |
| **SBCharacterOccluderEditor** | 1.0 | O | Editor | 캐릭터 오클루더 시스템 StaticMesh 에디터 통합 | SBCharacterOccluderEditor |
| **SBDataProvider** | 1.0 | — | Editor | SB2 DataTable 데이터를 외부 검색 도구에 노출하는 HTTP API 서버 | SBDataProvider |
| **SBDeepSearchDataExtractor** | 1.0 | — | Editor | DeepSearch 데이터 임베딩용 데이터 추출기 (Experimental) | SBDeepSearchDataExtractor |

### 1-2. AI/Copilot (IEGG/Tencent 계열)

| 플러그인 이름 | 버전 | 활성화 | 카테고리 | 설명 | 제작자 |
|---|---|---|---|---|---|
| **EditorUtilityCopilot** | 1.0 | X (비활성) | Other | AI 기반 에디터 유틸리티 코파일럿 | IEGG STH |
| **EverythingCopilot** | 1.0 | X (비활성) | Other | AI 기반 범용 코파일럿 (OpenAI API 사용) | IEGG |
| **PerformanceCopilot** | 1.0 | X (비활성) | Genesis | UE 퍼포먼스 최적화 도구 | IEGG |
| **WorldBuildCopilot** | 1.0 | X (비활성) | Genesis | 월드 빌드 AI 코파일럿 | IEGG |

### 1-3. PCG (NextPCG — IEGG/Tencent 계열)

| 플러그인 이름 | 버전 | 활성화 | 카테고리 | 설명 |
|---|---|---|---|---|
| **NextPCG** | 1.0 | O | Genesis | 기본 절차적 콘텐츠 생성 파이프라인 |
| **NextPCGHoudini** | 1.0 | O | Genesis | Houdini 연동 PCG 파이프라인 |
| **NextPCGTools** | 1.0 | O | Genesis | PCG 파이프라인 편집 도구 모음 |
| **NextPCGBiome** | 1.0 | O | Genesis | Biome 연동 PCG |
| **NextPCGLandscape** | 1.0 | O | Genesis | 절차적 랜드스케이프 코파일럿 |
| **NextPCGPython** | 1.0 | O | Genesis | Python 기반 PCG 파이프라인 |
| **NextPCGWater** | 1.0 | O | Genesis | Water 플러그인 연동 PCG |

### 1-4. MCP / AI 에디터 연동

| 플러그인 이름 | 버전 | 활성화 | 카테고리 | 설명 | 제작자 |
|---|---|---|---|---|---|
| **Monolith** | 0.12.1 | — | Editor | UE MCP 서버 — 1125 액션 (Blueprint, Material, Animation, Niagara, Mesh, GAS, AI 등 15 도메인) | tumourlove |
| **UnrealClaude** | 1.4.0 | — | Editor | Claude Code CLI 통합, UE 5.7 문서 컨텍스트 제공 | Natali Caggiano |

### 1-5. 애니메이션 — 서드파티

| 플러그인 이름 | 버전 | 활성화 | 카테고리 | 설명 | 제작자 |
|---|---|---|---|---|---|
| **KawaiiPhysics** | 1.19.0 | — | Animation | 본 기반 세컨더리 물리 (머리카락, 치마, 꼬리) | pafuhana1213 |
| **SPCRJointDynamics** | 1.0 | — | Animation | 본 클로스 물리 시뮬레이션 | SPARKCREATIVE |
| **PoseDriverConnect** | 1.1 | — | Animation | Pose Wrangler RBF 데이터 → PoseDriver 파이프라인 | Epic Games |

### 1-6. 렌더링 — 서드파티

| 플러그인 이름 | 버전 | 활성화 | 카테고리 | 설명 | 제작자 |
|---|---|---|---|---|---|
| **FSR3** | 3.1.0 | X (비활성) | Rendering | AMD FidelityFX Super Resolution 3.1 | AMD |
| **FSR3MovieRenderPipeline** | 3.0.4 | X (비활성) | Rendering | FSR3 + Movie Render Pipeline 지원 | AMD |
| **NiagaraUIRenderer** | 1.1.9 | O | FX | Niagara 파티클을 UI 위젯으로 렌더링 | Michal Smoleň |
| **Prismatiscape** | 1.04.01 | — | Other | 비주얼 이펙트 씬 레이어링 도구 | PrismaticaDev |
| **SkyCreatorPlugin** | 1.41.3 | — | Rendering | 동적 날씨 + 시간대 제어 (볼류메트릭 클라우드, 대기) | Dmitry Karpukhin |
| **ZibraVDB** | 1.5.2 | X (비활성) | Code Plugins | VDB 이펙트 압축 및 실시간 렌더링 | Zibra AI |

### 1-7. 기타 서드파티

| 플러그인 이름 | 버전 | 활성화 | 카테고리 | 설명 | 제작자 |
|---|---|---|---|---|---|
| **CrazyIvy** | 1.0 | — | Other | 자동 아이비(담쟁이) 생성 | Tav Shande |
| **DataTableMerge** | 1.0 | — | Editor | CSV → DataTable 병합 | wordwhale |
| **LowEntryExtStdLib** | 5.6.0 r0 | — | Low Entry | 블루프린트 확장 표준 라이브러리 (Blueprint 기능 확장) | Low Entry |
| **OverCrowd** | 1.0 (Beta) | O | Vertex Animation Toolkit | 버텍스 애니메이션 기반 10만+ 군중 시스템 | Ken MacLean |
| **PBL_Database** | 1.1 | — | Lighting | PBL(물리 기반 라이팅) 데이터베이스 | Arthur Tasquin |
| **RuleProcessor** | 1.0 | — | Editor | 포인트 클라우드 기반 룰 프로세서 (Epic prototype) | Epic Games |
| **Sentry** | 1.0.0-beta.1 | — | Code Plugins | 에러/퍼포먼스 이슈 추적 | Sentry |
| **Traffic** | 1.0 | O | AI | Mass + ZoneGraph 기반 차량 AI 교통 시스템 | Epic Games |

> **Nvidia 폴더** — 단일 .uplugin 없이 DLSS, DLSSMoviePipelineSupport, GeForceNOWWrapper 서브폴더로 구성. uproject에서 직접 활성화.

---

## 2. uproject Plugins 섹션 — 활성화 상태 전체

> `SB2.uproject` 기준. 여기 없는 프로젝트 플러그인은 기본값(비활성) 처리.

### 2-1. 애니메이션 관련 (Enabled)

| 플러그인 | 활성화 | 출처 |
|---|---|---|
| SBAnimation | O | 프로젝트 커스텀 |
| PoseSearch | O | 엔진 표준 |
| MotionWarping | O | 엔진 표준 |
| MotionTrajectory | O | 엔진 표준 |
| AnimationWarping | O | 엔진 표준 |
| AnimationLocomotionLibrary | O | 엔진 표준 |
| AnimationModifierLibrary | O | 엔진 표준 |
| ContextualAnimation | O | 엔진 표준 |
| PhysicsControl | O | 엔진 표준 |
| LiveLinkControlRig | O | 엔진 표준 |
| AlembicHairImporter | O | 엔진 표준 |
| Chooser | O | 엔진 표준 |
| ChaosClothAsset | O | 엔진 표준 |
| HairStrands | O | 엔진 표준 |
| HairCardGenerator | O | 엔진 표준 |
| Mutable | O | 엔진 표준 |
| HairStrandsMutable | O | 엔진 표준 |
| AppleARKitFaceSupport | O | 엔진 표준 |
| AnimToTexture | O | 엔진 표준 |
| **UAF** | **O** | 엔진 커스텀 (Experimental) |
| **UAFWarping** | **O** | 엔진 커스텀 (Experimental) |
| **UAFStateTree** | **O** | 엔진 커스텀 (Experimental) |
| **UAFPoseSearch** | **O** | 엔진 커스텀 (Experimental) |
| **UAFMirroring** | **O** | 엔진 커스텀 (Experimental) |
| **UAFControlRig** | **O** | 엔진 커스텀 (Experimental) |
| **UAFChooser** | **O** | 엔진 커스텀 (Experimental) |
| **UAFAnimGraph** | **O** | 엔진 커스텀 (Experimental) |
| **RigLogicUAF** | **O** | 엔진 커스텀 (Experimental) |
| **MoverAnimNext** | **O** | 엔진 커스텀 (Experimental) |
| **MetaHumanCharacterUAF** | **O** | 엔진 커스텀 (Experimental) |

### 2-2. MetaHuman 관련 (Enabled)

| 플러그인 | 활성화 |
|---|---|
| MetaHuman | O |
| MetaHumanCharacter | O |
| MetaHumanCalibrationProcessing | O |
| MetaHumanLiveLink | O |
| MetaHumanRuntime | O |
| MetaHumanCharacterUAF | O |

### 2-3. Mass AI / Crowd (Enabled)

| 플러그인 | 활성화 |
|---|---|
| MassAI | O |
| MassCrowd | O |
| MassGameplay | O |
| OverCrowd | O |
| Traffic | O |

### 2-4. PCG (Enabled)

| 플러그인 | 활성화 |
|---|---|
| PCG | O |
| PCGExternalDataInterop | O |
| PCGGeometryScriptInterop | O |
| PCGWaterInterop | O |
| NextPCG | O |
| NextPCGHoudini | O |
| NextPCGTools | O |
| NextPCGBiome | O |
| NextPCGLandscape | O |
| NextPCGPython | O |
| NextPCGWater | O |

### 2-5. Nvidia (Enabled)

| 플러그인 | 활성화 |
|---|---|
| StreamlineCore | O |
| StreamlineNGXCommon | O |
| Streamline | O |
| StreamlineReflex | O |
| StreamlineDeepDVC | O |
| StreamlineDLSSG | O |
| DLSS | O |
| DLSSMoviePipelineSupport | O |
| NIS | O |

### 2-6. 오디오 (Enabled)

AudioModulation, AudioMotorSim, AudioGameplay, AudioGameplayVolume, AudioInsights, Harmonix, SoundCueTemplates, SoundUtilities, Soundscape, Spatialization, WaveformEditor, AudioSynesthesia

### 2-7. 비활성화 플러그인

| 플러그인 | 이유 |
|---|---|
| FSR3 | Win64 전용, AMD GPU 한정 |
| FSR3MovieRenderPipeline | 동상 |
| UdpMessaging | 명시적 비활성 |
| NRD | Nvidia 노이즈 제거 (사용 안 함) |
| AnimationCopilot | 내부 빌드용, 미사용 |
| EditorUtilityCopilot | AI Copilot 계열, 비활성 |
| EverythingCopilot | AI Copilot 계열, 비활성 |
| PerformanceCopilot | AI Copilot 계열, 비활성 |
| WorldBuildCopilot | AI Copilot 계열, 비활성 |
| EcoJointDynamics | 사용 안 함 |
| ZibraVDB | 사용 안 함 |

---

## 3. 엔진 커스텀 플러그인 (표준 UE에 없는 것)

> `Engine/Plugins/Experimental/UAF/` 하위 — SHIFTUP licensee 빌드에 포함된 Epic 미출시 / UAF 전용 플러그인

| 플러그인 이름 | 버전 | 카테고리 | 설명 | 경로 |
|---|---|---|---|---|
| **UAF** | 0.1 | Animation | Unreal Animation Framework 핵심 — 함수형 데이터플로우 애니메이션 시스템 | `Engine/Plugins/Experimental/UAF/UAF/` |
| **UAFWarping** | 0.1 | Animation | UAF용 애니메이션·포즈 워핑 | `Engine/Plugins/Experimental/UAF/UAFWarping/` |
| **UAFStateTree** | 0.1 | Animation | UAF StateTree 연동 | `Engine/Plugins/Experimental/UAF/UAFStateTree/` |
| **UAFPoseSearch** | 0.1 | Animation | UAF Pose Search(Motion Matching) 연동 | `Engine/Plugins/Experimental/UAF/UAFPoseSearch/` |
| **UAFMirroring** | 0.1 | Other | UAF 키프레임 미러링 (Experimental) | `Engine/Plugins/Experimental/UAF/UAFMirroring/` |
| **UAFControlRig** | 0.1 | Animation | UAF Control Rig 연동 | `Engine/Plugins/Experimental/UAF/UAFControlRig/` |
| **UAFChooser** | 0.1 | Animation | UAF Chooser Table 연동 | `Engine/Plugins/Experimental/UAF/UAFChooser/` |
| **UAFAnimGraph** | 0.1 | Animation | UAF 애니메이션 그래프 프레임워크 | `Engine/Plugins/Experimental/UAF/UAFAnimGraph/` |
| **RigLogicUAF** | 1.0 | Animation | MetaHuman RigLogic → UAF 연동 (Experimental) | `Engine/Plugins/Experimental/RigLogicUAF/` |
| **MoverAnimNext** | 1.0 | Gameplay | Mover 플러그인 + UAF 연동 (Experimental) | `Engine/Plugins/Experimental/MoverAnimNext/` |
| **MetaHumanCharacterUAF** | 0.0.1 | MetaHuman | MetaHuman Creator UAF 지원 (Experimental) | `Engine/Plugins/Experimental/MetaHuman/MetaHumanCharacterUAF/` |

---

## 4. 애니메이션 관련 플러그인 종합 (상세)

### SBAnimation (SHIFTUP 자체 개발 — 핵심)

- **버전:** 1.0
- **활성화:** O (uproject에서 명시적 활성화)
- **설명:** SB 커스텀 애니메이션 노드 및 컨트롤러
- **모듈:**
  - `SBAnimationRuntime` (Runtime, PreDefault) — 런타임 애니메이션 노드
  - `SBAnimationEditor` (UncookedOnly, PreDefault) — 에디터 전용 툴
- **의존 플러그인:** EngineCameras, TemplateSequence
- **비고:** Binaries만 존재 (소스 없음), 팀 내부 빌드 전용

### UAF 스택 (엔진 내장, Epic Experimental)

| 플러그인 | 역할 | SB2 사용 |
|---|---|---|
| UAF | 핵심 프레임워크 (Workspace, Module, TraitStack) | O |
| UAFAnimGraph | 애니메이션 그래프 노드 레이어 | O |
| UAFWarping | Stride/Orientation/Slope 워핑 | O |
| UAFPoseSearch | Motion Matching 데이터베이스 연동 | O |
| UAFStateTree | StateTree 기반 조건 로직 | O |
| UAFControlRig | Control Rig 프로시저럴 IK 연동 | O |
| UAFChooser | Chooser Table 에셋 선택 | O |
| UAFMirroring | 포즈 미러링 | O |
| RigLogicUAF | MetaHuman RigLogic → UAF | O |
| MoverAnimNext | Mover 캐릭터 이동 → UAF | O |
| MetaHumanCharacterUAF | MetaHuman 캐릭터 UAF 지원 | O |

### 세컨더리 물리 (Secondary Motion)

| 플러그인 | 방식 | 활성화 상태 |
|---|---|---|
| KawaiiPhysics 1.19.0 | AnimGraph 노드, 본 체인 스프링 | uproject 미기재 (폴더 존재) |
| SPCRJointDynamics 1.0 | SPARKCREATIVE 본 클로스 물리 | uproject 미기재 (폴더 존재) |

> KawaiiPhysics, SPCRJointDynamics는 `Plugins/` 폴더에 존재하나 uproject Plugins 섹션에 명시 없음. 빌드 시 자동 탐색 또는 개별 레벨/프로젝트 설정으로 활성화 가능성 있음.

### 표준 UE 애니메이션 플러그인 (활성화 상태)

| 플러그인 | 용도 |
|---|---|
| PoseSearch | Motion Matching 데이터베이스 |
| MotionWarping | 루트모션 워핑 (타겟 맞춤) |
| MotionTrajectory | 예측 궤적 계산 |
| AnimationWarping | 스트라이드/오리엔테이션 워핑 |
| AnimationLocomotionLibrary | 로코모션 유틸 함수 라이브러리 |
| AnimationModifierLibrary | 애니메이션 수정자 라이브러리 |
| ContextualAnimation | 컨텍스추얼 애니메이션 (멀티캐릭터 상호작용) |
| PhysicsControl | 런타임 물리 컨트롤 |
| LiveLinkControlRig | LiveLink → Control Rig 연동 |
| Chooser | Chooser Table (상태 머신 대안) |
| ChaosClothAsset | Chaos Cloth 에셋 시스템 |
| HairStrands | Groom 헤어 시뮬레이션 |
| Mutable | 런타임 캐릭터 커스터마이제이션 |

---

## 참고

- **SBAnimation 소스 없음:** `Plugins/SBAnimation/` 에는 Binaries + .uplugin만 존재. Engine/Source 없이 팀 공식 빌드에서만 수정 가능.
- **UAF 버전:** 모두 v0.1 (Epic Experimental 단계). UE 5.7 기준 프로덕션 도입 수준으로 격상.
- **Copilot 계열 4종:** 모두 비활성. IEGG(Tencent) 제작, AI 에디터 자동화 도구. openai 1.57.2 의존성 내장.
- **Nvidia 스택:** Streamline + DLSS + NIS 조합으로 Win64 전용 활성화.
