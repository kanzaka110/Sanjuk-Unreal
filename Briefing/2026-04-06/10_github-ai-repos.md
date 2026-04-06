# GitHub + AI 프로젝트 — UE 애니메이션 관련

> 2026-04-06 브리핑 | [목차로 돌아가기](00_INDEX.md)

---

## 1. MCP 서버 (AI-UE 연동) — 15+ 프로젝트

### 종합형

| 프로젝트 | Stars | 설명 | 상태 |
| --------- | ------- | ------ | ------ |
| [**Monolith**](https://github.com/tumourlove/monolith) | - | 1,125 액션 / 15 모듈. 애니메이션 115 액션. UE 5.7 | **현재 사용 중** |
| [**Flopperam UE MCP**](https://github.com/flopperam/unreal-engine-mcp) | 679+ | Flop Agent: 자율 멀티스텝 워크플로. BP/레벨 빌딩 특화 | 활발 |
| [**GenOrca/unreal-mcp**](https://github.com/GenOrca/unreal-mcp) | - | Python + C++. 액터, 머티리얼, BP, BT 자연어 제어 | |
| [**ue-llm-toolkit**](https://github.com/ColtonWilley/ue-llm-toolkit) | - | 순수 C++ 플러그인. 37 도구 / 200+ 오퍼레이션. UE 5.7 | C++ 네이티브 |

### 경량/특화

| 프로젝트 | 특화 | 설명 |
| --------- | ------ | ------ |
| [runreal/unreal-mcp](https://github.com/runreal/unreal-mcp) | Python | 플러그인 불필요, Python Remote Exec 활용. **현재 사용 중** |
| [ChiR24/Unreal_mcp](https://github.com/ChiR24/Unreal_mcp) | Chaos Cloth | Cloth 시뮬 유일 지원. **현재 사용 중** |
| [remiphilippe/mcp-unreal](https://github.com/remiphilippe/mcp-unreal) | Go/헤드리스 | Go 바이너리, 헤드리스 빌드/테스트, UE 5.7 |
| [mirno-ehf/ue5-mcp](https://github.com/mirno-ehf/ue5-mcp) | BP 편집 | BP를 HTTP로 노출 |
| [gimmeDG/UnrealEngine5-mcp](https://github.com/gimmedg/unrealengine5-mcp) | GAS | GameplayAbilities 특화, RAG Python |
| [winyunq/UnrealMotionGraphicsMCP](https://github.com/winyunq/UnrealMotionGraphicsMCP) | UI/UMG | UI 레이아웃, 애니메이션 |
| [ayeletstudioindia/unreal-analyzer-mcp](https://github.com/ayeletstudioindia/unreal-analyzer-mcp) | 소스 분석 | UE 소스코드 분석 전용 |
| [Autonomix](https://github.com/PRQELT/Autonomix) | 자율 에이전트 | BP/C++/레벨/머티리얼 자연어 생성 |

---

## 2. AI 애니메이션 / 모캡 — 20+ 프로젝트

### AI 모캡

| 프로젝트 | 유형 | 설명 |
| --------- | ------ | ------ |
| [**NVIDIA Audio2Face-3D**](https://github.com/NVIDIA/Audio2Face-3D) | 페이셜 | 실시간 AI 립싱크, UE5 BP 노드, MetaHuman 연동. **즉시 활용 가능** |
| [**MediaPipe4U**](https://github.com/endink/Mediapipe4u-plugin) | 바디+페이셜 | 웹캠 모캡, 오프라인/저지연. UE 플러그인. **즉시 활용 가능** |
| [NeuroSync Player](https://github.com/AnimaVR/NeuroSync_Player) | 페이셜 | 오디오→페이셜 블렌드셰이프 LiveLink 스트리밍 |
| [PoseAI Camera API](https://github.com/PoseAI/PoseCameraAPI) | 포즈 추정 | AI 포즈→스켈레탈 애니메이션. UE 마켓 무료 |
| [UnrealSteel](https://github.com/HP-DEVGRU/UnrealSteel) | 바디 | YouTube 영상에서도 모캡 가능 |
| [MegaMocapVR](https://github.com/Megasteakman/MegaMocapVR) | VR 모캡 | SteamVR 기반, Take Recorder 호환 |
| [VActor](https://github.com/endink/VActor) | 3D 아바타 | MediaPipe + VRM4U + GStreamer |

### 립싱크 / 페이셜

| 프로젝트 | 설명 |
| --------- | ------ |
| [py_audio2face](https://github.com/SocAIty/py_audio2face) | A2F 헤드리스 서버 Python API |
| [Agentic MetaHumans](https://github.com/parthubhe/Agentic_MetaHumans) | A2F 립싱크 + LangChain 에이전트 |
| [Audio2Face-to-UE MetaHuman](https://github.com/QualityMinds/audio-to-face-to-unreal-metahuman-import-script) | A2F→MetaHuman 임포트 |

### 모션 매칭 확장

| 프로젝트 | 설명 |
| --------- | ------ |
| [GASPALS](https://github.com/PolygonHive/GASPALS) | GASP + ALS 오버레이 레이어링 |
| [GASP-ALS](https://github.com/Bizzy1234/GASP-ALS) | UE 5.5 Motion Matching + ALS + 리플리케이션 |
| [GASP Dynamic Additive Overlay](https://github.com/The-Recon-Project/GASP_DynamicAdditiveOverlay) | 다이나믹 애디티브 오버레이 |
| [AI4Animation](https://github.com/sebastianstarke/AI4Animation) | 딥러닝 모션 합성 (Unity, 학술 참고) |

### 리타게팅 / 리깅

| 프로젝트 | 설명 |
| --------- | ------ |
| [BEDLAM 2 Retargeting](https://github.com/PerceivingSystems/bedlam2_retargeting) | SMPL-X→UE IK Retargeter (NeurIPS 2025) |
| [VRM4U](https://github.com/ruyo/VRM4U) | UE5 VRM 로더. 본/블렌드셰이프/리그 자동 생성 |
| [VBG EditorRigTools](https://github.com/Vortex-Basis-LLC/Unreal-VBG_EditorRigTools) | UE4 호환 스켈레톤 IK Rig 자동 생성 |

---

## 3. AI NPC / 행동 제어 — 10+ 프로젝트

| 프로젝트 | 유형 | 설명 |
| --------- | ------ | ------ |
| [**Convai UE SDK**](https://github.com/Conv-AI/Convai-UnrealEngine-SDK) | 종합 NPC AI | 대화 + 환경 인식 + 음성 명령. 가장 종합적 |
| [Local LLMs UE5](https://github.com/joe-gibbs/local-llms-ue5) | 로컬 LLM | StyleTTS + llama.cpp + Mistral7b. 오프라인 가능 |
| [ARIS-Unreal-GPT](https://github.com/oscaem/ARIS-Unreal-GPT) | GPT-4 NPC | GPT-4 + Azure TTS. NPC가 게임 이벤트 인지 |
| [Dynamic NPC (AWS)](https://github.com/aws-solutions-library-samples/guidance-for-dynamic-game-npc-dialogue-on-aws) | 클라우드 | MetaHuman + Claude 3.5 + AWS |
| [EmotionEngine](https://github.com/josephkirk/EmotionEngine) | 감정 시스템 | UE 5.5 심리학 기반 캐릭터 감정 |
| [TobenotLLMGameplay](https://github.com/tobenot/TobenotLLMGameplay) | 범용 LLM | "UE C++용 Langchain". 게임플레이 로직 |
| [ReasonablePlanningAI](https://github.com/hollsteinm/ReasonablePlanningAI) | GOAP | Utility AI + GOAP. 데이터 주도 설계 |

---

## 4. ML/NN 프레임워크 — 15+ 프로젝트

### 강화학습

| 프로젝트 | 출처 | 설명 |
| --------- | ------ | ------ |
| [**AMD Schola v2**](https://github.com/GPUOpen-LibrariesAndSDKs/Schola) | AMD 공식 | UE RL 플러그인. Gymnasium/RLlib/SB3. ONNX 추론 내장 |
| UE Learning Agents | Epic 공식 | NPC 훈련 RL/IL. UE 5.3+ 내장 |
| [**UnrealZoo-Gym**](https://github.com/UnrealZoo/unrealzoo-gym) | ICCV 2025 | 100+ 포토리얼 씬. 인간/로봇/동물 에이전트. UE 5.5 |
| [UnrealMLAgents](https://github.com/AlanLaboratory/UnrealMLAgents) | 커뮤니티 | Unity ML-Agents를 UE로 포팅 |
| [MindMaker](https://github.com/krumiaa/MindMaker) | 커뮤니티 | UE4 ML 툴킷. 멀티에이전트/적대적 설정 |

### NN 추론 런타임

| 프로젝트 | 출처 | 설명 |
| --------- | ------ | ------ |
| UE NNE | Epic 공식 | Neural Network Engine. Beta (5.4+) |
| [MS ONNX Runtime UE](https://github.com/microsoft/OnnxRuntime-UnrealEngine) | MS 공식 | 스타일 전송 NN 실시간 적용 |
| [Intel OpenVINO NNE](https://github.com/GameTechDev/NNERuntimeOpenVINO) | Intel 공식 | CPU/GPU/NPU NNE 런타임 |
| [NVIDIA NVIGI](https://github.com/NVIDIA-RTX/NVIGI-UEPlugin) | NVIDIA 공식 | 인게임 AI 추론 SDK. RTX 30x0+ |
| [ARM Neural Graphics](https://github.com/arm/neural-graphics-for-unreal) | ARM 공식 | NNE 기반 ML 모델 추론 |

---

## 5. 프로시저럴 애니메이션

| 프로젝트 | 설명 |
| --------- | ------ |
| [ProceduralFPSAnimationsPlugin](https://github.com/gerlogu/ProceduralFPSAnimationsPlugin) | FPS 프로시저럴 애니메이션, 커브 기반 |
| [ue-procedural-limbs](https://github.com/mmmeri/ue-procedural-limbs) | 곤충형 다리 IK 프로시저럴 |
| [Nobunanim](https://github.com/Nobuna-no/Nobunanim) | UE4 프로시저럴 애니메이션 디자인 |
| [Skelly](https://github.com/enlight/Skelly) | 반프로시저럴 캐릭터 애니메이션 |

---

## 6. AI 코딩 도구 (UE 개발용)

### 에디터 내장

| 프로젝트 | 설명 |
| --------- | ------ |
| [**UnrealClaude**](https://github.com/Natfii/UnrealClaude) | Claude Code CLI를 UE 5.7 에디터에 통합. API 문서 컨텍스트 |
| [Unreal Agent](https://github.com/TREE-Ind/Unreal-Agent) | GPT 기반 에디터 코파일럿. 씬 쿼리, 스크린샷 |
| [Autonomix](https://github.com/PRQELT/Autonomix) | 자율 AI 에이전트. BP/C++/레벨 자연어 생성 |

### LLM 통합 플러그인

| 프로젝트 | 특징 |
| --------- | ------ |
| [**UnrealGenAISupport**](https://github.com/prajwalshettydev/UnrealGenAISupport) | GPT, Claude, Gemini, Qwen, Grok 등 멀티 LLM. C++ + BP |
| [**LLM-Connect**](https://github.com/yigit-altun-rootrootq/LLM-Connect) | BP 전용. GPT/Gemini/Claude/Ollama. 코딩 불필요 |
| [Llama-Unreal](https://github.com/getnamo/Llama-Unreal) | llama.cpp UE5 플러그인. 로컬 LLM |
| [MultiAIProvider](https://github.com/takashi-marimo/MultiAIProvider) | Claude/ChatGPT/Gemini 멀티 프로바이더 |

### 상용 서비스

| 서비스 | 설명 |
| -------- | ------ |
| **Aura (Ramen)** | 2026.01 출시. BP AI + Dragon Agent. 애니메이션/리깅 기능 추가 중 |
| **Ludus AI** | UE5 C++ 어시스턴트 + BP 코파일럿 + 씬 생성 |

---

## 7. 기타 주목할 프로젝트

### Stable Diffusion / 디퓨전

| 프로젝트 | 설명 |
| --------- | ------ |
| [ComfyTextures](https://github.com/AlexanderDzhoganov/ComfyTextures) | UE + ComfyUI 자동 텍스처링 |
| [Unreal-StableDiffusionTools](https://github.com/Mystfit/Unreal-StableDiffusionTools) | UE 씬 SD 애니메이트 |
| [StableGen](https://github.com/sakalond/StableGen) | 이미지/텍스트→텍스처 3D 메시 (TRELLIS.2) |

### NVIDIA 디지털 휴먼

| 프로젝트 | 설명 |
| --------- | ------ |
| [NVIDIA ACE](https://github.com/NVIDIA/ACE) | 실시간 언어/음성/애니메이션 디지털 휴먼 |
| [Digital Human Blueprint](https://github.com/NVIDIA-AI-Blueprints/digital-human) | Tokkio 3D 디지털 휴먼 |
| [A2F Training Framework](https://github.com/NVIDIA/Audio2Face-3D-Training-Framework) | A2F 모델 훈련 |

### 합성 데이터 / 컴퓨터 비전

| 프로젝트 | 설명 |
| --------- | ------ |
| [UnrealCV](https://github.com/unrealcv/unrealcv) | UE + CV 연구 연결. PyTorch/TF 연동 |
| [NVIDIA NDDS](https://github.com/NVIDIA/Dataset_Synthesizer) | 합성 데이터 (세그멘테이션, 뎁스, 포즈) |

### Awesome 리스트

| 리스트 | URL |
| ------- | ----- |
| awesome-unreal (Coop56) | [Coop56/awesome-unreal](https://github.com/Coop56/awesome-unreal) |
| awesome-unreal (insthync) | [insthync/awesome-unreal](https://github.com/insthync/awesome-unreal) |
