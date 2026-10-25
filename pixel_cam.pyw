"""Pixel Cam — No Screen. Double-click to open (Windows)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pixelcam.app import main  # noqa: E402

if __name__ == "__main__":
    main()
