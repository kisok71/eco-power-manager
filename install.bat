@echo off
chcp 65001 >nul
title 탄소중립 PC 전원 관리자 Pro 설치 및 자동 실행 등록

echo ================================================================
echo   🌿 [경기남부경찰청] 탄소중립 PC 전원 관리자 Pro 자동 설치기
echo ================================================================
echo.

set "INSTALL_DIR=%LOCALAPPDATA%\EcoPowerManager"
set "EXE_NAME=EcoPowerManagerPro.exe"
set "SRC_EXE=%~dp0%EXE_NAME%"
if not exist "%SRC_EXE%" (
    set "SRC_EXE=%~dp0web\downloads\%EXE_NAME%"
)
if not exist "%SRC_EXE%" (
    set "SRC_EXE=%~dp0dist\%EXE_NAME%"
)

if not exist "%SRC_EXE%" (
    echo [오류] %EXE_NAME% 파일을 찾을 수 없습니다.
    echo 실행 파일과 같은 폴더에 install.bat을 두고 실행해 주세요.
    echo.
    pause
    exit /b 1
)

echo [1/4] 실행 중인 기존 프로세스 정리 중...
taskkill /f /im %EXE_NAME% >nul 2>&1

echo [2/4] 프로그램 설치 폴더 구성 중 (%INSTALL_DIR%)...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
copy /y "%SRC_EXE%" "%INSTALL_DIR%\%EXE_NAME%" >nul

echo [3/4] Windows 부팅 시 자동 실행 등록 중...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "EcoPowerManagerPro" /t REG_SZ /d "\"%INSTALL_DIR%\%EXE_NAME%\"" /f >nul

echo [4/4] 바로가기 아이콘 생성 및 프로그램 실행 중...
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\탄소중립 PC 관리자.lnk'); $s.TargetPath = '%INSTALL_DIR%\%EXE_NAME%'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Save()" >nul 2>&1

start "" "%INSTALL_DIR%\%EXE_NAME%"

echo.
echo ================================================================
echo   ✅ 설치 및 Windows 부팅 시 자동 실행 등록이 완료되었습니다!
echo.
echo   - 설치 위치 : %INSTALL_DIR%
echo   - 바탕화면 바로가기 생성 완료
echo   - 시스템 트레이(우측 하단)에서 자동 관리가 시작됩니다.
echo ================================================================
echo.
timeout /t 5 >nul
exit /b 0