import discord
from discord import app_commands, Interaction
from discord.ext import commands
from ..storage.storage_sqlite import Storage
from ..config import CIRCLE_LIMIT, GAME_CHANNEL_ID
from ..gallery.gallery import make_gallery_image, make_theme_announcement_image
from ..prompts import PROMPT_LIST
import random
import datetime

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
            return
        if len(circle) >= CIRCLE_LIMIT:
            await interaction.followup.send(f"Sorry, the circle is full ({CIRCLE_LIMIT}/10). A spot will open when someone leaves.", ephemeral=True)
            return
        circle.append(user_id)
        Storage.set_player_circle(circle)
        channel = self.bot.get_channel(GAME_CHANNEL_ID)
        await channel.send(f"<@{user_id}> joined the Circle!")
        await interaction.followup.send(f"Welcome! The circle now has {len(circle)}/{CIRCLE_LIMIT} players.", ephemeral=True)
        state = Storage.get_game_state()
        if state and 'theme' in state:
            if user_id not in state.get('user_ids', []):
                state['user_ids'].append(user_id)
                Storage.set_game_state(state)
            try:
                user = await self.bot.fetch_user(user_id)
                await user.send(f"A game is currently running! Today's drawing theme: **{state['theme']}**. Please reply with your drawing as an image attachment.")
            except Exception:
                pass

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

async def setup(bot):
    await bot.add_cog(CircleManagement(bot))
