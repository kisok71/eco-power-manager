import os

install_bat_content = """@echo off
setlocal enabledelayedexpansion
chcp 949 >nul

echo ================================================================
echo   [경기남부경찰청] 탄소중립 PC 전원 관리자 Pro 자동 설치기
echo ================================================================
echo.

set "INSTALL_DIR=%LOCALAPPDATA%\\EcoPowerManager"
set "EXE_NAME=EcoPowerManagerPro.exe"

set "SRC_EXE=%~dp0%EXE_NAME%"
if exist "%SRC_EXE%" goto FOUND
set "SRC_EXE=%~dp0web\\downloads\\%EXE_NAME%"
if exist "%SRC_EXE%" goto FOUND
set "SRC_EXE=%~dp0dist\\%EXE_NAME%"
if exist "%SRC_EXE%" goto FOUND

echo [오류] %EXE_NAME% 실행 파일을 찾을 수 없습니다.
echo 실행 파일과 같은 폴더에 install.bat을 두고 실행해 주세요.
echo.
pause
exit /b 1

:FOUND
echo [1/4] 실행 중인 기존 프로그램 정리 중...
taskkill /f /im %EXE_NAME% >nul 2>&1

echo [2/4] 프로그램 설치 폴더로 복사 중... (%INSTALL_DIR%)
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
copy /y "%SRC_EXE%" "%INSTALL_DIR%\\%EXE_NAME%" >nul
if errorlevel 1 (
    echo [오류] 파일 복사에 실패했습니다.
    pause
    exit /b 1
)

echo [3/4] Windows 시작 시 자동 실행 등록 중...
reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "EcoPowerManagerPro" /t REG_SZ /d "\"%INSTALL_DIR%\\%EXE_NAME%\"" /f >nul

echo [4/4] 바탕화면 바로가기 생성 및 프로그램 실행 중...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $desktop = [Environment]::GetFolderPath('Desktop'); $shortcut = $ws.CreateShortcut($desktop + '\\탄소중립 PC 관리자.lnk'); $shortcut.TargetPath = '%INSTALL_DIR%\\%EXE_NAME%'; $shortcut.WorkingDirectory = '%INSTALL_DIR%'; $shortcut.Save(); Start-Process '%INSTALL_DIR%\\%EXE_NAME%' -WorkingDirectory '%INSTALL_DIR%'" >nul 2>&1

echo.
echo ================================================================
echo   [성공] 설치 및 자동 실행 등록이 완료되었습니다!
echo.
echo   - 설치 경로 : %INSTALL_DIR%
echo   - 바탕화면 바로가기 : 탄소중립 PC 관리자
echo   - 작업표시줄(우측 하단) 시스템 트레이에서 동작을 시작합니다.
echo ================================================================
echo.
ping -n 3 127.0.0.1 >nul
exit /b 0
"""

uninstall_bat_content = """@echo off
setlocal
chcp 949 >nul

echo ================================================================
echo   [경기남부경찰청] 탄소중립 PC 전원 관리자 Pro 삭제 (제거)
echo ================================================================
echo.

set "INSTALL_DIR=%LOCALAPPDATA%\\EcoPowerManager"
set "EXE_NAME=EcoPowerManagerPro.exe"

echo [1/3] 프로그램 프로세스 종료 중...
taskkill /f /im %EXE_NAME% >nul 2>&1

echo [2/3] 자동 실행 레지스트리 및 바로가기 삭제 중...
reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "EcoPowerManagerPro" /f >nul 2>&1
del /f /q "%USERPROFILE%\\Desktop\\탄소중립 PC 관리자.lnk" >nul 2>&1

echo [3/3] 프로그램 파일 삭제 중...
if exist "%INSTALL_DIR%" rmdir /s /q "%INSTALL_DIR%" >nul 2>&1

echo.
echo ================================================================
echo   [성공] 프로그램 및 자동 실행 등록이 완전히 제거되었습니다.
echo ================================================================
echo.
ping -n 3 127.0.0.1 >nul
exit /b 0
"""

with open('install.bat', 'w', encoding='cp949', newline='\r\n') as f:
    f.write(install_bat_content)

with open('uninstall.bat', 'w', encoding='cp949', newline='\r\n') as f:
    f.write(uninstall_bat_content)

print("Batch files generated in CP949 successfully!")
