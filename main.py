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
from src.actions import WakeBotActions


def print_banner():
    """Print startup banner"""
    banner = """
    ╔═══════════════════════════════════════╗
    ║          WakeBot v1.0                 ║
    ║    Clap-Controlled System Automation  ║
    ╚═══════════════════════════════════════╝
    
    Commands:
      • Single Clap  → Wake Screen
      • Double Clap  → Lock Screen
    
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
    
    actions = WakeBotActions(
        youtube_url=config.youtube_url,
        wake_key=config.wake_key,
        open_lock_screen=config.open_lock_screen
    )
    
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
                
                # Execute actions
                if action == "SINGLE":
                    logger.clap_detected("Single Clap", rms)
                    actions.wake_screen()
                elif action == "DOUBLE":
                    logger.clap_detected("Double Clap", rms)
                    actions.lock_screen()
                
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
        logger.info("WakeBot stopped.")


if __name__ == "__main__":
    main()
