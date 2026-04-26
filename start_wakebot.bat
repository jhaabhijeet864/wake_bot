@echo off
:: Navigate to the directory where this script is located
cd /d "%~dp0"

:: Activate the specific virtual environment for this project
if exist "wakebot_env\Scripts\activate.bat" (
    call wakebot_env\Scripts\activate.bat
)

:: Run the Audio mode by default as it is the primary interface
:: Using python (instead of pythonw) because run_hidden.vbs handles the window hiding
python -m wakebot audio

exit
