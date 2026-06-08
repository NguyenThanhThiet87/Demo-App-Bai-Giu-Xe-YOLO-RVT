import tkinter as tk
from tkinter import ttk
import os
import sys
import subprocess

def show_splash_and_run_main(app_dir, main_script_path):
    splash = tk.Tk()
    splash.overrideredirect(True)
    
    width = 420
    height = 160
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width / 2) - (width / 2)
    y = (screen_height / 2) - (height / 2)
    splash.geometry(f'{int(width)}x{int(height)}+{int(x)}+{int(y)}')
    
    splash.configure(bg='#1e1e1e', highlightbackground='#00aa00', highlightthickness=2)
    
    lbl_title = tk.Label(splash, text="AI PARKING SYSTEM", font=("Helvetica", 14, "bold"), bg='#1e1e1e', fg='white')
    lbl_title.pack(pady=(35, 10))
    
    lbl_loading = tk.Label(splash, text="Đang tải các mô hình AI hạng nặng, vui lòng đợi...", font=("Helvetica", 10), bg='#1e1e1e', fg='#00ff00')
    lbl_loading.pack(pady=(0, 15))

    progress = ttk.Progressbar(splash, orient="horizontal", length=300, mode="indeterminate")
    progress.pack()
    progress.start(10)

    if os.path.exists(main_script_path):
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW
        subprocess.Popen(
            [sys.executable, main_script_path],
            cwd=app_dir,
            creationflags=creationflags
        )

    splash.after(5000, splash.destroy)
    splash.mainloop()
