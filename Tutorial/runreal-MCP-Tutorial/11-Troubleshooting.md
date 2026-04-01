# 11. 트러블슈팅

> 자주 겪는 문제와 해결 방법

## 연결 문제

### "Connection attempt failed: Timed out"

**원인**: MCP 서버가 UE 에디터를 찾지 못함

**체크리스트**:
1. UE 에디터가 실행 중인가? (MCP 서버보다 먼저 켜야 함)
2. Python Editor Script Plugin이 활성화되어 있는가?
3. Project Settings > Python > Enable Remote Execution이 체크되어 있는가?
4. 방화벽이 UDP 6766 / TCP 6776을 차단하고 있지 않은가?

**해결 순서**:
```
1. UE 에디터 완전 종료
2. UE 에디터 재시작
3. Output Log에서 "Remote Execution Multicast Started" 확인
4. Claude Code 재시작 (MCP 서버 재시작)
```

### "Unexpected token 'C', Connection..."

**원인**: MCP 프로토콜 파싱 에러

**해결**:
1. UE 에디터 완전 재시작
2. Claude Code / Cursor 완전 종료 후 재시작
3. 좀비 Node.js 프로세스 확인 및 종료:

```bash
# Windows
tasklist | findstr node
taskkill /F /IM node.exe   # 주의: 모든 node 프로세스 종료

# 특정 프로세스만 종료
taskkill /F /PID {프로세스ID}
```

### 연결은 되는데 명령이 안 먹힘

**확인**:
1. UE 에디터가 모달 다이얼로그(팝업)를 표시하고 있지 않은지 확인
2. 에디터가 컴파일/로딩 중이 아닌지 확인 (Game Thread 블로킹)
3. Python 콘솔에서 직접 `print("test")` 실행 테스트

---

## Python 실행 문제

### "SyntaxError" 또는 예상치 못한 에러

**가장 흔한 원인: 주석**

```python
# 이렇게 하면 에러!
import unreal
# This is a comment  ← 이것 때문에 실패
print(unreal.SystemLibrary.get_engine_version())
```

```python
import unreal
print(unreal.SystemLibrary.get_engine_version())
```

runreal의 Remote Execution 프로토콜은 **주석을 지원하지 않습니다**.

### "ModuleNotFoundError: No module named 'unreal'"

**원인**: UE 에디터 외부에서 Python을 실행하려 함

`editor_run_python`은 UE 에디터 **내부**의 Python 인터프리터에서 실행됩니다. `unreal` 모듈은 에디터 내부에서만 사용 가능합니다.

### "AttributeError: module 'unreal' has no attribute..."

**원인**: 해당 API가 현재 UE 버전에서 지원되지 않음

```python
import unreal
print(dir(unreal))
```

사용 가능한 모든 클래스/함수 목록을 확인하세요. UE 버전에 따라 API가 다릅니다.

### 대용량 결과 반환 시 잘림

**원인**: TCP 버퍼 크기 제한

**해결**: 결과를 페이지네이션하세요:

```python
import unreal
import json

all_assets = unreal.EditorAssetLibrary.list_assets('/Game/', recursive=True)
page = all_assets[:50]
print(json.dumps([str(a) for a in page]))
```

---

## 스크린샷 문제

### 스크린샷이 검은색/빈 이미지

**원인**: UE 에디터 윈도우가 포커스(활성화) 상태가 아님

**해결**: 스크린샷 촬영 전에 UE 에디터를 클릭하여 포커스를 줘야 합니다. 3초 대기 후 캡처합니다.

### 스크린샷 해상도가 낮음

현재 640x520으로 고정되어 있습니다. runreal 코드 내 하드코딩이므로 변경 불가.

고해상도 스크린샷이 필요하면 `editor_run_python`으로:

```python
import unreal
unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, '/Game/Screenshots/test.png')
```

---

## 설정 문제

### 여러 UE 에디터가 열려 있을 때

runreal은 **첫 번째 발견된 에디터**에 자동 연결합니다. 특정 에디터에 연결하고 싶으면:

1. 다른 에디터의 Remote Execution을 비활성화
2. 또는 포트를 다르게 설정

### npm 설치 에러

```bash
# 캐시 정리 후 재시도
npm cache clean --force
npm install -g @runreal/unreal-mcp

# 권한 문제 (Windows)
# PowerShell을 관리자 권한으로 실행
```

### npx가 오래된 버전을 사용

```bash
# npx 캐시 정리
npx clear-npx-cache

# 또는 글로벌 설치로 전환
npm install -g @runreal/unreal-mcp
```

---

## 성능 문제

### 에디터가 멈춤 (프리즈)

**원인**: Python 코드가 Game Thread에서 동기 실행되어 긴 작업이 에디터를 블로킹

**해결**: 대량 작업에 `ScopedSlowTask` 사용:

```python
import unreal

items = list(range(1000))
with unreal.ScopedSlowTask(len(items), 'Processing...') as slow_task:
    slow_task.make_dialog(True)
    for i in items:
        if slow_task.should_cancel():
            break
        slow_task.enter_progress_frame(1)
        pass
```

### 응답이 느림

- 에셋이 많은 프로젝트에서 `list_assets`는 느릴 수 있음
- `recursive=True`를 `False`로 변경하거나 경로를 좁히세요
- 검색 결과에 `[:50]` 등 제한을 추가하세요

---

## 빠른 진단 명령

Claude에게 이렇게 요청하세요:

```
"UE 프로젝트 정보를 알려줘"
→ 연결 테스트 + 기본 정보 확인

"간단한 Python 테스트를 실행해줘: 엔진 버전 출력"
→ editor_run_python 동작 확인

"현재 맵 정보를 알려줘"
→ 에디터 상태 확인
```

## 다음 단계

[12. 참고자료](12-References.md)로 이동하세요.
