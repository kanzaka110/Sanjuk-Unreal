---
name: SB2 프로젝트 경로 및 엔진 구성
description: SB2 프로젝트의 실제 경로, 엔진 정보, Monolith 설치 상태
type: project
originSessionId: e6d479b5-60ae-4f17-9866-6f6bdbc6b8cd
---
SB2 프로젝트 실제 경로: `E:\Perforce\SB2\Workspace\Internal\SB2\SB2.uproject`
엔진 경로: `E:\Perforce\SB2\Workspace\Internal\Engine\` (바이너리 배포, Engine/Source 없음)
빌드 버전: `SBBuild.ver` → `0.0.0.3501` (SB2 커스텀 빌드 UE 5.7.4)

**Monolith 상태 (2026-04-16 확인):**
- `E:\Perforce\SB2\Workspace\Internal\SB2\Plugins\Monolith\` 존재
- 버전: **0.12.1** (엔진팀 공식 통합 완료)
- 포트 9316 정상 바인딩 확인 (초기 인덱싱 후 응답 가능)
- 주의: per-user setting으로 비활성화될 수 있음 — 로그에서 "Disabled by per-user setting" 확인

**주요 플러그인:**
- UnrealMCP, UnrealClaude (MCP 연동용)
- UAF 계열 (UAFWarping, UAFStateTree, UAFPoseSearch 등) — 애니메이션 프레임워크
- MetaHuman, MetaHumanCharacter, MetaHumanCharacterUAF
- MassAI, MassCrowd, MassGameplay — 군중 AI
- NextPCG 계열 — 절차적 컨텐츠 생성
- Copilot 계열 (EditorUtilityCopilot, EverythingCopilot 등) — **현재 비활성화**
- DLSS, Streamline (NVIDIA 업스케일링/프레임생성)
- FSR3 — **현재 비활성화**

**Why:** 2026-04-15 엔진팀 Monolith 공식 통합, 2026-04-16 P4 sync 후 확인 완료.

**How to apply:**
- 프로젝트 경로는 **E 드라이브** 기준 사용 (2026-04-16 D→E 변경)
- Monolith 관련 작업 시 `E:\...\Plugins\Monolith\` 경로 사용
- Copilot 플러그인들은 uproject에서 비활성화 상태임을 인지
- ProjectIndex.db 깨짐 시 삭제 후 재시작 (자동 재생성)
