#!/bin/bash
echo "Setting up WakeBot..."

# Install PortAudio
if [[ "$OSTYPE" == "darwin"* ]]; then
    brew install portaudio
else
    sudo apt-get install -y libasound-dev portaudio19-dev
fi

python -m venv wakebot_env
source wakebot_env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Setup complete! Run 'python calibrate.py' first."
