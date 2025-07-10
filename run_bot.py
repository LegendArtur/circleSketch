"""
This file is a simple launcher for the CircleSketch bot.

Usage:
- If your host does not support running the bot as a package (with `python -m circle_sketch.main`),
  you can run this file directly with `python run_bot.py` from the project root.
- This will import and execute the bot from circle_sketch/main.py, allowing relative imports to work.
"""

from circle_sketch.main import *
