import tkinter as tk
from tkinter import messagebox
import os
import json
from datetime import datetime
import threading
import time
import ctypes
import platform
import sys
import subprocess
import webbrowser
import urllib.request
import winreg

# 시스템 트레이 아이콘 및 이미지 라이브러리
import pystray
from PIL import Image, ImageDraw

# 프로그램 버전 및 웹 배포 설정
APP_VERSION = "2.2.0"
APP_TITLE = "탄소중립 PC 전원 관리자 Pro"
# 웹 배포 서버 URL (GitHub Pages)
WEB_DOWNLOAD_URL = "https://kisok71.github.io/eco-power-manager/"
VERSION_CHECK_URL = "https://kisok71.github.io/eco-power-manager/version.json"

# 콘솔 창 숨김 플래그 (Windows)
CREATE_NO_WINDOW = 0x08000000

# High-DPI 지원 활성화 (Windows 화면 배율 125%, 150% 등에서 폰트 번짐 방지)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# 실행 경로 기준 설정 (바로가기 실행/시작프로그램 실행 시 상대경로 오류 방지)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "eco_power_config.json")
LOG_FILE = os.path.join(BASE_DIR, "eco_power_log.txt")
AUTOSTART_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_REG_NAME = "EcoPowerManagerPro"


def remove_zone_identifier():
    """웹 브라우저 다운로드 시 파일에 붙는 Windows Zone.Identifier(보안 경고 팝업) ADS 스트림 자동 해제"""
    if sys.platform == "win32":
        try:
            target_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
            ads_path = f"{target_path}:Zone.Identifier"
            ctypes.windll.kernel32.DeleteFileW(ads_path)
        except Exception:
            pass


# 프로그램 구동 즉시 웹 다운로드 보안 차단(Zone.Identifier) 해제 실행
remove_zone_identifier()


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint)
    ]


