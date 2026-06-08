import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import os
import subprocess
from .utils import hide_console_window, get_file_hash
from .shortcut import create_desktop_shortcut

class InstallerGUI(tk.Tk):
    def __init__(self, base_dir, app_dir, req_path, main_script_path, hash_path):
        super().__init__()
        
        self.base_dir = base_dir
        self.app_dir = app_dir
        self.req_path = req_path
        self.main_script_path = main_script_path
        self.hash_path = hash_path
        
        hide_console_window()
        
        self.title("AI Parking - Trình Cài Đặt & Khởi Chạy")
        self.geometry("650x450")
        self.configure(padx=20, pady=20)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.lbl_title = ttk.Label(self, text="AI PARKING MANAGEMENT SYSTEM", font=("Helvetica", 14, "bold"))
        self.lbl_title.pack(pady=(0, 5))

        self.lbl_status = ttk.Label(self, text="Đang chuẩn bị cài đặt...", font=("Helvetica", 10))
        self.lbl_status.pack(pady=(0, 10), anchor="w")

        self.progress = ttk.Progressbar(self, orient="horizontal", length=610, mode="indeterminate")
        self.progress.pack(fill="x", pady=5)

        self.log_frame = ttk.Frame(self)
        self.log_frame.pack(fill="both", expand=True, pady=10)
        
        self.log_area = tk.Text(self.log_frame, height=15, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 9), wrap="word")
        self.log_area.pack(side="left", fill="both", expand=True)
        
        self.scrollbar = ttk.Scrollbar(self.log_frame, command=self.log_area.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.log_area.config(yscrollcommand=self.scrollbar.set)

        self.btn_frame = ttk.Frame(self)
        self.btn_frame.pack(fill="x", pady=5)
        
        self.btn_run = ttk.Button(self.btn_frame, text="Khởi chạy Ứng dụng", command=self.run_app, state="disabled")
        self.btn_run.pack(side="right", padx=5)
        
        self.btn_close = ttk.Button(self.btn_frame, text="Thoát", command=self.destroy)
        self.btn_close.pack(side="right", padx=5)

        self.process = None
        self.is_installing = True

        self.start_installation()

    def write_log(self, text):
        self.log_area.insert(tk.END, text)
        self.log_area.see(tk.END)

    def start_installation(self):
        if not os.path.exists(self.req_path):
            self.write_log(f"[!] Không tìm thấy {self.req_path}\nBỏ qua bước cài đặt thư viện.\n")
            self._installation_complete(True)
            return

        self.progress.start(10)
        self.lbl_status.config(text="Đang cài đặt thư viện phụ thuộc (pip install) - Vui lòng đợi...")
        
        threading.Thread(target=self._run_install_process, daemon=True).start()

    def _run_install_process(self):
        command = [sys.executable, "-m", "pip", "install", "-r", self.req_path]
        try:
            self.write_log(f"[*] Đang thực thi lệnh: {' '.join(command)}\n\n")
            
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW

            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace',
                creationflags=creationflags
            )

            for line in iter(self.process.stdout.readline, ''):
                self.after(0, self.write_log, line)

            self.process.stdout.close()
            self.process.wait()

            if self.process.returncode == 0:
                self.after(0, self._installation_complete, True)
            else:
                self.after(0, self._installation_complete, False)
                
        except Exception as e:
            self.after(0, self.write_log, f"\n[!] Lỗi ngoại lệ: {str(e)}\n")
            self.after(0, self._installation_complete, False)

    def _installation_complete(self, success):
        self.is_installing = False
        self.progress.stop()
        self.progress.config(mode="determinate", value=100)
        
        if success:
            self.lbl_status.config(text="Cài đặt hoàn tất thành công!", foreground="green")
            self.write_log("\n[+] HOÀN TẤT CÀI ĐẶT THƯ VIỆN!\n")
            
            try:
                current_hash = get_file_hash(self.req_path)
                if current_hash:
                    with open(self.hash_path, "w") as f:
                        f.write(current_hash)
            except:
                pass

            self.write_log("[*] Đang tạo biểu tượng ngoài Desktop (Shortcut)...\n")
            create_desktop_shortcut(self.base_dir)

            self.btn_run.config(state="normal")
            self.after(2000, self.run_app)
        else:
            self.lbl_status.config(text="Cài đặt thất bại. Vui lòng kiểm tra log bên trên.", foreground="red")

    def run_app(self):
        if not os.path.exists(self.main_script_path):
            messagebox.showerror("Lỗi", f"Không tìm thấy file: {self.main_script_path}")
            return
            
        self.lbl_status.config(text="Đang khởi chạy AI Parking...", foreground="blue")
        self.write_log(f"\n[*] Đang gọi: {self.main_script_path}\n")
        
        try:
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW
                
            subprocess.Popen(
                [sys.executable, self.main_script_path],
                cwd=self.app_dir,
                creationflags=creationflags
            )
            self.destroy()
        except Exception as e:
            self.write_log(f"\n[!] Lỗi khi chạy main.py: {str(e)}\n")

    def on_closing(self):
        if self.is_installing:
            if messagebox.askokcancel("Cảnh báo", "Đang cài đặt dở dang. Bạn có chắc chắn muốn thoát?"):
                if self.process:
                    try:
                        self.process.terminate()
                    except:
                        pass
                self.destroy()
        else:
            self.destroy()
