"""
블로그 원고 생성기 - 데스크탑 앱 (GUI)
==========================================

trend_pipeline/generate_blog_draft.py를 버튼 하나로 실행하는 작은 앱입니다.
기존 BrandConnectLinkGenerator 앱은 건드리지 않고 새로 만든 별도 프로그램입니다.
"""

import subprocess
import sys
import threading
import queue
from pathlib import Path

import tkinter as tk
from tkinter import scrolledtext, messagebox

BASE_DIR = Path(__file__).resolve().parent              # .../food_recommend/blog_generator_app
PROJECT_ROOT = BASE_DIR.parent                            # .../food_recommend
TREND_PIPELINE_DIR = PROJECT_ROOT / "trend_pipeline"
BLOG_DRAFTS_DIR = PROJECT_ROOT / "blog_drafts"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("애플소다 블로그 원고 생성기")
        self.geometry("720x560")
        self.log_queue = queue.Queue()
        self.top_n_var = tk.StringVar(value="")
        self.title_var = tk.StringVar(value="")
        self.last_output_path = None

        self._build_widgets()
        self.after(150, self._drain_log_queue)
        self.log("준비 완료. 먼저 trend_pipeline으로 키워드를 검증한 뒤 이 버튼을 눌러주세요.")

    # ---------- UI ----------
    def _build_widgets(self):
        form = tk.Frame(self)
        form.pack(fill="x", padx=10, pady=8)

        tk.Label(form, text="사용할 상위 키워드 개수 (비우면 전체):").grid(row=0, column=0, sticky="w", pady=4)
        tk.Entry(form, textvariable=self.top_n_var, width=10).grid(row=0, column=1, sticky="w", padx=6)

        tk.Label(form, text="포스팅 제목 (비우면 자동 생성):").grid(row=1, column=0, sticky="w", pady=4)
        tk.Entry(form, textvariable=self.title_var, width=50).grid(row=1, column=1, sticky="w", padx=6)

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=6)
        tk.Button(btn_frame, text="블로그 원고 생성 시작", width=24,
                  command=self.generate_blog).pack(side="left", padx=4)
        self.open_folder_btn = tk.Button(btn_frame, text="생성된 폴더 열기", width=20,
                                          command=self.open_output_folder, state="disabled")
        self.open_folder_btn.pack(side="left", padx=4)

        self.log_box = scrolledtext.ScrolledText(self, height=28, font=("Menlo", 11))
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

    # ---------- 동작 ----------
    def generate_blog(self):
        cmd = [sys.executable, "generate_blog_draft.py"]
        top_n = self.top_n_var.get().strip()
        if top_n:
            if not top_n.isdigit():
                messagebox.showwarning("입력 오류", "키워드 개수는 숫자로 입력해주세요.")
                return
            cmd += ["--top", top_n]
        title = self.title_var.get().strip()
        if title:
            cmd += ["--title", title]

        self.log("\n=== 블로그 원고 생성 시작 ===")

        def worker():
            self.log(f"$ {' '.join(cmd)}")
            try:
                proc = subprocess.Popen(
                    cmd, cwd=str(TREND_PIPELINE_DIR), stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, text=True, bufsize=1,
                )
                for line in proc.stdout:
                    self.log(line.rstrip())
                    if "저장 완료:" in line:
                        self.last_output_path = line.split("저장 완료:")[-1].strip()
                proc.wait()
                self.log(f"[종료 코드: {proc.returncode}]")
                if proc.returncode == 0:
                    self.open_folder_btn.config(state="normal")
            except Exception as e:
                self.log(f"[오류] {e}")

        threading.Thread(target=worker, daemon=True).start()

    def open_output_folder(self):
        try:
            subprocess.run(["open", str(BLOG_DRAFTS_DIR)], check=False)
        except Exception as e:
            self.log(f"[오류] 폴더를 열지 못했습니다: {e}")


if __name__ == "__main__":
    App().mainloop()
