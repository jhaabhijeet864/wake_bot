@echo off
:: Navigate to the directory where this script is located
cd /d "%~dp0"

:: Activate the specific virtual environment for this project
if exist "wakebot_env\Scripts\activate.bat" (
    call wakebot_env\Scripts\activate.bat
)

:: Set your Gemini API Key here for the AI Greeting
set GEMINI_API_KEY=your_actual_api_key_here

:: Run the Audio mode by default
python -m wakebot run audio

exit
