# 03. UE5 에디터 설정

> runreal이 UE5 에디터에 연결하려면 **Python Editor Script Plugin**과 **Remote Execution**이 활성화되어 있어야 합니다.

## Step 1: Python Editor Script Plugin 활성화

1. UE5 에디터를 엽니다
2. 상단 메뉴: `Edit` > `Plugins`
3. 검색창에 **"Python"** 입력
4. **"Python Editor Script Plugin"** 을 찾아 **Enabled** 체크
5. **에디터 재시작** 필요

```
Edit > Plugins
  └─ 검색: "Python"
      └─ ☑ Python Editor Script Plugin  ← 이것을 활성화
```

### 추가 권장 플러그인

| 플러그인 | 필수 여부 | 용도 |
|---------|:--------:|------|
| Python Editor Script Plugin | **필수** | Python 스크립팅 + Remote Execution |
| Editor Scripting Utilities | 권장 | 에디터 자동화 유틸리티 확장 |
| Sequencer Scripting | 선택 | 시퀀서 Python API (시네마틱 작업용) |

## Step 2: Remote Execution 활성화

1. 상단 메뉴: `Edit` > `Project Settings`
2. 왼쪽 패널에서 **"Python"** 검색 또는 `Plugins` > `Python` 찾기
3. **"Enable Remote Execution"** 체크

```
Edit > Project Settings
  └─ Plugins
      └─ Python
          ├─ ☑ Enable Remote Execution     ← 핵심! 반드시 체크
          ├─ Multicast Group Endpoint: 239.0.0.1:6766  (기본값 유지)
          ├─ Multicast Bind Address: 0.0.0.0           (기본값 유지)
          ├─ Multicast TTL: 0                          (기본값 유지)
          └─ ☑ Listen on Launch: True                  (기본값 유지)
```

## Step 3: 설정값 상세 설명

| 설정 | 기본값 | 설명 | 변경 필요? |
|------|--------|------|:---------:|
| Enable Remote Execution | False | Python 원격 실행 허용 | **반드시 True** |
| Multicast Group Endpoint | 239.0.0.1:6766 | UDP 디스커버리 주소 | 보통 안 건드림 |
| Multicast Bind Address | 0.0.0.0 | 수신 바인드 주소 | 보통 안 건드림 |
| Multicast TTL | 0 | 0 = localhost만 | 보통 안 건드림 |
| Command Endpoint | 127.0.0.1:6776 | TCP 명령 실행 포트 | 보통 안 건드림 |
| Listen on Launch | True | 에디터 시작 시 자동 리슨 | True 유지 |

### 여러 에디터 인스턴스를 동시에 쓸 때

두 번째 에디터는 포트 충돌이 나므로 Command Endpoint를 변경해야 합니다:
- 첫 번째 에디터: `127.0.0.1:6776` (기본)
- 두 번째 에디터: `127.0.0.1:6777`

## Step 4: DefaultEngine.ini로 설정 (선택)

에디터 UI 대신 ini 파일로 설정할 수도 있습니다:

```ini
; {프로젝트}/Config/DefaultEngine.ini에 추가
[/Script/PythonScriptPlugin.PythonScriptPluginSettings]
bRemoteExecution=True
RemoteExecutionMulticastGroupEndpoint=(Address="239.0.0.1",Port=6766)
RemoteExecutionMulticastBindAddress=0.0.0.0
RemoteExecutionMulticastTTL=0
bRemoteExecutionListenOnLaunch=True
```

> **P4 주의**: 이 설정이 DefaultEngine.ini에 들어가면 P4에 올라갑니다. 하지만 이것은 에디터 설정일 뿐이고 빌드/런타임에 영향 없으므로 보통 문제없습니다. 팀원에게도 유용할 수 있습니다.

## Step 5: 설정 확인

UE5 에디터의 **Output Log** (Window > Developer Tools > Output Log)에서:

```
LogPython: Remote Execution Multicast Started (listening on 239.0.0.1:6766)
```

이 메시지가 보이면 Remote Execution이 정상 동작 중입니다.

### Python 콘솔에서 테스트

UE5 에디터 하단의 **Python 콘솔** (또는 `Window` > `Developer Tools` > `Output Log`에서 드롭다운을 `Python`으로 변경):

```python
import unreal
print(unreal.SystemLibrary.get_engine_version())
```

엔진 버전이 출력되면 Python 환경이 정상입니다.

## 다음 단계

에디터 설정이 끝났으면 [04. Claude Code 연결](04-Connect-Claude-Code.md)로 이동하세요.
