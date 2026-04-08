@echo off
REM 로컬 PC에서 Sanjuk-Unreal remote-control 시작
REM 시작프로그램에 바로가기 등록하면 PC 부팅 시 자동 실행

cd /d C:\dev\Sanjuk-Unreal
claude remote-control --name "Sanjuk-Unreal (Local)"
