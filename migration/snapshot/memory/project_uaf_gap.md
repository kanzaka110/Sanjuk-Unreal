---
name: UAF MCP 지원 부재
description: Monolith v0.12.0에서도 UAF 에셋 제어 미지원, runreal로 커스텀 스크립트 필요
type: project
---

UAF(Universal Animation Framework)는 Monolith v0.12.0 (1,125 액션)에서도 지원하지 않음.
Monolith 애니메이션 모듈(115 액션)은 AnimSequence, Montage, BlendSpace, ABP, PoseSearch, IKRig, Control Rig만 커버.

**Why:** UAF는 UE5에서도 실험적/초기 단계이고, Monolith 개발자도 지원 계획 미언급.

**How to apply:** UAF 에셋 AI 제어가 필요하면 runreal MCP + 커스텀 Python 스크립트로 접근. UAF-Setup-Guide 참고.
