"""
WakeBot Unified CLI - Principal Architect Version
Main entry point for routing commands with support for 'run' sub-orchestration.
Includes: credentials management, startup registration, and system tray mode.
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
    run_subparsers.add_parser("audio", help="Start Audio Detection (Claps & Voice)")
    
    # Run Vision
    run_subparsers.add_parser("vision", help="Start Vision Detection (Camera)")

    # --- LEGACY/DIRECT Commands ---
    # Maintains compatibility for 'python -m wakebot audio'
    subparsers.add_parser("audio", help="Directly start Audio Detection")
    subparsers.add_parser("vision", help="Directly start Vision Detection")
    subparsers.add_parser("calibrate", help="Run the audio calibration tool")

    # --- SYSTEM TRAY ---
    subparsers.add_parser("tray", help="Launch WakeBot as a system tray application")

    # --- CREDENTIALS MANAGEMENT ---
    cred_parser = subparsers.add_parser("credentials", help="Manage API keys and credentials")
    cred_subparsers = cred_parser.add_subparsers(dest="cred_action", help="Credential actions")
    
    cred_set = cred_subparsers.add_parser("set", help="Store a credential securely")
    cred_set.add_argument("key", help="Credential name (e.g., GEMINI_API_KEY)")
    cred_set.add_argument("value", help="Credential value")
    
    cred_get = cred_subparsers.add_parser("get", help="Retrieve a stored credential")
    cred_get.add_argument("key", help="Credential name to retrieve")
    
    cred_del = cred_subparsers.add_parser("delete", help="Delete a stored credential")
    cred_del.add_argument("key", help="Credential name to delete")

    # --- STARTUP MANAGEMENT ---
    startup_parser = subparsers.add_parser("startup", help="Manage Windows startup registration")
    startup_parser.add_argument(
        "startup_action",
        choices=["enable", "disable", "status"],
        help="Enable, disable, or check startup registration"
    )
    
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
    elif target == "tray":
        from wakebot.core.tray import run_tray
        run_tray()
    elif target == "credentials":
        _handle_credentials(args)
    elif target == "startup":
        _handle_startup(args)
    else:
        # If 'run' was called without an engine, or no command at all
        if args.command == "run" and not args.engine:
            print("\n[!] Error: Please specify an engine to run (audio|vision)")
            run_parser.print_help()
        else:
            parser.print_help()
        sys.exit(1)


def _handle_credentials(args):
    """Route credential sub-commands."""
    from wakebot.core.credentials import get_credential, store_credential, delete_credential

    if args.cred_action == "set":
        if store_credential(args.key, args.value):
            print(f"✅ Credential '{args.key}' stored securely.")
        else:
            print(f"❌ Failed to store credential '{args.key}'.")
            sys.exit(1)
    elif args.cred_action == "get":
        value = get_credential(args.key)
        if value:
            # Mask the value for security (show first 4 + last 4 chars)
            if len(value) > 12:
                masked = value[:4] + "*" * (len(value) - 8) + value[-4:]
            else:
                masked = "****"
            print(f"🔑 {args.key} = {masked}")
        else:
            print(f"❌ Credential '{args.key}' not found.")
            sys.exit(1)
    elif args.cred_action == "delete":
        if delete_credential(args.key):
            print(f"🗑️  Credential '{args.key}' deleted.")
        else:
            print(f"❌ Failed to delete credential '{args.key}'.")
            sys.exit(1)
    else:
        print("\n[!] Error: Please specify an action (set|get|delete)")
        sys.exit(1)


def _handle_startup(args):
    """Route startup sub-commands."""
    from wakebot.core.startup import register_startup, unregister_startup, is_registered

    if args.startup_action == "enable":
        if register_startup():
            print("✅ WakeBot will start automatically with Windows.")
        else:
            print("❌ Failed to register startup.")
            sys.exit(1)
    elif args.startup_action == "disable":
        if unregister_startup():
            print("✅ WakeBot removed from Windows startup.")
        else:
            print("❌ Failed to unregister startup.")
            sys.exit(1)
    elif args.startup_action == "status":
        if is_registered():
            print("✅ WakeBot IS registered for Windows startup.")
        else:
            print("ℹ️  WakeBot is NOT registered for Windows startup.")


if __name__ == "__main__":
    main()
