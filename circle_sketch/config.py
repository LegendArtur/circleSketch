# Configuration for CircleSketch bot

import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GAME_CHANNEL_ID = int(os.getenv('GAME_CHANNEL_ID', 0))
SCHEDULED_GAME_TIME = os.getenv('SCHEDULED_GAME_TIME', '20:00')
