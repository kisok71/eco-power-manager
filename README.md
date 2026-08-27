# 🌿 탄소중립 PC 전원 관리자 Pro (Eco Power Manager Pro)

점심시간 모니터/본체 자동 절전 전환 및 퇴근 후 시스템 자동 종료를 통해 대기전력을 절감하는 Windows 전원 관리 솔루션입니다.

---

## 📁 프로젝트 구조

```text
eco/
├── eco_power_manager.py     # 데스크톱 프로그램 소스코드 (버전 확인 및 웹 연동 탑재)
├── build_for_web.py         # 원클릭 EXE 빌드 및 웹 패키징 자동화 스크립트
├── web/                     # 🌐 웹 배포 패키지 (웹서버 또는 GitHub Pages에 업로드할 폴더)
│   ├── index.html           # 공식 웹 배포 및 원클릭 다운로드 랜딩 페이지
│   ├── version.json         # 자동 업데이트 및 최신 버전 체크 메타데이터
│   └── downloads/           # 빌드된 EcoPowerManagerPro.exe 가 저장되는 폴더
└── README.md                # 설명서 및 배포 가이드
```

---

## 🚀 빠른 시작 및 웹 배포 방법

### 1단계: 필수 라이브러리 설치
```powershell
pip install pyinstaller pystray pillow
```

### 2단계: 원클릭 EXE 빌드 및 웹 패키징
```powershell
python build_for_web.py
```
- `dist/EcoPowerManagerPro.exe` 생성
- `web/downloads/EcoPowerManagerPro.exe`로 자동 복사 및 배포 준비 완료

### 3단계: 로컬에서 웹 다운로드 사이트 미리보기
```powershell
python build_for_web.py serve
```
- 브라우저(`http://localhost:8080`)가 열리며 웹 배포 랜딩 페이지와 다운로드 기능을 바로 테스트할 수 있습니다.

---

## 🌐 웹 배포 3가지 방법

### 방법 A. GitHub Pages 무료 웹 호스팅 (추천)
1. GitHub 저장소를 생성하고 프로젝트의 `web/` 폴더 내용물을 푸시합니다.
2. 저장소의 **Settings -> Pages**에서 `Deploy from a branch (main / root)`를 선택합니다.
3. 생성된 웹사이트 주소(예: `https://<아이디>.github.io/<저장소명>/`)를 `eco_power_manager.py`의 `WEB_DOWNLOAD_URL`에 입력하면 끝납니다.

### 방법 B. 사내 인트라넷 / 웹 서버 (경찰청/관공서 내부망)
1. 내부 IIS, Nginx 또는 Apache 웹 서버의 웹 루트 폴더(예: `C:\inetpub\wwwroot\ecopower\` 또는 `/var/www/html/`)에 `web/` 폴더 안의 파일들을 복사합니다.
2. 내부망 URL(예: `http://10.xxx.xxx.xxx/ecopower/`)로 직원들이 접속하여 즉시 다운로드받을 수 있습니다.

### 방법 C. 클라우드 드라이브 / 파일 공유 서버
- `EcoPowerManagerPro.exe` 파일을 구글 드라이브, 네이버 MYBOX, 또는 사내 NAS 공유 폴더에 업로드 후 다운로드 링크를 `index.html`의 버튼 링크에 연결합니다.
