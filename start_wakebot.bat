@echo off
:: Navigate to the directory where this script is located
cd /d "%~dp0"

:: Activate the specific virtual environment for this project
if exist "wakebot_env\Scripts\activate.bat" (
    call wakebot_env\Scripts\activate.bat
)

:: ============================================================
:: API KEY SETUP (choose one method):
::
:: METHOD 1 (Recommended - Secure):
::   python -m wakebot credentials set GEMINI_API_KEY your_key
::
:: METHOD 2 (Developer):
::   Copy .env.example to .env and fill in your key
::
:: METHOD 3 (Legacy - NOT recommended):
::   Uncomment the line below (key will be in plaintext!)
::   set GEMINI_API_KEY=your_actual_api_key_here
:: ============================================================

:: Run the Audio mode by default
python -m wakebot run audio

exit
