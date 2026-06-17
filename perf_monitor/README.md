# PerfMonitor — SB2 실시간 성능 대시보드

언리얼 에디터(PIE) 와 **별개의 브라우저 창**에서 프레임/GPU·애니메이션·물리·메모리
수치를 실시간 그래프로 본다. 같은 와이파이면 **모바일**에서도 접속 가능.

엔진 C++ 수정 0줄. 추가 pip 설치 0개 (Python 표준 라이브러리만 사용).
✅ SB2 5.7.4 + Monolith 라이브 환경 실측 검증 (2026-06-17).

## 데이터 경로 — 회전 캡처(rotating capture)

```
[server.py 수집 스레드]                              [브라우저 차트]
  start → 1s 캡처 → stop → 잠금풀린 .csv 마지막행 읽기 ──SSE──► localhost:8077
   ▲ Monolith editor.run_console_command (CsvProfile)    파일 삭제 → 반복
```

UE 는 CSV Profiler 캡처 중 .csv 를 **배타 잠금**(Windows `ERROR_SHARING_VIOLATION`)
하므로 캡처 파일을 tail 할 수 없다. 그래서 `start → 짧게 캡처 → stop → 잠금이 풀린
파일의 마지막 행을 읽고 → 파일 삭제` 사이클을 반복한다.

- **갱신 주기 ≈ 캡처창(1s) + 파이널라이즈(~2.2s) ≈ 3.5초.** (실측)
- 한 파일에서 4개 카테고리(프레임/GPU·애니·물리·메모리)를 모두 추출.
- 캡처 산출물은 매 사이클 자동 삭제(디스크 churn 0).

진짜 프레임 단위(sub-second) 가 필요하면 → **Phase 3**: SB2 에 작은
`UGameInstanceSubsystem` 을 넣어 매 프레임 JSON 을 localhost 로 POST (파일 잠금 무관, C++ 필요).

## 사용법

### 0. 사전 점검
```
py perf_monitor/server.py --probe     # csvprofile 가용성 + Monolith 연결 확인
```

### 1. 서버 기동 → 브라우저에서 시작
```
py perf_monitor/server.py             # 기동 후 대시보드 ▶ 버튼으로 모니터링 시작
py perf_monitor/server.py --start     # 기동 즉시 모니터링 시작
```
→ `http://localhost:8077` 접속. 모바일은 `http://<PC_IP>:8077`.
대시보드 **▶ 모니터링 시작 / ■ 정지** 로 캡처 루프를 켜고 끈다.

### 2. CSV 컬럼이 빌드별로 다를 때
SB2 표준 컬럼은 검증됨. 다른 빌드/버전에서 "미발견" 이 나오면 실제 헤더 확인:
```
py perf_monitor/server.py --start     # 캡처 한 번 돌려 파일 생성 (PERF_DELETE_CSV=0 권장)
py perf_monitor/list_columns.py       # 가장 최근 .csv 의 실제 헤더 + resolve 결과
```
출력된 실제 컬럼명을 `config.py` 의 해당 `Metric(..., candidates=(...))` 에 추가.

## 표시 메트릭 (✅ SB2 실측 컬럼)

| 그룹 | 메트릭 | CSV 컬럼 |
|------|--------|----------|
| 프레임/GPU | Frame / Game / Render / GPU / Draw Calls | `FrameTime` `GameThreadTime` `RenderThreadTime` `GPUTime` `RHI/DrawCalls` |
| 애니메이션 | Animation (GT) / SkelMesh 틱 | `Exclusive/GameThread/Animation` `Ticks/SBCharacterSkeletalMeshComponent` |
| 물리/시뮬 | Physics (GT) / Physics (Workers) / Cloth 틱 / Groom 틱 | `Exclusive/GameThread/Physics` `Exclusive/AllWorkers/Physics` `Ticks/SBChaosClothComponent` `Ticks/SBGroomComponent` |
| 메모리 | Physical Mem / GPU Mem | `PhysicalUsedMB` `GPUMem/LocalUsedMB` |

## 설정 (환경변수 override)

| 변수 | 기본값 | 용도 |
|------|--------|------|
| `SB2_PROJECT_ROOT` | `E:\Perforce\SB2\Workspace\Internal\SB2` | 프로젝트 루트 |
| `PERF_CSV_DIR` | `{root}/Saved/Profiling/CSV` | CSV 출력 폴더 직접 지정 |
| `PERF_PORT` | `8077` | 대시보드 포트 |
| `PERF_CAPTURE_WINDOW` | `1.0` | 캡처창(초). 길수록 평균 안정·갱신 느림 |
| `PERF_LOCK_TIMEOUT` | `6.0` | 파일 잠금 해제 대기 한도(초) |
| `PERF_DELETE_CSV` | `1` | 캡처 파일 자동 삭제(0=보존) |
| `PERF_AUTOSTART` | `0` | 기동 즉시 모니터링(1) |
| `PERF_HISTORY` | `120` | 스파크라인 보관 샘플 수 |
| `MONOLITH_ENDPOINT` | `http://localhost:9316/mcp` | Monolith RPC |

## 파일

| 파일 | 역할 |
|------|------|
| `config.py` | 설정 + 메트릭→CSV컬럼 매핑 정의 |
| `csv_source.py` | CSV 헤더 resolve · 잠금 대기 · 마지막 유효행 파싱 |
| `monolith_control.py` | Monolith 콘솔 명령으로 CsvProfile start/stop |
| `server.py` | SSE 웹서버 + 회전 캡처 수집 스레드 |
| `dashboard.html` | 브라우저 대시보드 (canvas 스파크라인, CDN 무의존) |
| `list_columns.py` | 실제 CSV 헤더 진단 |

## 한계 / 주의

- **캐처 중 에디터 부하**: 모니터링 ON 이면 매 ~3.5초마다 짧은 프로파일링이 돈다.
  미사용 시 ■ 로 정지. PIE 가 아닌 빈 에디터에서도 동작(에디터 프레임 수치).
- **갱신 주기 ~3.5초**: CSV Profiler 파이널라이즈 지연이 하한. 더 빠른 건 Phase 3 필요.
- **임계값**(warn/crit): Frame 16.6/33.3ms 는 60/30fps 기준. anim 3/6·physics 4/8ms 는
  보수적 추정(⚠ 미검증) — 프로젝트 예산에 맞게 `config.py` 조정.
- **Cloth/Groom 은 ms 가 아닌 틱 카운트**: SB2 CSV 에 cloth 전용 ms 컬럼이 없어 컴포넌트
  틱 수로 활동만 표시. 정밀 sim ms 는 Unreal Insights/Animation Insights 병행 권장.
