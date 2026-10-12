@echo off
rem Starts the web app. Works from any folder because it uses the location of this file.
cd /d "%~dp0"

rem If anything needed is missing, run the one-time setup first.
set NEED_SETUP=0
if not exist "%~dp0venv\Scripts\python.exe" if not exist "%~dp0myenv\Scripts\python.exe" set NEED_SETUP=1
if not exist "%~dp0DeOldify\deoldify" set NEED_SETUP=1
if not exist "%~dp0Real-ESRGAN\realesrgan" set NEED_SETUP=1
if not exist "%~dp0models\RealESRGAN_x4plus.pth" set NEED_SETUP=1
if not exist "%~dp0models\GFPGANv1.4.pth" set NEED_SETUP=1
if not exist "%~dp0models\ColorizeStable_gen.pth" set NEED_SETUP=1

if "%NEED_SETUP%"=="1" (
    echo Some required files are missing, running setup first.
    call "%~dp0setup.bat" fromrun
    if errorlevel 1 exit /b 1
)

rem DeOldify and Real-ESRGAN sit next to app.py, so Python needs their paths.
set PYTHONPATH=%~dp0DeOldify;%~dp0Real-ESRGAN

rem Use a local virtual environment if there is one, otherwise whatever "python" is on PATH.
set PY=python
if exist "%~dp0venv\Scripts\python.exe" set PY="%~dp0venv\Scripts\python.exe"
if exist "%~dp0myenv\Scripts\python.exe" set PY="%~dp0myenv\Scripts\python.exe"

%PY% app.py
pause
