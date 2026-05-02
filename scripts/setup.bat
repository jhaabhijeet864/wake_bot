@echo off
echo Setting up WakeBot...
python -m venv wakebot_env
call wakebot_env\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
echo Setup complete! Run 'python calibrate.py' first.
pause
