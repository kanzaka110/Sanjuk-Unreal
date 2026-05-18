---
name: 메모리는 kanzaka110@gmail.com 계정에서도 접근 가능해야 함
description: 로컬 SHIFTUP 계정에 저장하는 메모리/정보를 kanzaka110@gmail.com 환경에서도 확인 가능하도록 동기화 필요
type: feedback
originSessionId: 000356af-f6ab-4220-891c-ca3825b31e2a
---
내가 저장하는 메모리/정보 파일은 kanzaka110@gmail.com 계정(claude.ai/code 웹 또는 다른 환경)에서도 확인 가능해야 한다.

**Why:** 사용자가 여러 환경(로컬 SHIFTUP PC, GCP VM, 모바일 claude.ai/code 웹)에서 작업하므로 메모리가 한 환경에 갇히면 안 됨. 2026-04-27 명시 요청.

**How to apply:**
- 로컬 메모리 경로: `C:\Users\SHIFTUP\.claude\projects\C--Dev-Sanjuk-Unreal\memory\`
- 이 경로는 SHIFTUP Windows 계정 로컬 → 다른 환경에서 직접 접근 불가
- **동기화 옵션 (사용자 환경에 맞춰 택1 또는 조합)**:
  1. **Sanjuk-Unreal 레포에 커밋**: 메모리 디렉터리를 레포 하위로 이동/심볼릭 링크 후 git push → 다른 환경에서 pull
  2. **Google Drive 동기화**: kanzaka110@gmail.com Drive에 메모리 폴더 미러링
  3. **GCP VM 동기화**: `scripts/gcp-restart-remote.sh` 류로 VM에 메모리 동기화
- 새 메모리 저장 시 사용자에게 동기화 여부/방식 확인하고, 정해진 방식으로 반영
- 현재 동기화 메커니즘이 미설정이면 사용자에게 어떤 방식을 원하는지 먼저 질문
