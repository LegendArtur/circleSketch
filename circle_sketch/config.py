# Configuration for CircleSketch bot

import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GAME_CHANNEL_ID = int(os.getenv('GAME_CHANNEL_ID', 0))
SCHEDULED_GAME_TIME = os.getenv('SCHEDULED_GAME_TIME', '20:00')
CIRCLE_LIMIT = 10

# Setup rotating file logging for production
log_file = os.getenv('LOG_FILE', 'bot.log')
file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
file_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
logging.getLogger().addHandler(file_handler)
