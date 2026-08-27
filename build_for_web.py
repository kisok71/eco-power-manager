"""
탄소중립 PC 전원 관리자 Pro - 원클릭 EXE 빌드 및 웹 배포 패키징 스크립트
"""

import os
import sys
import subprocess
import shutil
import http.server
import socketserver
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")
DOWNLOADS_DIR = os.path.join(WEB_DIR, "downloads")
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")
SPEC_FILE = os.path.join(BASE_DIR, "EcoPowerManagerPro.spec")

def build_exe():
    print("=" * 60)
    print(" 🚀 [1/3] PyInstaller를 사용하여 단일 실행 파일(.exe) 빌드 시작")
    print("=" * 60)

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
        print("\n✅ EXE 파일 빌드 완료!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 빌드 실패: {e}")
        return False
    return True

def package_for_web():
    print("\n" + "=" * 60)
    print(" 📦 [2/3] 웹 배포 폴더(web/downloads/)로 파일 복사 및 패키징")
    print("=" * 60)

    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    built_exe = os.path.join(DIST_DIR, "EcoPowerManagerPro.exe")
    target_exe = os.path.join(DOWNLOADS_DIR, "EcoPowerManagerPro.exe")

    if os.path.exists(built_exe):
        shutil.copy2(built_exe, target_exe)
        file_size_mb = os.path.getsize(target_exe) / (1024 * 1024)
        print(f"✅ 파일 복사 성공: {target_exe} ({file_size_mb:.2f} MB)")
        return True
    else:
        print(f"❌ 빌드된 파일을 찾을 수 없습니다: {built_exe}")
        return False

def start_local_preview(port=8080):
    print("\n" + "=" * 60)
    print(f" 🌐 [3/3] 로컬 웹 배포 서버 시작 (http://localhost:{port})")
    print("=" * 60)
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
                print("\n🎉 웹 배포 준비가 모두 완료되었습니다!")
                print("\n[다음 안내]")
                print("1. 로컬에서 웹페이지를 미리 보려면: python build_for_web.py serve")
                print("2. GitHub Pages 또는 사내 인트라넷 웹서버에 'web' 폴더 안의 모든 파일을 업로드하면 배포가 완료됩니다.")
