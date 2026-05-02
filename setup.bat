@echo off
echo ==========================================
echo    WAKEBOT v2.1.0 SETUP & ENVIRONMENT
echo ==========================================

:: Check if venv exists
if not exist "wakebot_env" (
    echo [1/3] Creating virtual environment...
    python -m venv wakebot_env
) else (
    echo [1/3] Virtual environment already exists.
)

:: Activate and Upgrade Pip
echo [2/3] Upgrading pip...
call wakebot_env\Scripts\activate
python -m pip install --upgrade pip

:: Install Dependencies
echo [3/3] Installing dependencies...
:: Use nvidia-ml-py instead of pynvml to avoid deprecation warnings
pip install nvidia-ml-py onnxruntime-gpu sounddevice google-generativeai vosk
pip install -r requirements.txt

echo.
echo ==========================================
echo    SETUP COMPLETE! 
echo ==========================================
echo 🚀 To start the unified engine:
echo    python -m wakebot run vision
echo.
pause
