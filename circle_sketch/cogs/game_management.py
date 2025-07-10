import discord
from discord import app_commands, Interaction
from discord.ext import commands
from ..storage.storage_sqlite import Storage
from ..config import GAME_CHANNEL_ID
from ..gallery.gallery import make_gallery_image, make_theme_announcement_image
from ..prompts import PROMPT_LIST
import random
import datetime

class GameManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="start_manual_game", description="Start a manual game (ends only when ended by the starter)")
    async def start_manual_game(self, interaction: Interaction):
        # ...existing logic for start_manual_game...
        pass

    @app_commands.command(name="end_manual_game", description="End the current manual game and post the gallery.")
    async def end_manual_game(self, interaction: Interaction):
        # ...existing logic for end_manual_game...
        pass

    @app_commands.command(name="reset_circle", description="[Admin] Reset the player circle.")
    async def reset_circle(self, interaction: Interaction):
        # ...existing logic for reset_circle...
        pass

async def setup(bot):
    await bot.add_cog(GameManagement(bot))
