# WakeBot - Clap-Controlled System Automation

A Python-based background service that listens for clap patterns through your laptop microphone and performs system automation actions.

## Features

- **Single Clap**: Wake the screen (simulates keypress)
- **Double Clap**: Open YouTube in your default browser
- **Triple Clap**: Toggle the bot on/off (safe mode)
- **Robust Error Recovery**: Automatically handles microphone disconnections and stream errors
- **Calibration Tool**: Built-in calibration for optimal threshold detection
- **Configurable**: JSON-based configuration file
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Installation

### Windows

1. **Install Python** (3.8 or higher) from [python.org](https://www.python.org/downloads/)

2. **Run the setup script**:
   ```batch
   setup.bat
   ```

3. **Activate the virtual environment**:
   ```batch
   wakebot_env\Scripts\activate
   ```

### macOS / Linux

1. **Install system dependencies**:
   ```bash
   # macOS (requires Homebrew)
   brew install portaudio
   
   # Linux (Debian/Ubuntu)
   sudo apt-get install -y libasound-dev portaudio19-dev
   ```

2. **Run the setup script**:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Activate the virtual environment**:
   ```bash
   source wakebot_env/bin/activate
   ```

## Quick Start

### 1. Calibration (Required)

**Important**: You must run calibration first to set the correct threshold for your environment.

```bash
python calibrate.py
```

**Calibration Instructions**:
1. Run the script
2. Sit quietly for 5 seconds (observe ambient RMS values)
3. Clap loudly 5 times with 2-second gaps
4. Press `Ctrl+C` to stop
5. Note the recommended threshold value
6. Update `wakebot_config.json` with the recommended threshold

### 2. Run WakeBot

**With terminal output** (recommended for first run):
```bash
python main.py
```

**Background mode** (Windows, no console window):
```bash
pythonw wakebot.pyw
```

## Configuration

Configuration is stored in `wakebot_config.json` (auto-generated on first run).

### Configuration Options

```json
{
    "chunk_size": 1024,              // Audio buffer size
    "sample_rate": 44100,            // Audio sample rate
    "channels": 1,                   // Mono audio
    "threshold": 3000,               // RMS threshold for clap detection (CALIBRATE THIS!)
    "cooldown_ms": 100,              // Echo rejection period after clap
    "double_clap_window_ms": 500,    // Max time between claps for double clap
    "triple_clap_window_ms": 700,    // Max time between claps for triple clap
    "youtube_url": "https://www.youtube.com",
    "wake_key": "shift",             // Key to press for wake action
    "start_active": true,            // Initial active state
    "log_rms_values": false          // Enable RMS debugging output
}
```

### Updating Configuration

1. Edit `wakebot_config.json` directly, or
2. Modify the defaults in `src/config.py` and restart WakeBot

## Usage

### Commands

- **Single Clap**: Wakes the screen by simulating a `Shift` keypress
- **Double Clap**: Opens YouTube (or configured URL) in your default browser
- **Triple Clap**: Toggles the bot between active and paused states

### Status Indicators

The terminal will show colored status messages:
- **CYAN**: Informational messages
- **GREEN**: Clap detection and active status
- **YELLOW**: Action execution
- **RED**: Errors and paused status

Example output:
```
[12:34:56] INFO: Microphone initialized successfully
[12:34:56] STATUS: WakeBot is ACTIVE
[12:35:01] CLAP: Single (RMS: 4520)
[12:35:01] ACTION: Wake Screen
```

## Troubleshooting

### Microphone Not Detected

**Problem**: WakeBot cannot access the microphone.

**Solutions**:
- **Windows**: Check Privacy Settings → Microphone → Allow apps to access microphone
- **macOS**: System Preferences → Security & Privacy → Microphone → Enable Python
- **Linux**: Check microphone permissions and ALSA configuration
- Ensure no other application is exclusively using the microphone

### Claps Not Registering

**Problem**: Claps are not being detected.

**Solutions**:
1. Run `calibrate.py` again and ensure you're clapping loudly
2. Lower the `threshold` value in `wakebot_config.json` (try 70-80% of current value)
3. Check microphone volume/levels in system settings
4. Ensure you're in a quiet environment during testing
5. Try clapping closer to the microphone

### False Positives

**Problem**: WakeBot triggers on background noise or unintended sounds.

**Solutions**:
1. Run `calibrate.py` to recalculate threshold
2. Increase the `threshold` value in `wakebot_config.json`
3. Reduce background noise in your environment
4. Ensure microphone is not too sensitive in system settings

### Bot Doesn't Wake Screen

**Problem**: Single clap doesn't wake the display.

**Solutions**:
- Check power settings: Ensure display can wake from sleep (not deep sleep)
- Verify `wake_key` in configuration (try "shift", "ctrl", or "space")
- Ensure WakeBot is running and active (check for "ACTIVE" status)
- Test with double/triple clap to verify bot is functioning

### Stream Errors / Auto-Restart

**Problem**: See "Stream read error" or "Failed to restart stream" messages.

**Solutions**:
- This is normal when headphones are plugged/unplugged
- WakeBot will automatically attempt to restart the stream
- If errors persist, restart WakeBot manually
- Check that microphone device is not being used by another application

### Background Mode Not Working

**Problem**: `wakebot.pyw` doesn't run silently on Windows.

**Solutions**:
- Use `pythonw` (not `python`) to run `.pyw` files
- Create a shortcut to `wakebot.pyw` and set it to run with Pythonw
- For Linux/macOS, use `nohup` or system service manager

## Architecture

### Project Structure

```
wakebot/
├── main.py              # Entry point with terminal
├── wakebot.pyw          # Entry point for background (Windows)
├── calibrate.py         # Standalone calibration tool
├── config.py            # Configuration dataclass and loader
├── wakebot_config.json  # User configuration (generated)
├── src/
│   ├── __init__.py
│   ├── audio_engine.py  # PyAudio stream handling
│   ├── clap_detector.py # State machine pattern recognition
│   ├── actions.py       # System automation actions
│   └── logger.py        # Colored terminal logging
├── requirements.txt     # Python dependencies
├── setup.bat            # Windows setup script
├── setup.sh             # Linux/Mac setup script
└── README.md            # This file
```

### Module Overview

- **audio_engine.py**: Handles microphone stream with automatic error recovery
- **clap_detector.py**: State machine for pattern recognition (IDLE → COOLDOWN → WAITING_*)
- **actions.py**: System automation (keypress, browser, toggle)
- **logger.py**: Colored terminal output using colorama
- **config.py**: Centralized configuration management

## System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows 10+, macOS 10.14+, or Linux
- **Audio**: Microphone access permissions enabled
- **Power Settings**: Display should be configured to wake from sleep (not deep sleep)

## Dependencies

- `pyaudio`: Audio stream capture (requires PortAudio)
- `numpy`: Audio signal processing (RMS calculation)
- `pyautogui`: System automation (keypress simulation)
- `colorama`: Colored terminal output

## Development

### Running Tests

Test each module independently:

1. **Audio Engine**: Run `calibrate.py` to verify microphone access
2. **Clap Detector**: Enable `log_rms_values` in config and observe detection
3. **Actions**: Manually test wake screen, browser, and toggle

### Adding Custom Actions

To add custom actions:

1. Extend `WakeBotActions` class in `src/actions.py`
2. Add detection state in `src/clap_detector.py` (if new pattern needed)
3. Wire action in `main.py` main loop

## Known Limitations

- Clap detection works best in quiet environments
- Very loud ambient noise may cause false positives
- Multiple microphones: Uses system default (no device selection UI)
- Windows background mode: Requires `pythonw` execution

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please feel free to submit issues or pull requests.

## Support

For issues, bugs, or feature requests, please open an issue on the project repository.

---

**Enjoy your clap-controlled automation! 👏**
