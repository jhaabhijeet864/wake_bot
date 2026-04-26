"""
WakeBot Unified CLI - Principal Architect Version
Main entry point for routing commands with support for 'run' sub-orchestration.
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="WakeBot: System automation via Audio and Vision triggers.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # --- RUN Sub-Orchestrator ---
    # This allows for the 'python -m wakebot run audio' syntax
    run_parser = subparsers.add_parser("run", help="Execute a detection engine")
    run_subparsers = run_parser.add_subparsers(dest="engine", help="Engines to run")
    
    # Run Audio
    run_audio_parser = run_subparsers.add_parser("audio", help="Start Audio Detection (Claps & Voice)")
    
    # Run Vision
    run_vision_parser = run_subparsers.add_parser("vision", help="Start Vision Detection (Camera)")

    # --- LEGACY/DIRECT Commands ---
    # Maintains compatibility for 'python -m wakebot audio'
    audio_parser = subparsers.add_parser("audio", help="Directly start Audio Detection")
    vision_parser = subparsers.add_parser("vision", help="Directly start Vision Detection")
    calibrate_parser = subparsers.add_parser("calibrate", help="Run the audio calibration tool")
    
    args = parser.parse_args()
    
    # ROUTING LOGIC
    # Determine the target engine (handles both 'run audio' and 'audio')
    target = None
    if args.command == "run":
        target = args.engine
    else:
        target = args.command

    # Execution
    if target == "audio":
        from wakebot.cli.audio_cmd import run_audio
        run_audio()
    elif target == "vision":
        from wakebot.cli.vision_cmd import run_vision
        run_vision()
    elif target == "calibrate":
        from wakebot.cli.calibrate_cmd import run_calibrate
        run_calibrate()
    else:
        # If 'run' was called without an engine, or no command at all
        if args.command == "run" and not args.engine:
            print("\n[!] Error: Please specify an engine to run (audio|vision)")
            run_parser.print_help()
        else:
            parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
