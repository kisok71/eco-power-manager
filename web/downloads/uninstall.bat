@echo off
chcp 65001 >nul
title 탄소중립 PC 전원 관리자 Pro 삭제

echo ================================================================
echo   🗑️ 탄소중립 PC 전원 관리자 Pro 삭제 (제거)
echo ================================================================
echo.

set "INSTALL_DIR=%LOCALAPPDATA%\EcoPowerManager"
set "EXE_NAME=EcoPowerManagerPro.exe"

echo [1/3] 프로그램 프로세스 종료 중...
taskkill /f /im %EXE_NAME% >nul 2>&1

echo [2/3] 자동 실행 레지스트리 및 바로가기 삭제 중...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "EcoPowerManagerPro" /f >nul 2>&1
del /f /q "%USERPROFILE%\Desktop\탄소중립 PC 관리자.lnk" >nul 2>&1

echo [3/3] 프로그램 파일 삭제 중...
if exist "%INSTALL_DIR%" rmdir /s /q "%INSTALL_DIR%" >nul 2>&1

echo.
echo ================================================================
echo   ✅ 프로그램 및 자동 실행 등록이 완전히 제거되었습니다.
echo ================================================================
echo.
timeout /t 3 >nul
exit /b 0