class EcoPowerManager:
    def __init__(self, root):
        if platform.system() != "Windows":
            messagebox.showerror("OS 오류", "이 프로그램은 Windows 환경에서만 작동합니다.")
            root.destroy()
            return

        self.root = root
        self.root.title(f"{APP_TITLE} (v{APP_VERSION})")
        self.root.geometry("460x470")
        self.root.resizable(False, False)

        # 윈도우 기본 폰트 설정 (맑은 고딕)
        self.font_title = ("Malgun Gothic", 14, "bold")
        self.font_label = ("Malgun Gothic", 10, "bold")
        self.font_entry = ("Malgun Gothic", 10)
        self.font_sub = ("Malgun Gothic", 9)
        self.font_status = ("Malgun Gothic", 9, "bold")

        # 상태 변수 초기화
        self.is_running = False
        self.last_sleep_date = None
        self.last_shutdown_date = None
        self.target_lunch = ""
        self.target_work = ""
        self.target_idle_seconds = 0
        self.only_weekdays = True
        self.screen_off_triggered = False
        
        # 5분(300초) 미입력 시 자동 시작 카운트다운 타이머
        self.auto_start_countdown = 300
        self.auto_start_timer_job = None
        
        self.tray_icon = None
        self.sleep_dialog = None
        self.shutdown_dialog = None
        self.sleep_timer_job = None
        self.shutdown_timer_job = None
        self.status_update_job = None

        # --- 메인 타이틀 ---
        tk.Label(root, text=f"🌿 {APP_TITLE} 🌿", font=self.font_title, fg="#2E7D32").pack(pady=(12, 2))
        
        # 버전 및 웹페이지 링크
        header_sub_frame = tk.Frame(root)
        header_sub_frame.pack(pady=(0, 6))
        tk.Label(header_sub_frame, text=f"v{APP_VERSION} | ", font=self.font_sub, fg="#757575").pack(side=tk.LEFT)
        web_link = tk.Label(header_sub_frame, text="🌐 웹 배포 페이지", font=self.font_sub, fg="#1565C0", cursor="hand2")
        web_link.pack(side=tk.LEFT)
        web_link.bind("<Button-1>", lambda e: self.open_web_page())
        
        # 실시간 상태 표시 레이블
        self.status_label = tk.Label(root, text="상태: 자동 관리 대기 중 (5분 후 자동 시작)", font=self.font_status, fg="#1565C0")
        self.status_label.pack(pady=(0, 6))

        # --- 설정 불러오기 ---
        loaded_lunch, loaded_work, loaded_idle, loaded_weekdays, loaded_autostart = self.load_settings()

        # --- 입력 폼 프레임 (Grid 레이아웃) ---
        input_frame = tk.Frame(root)
        input_frame.pack(pady=4, padx=20, fill="x")

        # 1. 점심시간 설정
        tk.Label(input_frame, text="점심시간 (절전) [HH:MM]:", font=self.font_label).grid(row=0, column=0, sticky="e", pady=5)
        self.lunch_entry = tk.Entry(input_frame, width=10, justify="center", font=self.font_entry)
        self.lunch_entry.insert(0, loaded_lunch)
        self.lunch_entry.grid(row=0, column=1, sticky="w", padx=8, pady=5)
        self.lunch_entry.bind("<KeyRelease>", self.format_time_input)

        # 2. 퇴근시간 설정
        tk.Label(input_frame, text="퇴근시간 (종료) [HH:MM]:", font=self.font_label).grid(row=1, column=0, sticky="e", pady=5)
        self.work_entry = tk.Entry(input_frame, width=10, justify="center", font=self.font_entry)
        self.work_entry.insert(0, loaded_work)
        self.work_entry.grid(row=1, column=1, sticky="w", padx=8, pady=5)
        self.work_entry.bind("<KeyRelease>", self.format_time_input)

        # 3. 화면 끄기 설정
        tk.Label(input_frame, text="화면 끄기 (미사용) [분]:", font=self.font_label).grid(row=2, column=0, sticky="e", pady=5)
        self.idle_entry = tk.Entry(input_frame, width=10, justify="center", font=self.font_entry)
        self.idle_entry.insert(0, loaded_idle)
        self.idle_entry.grid(row=2, column=1, sticky="w", padx=8, pady=5)
        tk.Label(input_frame, text="(0=사용안함)", font=self.font_sub, fg="gray").grid(row=2, column=2, sticky="w")

        # 4. 부가 옵션 체크박스
        opt_frame = tk.Frame(root)
        opt_frame.pack(pady=4, padx=30, fill="x")

        self.weekday_var = tk.BooleanVar(value=loaded_weekdays)
        self.weekday_chk = tk.Checkbutton(opt_frame, text="평일(월~금)만 작동 (주말 제외)", variable=self.weekday_var, font=self.font_sub)
        self.weekday_chk.pack(anchor="w")

        self.autostart_var = tk.BooleanVar(value=loaded_autostart)
        self.autostart_chk = tk.Checkbutton(opt_frame, text="Windows 부팅 시 자동 실행", variable=self.autostart_var,
                                            command=self.toggle_autostart_reg, font=self.font_sub)
        self.autostart_chk.pack(anchor="w")

        # --- 제어 버튼 영역 ---
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=8)

        self.toggle_btn = tk.Button(btn_frame, text="▶ 자동 관리 시작", font=("Malgun Gothic", 11, "bold"),
                                    bg="#A5D6A7", fg="#1B5E20", activebackground="#81C784",
                                    command=self.toggle_timer, width=18, height=2, relief="groove")
        self.toggle_btn.pack(side=tk.LEFT, padx=5)

        self.tray_btn = tk.Button(btn_frame, text="트레이로 숨기기", font=self.font_sub,
                                  command=self.hide_to_tray, width=13, height=2)
        self.tray_btn.pack(side=tk.LEFT, padx=5)

        # 하단 도구 링크 프레임 (업데이트 확인 등)
        tool_frame = tk.Frame(root)
        tool_frame.pack(pady=4)
        
        btn_update = tk.Button(tool_frame, text="🔄 최신 업데이트 확인", font=("Malgun Gothic", 8),
                               relief="flat", fg="#424242", command=self.check_for_updates_manual)
        btn_update.pack(side=tk.LEFT, padx=5)

        # --- 하단 소속 안내 문구 ---
        tk.Label(root, text="경기남부경찰청 정보화장비과", font=self.font_sub, fg="#757575").pack(side=tk.BOTTOM, pady=8)

        # 윈도우 닫기 이벤트 바인딩
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # UI 실시간 상태 갱신 루프 시작
        self.update_status_ui()

        # 5분 미작동 시 자동 시작 카운트다운 가동
        self.start_auto_start_timer()

        # 백그라운드에서 신규 버전 자동 확인 (비동기)
        threading.Thread(target=self.check_for_updates_silent, daemon=True).start()

    def open_web_page(self):
        """웹 배포/다운로드 사이트 열기"""
        try:
            webbrowser.open(WEB_DOWNLOAD_URL)
        except Exception as e:
            messagebox.showerror("오류", f"웹페이지를 열 수 없습니다: {e}")

    def check_for_updates_silent(self):
        """프로그램 시작 시 조용히 업데이트 확인"""
        try:
            req = urllib.request.Request(VERSION_CHECK_URL, headers={'User-Agent': f'EcoPowerManager/{APP_VERSION}'})
            with urllib.request.urlopen(req, timeout=3) as res:
                if res.status == 200:
                    data = json.loads(res.read().decode('utf-8'))
                    latest_ver = data.get("latest_version", "")
                    download_url = data.get("download_url", WEB_DOWNLOAD_URL)
                    changelog = data.get("changelog", "")

                    if latest_ver and latest_ver != APP_VERSION:
                        # 신규 버전 발견 시 메인 스레드에서 알림
                        self.root.after(1000, lambda: self.show_update_dialog(latest_ver, download_url, changelog))
        except Exception:
            # 네트워크 미연결 또는 오프라인 환경에서는 무시
            pass

    def check_for_updates_manual(self):
        """사용자가 직접 업데이트 확인 버튼 클릭 시"""
        try:
            req = urllib.request.Request(VERSION_CHECK_URL, headers={'User-Agent': f'EcoPowerManager/{APP_VERSION}'})
            with urllib.request.urlopen(req, timeout=4) as res:
                if res.status == 200:
                    data = json.loads(res.read().decode('utf-8'))
                    latest_ver = data.get("latest_version", "")
                    download_url = data.get("download_url", WEB_DOWNLOAD_URL)
                    changelog = data.get("changelog", "")

                    if latest_ver and latest_ver != APP_VERSION:
                        self.show_update_dialog(latest_ver, download_url, changelog)
                    else:
                        messagebox.showinfo("업데이트 확인", f"현재 최신 버전(v{APP_VERSION})을 사용 중입니다.")
        except Exception as e:
            messagebox.showwarning("업데이트 확인 실패", f"서버에 연결할 수 없습니다.\n인터넷 연결 상태를 확인해 주세요.\n(배포 웹페이지: {WEB_DOWNLOAD_URL})")

    def show_update_dialog(self, latest_version, download_url, changelog):
        """새 버전 알림 창 표시"""
        msg = f"새로운 버전(v{latest_version})이 출시되었습니다!\n\n현재 버전: v{APP_VERSION}\n최신 버전: v{latest_version}\n\n[주요 변경사항]\n{changelog}\n\n웹 배포 페이지로 이동하여 다운로드하시겠습니까?"
        if messagebox.askyesno("업데이트 알림", msg):
            webbrowser.open(download_url)

    def center_window(self, win, width, height):
        """윈도우를 화면 정중앙에 배치"""
        win.update_idletasks()
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        win.geometry(f"{width}x{height}+{x}+{y}")

    def format_time_input(self, event):
        """시간 입력 필드 자동 콜론(:) 서식 및 4자리 제한"""
        if event.keysym in ['BackSpace', 'Delete', 'Left', 'Right', 'Up', 'Down', 'Tab', 'Return']:
            return

        widget = event.widget
        text = widget.get()
        cleaned = "".join(filter(str.isdigit, text))[:4]

        if len(cleaned) >= 3:
            formatted = f"{cleaned[:2]}:{cleaned[2:4]}"
        elif len(cleaned) == 2 and not text.endswith(":"):
            formatted = f"{cleaned}:"
        else:
            formatted = cleaned

        if text != formatted:
            cursor_pos = widget.index(tk.INSERT)
            widget.delete(0, tk.END)
            widget.insert(0, formatted)
            widget.icursor(min(cursor_pos + 1, len(formatted)))

    def log_event(self, message):
        """로그 파일에 타임스탬프와 함께 기록"""
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{now_str}] {message}\n")
        except Exception as e:
            print(f"로그 저장 실패: {e}")

    def load_settings(self):
        """설정 파일 로드 (부팅 자동 실행 레지스트리 상태도 동기화)"""
        default_lunch = "12:00"
        default_work = "18:00"
        default_idle = "15"
        default_weekdays = True
        autostart_active = self.is_autostart_registered()

        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return (
                        data.get("lunch", default_lunch),
                        data.get("work", default_work),
                        data.get("idle", default_idle),
                        data.get("weekdays", default_weekdays),
                        autostart_active
                    )
        except Exception as e:
            self.log_event(f"설정 로드 실패: {e}")
            
        return default_lunch, default_work, default_idle, default_weekdays, autostart_active

    def save_settings(self, lunch, work, idle, weekdays):
        """설정 파일 저장"""
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "lunch": lunch,
                    "work": work,
                    "idle": idle,
                    "weekdays": weekdays
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log_event(f"설정 저장 실패: {e}")

    def is_autostart_registered(self):
        """레지스트리에 시작프로그램으로 등록되어 있는지 확인"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_REG_KEY, 0, winreg.KEY_READ) as key:
                val, _ = winreg.QueryValueEx(key, APP_REG_NAME)
                return bool(val)
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def toggle_autostart_reg(self):
        """시작프로그램 레지스트리 등록/해제 토글"""
        is_enable = self.autostart_var.get()
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_REG_KEY, 0, winreg.KEY_SET_VALUE) as key:
                if is_enable:
                    if getattr(sys, 'frozen', False):
                        cmd = f'"{sys.executable}"'
                    else:
                        cmd = f'"{sys.executable}" "{os.path.abspath(__file__)}"'
                    winreg.SetValueEx(key, APP_REG_NAME, 0, winreg.REG_SZ, cmd)
                    self.log_event("시작프로그램 자동 실행 등록 완료")
                else:
                    try:
                        winreg.DeleteValue(key, APP_REG_NAME)
                        self.log_event("시작프로그램 자동 실행 해제 완료")
                    except FileNotFoundError:
                        pass
        except Exception as e:
            messagebox.showerror("레지스트리 오류", f"시작프로그램 설정 변경 중 오류가 발생했습니다:\n{e}")
            self.autostart_var.set(not is_enable)

    def validate_time(self, time_str):
        """시간 형식(HH:MM, 00:00~23:59) 유효성 검사"""
        try:
            parts = time_str.split(":")
            if len(parts) != 2:
                return False
            h, m = int(parts[0]), int(parts[1])
            return 0 <= h <= 23 and 0 <= m <= 59
        except Exception:
            return False

    def start_auto_start_timer(self):
        """5분(300초) 동안 사용자 시작 조작이 없을 경우 자동 시작 카운트다운"""
        if self.auto_start_timer_job:
            self.root.after_cancel(self.auto_start_timer_job)
            self.auto_start_timer_job = None

        if not self.is_running and self.auto_start_countdown > 0:
            self.update_auto_start_timer()

    def update_auto_start_timer(self):
        """1초마다 5분 카운트다운 갱신 및 0초 도달 시 자동 시작 실행"""
        if self.is_running:
            return

        if self.auto_start_countdown > 0:
            mins, secs = divmod(self.auto_start_countdown, 60)
            self.status_label.config(
                text=f"상태: 자동 관리 대기 중 ({mins}분 {secs:02d}초 후 자동 시작)",
                fg="#1565C0"
            )
            self.auto_start_countdown -= 1
            self.auto_start_timer_job = self.root.after(1000, self.update_auto_start_timer)
        else:
            self.log_event("5분간 대기 후 사용자 입력이 없어 자동 관리를 자동 시작합니다.")
            self.toggle_timer()

    def update_status_ui(self):
        """메인 창 상태 문구 실시간 갱신"""
        if self.is_running:
            now = datetime.now()
            today = now.date()
            is_weekend = today.weekday() >= 5

            if self.only_weekdays and is_weekend:
                status_text = "상태: 주말 작동 일시 정지 중 (월요일 자동 재개)"
                fg_color = "#E65100"
            else:
                status_text = f"상태: 자동 관리 동작 중 (점심 {self.target_lunch} / 퇴근 {self.target_work})"
                fg_color = "#1B5E20"
            self.status_label.config(text=status_text, fg=fg_color)
        else:
            if self.auto_start_countdown <= 0:
                self.status_label.config(text="상태: 자동 관리 대기(중지) 중", fg="#555555")

        self.status_update_job = self.root.after(2000, self.update_status_ui)

    def toggle_timer(self):
        """자동 관리 시작/중지 전환"""
        # 5분 자동 시작 카운트다운 타이머 중단
        if self.auto_start_timer_job:
            self.root.after_cancel(self.auto_start_timer_job)
            self.auto_start_timer_job = None
        self.auto_start_countdown = 0

        if not self.is_running:
            lunch_val = self.lunch_entry.get().strip()
            work_val = self.work_entry.get().strip()
            idle_val = self.idle_entry.get().strip()
            weekdays_val = self.weekday_var.get()

            # 입력값 검증
            if not self.validate_time(lunch_val) or not self.validate_time(work_val):
                messagebox.showerror("입력 오류", "시간 형식(HH:MM, 00:00~23:59)을 정확히 입력하세요.\n(예: 12:00, 18:00)")
                return

            if not idle_val.isdigit() or int(idle_val) < 0:
                messagebox.showerror("입력 오류", "화면 끄기 시간은 0 이상의 숫자로만 입력하세요.\n(0 입력 시 화면 끄기 사용 안 함)")
                return

            # 설정 저장
            self.save_settings(lunch_val, work_val, idle_val, weekdays_val)

            # 타겟 변수 및 플래그 갱신
            self.last_sleep_date = None
            self.last_shutdown_date = None
            self.screen_off_triggered = False

            self.target_lunch = lunch_val
            self.target_work = work_val
            self.target_idle_seconds = int(idle_val) * 60
            self.only_weekdays = weekdays_val

            self.is_running = True

            # 입력창 비활성화
            self.lunch_entry.config(state="disabled")
            self.work_entry.config(state="disabled")
            self.idle_entry.config(state="disabled")
            self.weekday_chk.config(state="disabled")

            # 버튼 스타일 변경
            self.toggle_btn.config(text="⏹ 자동 관리 중지", bg="#FFCDD2", fg="#B71C1C", activebackground="#EF9A9A")
            self.log_event(f"자동 관리 시작 (점심:{lunch_val}, 퇴근:{work_val}, 화면끄기:{idle_val}분, 평일전용:{weekdays_val})")

            # 백그라운드 체크 스레드 시작
            threading.Thread(target=self.check_time_loop, daemon=True).start()

            # 시작 시 자동으로 시스템 트레이로 숨김
            self.hide_to_tray()

        else:
            self.stop_timer()

    def stop_timer(self):
        """자동 관리 중지 처리"""
        self.is_running = False

        # 자동 시작 타이머 완전 정지
        if self.auto_start_timer_job:
            self.root.after_cancel(self.auto_start_timer_job)
            self.auto_start_timer_job = None
        self.auto_start_countdown = 0

        # 입력창 활성화
        self.lunch_entry.config(state="normal")
        self.work_entry.config(state="normal")
        self.idle_entry.config(state="normal")
        self.weekday_chk.config(state="normal")

        # 버튼 스타일 원복
        self.toggle_btn.config(text="▶ 자동 관리 시작", bg="#A5D6A7", fg="#1B5E20", activebackground="#81C784")

        # 진행 중인 팝업 카운트다운 타이머 취소
        self.cancel_sleep(manual=False)
        self.cancel_shutdown(manual=False)

        # 시스템 종료 예약 취소
        subprocess.run(["shutdown", "-a"], capture_output=True, creationflags=CREATE_NO_WINDOW)
        self.log_event("자동 관리 중지 및 종료 예약 취소")

    def get_idle_time(self):
        """사용자 미입력(키보드/마우스 유휴) 시간 계산 (초 단위)"""
        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        ctypes.windll.user32.GetLastInputInfo.argtypes = [ctypes.POINTER(LASTINPUTINFO)]
        ctypes.windll.user32.GetLastInputInfo.restype = ctypes.c_bool
        ctypes.windll.kernel32.GetTickCount.restype = ctypes.c_uint

        if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
            tick = ctypes.windll.kernel32.GetTickCount()
            diff = (tick - lii.dwTime) & 0xFFFFFFFF
            return diff / 1000.0
        return 0

    def turn_off_screen(self):
        """모니터 절전(화면 끄기) 명령 전송"""
        self.log_event("장시간 미사용으로 모니터 화면 끄기 실행")
        ctypes.windll.user32.SendNotifyMessageW(0xFFFF, 0x0112, 0xF170, 2)

    def create_tray_icon_image(self):
        """시스템 트레이용 에코 아이콘 생성"""
        image = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((8, 8, 56, 56), fill=(46, 125, 50, 255))
        draw.ellipse((22, 22, 42, 42), fill=(165, 214, 167, 255))
        return image

    def hide_to_tray(self):
        """창을 숨기고 시스템 트레이 아이콘 활성화"""
        self.root.withdraw()

        if self.tray_icon is None:
            menu = pystray.Menu(
                pystray.MenuItem('설정 열기', self.show_window, default=True),
                pystray.MenuItem('자동 관리 시작/중지', self.toggle_from_tray),
                pystray.MenuItem('🌐 웹 배포 사이트', lambda icon, item: self.open_web_page()),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem('프로그램 완전 종료', self.quit_program)
            )
            self.tray_icon = pystray.Icon("EcoPower", self.create_tray_icon_image(), f"{APP_TITLE} v{APP_VERSION}", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self, icon=None, item=None):
        """트레이에서 메인 창 복원"""
        self.root.after(0, self._restore_window)

    def _restore_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def toggle_from_tray(self, icon=None, item=None):
        """트레이 메뉴에서 시작/중지 제어"""
        self.root.after(0, self.toggle_timer)

    def quit_program(self, icon=None, item=None):
        """트레이 메뉴에서 완전 종료"""
        self.root.after(0, self._show_and_close)

    def _show_and_close(self):
        self.root.deiconify()
        self.on_close()

    def check_time_loop(self):
        """시간 및 유휴 상태 감시 백그라운드 루프"""
        while self.is_running:
            now = datetime.now()
            now_str = now.strftime("%H:%M")
            today = now.date()
            is_weekend = today.weekday() >= 5

            # 평일 옵션 체크 (주말이면 시간 체크 건너뜀)
            if not (self.only_weekdays and is_weekend):
                # 점심시간 체크
                if now_str == self.target_lunch and self.last_sleep_date != today:
                    self.last_sleep_date = today
                    self.root.after(0, self.execute_sleep)

                # 퇴근시간 체크
                elif now_str == self.target_work and self.last_shutdown_date != today:
                    self.last_shutdown_date = today
                    self.root.after(0, self.execute_shutdown)

            # 화면 끄기(유휴 시간) 체크 - 팝업 카운트다운 중이 아닐 때만
            is_dialog_active = (
                (self.sleep_dialog is not None and self.sleep_dialog.winfo_exists()) or
                (self.shutdown_dialog is not None and self.shutdown_dialog.winfo_exists())
            )

            if self.target_idle_seconds > 0 and not is_dialog_active:
                idle_seconds = self.get_idle_time()

                if idle_seconds >= self.target_idle_seconds and not self.screen_off_triggered:
                    self.screen_off_triggered = True
                    self.turn_off_screen()

                elif idle_seconds < self.target_idle_seconds and self.screen_off_triggered:
                    self.screen_off_triggered = False

            time.sleep(1)

    # --- 절전 모드 관련 메서드 ---
    def execute_sleep(self):
        """점심 절전 모드 알림 다이얼로그 표시"""
        self.log_event("점심시간 절전 모드 60초 카운트다운 시작")

        if self.sleep_dialog and self.sleep_dialog.winfo_exists():
            self.sleep_dialog.destroy()

        self.sleep_dialog = tk.Toplevel(self.root)
        self.sleep_dialog.title("점심시간 절전 모드 알림")
        self.center_window(self.sleep_dialog, 460, 200)
        self.sleep_dialog.attributes("-topmost", True)
        self.sleep_dialog.resizable(False, False)
        self.sleep_dialog.protocol("WM_DELETE_WINDOW", self.cancel_sleep)

        self.sleep_countdown = 60

        tk.Label(self.sleep_dialog, text="🌿 점심시간입니다! 🌿\n지구를 위한 휴식, PC가 곧 절전 모드로 전환됩니다.",
                 font=("Malgun Gothic", 12, "bold"), fg="#1B5E20", pady=10).pack()

        self.lbl_sleep_timer = tk.Label(self.sleep_dialog, text=f"{self.sleep_countdown}초 후 자동으로 절전 전환됩니다.",
                                        font=("Malgun Gothic", 11, "bold"), fg="#D32F2F")
        self.lbl_sleep_timer.pack(pady=5)

        btn_frame = tk.Frame(self.sleep_dialog)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="지금 절전", font=self.font_sub, bg="#C8E6C9",
                  command=self.force_sleep, width=12, height=1).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="절전 취소", font=self.font_sub,
                  command=self.cancel_sleep, width=12, height=1).pack(side=tk.LEFT, padx=10)

        self.update_sleep_timer()

    def update_sleep_timer(self):
        """절전 카운트다운 갱신"""
        if not (self.sleep_dialog and self.sleep_dialog.winfo_exists()):
            return

        if self.sleep_countdown > 0:
            self.lbl_sleep_timer.config(text=f"{self.sleep_countdown}초 후 자동으로 절전 전환됩니다.")
            self.sleep_countdown -= 1
            self.sleep_timer_job = self.root.after(1000, self.update_sleep_timer)
        else:
            self.force_sleep()

    def force_sleep(self):
        """즉시 절전 모드 진입"""
        self.log_event("점심 절전 모드 실행")
        if self.sleep_timer_job:
            self.root.after_cancel(self.sleep_timer_job)
            self.sleep_timer_job = None

        if self.sleep_dialog and self.sleep_dialog.winfo_exists():
            self.sleep_dialog.destroy()
            self.sleep_dialog = None

        try:
            ctypes.windll.powrprof.SetSuspendState.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
            ctypes.windll.powrprof.SetSuspendState.restype = ctypes.c_int
            # (bHibernate=0, bForce=0, bWakeupEventsDisabled=0) -> 대기 모드(Sleep)
            ctypes.windll.powrprof.SetSuspendState(0, 0, 0)
        except Exception as e:
            self.log_event(f"절전 모드 실행 실패: {e}")
            messagebox.showerror("실행 오류", f"절전 모드 실행 중 오류가 발생했습니다:\n{e}")

    def cancel_sleep(self, manual=True):
        """절전 모드 취소"""
        if manual:
            self.log_event("사용자가 점심 절전 모드를 취소함")

        if self.sleep_timer_job:
            self.root.after_cancel(self.sleep_timer_job)
            self.sleep_timer_job = None

        if self.sleep_dialog and self.sleep_dialog.winfo_exists():
            self.sleep_dialog.destroy()
            self.sleep_dialog = None

    # --- 시스템 종료 관련 메서드 ---
    def execute_shutdown(self):
        """퇴근 시스템 종료 알림 다이얼로그 표시"""
        self.log_event("퇴근시간 시스템 종료 60초 카운트다운 시작")

        if self.shutdown_dialog and self.shutdown_dialog.winfo_exists():
            self.shutdown_dialog.destroy()

        self.shutdown_dialog = tk.Toplevel(self.root)
        self.shutdown_dialog.title("퇴근시간 시스템 종료 알림")
        self.center_window(self.shutdown_dialog, 460, 210)
        self.shutdown_dialog.attributes("-topmost", True)
        self.shutdown_dialog.resizable(False, False)
        self.shutdown_dialog.protocol("WM_DELETE_WINDOW", self.cancel_shutdown)

        self.shutdown_countdown = 60

        tk.Label(self.shutdown_dialog, text="⏰ 퇴근시간입니다! ⏰\n60초 후 PC가 자동으로 완전 종료됩니다.\n진행 중인 모든 작업물을 미리 저장해 주세요.",
                 font=("Malgun Gothic", 11, "bold"), fg="#D32F2F", pady=10).pack()

        self.lbl_shutdown_timer = tk.Label(self.shutdown_dialog, text=f"{self.shutdown_countdown}초 후 자동 종료됩니다.",
                                           font=("Malgun Gothic", 11, "bold"), fg="#B71C1C")
        self.lbl_shutdown_timer.pack(pady=5)

        btn_frame = tk.Frame(self.shutdown_dialog)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="지금 종료", font=self.font_sub, bg="#FFCDD2",
                  command=self.force_shutdown, width=12, height=1).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="종료 취소 (야근)", font=self.font_sub,
                  command=self.cancel_shutdown, width=14, height=1).pack(side=tk.LEFT, padx=10)

        self.update_shutdown_timer()

    def update_shutdown_timer(self):
        """종료 카운트다운 갱신"""
        if not (self.shutdown_dialog and self.shutdown_dialog.winfo_exists()):
            return

        if self.shutdown_countdown > 0:
            self.lbl_shutdown_timer.config(text=f"{self.shutdown_countdown}초 후 자동 종료됩니다.")
            self.shutdown_countdown -= 1
            self.shutdown_timer_job = self.root.after(1000, self.update_shutdown_timer)
        else:
            self.force_shutdown()

    def force_shutdown(self):
        """즉시 시스템 종료"""
        self.log_event("퇴근 시스템 종료 실행")
        if self.shutdown_timer_job:
            self.root.after_cancel(self.shutdown_timer_job)
            self.shutdown_timer_job = None

        if self.shutdown_dialog and self.shutdown_dialog.winfo_exists():
            self.shutdown_dialog.destroy()
            self.shutdown_dialog = None

        try:
            subprocess.run(["shutdown", "-s", "-t", "0"], capture_output=True, creationflags=CREATE_NO_WINDOW)
        except Exception as e:
            self.log_event(f"종료 명령 실행 실패: {e}")
            messagebox.showerror("실행 오류", f"종료 실행 중 오류가 발생했습니다:\n{e}")

    def cancel_shutdown(self, manual=True):
        """시스템 종료 취소"""
        if manual:
            self.log_event("사용자가 퇴근 시스템 종료를 취소함 (야근/작업 연장)")

        if self.shutdown_timer_job:
            self.root.after_cancel(self.shutdown_timer_job)
            self.shutdown_timer_job = None

        if self.shutdown_dialog and self.shutdown_dialog.winfo_exists():
            self.shutdown_dialog.destroy()
            self.shutdown_dialog = None

        subprocess.run(["shutdown", "-a"], capture_output=True, creationflags=CREATE_NO_WINDOW)

    def on_close(self):
        """메인 윈도우 종료 처리"""
        if messagebox.askyesno("프로그램 종료", "프로그램을 완전히 종료하시겠습니까?\n\n(참고: '트레이로 숨기기'를 누르면 백그라운드에서 계속 전원 관리가 동작합니다.)"):
            self.is_running = False
            
            # 모든 타이머 잡 및 예약 취소
            if self.auto_start_timer_job:
                self.root.after_cancel(self.auto_start_timer_job)
            if self.status_update_job:
                self.root.after_cancel(self.status_update_job)
            if self.sleep_timer_job:
                self.root.after_cancel(self.sleep_timer_job)
            if self.shutdown_timer_job:
                self.root.after_cancel(self.shutdown_timer_job)

            subprocess.run(["shutdown", "-a"], capture_output=True, creationflags=CREATE_NO_WINDOW)

            if self.tray_icon:
                try:
                    self.tray_icon.stop()
                except Exception:
                    pass

            self.log_event("프로그램 완전 종료")
            self.root.destroy()
            sys.exit(0)


if __name__ == "__main__":
    mutex_name = "EcoPowerManager_Pro_Unique_Mutex_v2"
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    last_error = ctypes.windll.kernel32.GetLastError()

    # ERROR_ALREADY_EXISTS = 183
    if last_error == 183:
        temp_root = tk.Tk()
        temp_root.withdraw()
        messagebox.showwarning("실행 알림", f"{APP_TITLE}가 이미 실행 중입니다.\n\n화면 우측 하단 작업표시줄(시스템 트레이) 아이콘을 확인해 주세요.")
        temp_root.destroy()
        sys.exit(0)

    root = tk.Tk()
    app = EcoPowerManager(root)
    root.mainloop()
