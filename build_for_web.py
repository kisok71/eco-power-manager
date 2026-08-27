"""
탄소중립 PC 전원 관리자 Pro - 원클릭 EXE 빌드, ZIP 패키징 및 웹 배포 도구
"""

import os
import sys
import subprocess
import shutil
import zipfile
import http.server
import socketserver
import webbrowser

# 콘솔 출력 인코딩 UTF-8 대응
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")
DOWNLOADS_DIR = os.path.join(WEB_DIR, "downloads")
DIST_DIR = os.path.join(BASE_DIR, "dist")
VERSION = "2.2.0"

def build_exe():
    print("=" * 65)
    print(" [1/3] PyInstaller를 사용하여 단일 실행 파일(.exe) 빌드 시작")
    print("=" * 65)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",
        "--onefile",
        "--name", "EcoPowerManagerPro",
        "--clean",
        "eco_power_manager.py"
    ]

    try:
        subprocess.run(cmd, cwd=BASE_DIR, check=True)
        print("\n[OK] EXE 파일 빌드 완료!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[FAIL] 빌드 실패: {e}")
        return False

def package_for_web():
    print("\n" + "=" * 65)
    print(" [2/3] 웹 배포 폴더(web/downloads/)로 파일 복사 및 ZIP 압축")
    print("=" * 65)

    try:
        import generate_bat_files
        generate_bat_files.generate()
    except Exception as e:
        print(f"[WARN] 배치 파일 생성 중 예외 발생: {e}")

    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    built_exe = os.path.join(DIST_DIR, "EcoPowerManagerPro.exe")
    target_exe = os.path.join(DOWNLOADS_DIR, "EcoPowerManagerPro.exe")
    install_bat = os.path.join(BASE_DIR, "install.bat")
    uninstall_bat = os.path.join(BASE_DIR, "uninstall.bat")

    if not os.path.exists(built_exe):
        print(f"[FAIL] 빌드된 파일을 찾을 수 없습니다: {built_exe}")
        return False

    # 1. EXE 복사
    shutil.copy2(built_exe, target_exe)
    file_size_mb = os.path.getsize(target_exe) / (1024 * 1024)
    print(f"[OK] 실행 파일 복사: {target_exe} ({file_size_mb:.2f} MB)")

    # 2. 배치 파일 복사
    if os.path.exists(install_bat):
        shutil.copy2(install_bat, os.path.join(DOWNLOADS_DIR, "install.bat"))
    if os.path.exists(uninstall_bat):
        shutil.copy2(uninstall_bat, os.path.join(DOWNLOADS_DIR, "uninstall.bat"))

    # 3. 통합 ZIP 압축 패키지 생성
    zip_name = f"EcoPowerManagerPro_v{VERSION}_Installer.zip"
    zip_path = os.path.join(DOWNLOADS_DIR, zip_name)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(target_exe, "EcoPowerManagerPro.exe")
        if os.path.exists(install_bat):
            zf.write(install_bat, "install.bat")
        if os.path.exists(uninstall_bat):
            zf.write(uninstall_bat, "uninstall.bat")

    zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"[OK] 통합 자동설치 ZIP 생성: {zip_path} ({zip_size_mb:.2f} MB)")

    return True

def start_local_preview(port=8080):
    print("\n" + "=" * 65)
    print(f" [3/3] 로컬 웹 배포 서버 시작 (http://localhost:{port})")
    print("=" * 65)
    print("브라우저에서 배포 랜딩 페이지를 확인하고 다운로드를 테스트할 수 있습니다.")
    print("종료하려면 콘솔에서 Ctrl + C를 누르세요.\n")

    os.chdir(WEB_DIR)
    Handler = http.server.SimpleHTTPRequestHandler

    try:
        with socketserver.TCPServer(("", port), Handler) as httpd:
            webbrowser.open(f"http://localhost:{port}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n웹 서버가 종료되었습니다.")
    except Exception as e:
        print(f"웹 서버 실행 오류: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        start_local_preview()
    else:
        success = build_exe()
        if success:
            if package_for_web():
                print("\n[COMPLETE] 모든 빌드 및 웹 패키징 작업이 성공적으로 완료되었습니다!")
