@echo off
REM PerfMonitor 서버 전용 런처 — 외부 브라우저는 열지 않는다.
REM EUW 안 WebBrowser 위젯이 localhost:8077 을 직접 로드하는 임베드용.
setlocal
set "ROOT=C:\Dev\Sanjuk-Unreal"
set "PORT=8077"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$busy = Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue;" ^
  "if (-not $busy) { Start-Process -WindowStyle Hidden -FilePath 'py' -ArgumentList @('%ROOT%\perf_monitor\server.py','--start') -WorkingDirectory '%ROOT%' }"
endlocal
