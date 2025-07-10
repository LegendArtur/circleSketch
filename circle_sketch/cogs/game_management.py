import discord
from discord import app_commands, Interaction
from discord.ext import commands
from ..storage.storage_sqlite import Storage
from ..config import GAME_CHANNEL_ID
from ..prompts import PROMPT_LIST
from ..gallery.gallery import make_gallery_image, make_theme_announcement_image
import random
import datetime

# --- Admin Check ---
def is_admin(interaction: Interaction):
    return interaction.user.guild_permissions.administrator

class GameManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.manual_game_starter_id = None

    @app_commands.command(name="start_manual_game", description="Start a manual game (ends only when ended by the starter)")
    async def start_manual_game(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        if getattr(self, 'manual_game_starter_id', None) is not None:
            await interaction.followup.send("A manual game is already running.", ephemeral=True)
            return
        self.manual_game_starter_id = interaction.user.id
        circle = Storage.get_player_circle()
        if len(circle) < 1:
            await interaction.followup.send("Not enough players to start the game.", ephemeral=True)
            return
        prompt = random.choice(PROMPT_LIST)
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        Storage.set_game_state({'theme': prompt, 'date': today, 'user_ids': circle, 'submissions': {}, 'gallery': {}})
        channel = self.bot.get_channel(GAME_CHANNEL_ID)
        # Post theme announcement image in channel
        img_bytes = make_theme_announcement_image(prompt)
        file = discord.File(img_bytes, filename="theme.png")
        await channel.send(content="@everyone Today's game is starting!", file=file)
        # DM text only to each user        
        for user_id in circle:
            try:
                user = await self.bot.fetch_user(user_id)
                await user.send(f"Today's drawing theme: **{prompt}**. Please reply with your drawing as an image attachment.")
            except Exception:
                pass
        await interaction.followup.send("Manual game started! Prompt posted.", ephemeral=True)

    @app_commands.command(name="end_manual_game", description="End the current manual game and post the gallery.")
    async def end_manual_game(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        if getattr(self, 'manual_game_starter_id', None) is None:
            await interaction.followup.send("No manual game is running.", ephemeral=True)
            return
        if interaction.user.id != self.manual_game_starter_id and not is_admin(interaction):
            await interaction.followup.send("Only the game starter or an admin can end the game.", ephemeral=True)
            return
        state = Storage.get_game_state()
        if not state or 'theme' not in state:
            await interaction.followup.send("No game is currently running.", ephemeral=True)
            self.manual_game_starter_id = None
            return
        theme = state['theme']
        date = state.get('date', 'unknown')
        gallery = state.get('gallery', {})
        channel = self.bot.get_channel(GAME_CHANNEL_ID)
        if not gallery:
            await channel.send(f"No submissions for today's theme: **{theme}**.")
        else:
            await channel.send(f"Gallery for '**{theme}**' - {date}!")
            for user_id, img_url in gallery.items():
                user = await self.bot.fetch_user(int(user_id))
                img_bytes = await make_gallery_image(theme, date, user, img_url)
                file = discord.File(img_bytes, filename=f"gallery_{user_id}.png")
                await channel.send(file=file)
        Storage.set_game_state({})
        self.manual_game_starter_id = None
        await interaction.followup.send("Manual game ended and gallery posted.", ephemeral=True)

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

    @app_commands.command(name="game_status", description="Show the current game status.")
    async def game_status(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        state = Storage.get_game_state()
        if not state or 'theme' not in state:
            await interaction.followup.send("No game is currently running.", ephemeral=True)
            return
        theme = state['theme']
        date = state.get('date', 'unknown')
        user_ids = state.get('user_ids', [])
        await interaction.followup.send(f"Current game theme: **{theme}** (started {date}). Players: {len(user_ids)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(GameManagement(bot))
