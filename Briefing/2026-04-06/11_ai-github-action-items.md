# GitHub + AI 프로젝트 — TA 액션 아이템

> 2026-04-06 브리핑 | [목차로 돌아가기](00_INDEX.md)

---

## 즉시 활용 가능 (현재 워크플로우 확장)

| 우선순위 | 프로젝트 | 왜 지금? |
|---------|---------|---------|
| 1 | [NVIDIA Audio2Face-3D](https://github.com/NVIDIA/Audio2Face-3D) | MetaHuman 실시간 AI 립싱크, UE5 BP 노드로 바로 연동 |
| 2 | [MediaPipe4U](https://github.com/endink/Mediapipe4u-plugin) | 웹캠 바디+페이셜 모캡, 오프라인/저지연, 장비 불필요 |
| 3 | [Flopperam UE MCP](https://github.com/flopperam/unreal-engine-mcp) | 679+ Stars, Monolith 보완 (레벨 빌딩/BP 자율 에이전트) |
| 4 | [ue-llm-toolkit](https://github.com/ColtonWilley/ue-llm-toolkit) | C++ 네이티브 37 도구, Monolith 대안/보완 검토 |
| 5 | [UnrealClaude](https://github.com/Natfii/UnrealClaude) | Claude Code를 UE 에디터 내에서 바로 사용 |

---

## 중기 검토 (이번 분기)

| 프로젝트 | 용도 |
|---------|------|
| [AMD Schola v2](https://github.com/GPUOpen-LibrariesAndSDKs/Schola) | NPC 애니메이션 행동 RL 훈련 + ONNX 추론 |
| [BEDLAM 2 Retargeting](https://github.com/PerceivingSystems/bedlam2_retargeting) | SMPL-X 대량 모캡 → UE IK Retargeter |
| [Autonomix](https://github.com/PRQELT/Autonomix) | BP/레벨/머티리얼 자율 AI 생성 |
| [LLM-Connect](https://github.com/yigit-altun-rootrootq/LLM-Connect) | BP 전용 LLM 통합 (코딩 불필요) |
| [GASPALS](https://github.com/PolygonHive/GASPALS) | GASP + ALS 레이어링 레퍼런스 |
| [Convai UE SDK](https://github.com/Conv-AI/Convai-UnrealEngine-SDK) | 대화형 AI NPC 종합 솔루션 |

---

## 장기 모니터링

| 프로젝트 | 이유 |
|---------|------|
| [UnrealZoo-Gym](https://github.com/UnrealZoo/unrealzoo-gym) | ICCV 2025, 100+ 씬 Embodied AI (UE 5.5) |
| [NVIDIA NVIGI](https://github.com/NVIDIA-RTX/NVIGI) | 인게임 AI 추론 SDK, 차세대 NPC |
| Epic NNE / Learning Agents | 공식 엔진 내장 AI, AnimNext 통합 방향 |
| [AI4Animation](https://github.com/sebastianstarke/AI4Animation) | 딥러닝 모션 합성 학술 연구 (Unity) |
| Aura (Ramen) | 상용 에디터 AI, 애니메이션/리깅 에이전트 |

---

## MCP 서버 확장 검토

현재 조합: **Monolith + runreal + ChiR24**

추가 검토 대상:

```
현재:  Monolith (애니메이션 메인)
       + runreal (Python 확장)
       + ChiR24 (Chaos Cloth)

검토:  + Flopperam (레벨/BP 자율 에이전트, 679+ Stars)
       + ue-llm-toolkit (C++ 네이티브 대안)
       + remiphilippe/mcp-unreal (Go, 헤드리스 빌드/테스트)
```

---

## 체크리스트

### 이번 주
- [ ] NVIDIA Audio2Face-3D UE5 플러그인 설치 및 MetaHuman 연동 테스트
- [ ] MediaPipe4U 웹캠 모캡 워크플로 검증
- [ ] Flopperam UE MCP 설치 후 Monolith와 병행 테스트

### 이번 달
- [ ] UnrealClaude 설치 → 에디터 내 Claude Code 활용
- [ ] ue-llm-toolkit C++ 도구 Monolith 대비 기능 비교
- [ ] AMD Schola v2 RL 훈련 파이프라인 프로토타이핑
- [ ] GASPALS 레퍼런스 분석 (Motion Matching + ALS)

### 이번 분기
- [ ] BEDLAM 2 리타게팅 파이프라인 구축 (대량 모션 데이터)
- [ ] Convai SDK NPC 대화+애니메이션 통합 PoC
- [ ] Autonomix 자율 에이전트 레벨 빌딩 실험
