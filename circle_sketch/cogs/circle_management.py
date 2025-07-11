import logging
import queue
from logging.handlers import QueueHandler, QueueListener
# --- Logging Setup ---
log_queue = queue.Queue(-1)
queue_handler = QueueHandler(log_queue)
formatter = logging.Formatter('[%(levelname)s] %(asctime)s %(name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
queue_listener = QueueListener(log_queue, stream_handler)
logging.basicConfig(level=logging.INFO, handlers=[queue_handler])
logger = logging.getLogger('circle_sketch')
queue_listener.start()

import discord
from discord import app_commands, Interaction
from discord.ext import commands
from ..storage.storage import Storage
from ..config import CIRCLE_LIMIT, GAME_CHANNEL_ID
from ..gallery.gallery import make_gallery_image, make_theme_announcement_image
from ..prompts import PROMPT_LIST
import random
import datetime

# --- Admin Check ---
def is_admin(interaction: Interaction):
    return interaction.user.guild_permissions.administrator

class CircleManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="join_circle", description="Join the persistent player circle.")
    async def join_circle(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        username = interaction.user.display_name
        circle = Storage.get_player_circle()
        if user_id in circle:
            await interaction.followup.send("You are already in the circle.", ephemeral=True)
            logger.info(f"User {user_id} attempted to join but is already in the circle.")
            return
        if len(circle) >= CIRCLE_LIMIT:
            await interaction.followup.send(f"Sorry, the circle is full ({CIRCLE_LIMIT}/10). A spot will open when someone leaves.", ephemeral=True)
            logger.warning("Circle is full. User could not join.")
            return
        circle.append(user_id)
        Storage.set_player_circle(circle)
        channel = self.bot.get_channel(GAME_CHANNEL_ID)
        await channel.send(f"<@{user_id}> joined the Circle!")
        logger.info(f"User {user_id} joined the circle.")
        await interaction.followup.send(f"Welcome! The circle now has {len(circle)}/{CIRCLE_LIMIT} players.", ephemeral=True)
        state = Storage.get_game_state()
        if state and 'theme' in state:
            if user_id not in state.get('user_ids', []):
                state['user_ids'].append(user_id)
                Storage.set_game_state(state)
            try:
                user = await self.bot.fetch_user(user_id)
                await user.send(f"A game is currently running! Today's drawing theme: **{state['theme']}**. Please reply with your drawing as an image attachment.")
            except Exception as e:
                logger.error(f"Failed to DM user {user_id}: {e}")

    @app_commands.command(name="leave_circle", description="Leave the persistent player circle.")
    async def leave_circle(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        username = interaction.user.display_name
        circle = Storage.get_player_circle()
        if user_id not in circle:
            await interaction.followup.send("You are not in the circle.", ephemeral=True)
            return
        circle.remove(user_id)
        Storage.set_player_circle(circle)
        await interaction.followup.send("You have left the circle.", ephemeral=True)

    @app_commands.command(name="list_circle", description="List current members of the player circle.")
    async def list_circle(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        circle = Storage.get_player_circle()
        if not circle:
            await interaction.followup.send("The player circle is currently empty.", ephemeral=True)
            return
        members = []
        for user_id in circle:
            member = interaction.guild.get_member(user_id)
            if member:
                members.append(f"{member.display_name} ({user_id})")
            else:
                members.append(f"<@{user_id}>")
        await interaction.followup.send(f"Current Players ({len(circle)}/{CIRCLE_LIMIT}): {', '.join(members)}", ephemeral=True)

    @app_commands.command(name="reset_circle", description="[Admin] Reset the player circle.")
    @app_commands.check(is_admin)
    async def reset_circle(self, interaction: Interaction):
        class Confirm(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)
                self.value = None
            @discord.ui.button(label="Yes. I am sure.", style=discord.ButtonStyle.danger)
            async def confirm(self, interaction2: Interaction, button: discord.ui.Button):
                Storage.set_player_circle([])
                await interaction2.response.edit_message(content="Player circle has been reset.", view=None)
                self.value = True
                self.stop()
            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True
                try:
                    await self.message.edit(content="Reset cancelled (no confirmation received).", view=None)
                except Exception:
                    pass
        view = Confirm()
        msg = await interaction.response.send_message("Are you sure you want to reset the player circle?", ephemeral=True, view=view)
        view.message = msg

    @reset_circle.error
    async def reset_circle_error(self, interaction: Interaction, error):
        if isinstance(error, app_commands.errors.CheckFailure):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CircleManagement(bot))
