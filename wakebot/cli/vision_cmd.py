"""
WakeBot Vision Command
Logic for running the camera-based presence detection bot.
"""

import time
import cv2
from wakebot.core import load_config, WakeBotLogger, WakeBotActions
from wakebot.triggers.vision.engine import CameraEngine
from wakebot.triggers.vision.detector import PersonDetector


def run_vision():
    """Run the camera presence loop"""
    config = load_config()
    logger = WakeBotLogger()
    
    # Initialize components
    camera_engine = CameraEngine(camera_index=config.camera_index)
    person_detector = PersonDetector()
    actions = WakeBotActions(logger=logger)
    
    print(f"""
    ╔═══════════════════════════════════════╗
    ║          WakeBot Vision Mode          ║
    ║    Camera Presence Detection Active   ║
    ╚═══════════════════════════════════════╝
    • Unlock on Detection: {config.vision_enabled}
    """)
    
    if not camera_engine.initialize():
        logger.error("Could not open camera.")
        return
        
    logger.info("Camera initialized. Monitoring presence...")
    
    try:
        while True:
            ret, frame = camera_engine.read_frame()
            if not ret:
                logger.error("Failed to read from camera")
                time.sleep(1)
                continue
                
            action = person_detector.process(frame)
            if action == "PERSON_DETECTED":
                actions.wake_monitor()
                
            # Wait to avoid high CPU usage
            time.sleep(0.2)
            
    except KeyboardInterrupt:
        logger.info("Stopping Vision Bot...")
    finally:
        camera_engine.release()
