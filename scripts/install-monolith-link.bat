@echo off
setlocal

set LINK_PATH=C:\Program Files\Epic Games\UE_5.7\Engine\Plugins\Marketplace\Monolith
set TARGET_PATH=C:\Dev\Sanjuk-Claude-Code\plugins\Monolith-v0.10.0

echo === Monolith 심볼릭 링크 설치 ===
echo Link:   %LINK_PATH%
echo Target: %TARGET_PATH%
echo.

if not exist "%TARGET_PATH%\Monolith.uplugin" (
    echo [ERROR] 플러그인 소스가 없습니다: %TARGET_PATH%
    pause
    exit /b 1
)

if not exist "C:\Program Files\Epic Games\UE_5.7\Engine\Plugins\Marketplace" (
    echo Marketplace 폴더 생성 중...
    mkdir "C:\Program Files\Epic Games\UE_5.7\Engine\Plugins\Marketplace"
)

if exist "%LINK_PATH%" (
    echo [경고] 링크/폴더가 이미 존재합니다. 제거 후 재생성합니다.
    rmdir "%LINK_PATH%" 2>nul
)

mklink /D "%LINK_PATH%" "%TARGET_PATH%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] 링크 생성 완료
    echo.
    dir "C:\Program Files\Epic Games\UE_5.7\Engine\Plugins\Marketplace\Monolith\Monolith.uplugin"
) else (
    echo.
    echo [FAIL] 링크 생성 실패. 관리자 권한으로 다시 실행해보세요.
)

pause
