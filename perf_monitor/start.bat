@echo off
REM PerfMonitor 런처 — 서버가 안 떠 있으면 띄우고, 브라우저로 대시보드를 연다.
REM 더블클릭 / 에디터 Launch URL / 작업표시줄 고정 등 어디서 호출해도 동작.
setlocal
set "ROOT=C:\Dev\Sanjuk-Unreal"
set "PORT=8077"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$busy = Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue;" ^
  "if (-not $busy) { Start-Process -WindowStyle Hidden -FilePath 'py' -ArgumentList @('%ROOT%\perf_monitor\server.py','--start') -WorkingDirectory '%ROOT%'; Start-Sleep -Seconds 2 };" ^
  "Start-Process 'http://localhost:%PORT%'"

endlocal
