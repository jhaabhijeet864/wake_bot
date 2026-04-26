"""
WakeBot Unified CLI
Main entry point for routing commands.
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="WakeBot: System automation via Audio and Vision triggers.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Audio Command
    audio_parser = subparsers.add_parser("audio", help="Start the Audio Detection Bot (Claps & Voice)")
    
    # Vision Command
    vision_parser = subparsers.add_parser("vision", help="Start the Vision Detection Bot (Camera Presence)")

    # Calibrate Command
    calibrate_parser = subparsers.add_parser("calibrate", help="Run the audio calibration tool")
    
    args = parser.parse_args()
    
    # Lazy imports to prevent dependency crashes for unused modules
    if args.command == "audio":
        from wakebot.cli.audio_cmd import run_audio
        run_audio()
    elif args.command == "vision":
        from wakebot.cli.vision_cmd import run_vision
        run_vision()
    elif args.command == "calibrate":
        from wakebot.cli.calibrate_cmd import run_calibrate
        run_calibrate()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
