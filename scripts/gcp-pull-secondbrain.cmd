@echo off
REM GCP AI Context Hub -> 회사 로컬 미러(C:\dev\Hermes-SecondBrain) pull
REM 옵션 그대로 전달: gcp-pull-secondbrain.cmd -Mirror  /  -DryRun
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0gcp-pull-secondbrain.ps1" %*
