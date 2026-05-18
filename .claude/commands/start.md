# 세션 시작 — 컨텍스트 빠른 복원

매 세션 첫 호출용. `/doctor` 보다 가벼운 daily-start. 5분 내 "어제까지 뭐 했지?" 답.

## 실행 순서

### 1단계: 환경 빠른 점검 (병렬)

병렬로 실행:
```bash
# Monolith 살아있나
curl -s -m 2 -o /dev/null -w "%{http_code}" http://localhost:9316/mcp

# UnrealClaude (보조)
curl -s -m 2 -o /dev/null -w "%{http_code}" http://localhost:3000/mcp/status

# Git 상태
git fetch --quiet origin 2>&1
git log HEAD..origin/master --oneline 2>&1 | head -10
git status --short
```

응답 표 한 줄로:
```
Monolith  : ✅ (또는 ❌ /recover 안내)
UnrealClaude: ✅ / ❌
Git       : clean / N커밋 dirty / origin 대비 N커밋 뒤
```

### 2단계: 어제까지의 작업 컨텍스트

순서대로 보고 (간략):

1. **마지막 Briefing 확인**:
   ```bash
   ls -t Briefing/*.md 2>&1 | head -3
   ```
   가장 최근 1건 제목 + 한 줄 요약. `_tmp/` 는 제외.

2. **최근 커밋 5건**:
   ```bash
   git log --oneline -5
   ```

3. **현재 최종 작업 상태** (메모리에서):
   ```
   MEMORY.md → "PC_01 (상세는 sub-index)" 줄의 "현재 최종" 부분 + 다음 작업
   MEMORY_PC01.md → "⭐ 현재 최종 상태" 섹션 첫 줄
   ```

### 3단계: 신규 액션 / 새 메모리 감지

1. **Monolith 카탈로그 변동**:
   ```bash
   py scripts/save_discover_snapshot.py 2>&1 | head -5
   ls -t .claude/state/catalog_history/ | head -2
   ```
   가장 최근 2 스냅샷 비교 → 신규 액션 있으면 enumerate.

2. **새 메모리 (지난 7일)**:
   ```bash
   find ~/.claude/projects/C--Dev-Sanjuk-Unreal/memory -name "*.md" -mtime -7 2>&1 | head -10
   ```
   ~7일 안에 추가/변경된 메모리 파일명만 표시.

### 4단계: 오늘 작업 제안

위 결과 종합:
- 어제 마지막 작업 (Briefing + 메모리 + 최종 커밋) → 자연스러운 다음 step
- pending 작업 (`/doctor` 의 Task 7단계 보다 가벼움)
- 보류 작업 알림 (예: [[project-sb2-internal-mcp-pending]], [[feedback-sb2-python-plugin-disabled]])

## 출력 형식 (예)

```
[start] 환경 점검 ✅✅ / Git clean / origin 대비 동일

마지막 작업:
  - 2026-05-16 (Briefing): SB2 업무 플랫폼 3-Track 비전
  - 최종 메모리: pc01-session-end-2026-05-15 — smooth chain만 살아있음
  - 다음 step: IsTransition 정의

카탈로그 변동:
  - Monolith 893 → 895 (+2): graymap_validate_door_clearance, graymap_validate_traversal

새 메모리 (지난 7일):
  - reference_animation_query_sm_dump.md (5/18)
  - reference_animgraph_node_editing.md (5/18)
  - reference_sb2_internal_mcps.md (5/18)
  - ...

보류:
  - 사내 MCP 3종 등록 (P4 sync 필요)
  - PythonScriptPlugin 활성화 (.uproject 잠금)

오늘 시작 추천:
  1. IsTransition gate 작업 (다음주 계획 시작)
  2. PythonScriptPlugin 활성화 → Chooser/SM/Enum 우회 PoC 재개
```

## 사용 시점

- 매일 첫 세션
- 휴식 후 작업 복귀
- 큰 변동 (P4 sync / 엔진팀 빌드 통보 / 사내 MCP 등록) 후 첫 호출
- `/doctor` 의 7단계 전체 검사는 부담스러울 때
