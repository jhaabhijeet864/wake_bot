"""
WakeBot - Clap-Controlled System Automation

Usage:
    python main.py           # Run with terminal output
    pythonw wakebot.pyw      # Run as background service (Windows)
"""

import sys
import time

# Add src to path
sys.path.insert(0, '.')

from src.config import load_config
from src.logger import WakeBotLogger
from src.audio_engine import AudioStream
from src.clap_detector import ClapDetector
from src.voice_detector import VoiceDetector
from wakebot.core.actions import WakeBotActions


def print_banner():
    """Print startup banner"""
    banner = """
    ╔═══════════════════════════════════════╗
    ║          WakeBot v1.0                 ║
    ║    Clap-Controlled System Automation  ║
    ╚═══════════════════════════════════════╝
    
    Commands:
      • Single Clap  → Welcome Home (Wake + VS Code + Music)
      • Double Clap  → Goodnight (Pause Music + Screen Off)
    
    Press Ctrl+C to exit
    """
    print(banner)


def main():
    """Main entry point"""
    # Load configuration
    config = load_config()
    logger = WakeBotLogger()
    
    # Initialize components
    audio_engine = AudioStream(
        chunk_size=config.chunk_size,
        sample_rate=config.sample_rate,
        channels=config.channels
    )
    
    clap_detector = ClapDetector(
        threshold=config.threshold,
        double_clap_window_ms=config.double_clap_window_ms
    )
    
    # Initialize voice detector (optional)
    voice_detector = None
    if config.voice_enabled:
        logger.info("Initializing voice detector...")
        voice_detector = VoiceDetector(
            model_path=config.model_path,
            wake_phrases=config.wake_phrases,
            sample_rate=config.sample_rate
        )
        if voice_detector.initialize():
            logger.info("Voice detector initialized successfully")
        else:
            logger.warning("Voice detector failed to initialize - continuing with clap only")
            voice_detector = None
    
    actions = WakeBotActions(logger=logger)
    
    # Print startup banner
    print_banner()
    
    # Start audio stream
    logger.info("Initializing microphone...")
    if not audio_engine.start_stream():
        logger.error("Failed to initialize microphone. Check permissions and device availability.")
        return
    
    logger.info("Microphone initialized successfully")
    logger.info("WakeBot is active and listening for claps...\n")
    
    # Main loop
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    try:
        while True:
            try:
                # Read audio chunk
                chunk = audio_engine.read_chunk()
                rms = audio_engine.calculate_rms(chunk)
                
                # Log RMS values if debugging enabled
                if config.log_rms_values:
                    logger.info(f"RMS: {rms:.0f}")
                
                # Process through clap detector
                action = clap_detector.process(rms)
                
                # Process through voice detector if available
                is_voice = False
                if voice_detector:
                    voice_action = voice_detector.process_from_rms(audio_engine.last_chunk, rms)
                    if voice_action:
                        action = voice_action
                        is_voice = True
                
                # Execute actions
                if action == "SINGLE":
                    if is_voice:
                        logger.info("Voice Command Detected: Waking Screen")
                    else:
                        logger.clap_detected("Single Clap", rms)
                    actions.welcome_home()
                elif action == "DOUBLE":
                    logger.clap_detected("Double Clap", rms)
                    actions.goodnight()
                
                # Reset error counter on success
                consecutive_errors = 0
                
                # Small delay to prevent CPU spinning
                time.sleep(0.01)
                
            except KeyboardInterrupt:
                raise
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error: {e}")
                
                # If too many errors, try restarting stream
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"Multiple consecutive errors. Attempting stream restart...")
                    if audio_engine.restart_stream():
                        logger.info("Stream restarted successfully")
                        consecutive_errors = 0
                    else:
                        logger.error("Failed to restart stream. Waiting before retry...")
                        time.sleep(2)
                        consecutive_errors = 0
                else:
                    time.sleep(0.1)  # Brief pause before retry
                    
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        audio_engine.stop_stream()
        if voice_detector:
            voice_detector.stop()
        logger.info("WakeBot stopped.")


if __name__ == "__main__":
    main()
