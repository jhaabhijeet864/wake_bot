"""
WakeBot Background Service Entry Point (Windows)

This file runs WakeBot in the background without showing a console window.
Use pythonw wakebot.pyw to run silently.
"""

import sys
import os

# Redirect stdout/stderr to prevent console window (Windows)
if sys.platform == "win32":
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

# Import and run main
import main

if __name__ == "__main__":
    main.main()
