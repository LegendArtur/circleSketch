"""
This file is a simple launcher for the CircleSketch bot.

Usage:
- If your host does not support running the bot as a package (with `python -m circle_sketch.main`),
  you can run this file directly with `python run_bot.py` from the project root.
- This will import and execute the bot from circle_sketch/main.py, allowing relative imports to work.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from circle_sketch.main import main

if __name__ == "__main__":
    main()
