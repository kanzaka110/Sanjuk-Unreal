# UE 크래시 / 빌드 실패 진단

UE5 에디터 크래시, 빌드 실패, 패키징 오류를 단계별로 진단하는 명령어.

## 입력

사용자가 제공하는 정보:
- 오류 메시지 또는 크래시 로그 (텍스트 / 스크린샷)
- 발생 시점 (에디터 시작, 빌드, PIE, 패키징 등)

## 진단 순서

### 1단계: 로그 수집

```bash
# 최근 UE 로그 확인 (MonolithTest 기준)
ls -lt "C:/Users/ohmil/OneDrive/문서/Unreal Projects/MonolithTest/Saved/Logs/" | head -5

# 최근 크래시 리포트 확인
ls -lt "C:/Users/ohmil/OneDrive/문서/Unreal Projects/MonolithTest/Saved/Crashes/" 2>/dev/null | head -5
```

### 2단계: 오류 패턴 분류

| 패턴 | 분류 | 1차 조치 |
|------|------|---------|
| `LNK2019` / `LNK2001` | 링커 에러 | 모듈 의존성 (.Build.cs) 확인 |
| `C2065` / `C2039` | 컴파일 에러 | include 누락, API 변경 확인 |
| `Assertion failed` | 런타임 에셋 | 에셋 경로/타입 확인 |
| `Access violation` | 널 포인터 | 콜스택에서 원인 함수 추적 |
| `Out of memory` | 메모리 | 에셋 최적화, LOD 확인 |
| `Shader compile` | 셰이더 | DDC 삭제 후 재빌드 |
| `Plugin failed to load` | 플러그인 | 버전 호환성, 바이너리 확인 |

### 3단계: 자동 조치 시도

1. **DDC 삭제** (셰이더/에셋 캐시 문제 시):
   ```bash
   rm -rf "C:/Users/ohmil/OneDrive/문서/Unreal Projects/MonolithTest/DerivedDataCache"
   rm -rf "C:/Users/ohmil/OneDrive/문서/Unreal Projects/MonolithTest/Intermediate"
   ```

2. **Monolith 플러그인 상태 확인**:
   ```bash
   ls "C:/Users/ohmil/OneDrive/문서/Unreal Projects/MonolithTest/Plugins/Monolith/Binaries/Win64/"
   ```

3. **.Build.cs 모듈 검사** (링커 에러 시):
   해당 모듈의 Build.cs 읽고 누락된 의존성 제안

### 4단계: 진단 리포트

| 항목 | 결과 |
|------|------|
| 오류 분류 | (패턴) |
| 원인 추정 | (설명) |
| 권장 조치 | (단계별) |
| 관련 파일 | (경로) |

위험한 조치 (파일 삭제, 설정 변경)는 반드시 사용자 확인 후 실행.
