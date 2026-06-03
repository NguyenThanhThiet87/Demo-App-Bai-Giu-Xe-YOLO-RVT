@echo off
setlocal enabledelayedexpansion
title AI Parking - Auto Installer ^& Runner

set "MINICONDA_DIR=%~dp0miniconda"
set "PYTHON_EXE=%MINICONDA_DIR%\python.exe"

:: Tu dong phat hien cau truc thu muc (De rieng trong thu muc "app" hoac de chung voi bat)
if exist "%~dp0app\main.py" (
    set "APP_DIR=%~dp0app"
    echo [+] Phat hien ma nguon nam trong thu muc: \app
) else (
    set "APP_DIR=%~dp0"
    echo [+] Su dung thu muc hien tai lam thu muc ma nguon
)

echo ====================================================================
echo             AI PARKING MANAGEMENT SYSTEM - KHOI TONG TU DONG
echo ====================================================================
echo.

:: 1. Kiem tra neu moi truong miniconda da ton tai
if exist "%PYTHON_EXE%" (
    echo [+] Da tim thay moi truong Python cuc bo. Dang khoi chay ung dung...
    goto RUN_APP
)

echo [-] Chua co moi truong Python cuc bo. Dang bat dau thiet lap...
echo [*] Dang tai xuong Miniconda (khoang 70MB)...
powershell -Command "Invoke-WebRequest -Uri 'https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe' -OutFile 'miniconda_installer.exe' -UserAgent 'Mozilla/5.0'"

if not exist "miniconda_installer.exe" (
    echo [!] Loi: Khong the tai xuong Miniconda. Vui long kiem tra ket noi Internet.
    pause
    exit /b 1
)

echo [*] Dang cai dat Miniconda am tham vao thu muc: %MINICONDA_DIR%
start /wait "" miniconda_installer.exe /RegisterPython=0 /S /D=%MINICONDA_DIR%
del miniconda_installer.exe

if not exist "%PYTHON_EXE%" (
    echo [!] Loi: Cai dat Miniconda that bai.
    pause
    exit /b 1
)

echo [+] Cai dat Miniconda thanh cong!
echo [*] Dang cai dat cac thu vien phu thuoc tu requirements.txt...
"%MINICONDA_DIR%\Scripts\pip.exe" install -r "%APP_DIR%\requirements.txt"

if %ERRORLEVEL% neq 0 (
    echo [!] Loi: Khong the cai dat cac thu vien phu thuoc.
    pause
    exit /b 1
)

echo [+] Cai dat thu vien hoan tat!
echo.

:RUN_APP
echo [*] Dang chay ung dung AI Parking...
cd /d "%APP_DIR%"
"%PYTHON_EXE%" main.py
if %ERRORLEVEL% neq 0 (
    echo [!] Ung dung da dung lai voi loi: %ERRORLEVEL%.
    pause
)
