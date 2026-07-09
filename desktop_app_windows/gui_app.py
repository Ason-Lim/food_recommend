"""
브랜드커넥트 링크 생성기 - 데스크탑 앱 (Windows용)
======================================================

맥용 gui_app.py와 기능은 동일하고, 3번 버튼에서 새 터미널을 여는 방식만
윈도우에 맞게 바꿨습니다 (macOS는 Terminal.app/osascript, Windows는 cmd.exe).

버튼 구성:
  1) 트렌드 분석 + 데이터랩 검증 실행
  2) 브랜드커넥트 로그인 창 열기 (실제 로그인은 항상 사용자가 직접)
  3) 키워드로 링크 자동 생성 (캡차 대응 위해 새 명령 프롬프트 창에서 실행)
"""

import subprocess
import sys
import platform
import threading
import queue
from pathlib import Path

import tkinter as tk
from tkinter import scrolledtext, messagebox

BASE_DIR = Path(__file__).resolve().parent            # .../food_recommend/desktop_app_windows
PROJECT_ROOT = BASE_DIR.parent                          # .../food_recommend
TREND_PIPELINE_DIR = PROJECT_ROOT / "trend_pipeline"
BRANDCONNECT_TOOL_DIR = PROJECT_ROOT / "brandconnect_link_tool"
KEYWORDS_FILE = TREND_PIPELINE_DIR / "trend_analysis" / "keywords_for_brandconnect.txt"

DEFAULT_CREATOR_ID = "971564859961248"
IS_WINDOWS = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("브랜드커넥트 링크 생성기 (Windows)")
        self.geometry("760x580")
        self.log_queue = queue.Queue()
        self.creator_id_var = tk.StringVar(value=DEFAULT_CREATOR_ID)

        self._build_widgets()
        self.after(150, self._drain_log_queue)
        self.log("준비 완료. 1) → 2) → 3) 순서로 눌러주세요.")
        if not IS_WINDOWS:
            self.log(f"[참고] 현재 OS는 {platform.system()}입니다. 이 버전은 Windows용으로 만들었습니다.")

    # ---------- UI ----------
    def _build_widgets(self):
        top = tk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)
        tk.Label(top, text="브랜드커넥트 크리에이터 ID:").pack(side="left")
        tk.Entry(top, textvariable=self.creator_id_var, width=22).pack(side="left", padx=6)

        btns = tk.Frame(self)
        btns.pack(fill="x", padx=10, pady=4)
        tk.Button(btns, text="1) 트렌드 분석 + 검증 실행", width=26,
                  command=self.run_trend_analysis).pack(side="left", padx=4)
        tk.Button(btns, text="2) 브랜드커넥트 로그인 창 열기", width=26,
                  command=self.open_login).pack(side="left", padx=4)
        tk.Button(btns, text="3) 키워드로 링크 자동 생성", width=26,
                  command=self.generate_links).pack(side="left", padx=4)

        self.log_box = scrolledtext.ScrolledText(self, height=30, font=("Consolas", 11))
        self.log_box.pack(fill="both", expand=True, padx=10, pady=8)
        self.log_box.configure(state="disabled")

    # ---------- 로그 처리 ----------
    def log(self, msg):
        self.log_queue.put(msg)

    def _drain_log_queue(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get_nowait()
            self.log_box.configure(state="normal")
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.after(150, self._drain_log_queue)

    def _run_subprocess_async(self, cmd, cwd):
        def worker():
            self.log(f"$ {' '.join(str(c) for c in cmd)}")
            try:
                proc = subprocess.Popen(
                    cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1,
                )
                for line in proc.stdout:
                    self.log(line.rstrip())
                proc.wait()
                self.log(f"[종료 코드: {proc.returncode}]")
            except Exception as e:
                self.log(f"[오류] {e}")
        threading.Thread(target=worker, daemon=True).start()

    # ---------- 버튼 동작 ----------
    def run_trend_analysis(self):
        self.log("\n=== 1) 트렌드 분석 + 데이터랩 검증 시작 ===")
        self._run_subprocess_async([sys.executable, "run_pipeline.py"], cwd=str(TREND_PIPELINE_DIR))

    def open_login(self):
        self.log("\n=== 2) 브랜드커넥트 로그인 창 여는 중... ===")
        creator_id = self.creator_id_var.get().strip() or DEFAULT_CREATOR_ID
        script = BASE_DIR / "open_brandconnect_login.py"
        self._run_subprocess_async(
            [sys.executable, str(script), creator_id],
            cwd=str(BRANDCONNECT_TOOL_DIR),
        )

    def generate_links(self):
        if not KEYWORDS_FILE.exists():
            messagebox.showwarning(
                "키워드 파일 없음",
                "먼저 1) 트렌드 분석을 실행해서 keywords_for_brandconnect.txt를 만들어주세요.",
            )
            return

        creator_id = self.creator_id_var.get().strip() or DEFAULT_CREATOR_ID
        self.log("\n=== 3) 링크 생성을 새 명령 프롬프트 창에서 시작합니다 ===")
        self.log("(캡차나 화면 요소를 못 찾는 경우 그 창에서 직접 진행해주세요.)")

        py = sys.executable
        args = [
            py, "brandconnect_link_generator.py",
            "--creator-id", creator_id,
            "--keywords-file", str(KEYWORDS_FILE),
        ]

        try:
            if IS_WINDOWS:
                # 새 cmd 창을 열어서 그 안에서 실행 (입력이 필요한 캡차/수동클릭 대응 가능)
                quoted = " ".join(f'"{a}"' if " " in str(a) else str(a) for a in args)
                subprocess.Popen(
                    f'start "BrandConnect 링크 생성" cmd /k "cd /d {str(BRANDCONNECT_TOOL_DIR)} && {quoted}"',
                    shell=True,
                )
                self.log("명령 프롬프트 창을 열었습니다.")
            elif IS_MAC:
                import shlex
                cmd_str = (
                    f"cd {shlex.quote(str(BRANDCONNECT_TOOL_DIR))} && "
                    f"{shlex.quote(py)} brandconnect_link_generator.py "
                    f"--creator-id {shlex.quote(creator_id)} "
                    f"--keywords-file {shlex.quote(str(KEYWORDS_FILE))}"
                )
                applescript = f'tell application "Terminal" to do script "{cmd_str}"'
                subprocess.run(["osascript", "-e", applescript], check=True)
                self.log("터미널 창을 열었습니다.")
            else:
                # 그 외 OS: 새 창 없이 이 앱 로그 창에 바로 출력 (수동 개입 프롬프트는 동작하지 않을 수 있음)
                self.log("[참고] 이 OS에서는 새 터미널을 열 수 없어 로그 창에 바로 출력합니다.")
                self._run_subprocess_async(args, cwd=str(BRANDCONNECT_TOOL_DIR))
        except Exception as e:
            self.log(f"[오류] 새 창을 열지 못했습니다: {e}")
            messagebox.showerror("오류", f"새 창을 여는 데 실패했습니다:\n{e}")


if __name__ == "__main__":
    App().mainloop()
