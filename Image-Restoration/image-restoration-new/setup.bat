@echo off
setlocal
cd /d "%~dp0"

echo Setting up the image restoration app.
echo Steps that were already done are skipped.
echo.

rem --- Git is needed to fetch DeOldify and Real-ESRGAN ---
git --version >nul 2>&1
if errorlevel 1 (
    echo Git was not found. Install it from git-scm.com and run this again.
    goto fail
)

rem --- Find an existing local environment, or create one ---
set PY=
if exist "venv\Scripts\python.exe" set PY=venv\Scripts\python.exe
if exist "myenv\Scripts\python.exe" set PY=myenv\Scripts\python.exe

if not defined PY (
    py -3.10 --version >nul 2>&1
    if errorlevel 1 (
        echo Python 3.10 was not found. Install it from python.org and run this again.
        goto fail
    )
    echo Creating the virtual environment in the venv folder.
    py -3.10 -m venv venv
    if errorlevel 1 goto fail
    set PY=venv\Scripts\python.exe
)

rem --- Python packages, only for the venv this script creates ---
if "%PY%"=="venv\Scripts\python.exe" if not exist "venv\.requirements_ok" (
    echo Installing Python packages. This downloads a few GB and can take a while.
    "%PY%" -m pip install --upgrade pip
    if errorlevel 1 goto fail
    "%PY%" -m pip install torch==1.11.0+cu113 torchvision==0.12.0+cu113 --extra-index-url https://download.pytorch.org/whl/cu113
    if errorlevel 1 goto fail
    "%PY%" -m pip install -r requirements.txt
    if errorlevel 1 goto fail
    echo ok> "venv\.requirements_ok"
)

rem --- DeOldify and Real-ESRGAN, at the versions the app was built with ---
if not exist "DeOldify\deoldify" (
    echo Cloning DeOldify.
    git clone https://github.com/jantic/DeOldify.git DeOldify
    if errorlevel 1 goto fail
    git -C DeOldify checkout 5f86c28
    if errorlevel 1 goto fail
)
if not exist "Real-ESRGAN\realesrgan" (
    echo Cloning Real-ESRGAN.
    git clone https://github.com/xinntao/Real-ESRGAN.git Real-ESRGAN
    if errorlevel 1 goto fail
    git -C Real-ESRGAN checkout a4abfb2
    if errorlevel 1 goto fail
)

rem Real-ESRGAN generates realesrgan\version.py while installing, so install it once.
if not exist "Real-ESRGAN\realesrgan\version.py" (
    echo Installing Real-ESRGAN.
    "%PY%" -m pip install --no-deps -e Real-ESRGAN
    if errorlevel 1 goto fail
)

rem --- Model weights ---
"%PY%" download_models.py
if errorlevel 1 goto fail

echo.
echo Setup finished.
if "%1"=="" pause
exit /b 0

:fail
echo.
echo Setup stopped because of an error, see the messages above.
pause
exit /b 1
