# UE5 + AI GitHub 리포지토리 리서치 보고서

> 조사일: 2026-04-06
> 대상: 언리얼 엔진 + AI 관련 오픈소스 프로젝트 (GitHub 중심)
> 관점: UE5 애니메이션 TA / MCP 기반 AI-UE 연동 워크플로우

---

## 1. MCP 서버 (AI-UE 연동)

MCP(Model Context Protocol)를 통해 AI 어시스턴트(Claude, Cursor, Windsurf 등)가 UE 에디터를 직접 제어할 수 있게 해주는 프로젝트들.

### 1-1. 종합형 MCP 플러그인

| 프로젝트 | URL | 설명 | 비고 |
|---------|-----|------|------|
| **Monolith** | [tumourlove/monolith](https://github.com/tumourlove/monolith) | UE 5.7 전용. 13 MCP 도구 / 1,125+ 액션 / 15 모듈. BP, Material, Niagara, Animation, UI 등 풀 읽기/쓰기. 애니메이션 모듈만 115 액션(시퀀스, 몽타주, 블렌드스페이스, ABP 그래프 작성, PoseSearch, ControlRig, IK Rig, 리타겟 등). | **현재 사용 중 (v0.12.0)** |
| **Flopperam UE MCP** | [flopperam/unreal-engine-mcp](https://github.com/flopperam/unreal-engine-mcp) | UE 5.5+ 지원. 679+ Stars. Flop Agent: 자율 AI가 멀티스텝 워크플로 계획/실행/에러복구. BP 그래프 생성, 레벨 빌딩 특화. Cursor, Claude Code, Windsurf, VS Code Copilot 지원. | 활발한 업데이트 |
| **GenOrca unreal-mcp** | [GenOrca/unreal-mcp](https://github.com/GenOrca/unreal-mcp) | Python + C++. 액터 스폰, 머티리얼 편집, BP 그래프 빌드, Behavior Tree 구성을 자연어로 수행. | Python/C++ 확장 가능 |
| **ue-llm-toolkit** | [ColtonWilley/ue-llm-toolkit](https://github.com/ColtonWilley/ue-llm-toolkit) | 순수 C++ 플러그인. 37 도구 / 200+ 오퍼레이션을 HTTP로 노출. UE 5.7 지원. Claude Code, Cursor 등과 연동. | C++ 네이티브 |

### 1-2. 경량/특화 MCP 서버

| 프로젝트 | URL | 설명 | 비고 |
|---------|-----|------|------|
| **runreal/unreal-mcp** | [runreal/unreal-mcp](https://github.com/runreal/unreal-mcp) | Python 기반. UE 내장 Python Remote Execution 활용으로 별도 플러그인 불필요. 67+ Stars. | **현재 사용 중** |
| **chongdashu/unreal-mcp** | [chongdashu/unreal-mcp](https://github.com/chongdashu/unreal-mcp) | Cursor, Windsurf, Claude Desktop 지원. 자연어로 UE 제어. | |
| **ChiR24/Unreal_mcp** | [ChiR24/Unreal_mcp](https://github.com/ChiR24/Unreal_mcp) | TypeScript + C++ Automation Bridge. Cloth 시뮬레이션(Chaos Cloth) 유일 지원. | **현재 사용 중** |
| **mirno-ehf/ue5-mcp** | [mirno-ehf/ue5-mcp](https://github.com/mirno-ehf/ue5-mcp) | Blueprint를 HTTP로 노출 후 MCP 래핑. Claude Code 연동. | BP 편집 특화 |
| **remiphilippe/mcp-unreal** | [remiphilippe/mcp-unreal](https://github.com/remiphilippe/mcp-unreal) | Go 바이너리. UE 5.7. 헤드리스 빌드/테스트, BP 편집, 프로시저럴 메시, UE API 문서 조회. | |
| **VedantRGosavi/UE5-MCP** | [VedantRGosavi/UE5-MCP](https://github.com/VedantRGosavi/UE5-MCP) | 레벨 셋업 중심. 리서치 문서 포함. | |
| **kvick-games/UnrealMCP** | [kvick-games/UnrealMCP](https://github.com/kvick-games/UnrealMCP) | Python 스크립트로 씬 조작. | |
| **Natfii/ue5-mcp-bridge** | [Natfii/ue5-mcp-bridge](https://github.com/Natfii/ue5-mcp-bridge) | MCP 서버 브릿지. UE5 에디터 연결. | |
| **appleweed/UnrealMCPBridge** | [appleweed/UnrealMCPBridge](https://github.com/appleweed/UnrealMCPBridge) | UE Editor Python API 접근 MCP 서버 플러그인. | |
| **gimmeDG/UnrealEngine5-mcp** | [gimmeDG/UnrealEngine5-mcp](https://github.com/gimmedg/unrealengine5-mcp) | UE 5.6+. GAS(GameplayAbilities) 지원. RAG 기반 Python 스크립팅. | GAS 특화 |
| **ayeletstudioindia/unreal-analyzer-mcp** | [ayeletstudioindia/unreal-analyzer-mcp](https://github.com/ayeletstudioindia/unreal-analyzer-mcp) | UE 소스코드 분석 특화. Claude/Cline으로 UE 소스 분석. | 분석 전용 |
| **winyunq/UnrealMotionGraphicsMCP** | [winyunq/UnrealMotionGraphicsMCP](https://github.com/winyunq/UnrealMotionGraphicsMCP) | UMG 레이아웃 특화. UI 구조, 애니메이션, BP 통합. | UI 특화 |
| **edi3on/py-ue5-mcp-server** | [edi3on/py-ue5-mcp-server](https://github.com/edi3on/py-ue5-mcp-server) | BP 액터 함수 접근용 Python MCP 서버. | |

---

## 2. AI 애니메이션 생성 / 모캡

### 2-1. AI 기반 모션캡처

| 프로젝트 | URL | 설명 | 비고 |
|---------|-----|------|------|
| **MediaPipe4U** | [endink/Mediapipe4u-plugin](https://github.com/endink/Mediapipe4u-plugin) | UE 플러그인. MediaPipe 기반 실시간 바디/페이셜 모캡, TTS, 음성인식. 오프라인/저지연. | 종합 AI 모캡 솔루션 |
| **NVIDIA Audio2Face-3D** | [NVIDIA/Audio2Face-3D](https://github.com/NVIDIA/Audio2Face-3D) | UE5 플러그인 (v2.5). 실시간 AI 기반 페이셜 애니메이션. BP 노드로 캐릭터 리그 연결. UE 5.5/5.6 지원. | 산업 표준급 |
| **NeuroSync Player** | [AnimaVR/NeuroSync_Player](https://github.com/AnimaVR/NeuroSync_Player) | 실시간 페이셜 블렌드셰이프 스트리밍 (LiveLink). 오디오 입력에서 페이셜 애니메이션. | |
| **UE5 Motion Capture** | [albertotrunk/ue5-motion-capture](https://github.com/albertotrunk/ue5-motion-capture) | UE5 MediaPipe 무료 모캡 + 페이셜 플러그인. | |
| **Phiz** | [SpookyCorgi/phiz](https://github.com/SpookyCorgi/phiz) | 브라우저 기반 페이셜 모캡. 블렌드셰이프 데이터를 게임엔진으로 전송. | 웹캠 기반 |
| **PoseAI Camera API** | [PoseAI/PoseCameraAPI](https://github.com/PoseAI/PoseCameraAPI) | AI 포즈 추정 + 스켈레탈 애니메이션 스트리밍. UE4 매니킨/메타휴먼 설정 포함. UE 마켓플레이스 무료. | |
| **OpenFaceUE** | [tbarbanti/OpenFaceUE](https://github.com/tbarbanti/OpenFaceUE) | UE4 플러그인. 페이셜 랜드마크, 헤드 포즈 추정, AU 인식, 시선 추정. 실시간 페이셜 애니메이션. | |
| **UnrealSteel** | [HP-DEVGRU/UnrealSteel](https://github.com/HP-DEVGRU/UnrealSteel) | 유저 모션을 실시간으로 3D 캐릭터에 적용. YouTube 영상에서도 모캡 가능. | |
| **MegaMocapVR** | [Megasteakman/MegaMocapVR](https://github.com/Megasteakman/MegaMocapVR) | SteamVR 기반 모캡. Take Recorder 호환. VTuber 활용 가능. | |
| **VActor** | [endink/VActor](https://github.com/endink/VActor) | 3D 아바타 모캡. MediaPipe + VRM4U + GStreamer 통합. | |

### 2-2. 모션 매칭 / 모션 합성

| 프로젝트 | URL | 설명 | 비고 |
|---------|-----|------|------|
| **GASPALS** | [PolygonHive/GASPALS](https://github.com/PolygonHive/GASPALS) | UE5 Game Animation Sample + ALS 오버레이 레이어링. 모션 매칭 기반. | |
| **GASP-ALS (5.5)** | [Bizzy1234/GASP-ALS](https://github.com/Bizzy1234/GASP-ALS) | UE 5.5 모션 매칭 + ALS. 리플리케이션 포함. | |
| **GASP-ALS-Rep** | [Sparkness/GASP-ALS-Rep](https://github.com/Sparkness/GASP-ALS-Rep) | UE 5.5 모션 매칭 + ALS + 리플리케이션. | |
| **GASP Dynamic Additive Overlay** | [The-Recon-Project/GASP_DynamicAdditiveOverlay](https://github.com/The-Recon-Project/GASP_DynamicAdditiveOverlay) | 다이나믹 애디티브 오버레이 기법을 모션 매칭 시스템에 적용. | |
| **Motion Symphony 2** | [Animation-Uprising/MoSymph2.0-Example-Project](https://github.com/Animation-Uprising/MoSymph2.0-Example-Project) | Motion Symphony 2 예제 프로젝트. UE5 모션 매칭. | |
| **AI4Animation** (Unity) | [sebastianstarke/AI4Animation](https://github.com/sebastianstarke/AI4Animation) | 딥러닝 기반 인터랙티브 모션 합성. 비구조화 모션 데이터에서 라벨링 없이 애니메이션 합성. Unity 기반이나 연구 참고 가치 높음. | 학술 연구 |

### 2-3. 리타게팅 / 리깅

| 프로젝트 | URL | 설명 | 비고 |
|---------|-----|------|------|
| **VBG EditorRigTools** | [Vortex-Basis-LLC/Unreal-VBG_EditorRigTools](https://github.com/Vortex-Basis-LLC/Unreal-VBG_EditorRigTools) | UE5 플러그인. UE4 호환 스켈레톤용 IK Rig 자동 생성. | |
| **BEDLAM 2 Retargeting** | [PerceivingSystems/bedlam2_retargeting](https://github.com/PerceivingSystems/bedlam2_retargeting) | SMPL-X 모션을 UE IK Retargeter로 리타게팅. NeurIPS 2025. | 학술/산업 |
| **VRM4U** | [ruyo/VRM4U](https://github.com/ruyo/VRM4U) | UE5 런타임 VRM 로더. 본, 블렌드셰이프, 스윙본, 콜리전, 휴머노이드 리그 자동 생성. | VRM 아바타 필수 |
| **A2F-UE** | [ahnGeo/A2F-UE](https://github.com/ahnGeo/A2F-UE) | Audio2Face에서 UE로 커브 키 추가. | |

### 2-4. 립싱크 / 페이셜 애니메이션

| 프로젝트 | URL | 설명 | 비고 |
|---------|-----|------|------|
| **NVIDIA Audio2Face-3D** | (위 참조) | 실시간 AI 립싱크. UE5 BP 노드. | |
| **py_audio2face** | [SocAIty/py_audio2face](https://github.com/SocAIty/py_audio2face) | NVIDIA A2F 헤드리스 서버 Python API. USD 파일 생성. 실시간 스트리밍. | |
| **Agentic MetaHumans** | [parthubhe/Agentic_MetaHumans](https://github.com/parthubhe/Agentic_MetaHumans) | A2F 립싱크 + 텍스트 기반 표정 + LangChain 에이전트. 메타휴먼용. | |
| **Audio2Face-to-UE MetaHuman** | [QualityMinds/audio-to-face-to-unreal-metahuman-import-script](https://github.com/QualityMinds/audio-to-face-to-unreal-metahuman-import-script) | A2F 페이셜 애니메이션을 UE5 메타휴먼으로 임포트. | |
| **Oculus LipSync UE5** | [Shiyatzu/OculusLipsyncPlugin-UE5](https://github.com/Shiyatzu/OculusLipsyncPlugin-UE5) | Oculus LipSync UE5 컴파일 버전. | |

---

## 3. AI NPC / 행동 제어

### 3-1. LLM 기반 NPC

| 프로젝트 | URL | 설명 | 비고 |
|---------|-----|------|------|
| **Convai UE SDK** | [Conv-AI/Convai-UnrealEngine-SDK](https://github.com/Conv-AI/Convai-UnrealEngine-SDK) | 대화형 AI NPC. 환경 인식 + 음성 명령 응답. 가장 종합적인 NPC AI SDK. | 상용 서비스 |
| **AI NPCs with Actions+Dialogue** | [AkshitIreddy/AI-NPCs-that-can-Control-their-Actions-along-with-Dialogue](https://github.com/AkshitIreddy/AI-NPCs-that-can-Control-their-Actions-along-with-Dialogue) | NPC가 대화하면서 행동도 수행 (예: 마법 주문 + 시전). Cohere Command 모델. | |
| **NPC Plugin Project** | [Afterlife1707/NPC-Plugin-Project](https://github.com/Afterlife1707/NPC-Plugin-Project) | GPT 기반 NPC. 동적 메모리, 순찰 행동, 동반자 NPC. C++ 프로젝트. | |
| **Local LLMs UE5** | [joe-gibbs/local-llms-ue5](https://github.com/joe-gibbs/local-llms-ue5) | 로컬 LLM NPC 데모. StyleTTS + llama.cpp + Mistral7b. UE 5.3. | 오프라인 가능 |
| **ChatGPT-NPC** | [utkualkan4112/ChatGPT-NPC](https://github.com/utkualkan4112/ChatGPT-NPC) | ChatGPT + Eleven Labs TTS로 지능형 RPG NPC. | |
| **ARIS-Unreal-GPT** | [oscaem/ARIS-Unreal-GPT](https://github.com/oscaem/ARIS-Unreal-GPT) | GPT-4 + Azure TTS + UE5 데모 게임. NPC가 게임 이벤트 인지 + 행동. | |
| **Dynamic NPC Dialogue (AWS)** | [aws-solutions-library-samples/guidance-for-dynamic-game-npc-dialogue-on-aws](https://github.com/aws-solutions-library-samples/guidance-for-dynamic-game-npc-dialogue-on-aws) | MetaHuman + Claude 3.5 + AWS 인프라. NPC 대화 자동화. | AWS 종속 |
| **Intelligent-NPCs** | [brandybrawler/Intelligent-NPCs](https://github.com/brandybrawler/Intelligent-NPCs) | UE5 플러그인. BP에서 NPC 행동, 욕구, 루틴 시스템. | |

### 3-2. 감정 / 행동 시스템

| 프로젝트 | URL | 설명 | 비고 |
|---------|-----|------|------|
| **EmotionEngine** | [josephkirk/EmotionEngine](https://github.com/josephkirk/EmotionEngine) | UE 5.5 플러그인. 심리학 기반 캐릭터 감정 시스템. | |
| **ReasonablePlanningAI** | [hollsteinm/ReasonablePlanningAI](https://github.com/hollsteinm/ReasonablePlanningAI) | UE4/5 AIModule 확장. Utility AI + GOAP(Goal Oriented Action Planning). 데이터 주도 설계. | |
| **TobenotLLMGameplay** | [tobenot/TobenotLLMGameplay](https://github.com/tobenot/TobenotLLMGameplay) | "UE C++용 Langchain". LLM 게임플레이 범용 로직 플러그인 컬렉션. | |

---

## 4. ML/NN 프레임워크 & 플러그인

### 4-1. 강화학습 (Reinforcement Learning)

| 프로젝트 | URL | 설명 | 비고 |
|---------|-----|------|------|
| **AMD Schola v2** | [GPUOpen-LibrariesAndSDKs/Schola](https://github.com/GPUOpen-LibrariesAndSDKs/Schola) | AMD 공식. UE RL 플러그인. Gymnasium, RLlib, SB3 연동. ONNX 모델 추론. 동적 에이전트 생성/삭제. Minari 데이터셋 지원. | 활발한 개발 |
| **UE Learning Agents** | (Epic 공식, UE 내장) | NPC 훈련용 강화학습/모방학습. UE 5.3+. | 에픽 공식 |
| **UnrealMLAgents** | [AlanLaboratory/UnrealMLAgents](https://github.com/AlanLaboratory/UnrealMLAgents) | Unity ML-Agents를 UE로 포팅. 딥 강화학습. | |
| **NevarokML** | [nevarok/NevarokML](https://github.com/nevarok/NevarokML) | UE에서 stable-baselines3로 RL 훈련. | |
| **MindMaker** | [krumiaa/MindMaker](https://github.com/krumiaa/MindMaker) | UE4 ML 툴킷. 다수의 Python ML 라이브러리 통합. 멀티에이전트/적대적 설정. | |
| **MaRLEnE** | [ducandu/MaRLEnE](https://github.com/ducandu/MaRLEnE) | UE4 + TensorForce. 병렬화된 RL 파이프라인. | |
| **Gym-UnrealCV** | [zfw1226/gym-unrealcv](https://github.com/zfw1226/gym-unrealcv) | UE + OpenAI Gym. 시각적 강화학습. 멀티에이전트 RL. | |
| **UnrealZoo-Gym** | [UnrealZoo/unrealzoo-gym](https://github.com/UnrealZoo/unrealzoo-gym) | **ICCV 2025 Highlights**. 대규모 포토리얼리스틱 가상 세계. 100+ 씬. 인간/로봇/차량/동물 에이전트. UE 5.5. | 학술 최신 |

### 4-2. 뉴럴 네트워크 추론 (NNE / ONNX)

| 프로젝트 | URL | 설명 | 비고 |
|---------|-----|------|------|
| **UE NNE** | (Epic 공식, UE 내장) | Neural Network Engine. 실험->베타. 사전훈련 모델 로드/실행. 애니메이션, 렌더링, 물리 등. | UE 5.4+ |
| **MS ONNX Runtime UE** | [microsoft/OnnxRuntime-UnrealEngine](https://github.com/microsoft/OnnxRuntime-UnrealEngine) | 스타일 전송 뉴럴넷 실시간 적용. CPU/GPU 추론. UE ~5.2. | MS 공식 |
| **Intel OpenVINO NNE** | [GameTechDev/NNERuntimeOpenVINO](https://github.com/GameTechDev/NNERuntimeOpenVINO) | Intel OpenVINO NNE 런타임. CPU/GPU/NPU 지원. | Intel 공식 |
| **ARM ML Extensions for Vulkan** | [arm/ml-extensions-for-vulkan-unreal-plugin](https://github.com/arm/ml-extensions-for-vulkan-unreal-plugin) | NNE 확장. Vulkan ML Extensions 런타임. | ARM 공식 |
| **ARM Neural Graphics** | [arm/neural-graphics-for-unreal](https://github.com/arm/neural-graphics-for-unreal) | NNE 기반 ML 모델 추론. UE 5.5. | ARM 공식 |
| **NVIDIA NVIGI UE Plugin** | [NVIDIA-RTX/NVIGI-UEPlugin](https://github.com/NVIDIA-RTX/NVIGI-UEPlugin) | In-Game Inference SDK UE 샘플. GPT/LLM 챗봇 통합 예제. RTX 30x0+ 필요. UE 5.5. | NVIDIA 공식 |
| **NVIDIA NVIGI Core** | [NVIDIA-RTX/NVIGI](https://github.com/NVIDIA-RTX/NVIGI) | 크로스 플랫폼 In-Game Inferencing. AI 추론 + 그래픽스 통합. | NVIDIA 공식 |

### 4-3. 머신러닝 범용

| 프로젝트 | URL | 설명 | 비고 |
|---------|-----|------|------|
| **MachineLearningRemote-Unreal** | [getnamo/MachineLearningRemote-Unreal](https://github.com/getnamo/MachineLearningRemote-Unreal) | TensorFlow/PyTorch 원격 서버 호출 플러그인. | |
| **SelfLearning AI Plugin** | [Pogbino395/SelfLearning_AI_Plugin_UE5.3](https://github.com/Pogbino395/SelfLearning_AI_Plugin_UE5.3) | UE 5.3 자기학습 AI 플러그인. | |
| **UE Learning Agents Environment** | [XanderBert/Unreal-Engine-Learning-Agents-Learning-Environment](https://github.com/XanderBert/Unreal-Engine-Learning-Agents-Learning-Environment) | UE Learning Agents 튜토리얼/라이트업. | |

---

## 5. 프로시저럴 애니메이션

| 프로젝트 | URL | 설명 | 비고 |
|---------|-----|------|------|
| **ProceduralFPSAnimationsPlugin** | [gerlogu/ProceduralFPSAnimationsPlugin](https://github.com/gerlogu/ProceduralFPSAnimationsPlugin) | UE4/5 FPS 프로시저럴 애니메이션. 커브 기반. | |
| **Nobunanim** | [Nobuna-no/Nobunanim](https://github.com/Nobuna-no/Nobunanim) | UE4 프로시저럴 애니메이션 디자인 플러그인. MIT. | |
| **Skelly** | [enlight/Skelly](https://github.com/enlight/Skelly) | UE4 반프로시저럴 캐릭터 애니메이션. 포즈 생성 + 프로시저럴 보간. | |
| **ue-procedural-limbs** | [mmmeri/ue-procedural-limbs](https://github.com/mmmeri/ue-procedural-limbs) | 곤충형 다리 프로시저럴 애니메이션. IK 기반 자동 리밍 + 바디 반응. | |

---

## 6. AI 코딩 도구 (UE 개발용)

### 6-1. 에디터 내장 AI 어시스턴트

| 프로젝트 | URL | 설명 | 비고 |
|---------|-----|------|------|
| **UnrealClaude** | [Natfii/UnrealClaude](https://github.com/Natfii/UnrealClaude) | Claude Code CLI를 UE 5.7 에디터에 통합. 내장 UE 5.7 API 문서 컨텍스트. 채팅 패널에서 라이브 스트리밍. | |
| **Unreal Agent** | [TREE-Ind/Unreal-Agent](https://github.com/TREE-Ind/Unreal-Agent) | GPT 기반 에디터 코파일럿. 도커블 탭. Python, 씬 쿼리, 스크린샷, 외부 도구 연동. | |
| **Autonomix** | [PRQELT/Autonomix](https://github.com/PRQELT/Autonomix) | 자율 AI 에이전트. BP, C++, 레벨, 머티리얼, 위젯 생성을 자연어로. UE5 에디터 내. | |
| **unreal_ai_assistant** | [hamleetski/unreal_ai_assistant](https://github.com/hamleetski/unreal_ai_assistant) | LLM이 BP 이벤트그래프 읽기/설명/이슈 식별/자동 수정. | BP 분석 |

### 6-2. LLM / GenAI 통합 플러그인

| 프로젝트 | URL | 설명 | 비고 |
|---------|-----|------|------|
| **UnrealGenAISupport** | [prajwalshettydev/UnrealGenAISupport](https://github.com/prajwalshettydev/UnrealGenAISupport) | GPT, Deepseek, Claude, Gemini 3, Qwen, Grok 4.1 등 멀티 LLM. C++ + BP. MCP 서버 포함. TTS/Inworld 추가 예정. | 가장 포괄적 |
| **LLM-Connect** | [yigit-altun-rootrootq/LLM-Connect](https://github.com/yigit-altun-rootrootq/LLM-Connect) | BP 전용. GPT, Gemini, Claude, Ollama. 드롭다운으로 모델 전환. 코딩 불필요. | BP 전용 |
| **Llama-Unreal** | [getnamo/Llama-Unreal](https://github.com/getnamo/Llama-Unreal) | llama.cpp UE5 플러그인. 로컬 LLM 임베딩. GPU 레이어, Jinja 템플릿, 채팅 히스토리. | 로컬 LLM |
| **UnrealAiConnector** | [Sovahero/UnrealAiConnector](https://github.com/Sovahero/UnrealAiConnector) | LLM Connector 플러그인. OpenRouter 등 API 서비스 연동. | |
| **LocalLLM-Demo-UE5** | [Akiya-Research-Institute/LocalLLM-Demo-UE5](https://github.com/Akiya-Research-Institute/LocalLLM-Demo-UE5) | GGUF 포맷 로컬 LLM 로드/실행. UE 5.4. | |
| **HttpGPT** | [lucoiso/UEHttpGPT](https://github.com/lucoiso/UEHttpGPT) | OpenAI GPT (ChatGPT/DALL-E) 비동기 REST 통합. | |
| **OpenAI-Api-Unreal** | [KellanM/OpenAI-Api-Unreal](https://github.com/KellanM/OpenAI-Api-Unreal) | OpenAI API UE 통합. UE 4.26~5.3. | |
| **UnrealOpenAIPlugin** | [life-exe/UnrealOpenAIPlugin](https://github.com/life-exe/UnrealOpenAIPlugin) | OpenAI API 종합 래퍼. | |
| **MultiAIProvider** | [takashi-marimo/MultiAIProvider](https://github.com/takashi-marimo/MultiAIProvider) | Claude, ChatGPT, Gemini 멀티 프로바이더. BP 지원 + 비동기. | |
| **Bluepy** | [ZackBradshaw/Bluepy](https://github.com/ZackBradshaw/Bluepy) | OpenAI API로 BP 노드 생성. | |

### 6-3. 상용/SaaS AI 도구

| 서비스 | 설명 | 비고 |
|---------|------|------|
| **Aura (Ramen)** | 2026년 1월 출시. UE5 에디터 AI 어시스턴트. Telos 2.0 (BP AI), Dragon Agent (자율 에이전트 루프). Aura 12.0 beta: 애니메이션/리깅 기능 추가. | 초대 전용 |
| **Ludus AI** | UE5 C++ 어시스턴트, BP 코파일럿, 씬 생성, AI UE 전문가. | 상용 |
| **CodeGPT** | UE5.5 AI 개발. C++ 코드 생성, BP 생성. Nanite/Lumen/MetaHuman 지원. | SaaS |
| **ClaudeAI Plugin** | UE5 AI 어시스턴트. 코드 생성, BP 지원, 실시간 가이드. | 상용 |

---

## 7. 기타 주목할 프로젝트

### 7-1. Stable Diffusion / 디퓨전 모델

| 프로젝트 | URL | 설명 | 비고 |
|---------|-----|------|------|
| **ComfyTextures** | [AlexanderDzhoganov/ComfyTextures](https://github.com/AlexanderDzhoganov/ComfyTextures) | UE + ComfyUI 통합. 디퓨전 모델로 자동 텍스처링. | |
| **Unreal-StableDiffusionTools** | [Mystfit/Unreal-StableDiffusionTools](https://github.com/Mystfit/Unreal-StableDiffusionTools) | UE 씬을 Stable Diffusion으로 애니메이트. 로컬/Stability.AI/Stable Horde 지원. | |
| **Unreal-Diffusion** | [emomilol1213/Unreal-Diffusion](https://github.com/emomilol1213/Unreal-Diffusion) | InvokeAI 기반 UE 내 텍스처 생성 GUI. | |
| **SdiffusionUE** | [Ow1onp/SdiffusionUE](https://github.com/Ow1onp/SdiffusionUE) | 로컬 SD API로 UE 내 이미지 생성. | |
| **StableGen** | [sakalond/StableGen](https://github.com/sakalond/StableGen) | 단일 이미지/텍스트에서 텍스처 입힌 3D 메시 생성. TRELLIS.2 기반. | |

### 7-2. NVIDIA ACE / 디지털 휴먼

| 프로젝트 | URL | 설명 | 비고 |
|---------|-----|------|------|
| **NVIDIA ACE** | [NVIDIA/ACE](https://github.com/NVIDIA/ACE) | 디지털 어시스턴트 워크플로. 실시간 언어/음성/애니메이션. Tokkio 포함. | NVIDIA 공식 |
| **Digital Human Blueprint** | [NVIDIA-AI-Blueprints/digital-human](https://github.com/NVIDIA-AI-Blueprints/digital-human) | Tokkio 기반 3D 애니메이션 디지털 휴먼 인터페이스. | NVIDIA 공식 |
| **Audio2Face-3D Training Framework** | [NVIDIA/Audio2Face-3D-Training-Framework](https://github.com/NVIDIA/Audio2Face-3D-Training-Framework) | A2F 모델 훈련 프레임워크. | NVIDIA 공식 |

### 7-3. 합성 데이터 / 컴퓨터 비전

| 프로젝트 | URL | 설명 | 비고 |
|---------|-----|------|------|
| **UnrealCV** | [unrealcv/unrealcv](https://github.com/unrealcv/unrealcv) | UE + 컴퓨터 비전 연구 연결. PyTorch/TensorFlow 연동. | |
| **UnrealGT** | [unrealgt/unrealgt](https://github.com/unrealgt/unrealgt) | UE 기반 합성 테스트 데이터 생성 프레임워크. | |
| **NVIDIA NDDS** | [NVIDIA/Dataset_Synthesizer](https://github.com/NVIDIA/Dataset_Synthesizer) | UE4 합성 데이터. 세그멘테이션, 뎁스, 포즈, 키포인트 등. | NVIDIA 공식 |
| **SynavisUE** | [dhelmrich/SynavisUE](https://github.com/dhelmrich/SynavisUE) | WebRTC 합성 데이터 훈련. | |

### 7-4. Embodied AI / 시뮬레이션

| 프로젝트 | URL | 설명 | 비고 |
|---------|-----|------|------|
| **UnrealZoo-Gym** | [UnrealZoo/unrealzoo-gym](https://github.com/UnrealZoo/unrealzoo-gym) | **ICCV 2025**. 100+ 포토리얼 씬. 인간/로봇/차량/동물 에이전트. UE 5.5. OpenAI Gym 호환. | 최신 학술 |
| **FarmSimulator-RL** | [GP2P/FarmSimulator-RL](https://github.com/GP2P/FarmSimulator-RL) | RL 기반 에이전트 시뮬레이션. 각 NPC가 Behavior Tree로 태스크 수행. | |

### 7-5. Awesome 리스트 / 리소스 모음

| 프로젝트 | URL | 설명 |
|---------|-----|------|
| **awesome-unreal (Coop56)** | [Coop56/awesome-unreal](https://github.com/Coop56/awesome-unreal) | UE5 리소스 큐레이션. |
| **awesome-unreal (insthync)** | [insthync/awesome-unreal](https://github.com/insthync/awesome-unreal) | UE4/5 오픈소스 리포 카테고리별 정리. |
| **awesome-ue4** | [terrehbyte/awesome-ue4](https://github.com/terrehbyte/awesome-ue4) | UE4 리소스 큐레이션 리스트. |
| **Papers with UnrealCV** | [unrealcv/papers-with-unrealcv](https://github.com/unrealcv/papers-with-unrealcv) | UnrealCV 활용 논문 큐레이션. |
| **awesome-3d-diffusion** | [cwchenwang/awesome-3d-diffusion](https://github.com/cwchenwang/awesome-3d-diffusion) | 3D 생성 디퓨전 모델 논문 모음. |

---

## 핵심 요약: 애니메이션 TA 관점 우선순위

### 즉시 활용 가능 (현재 워크플로우 확장)

1. **NVIDIA Audio2Face-3D** -- 실시간 AI 립싱크/페이셜, UE5 플러그인으로 메타휴먼 연동 바로 가능
2. **MediaPipe4U** -- 웹캠만으로 바디+페이셜 모캡, UE 플러그인 형태
3. **Flopperam UE MCP** -- Monolith와 병행 사용 가능한 MCP. 레벨 빌딩/BP 생성에 강점
4. **AMD Schola v2** -- UE RL 플러그인. NPC 애니메이션 행동 훈련에 활용 가능
5. **ue-llm-toolkit** -- C++ 네이티브 37 도구. Monolith 대안/보완으로 검토 가치

### 중기 검토 (연구/실험)

6. **UnrealZoo-Gym** -- Embodied AI 연구. 다양한 캐릭터/환경으로 모션 학습 실험 가능
7. **BEDLAM 2 Retargeting** -- SMPL-X 모캡 데이터 리타게팅. 대량 모션 데이터 활용 파이프라인
8. **Autonomix** -- 자율 AI 에이전트로 BP/레벨/머티리얼 생성 자동화
9. **LLM-Connect** -- BP 전용 LLM 통합. 프로토타이핑에 유용
10. **NVIDIA NVIGI** -- 인게임 AI 추론. 향후 실시간 NPC 행동에 활용 가능

### 장기 모니터링

11. **Epic NNE/Learning Agents** -- 공식 엔진 내장 AI. AnimNext와의 통합 방향 주시
12. **AI4Animation** (Unity) -- 학술 연구 참고. 유사 접근법의 UE 적용 가능성
13. **Aura (Ramen)** -- 상용 AI 어시스턴트. 애니메이션/리깅 에이전트 기능 추가 중

---

## Epic Games 공식 AI 기술 현황 (2025-2026)

| 기술 | 상태 | 비고 |
|------|------|------|
| **NNE (Neural Network Engine)** | Beta (5.4+) | 사전훈련 모델 로드/실행. 애니메이션/렌더링/물리 |
| **Learning Agents** | Beta (5.3+) | RL/IL로 NPC 훈련. 에픽 공식 ML 플러그인 |
| **AnimNext** | 실험적 | 차세대 애니메이션 시스템. ABP 대체 목표 |
| **I/ITSEC 2025** | 발표 | NNE 라이브 데모 + ROS 지원 업데이트 |

---

Sources:
- [Monolith](https://github.com/tumourlove/monolith)
- [Flopperam UE MCP](https://github.com/flopperam/unreal-engine-mcp)
- [runreal/unreal-mcp](https://github.com/runreal/unreal-mcp)
- [ChiR24/Unreal_mcp](https://github.com/ChiR24/Unreal_mcp)
- [GenOrca/unreal-mcp](https://github.com/GenOrca/unreal-mcp)
- [ue-llm-toolkit](https://github.com/ColtonWilley/ue-llm-toolkit)
- [NVIDIA Audio2Face-3D](https://github.com/NVIDIA/Audio2Face-3D)
- [NVIDIA ACE](https://github.com/NVIDIA/ACE)
- [NVIDIA NVIGI](https://github.com/NVIDIA-RTX/NVIGI)
- [MediaPipe4U](https://github.com/endink/Mediapipe4u-plugin)
- [AMD Schola](https://github.com/GPUOpen-LibrariesAndSDKs/Schola)
- [UnrealMLAgents](https://github.com/AlanLaboratory/UnrealMLAgents)
- [UnrealZoo-Gym](https://github.com/UnrealZoo/unrealzoo-gym)
- [UnrealGenAISupport](https://github.com/prajwalshettydev/UnrealGenAISupport)
- [LLM-Connect](https://github.com/yigit-altun-rootrootq/LLM-Connect)
- [Llama-Unreal](https://github.com/getnamo/Llama-Unreal)
- [Convai UE SDK](https://github.com/Conv-AI/Convai-UnrealEngine-SDK)
- [ComfyTextures](https://github.com/AlexanderDzhoganov/ComfyTextures)
- [VRM4U](https://github.com/ruyo/VRM4U)
- [BEDLAM 2 Retargeting](https://github.com/PerceivingSystems/bedlam2_retargeting)
- [Autonomix](https://github.com/PRQELT/Autonomix)
- [UnrealClaude](https://github.com/Natfii/UnrealClaude)
- [AI4Animation](https://github.com/sebastianstarke/AI4Animation)
- [Microsoft ONNX Runtime UE](https://github.com/microsoft/OnnxRuntime-UnrealEngine)
- [Intel OpenVINO NNE](https://github.com/GameTechDev/NNERuntimeOpenVINO)
- [Awesome Unreal](https://github.com/Coop56/awesome-unreal)
- [UnrealCV](https://github.com/unrealcv/unrealcv)
- [Epic NNE Docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/neural-network-engine-in-unreal-engine)
- [Epic Learning Agents](https://dev.epicgames.com/community/learning/tutorials/8OWY/unreal-engine-learning-agents-introduction-5-3)
