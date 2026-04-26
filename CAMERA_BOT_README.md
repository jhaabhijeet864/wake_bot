# Camera Presence Bot

A Python script that monitors your webcam for human presence and automatically manages your screen lock:
- **Person detected** → Unlocks/wakes the screen
- **No person detected** → Puts system to sleep after threshold

## Features

- 🎥 Real-time face detection using OpenCV
- 🔓 Automatic screen unlock when you appear
- 😴 Automatic sleep mode when you leave
- ⚙️ Fully configurable via JSON config file
- 📊 Optional camera preview window
- 📝 Detection logging

## Requirements

- Python 3.7+
- Webcam/Camera
- Windows OS (for sleep functionality)

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r camera_requirements.txt
   ```

   Or install manually:
   ```bash
   pip install opencv-python numpy pyautogui
   ```

2. **Run the script:**
   ```bash
   python camera_presence_bot.py
   ```

## Configuration

Edit `camera_bot_config.json` to customize behavior:

```json
{
    "camera_index": 0,              // Camera device index (0 = default)
    "detection_interval": 2.0,       // Seconds between checks
    "no_person_threshold": 5,        // Checks before triggering sleep
    "min_face_size": [50, 50],       // Minimum face size to detect
    "scale_factor": 1.1,             // Detection sensitivity
    "min_neighbors": 5,              // Detection quality threshold
    "unlock_on_detect": true,        // Enable screen unlock
    "sleep_on_absence": true,        // Enable auto-sleep
    "show_preview": false,           // Show camera feed window
    "log_detections": true           // Print detection logs
}
```

### Key Settings

- **detection_interval**: How often to check for presence (in seconds)
  - Lower = more responsive, higher CPU usage
  - Higher = less responsive, lower CPU usage

- **no_person_threshold**: Number of consecutive "no person" detections before sleeping
  - Example: threshold=5, interval=2s → sleep after 10 seconds without detection

- **show_preview**: Set to `true` to see the camera feed with detection boxes
  - Press 'q' in the preview window to quit

## Usage

### Basic Usage
```bash
python camera_presence_bot.py
```

### With Camera Preview
Edit config and set `"show_preview": true`, then run:
```bash
python camera_presence_bot.py
```

### Stop the Bot
- Press `Ctrl+C` in the terminal
- Or press `q` in the preview window (if enabled)

## How It Works

1. **Initialization**: Opens camera and loads face detection model
2. **Monitoring Loop**:
   - Captures frame from camera
   - Detects faces using Haar Cascade classifier
   - If face detected → unlocks screen (simulates Shift key press)
   - If no face → increments counter
   - If counter reaches threshold → puts system to sleep
3. **Cleanup**: Releases camera on exit

## Troubleshooting

### Camera not opening
- Check if another application is using the camera
- Try changing `camera_index` in config (0, 1, 2, etc.)
- Verify camera permissions in Windows settings

### Not detecting faces
- Ensure good lighting
- Face the camera directly
- Adjust `scale_factor` and `min_neighbors` in config
- Lower `min_face_size` values
- Enable `show_preview` to see what the camera sees

### Screen not unlocking
- Ensure pyautogui is installed: `pip install pyautogui`
- Check Windows permissions for automation
- Try manually pressing Shift to verify screen responds

### System not sleeping
- Run as Administrator for sleep permissions
- Verify `sleep_on_absence` is `true` in config
- Check Windows power settings

## Advanced Usage

### Running in Background
To run without console window, rename to `.pyw`:
```bash
pythonw camera_presence_bot.py
```

Or create a shortcut and set to minimized.

### Auto-start on Login
1. Press `Win+R`, type `shell:startup`, press Enter
2. Create a shortcut to `camera_presence_bot.py`
3. Edit shortcut properties, set "Run: Minimized"

### Multiple Cameras
Create multiple config files for different cameras:
```bash
python camera_presence_bot.py camera_bot_config_front.json
python camera_presence_bot.py camera_bot_config_side.json
```

## Security & Privacy

⚠️ **CRITICAL SECURITY WARNINGS:**

- **NO AUTHENTICATION:** This bot uses basic face detection (Haar Cascades) which provides **NO REAL SECURITY**. It can be easily spoofed with a photograph or video of your face.
- **WAKE ONLY:** For safety, the 'unlock' feature has been modified to only **WAKE** the screen. It will NOT bypass your Windows login password or PIN. This ensures your computer remains secure if you have a password set.
- **PRIVACY:** This bot has continuous access to your camera while running. Although it processes frames locally and does not save images, you should be aware that the camera is active.
- **INPUT INJECTION:** The bot simulates mouse movements to wake the screen. While minimal, be aware that automated input can occasionally interfere with active applications.

**Privacy Notes:**
- Camera feed is processed locally only.
- No data is sent to external servers.
- No images/videos are saved.

## Performance Tips

- Increase `detection_interval` to reduce CPU usage
- Set `show_preview` to `false` for better performance
- Use lower camera resolution in code if needed
- Close other camera-using applications

## Compatibility

- **OS**: Windows 10/11 (sleep command is Windows-specific)
- **Python**: 3.7 or higher
- **Camera**: Any webcam compatible with OpenCV

## License

Free to use and modify.

## Support

For issues or questions, check:
1. This README troubleshooting section
2. OpenCV documentation: https://docs.opencv.org/
3. Windows power management settings
