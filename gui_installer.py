import os
import sys
from installer_core.utils import hide_console_window, get_file_hash
from installer_core.shortcut import create_desktop_shortcut
from installer_core.splash import show_splash_and_run_main
from installer_core.gui import InstallerGUI

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.join(base_dir, "app")
    if not os.path.exists(app_dir):
        app_dir = base_dir
    req_path = os.path.join(app_dir, "requirements.txt")
    hash_path = os.path.join(base_dir, ".req_hash")
    main_script_path = os.path.join(app_dir, "main.py")

    # Kiểm tra xem requirements.txt đã được cài đặt ở lần trước chưa
    current_hash = get_file_hash(req_path)
    saved_hash = ""
    if os.path.exists(hash_path):
        try:
            with open(hash_path, "r") as f:
                saved_hash = f.read().strip()
        except:
            pass

    if current_hash and current_hash == saved_hash:
        # Đã cài xong -> Ẩn terminal và hiện màn hình chờ AI
        hide_console_window()
        
        # Đảm bảo khôi phục lại lối tắt nếu người dùng lỡ xoá
        desktop_dir = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop") if sys.platform == 'win32' else os.path.join(os.path.expanduser("~"), "Desktop")
        if sys.platform == 'win32' and not os.path.exists(os.path.join(desktop_dir, "AI Parking.lnk")):
            create_desktop_shortcut(base_dir)
        elif sys.platform != 'win32' and not os.path.exists(os.path.join(desktop_dir, "AI_Parking.desktop")):
            create_desktop_shortcut(base_dir)
            
        show_splash_and_run_main(app_dir, main_script_path)
        sys.exit(0)

    # Nếu chưa cài hoặc requirements.txt có thay đổi -> Mở GUI Installer
    app = InstallerGUI(base_dir, app_dir, req_path, main_script_path, hash_path)
    app.mainloop()

if __name__ == "__main__":
    main()
