"""
브랜드커넥트 링크 생성기 - 데스크탑 앱 (GUI)
================================================

trend_pipeline(트렌드 분석/검증)과 brandconnect_link_tool(링크 자동 생성)을
버튼 3개로 실행할 수 있는 간단한 데스크탑 창입니다.

버튼 구성:
  1) 트렌드 분석 + 데이터랩 검증 실행
     -> trend_pipeline/run_pipeline.py 실행, 로그를 이 창에 실시간 표시

  2) 브랜드커넥트 로그인 창 열기
     -> 실제 네이버 로그인 페이지를 브라우저 창으로 띄웁니다.
        (캡차/2단계 인증 등은 반드시 사용자가 직접 처리해야 하므로,
         자동 로그인이 아니라 '진짜 로그인 창을 열어주는' 버튼입니다.)
        로그인 세션은 파일로 저장되어 다음부터는 다시 로그인할 필요가 없습니다.

  3) 키워드로 링크 자동 생성 시작
     -> 1번에서 만든 keywords_for_brandconnect.txt를 이용해
        brandconnect_link_generator.py를 새 터미널 창에서 실행합니다.
        (캡차가 뜨거나 화면 요소를 못 찾을 때 사용자가 직접 개입해야 하므로,
         입력이 가능한 진짜 터미널 창에서 실행합니다.)
"""

import subprocess
import sys
import shlex
import threading
import queue
from pathlib import Path

import tkinter as tk
from tkinter import scrolledtext, messagebox

BASE_DIR = Path(__file__).resolve().parent            # .../food_recommend/desktop_app
PROJECT_ROOT = BASE_DIR.parent                          # .../food_recommend
TREND_PIPELINE_DIR = PROJECT_ROOT / "trend_pipeline"
BRANDCONNECT_TOOL_DIR = PROJECT_ROOT / "brandconnect_link_tool"
KEYWORDS_FILE = TREND_PIPELINE_DIR / "trend_analysis" / "keywords_for_brandconnect.txt"

DEFAULT_CREATOR_ID = "971564859961248"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("브랜드커넥트 링크 생성기")
        self.geometry("760x580")
        self.log_queue = queue.Queue()
        self.creator_id_var = tk.StringVar(value=DEFAULT_CREATOR_ID)

        self._build_widgets()
        self.after(150, self._drain_log_queue)
        self.log("준비 완료. 1) → 2) → 3) 순서로 눌러주세요.")

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

        self.log_box = scrolledtext.ScrolledText(self, height=30, font=("Menlo", 11))
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
        self.log("\n=== 3) 링크 생성을 새 터미널 창에서 시작합니다 ===")
        self.log("(캡차나 화면 요소를 못 찾는 경우 그 터미널 창에서 직접 진행해주세요.)")

        py = sys.executable
        cmd_str = (
            f"cd {shlex.quote(str(BRANDCONNECT_TOOL_DIR))} && "
            f"{shlex.quote(py)} brandconnect_link_generator.py "
            f"--creator-id {shlex.quote(creator_id)} "
            f"--keywords-file {shlex.quote(str(KEYWORDS_FILE))}"
        )
        # AppleScript 문자열 안에 들어가므로 큰따옴표를 이스케이프
        applescript = f'tell application "Terminal" to do script "{cmd_str}"'
        try:
            subprocess.run(["osascript", "-e", applescript], check=True)
            self.log("터미널 창을 열었습니다.")
        except Exception as e:
            self.log(f"[오류] 터미널을 열지 못했습니다: {e}")
            messagebox.showerror("오류", f"터미널을 여는 데 실패했습니다:\n{e}")


if __name__ == "__main__":
    App().mainloop()
