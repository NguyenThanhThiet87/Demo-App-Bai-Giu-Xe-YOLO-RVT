import os
import sys
import subprocess

def create_desktop_shortcut(base_dir):
    if sys.platform == 'win32':
        import tempfile
        bat_path = os.path.join(base_dir, "run_app.bat")
        vbs_code = f"""
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = oWS.ExpandEnvironmentStrings("%USERPROFILE%\\Desktop\\AI Parking.lnk")
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{bat_path}"
oLink.WorkingDirectory = "{base_dir}"
oLink.Description = "AI Parking Management System"
oLink.IconLocation = "{base_dir}\\logo\\logo.ico"
oLink.Save
"""
        try:
            vbs_path = os.path.join(tempfile.gettempdir(), "create_ai_parking_shortcut.vbs")
            with open(vbs_path, "w", encoding="utf-8") as f:
                f.write(vbs_code)
            subprocess.run(["cscript.exe", "//Nologo", vbs_path], creationflags=subprocess.CREATE_NO_WINDOW)
            os.remove(vbs_path)
        except Exception:
            pass
            
    else:
        sh_path = os.path.join(base_dir, "run_app.sh")
        desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(desktop_dir):
            desktop_dir = os.path.join(os.path.expanduser("~"), "Bàn làm việc")
            
        if os.path.exists(desktop_dir):
            shortcut_path = os.path.join(desktop_dir, "AI_Parking.desktop")
            desktop_content = f"""[Desktop Entry]
Name=AI Parking
Exec=bash "{sh_path}"
Path={base_dir}
Type=Application
Terminal=false
Categories=Utility;
Icon={base_dir}/logo/logo.png 
"""
            try:
                with open(shortcut_path, "w", encoding="utf-8") as f:
                    f.write(desktop_content)
                os.chmod(shortcut_path, 0o755)
            except Exception:
                pass
