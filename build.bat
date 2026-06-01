@echo off
title Building Auto Key Presser...
color 0A

echo Auto Key Presser - Build Tool
echo.

echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python not found. Install from https://python.org
    pause & exit /b 1
)
echo [OK] Python found.

echo.
echo [2/4] Installing dependencies...
py -m pip install pyinstaller pynput >nul 2>&1
echo [OK] Dependencies ready.

echo.
echo [3/4] Building AutoKeyPresser.exe (Portable)...
py -m PyInstaller --onefile --noconsole --name "AutoKeyPresser" ^
  --hidden-import pynput ^
  --hidden-import pynput.keyboard ^
  --hidden-import pynput._util.win32 ^
  --distpath output ^
  app.py

if not exist "output\AutoKeyPresser.exe" (
    echo.
    echo [!] Build failed. Check errors above.
    pause & exit /b 1
)
echo [OK] Portable EXE built at output\AutoKeyPresser.exe

echo.
echo [4/4] Looking for Inno Setup (for Installer)...

set INNO="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %INNO% (
    echo.
    echo [!] Inno Setup not found at default path.
    echo Download it from: https://jrsoftware.org/isdl.php
    echo Install it, then re-run this script.
    echo.
    echo [i] Your portable EXE is ready at output\AutoKeyPresser.exe
    echo You can use it directly without the installer.
    pause & exit /b 0
)

%INNO% installer.iss

if not exist "output\AutoKeyPresser_Setup.exe" (
    echo [!] Installer build failed.
    pause & exit /b 1
)

echo.
echo Done! Both outputs ready in output/ folder:
echo   - Portable: output\AutoKeyPresser.exe
echo   - Installer: output\AutoKeyPresser_Setup.exe
echo.
pause