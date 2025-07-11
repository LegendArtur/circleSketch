import discord
from discord import app_commands, Interaction
from discord.ext import commands
from ..storage.storage import Storage
from ..config import GAME_CHANNEL_ID
from ..prompts import PROMPT_LIST
from ..gallery.gallery import make_gallery_image, make_theme_announcement_image
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import random
import datetime
import os
import shutil
import io
import logging
import queue
from logging.handlers import QueueHandler, QueueListener

EST = pytz.timezone('America/New_York')

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

# --- Admin Check ---
def is_admin(interaction: Interaction):
    return interaction.user.guild_permissions.administrator

IMAGE_STORAGE_DIR = os.path.join(os.path.dirname(__file__), '..', 'gallery', 'submissions')
os.makedirs(IMAGE_STORAGE_DIR, exist_ok=True)

def save_submission_image(user_id, img_url):
    import requests
    ext = os.path.splitext(img_url)[-1].split('?')[0] or '.png'
    local_path = os.path.join(IMAGE_STORAGE_DIR, f"{user_id}{ext}")
    r = requests.get(img_url, stream=True)
    with open(local_path, 'wb') as f:
        shutil.copyfileobj(r.raw, f)
    return local_path

def clear_submission_images(user_ids):
    for user_id in user_ids:
        for ext in ['.png', '.jpg', '.jpeg', '.webp']:
            try:
                os.remove(os.path.join(IMAGE_STORAGE_DIR, f"{user_id}{ext}"))
            except FileNotFoundError:
                pass

class GameManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone=EST)
        # End game at 5:00 PM, then start new game at 5:00:10 PM
        self.scheduler.add_job(self.scheduled_end_game, CronTrigger(hour=17, minute=0, timezone=EST))
        self.scheduler.add_job(self.scheduled_start_game, CronTrigger(hour=17, minute=0, second=10, timezone=EST))
        self.scheduler.start()

    @commands.Cog.listener()
    async def on_resumed(self):
        logger.info("Bot connection resumed (reconnected to Discord gateway)")

    @app_commands.command(name="start_manual_game", description="Start a manual game (ends only when ended by the starter)")
    async def start_manual_game(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        state = Storage.get_game_state() or {}
        # If a game is running, block start
        if state.get('theme') and state.get('manual_game_starter_id'):
            await interaction.followup.send("A manual game is already running.", ephemeral=True)
            return
        circle = Storage.get_player_circle(interaction.guild.id)
        if len(circle) < 1:
            await interaction.followup.send("Not enough players to start the game.", ephemeral=True)
            logger.warning("Not enough players to start the game.")
            return
        prompt = random.choice(PROMPT_LIST)
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        new_state = {
            'theme': prompt,
            'date': today,
            'user_ids': circle,
            'submissions': {},
            'gallery': {},
            'manual_game_starter_id': interaction.user.id,
            'guild_id': interaction.guild.id
        }
        Storage.set_game_state(new_state)
        channel = self.bot.get_channel(GAME_CHANNEL_ID)
        img_bytes = make_theme_announcement_image(prompt)
        file = discord.File(img_bytes, filename="theme.png")
        await channel.send(content="@everyone Today's game is starting!", file=file)
        logger.info(f"Manual game started with prompt: {prompt}")
        for user_id in circle:
            try:
                user = await self.bot.fetch_user(user_id)
                await user.send(f"Today's drawing theme: **{prompt}**. Please reply with your drawing as an image attachment.")
            except Exception as e:
                logger.error(f"Failed to DM user {user_id}: {e}")
        await interaction.followup.send("Manual game started! Prompt posted.", ephemeral=True)

    async def end_game_phase(self, channel, state):
        theme = state['theme']
        date = state.get('date', 'unknown')
        gallery = state.get('gallery', {})
        streak = Storage.get_group_streak()
        user_streaks = {}
        if not gallery:
            await channel.send(f"No submissions for today's theme: **{theme}**. The streak has ended at {streak}.")
            Storage.set_group_streak(0)
            # Reset all user streaks
            for user_id in state.get('user_ids', []):
                Storage.set_user_streak(user_id, 0)
        else:
            # Increment group streak
            Storage.set_group_streak(streak + 1)
            # Increment user streaks for submitters, reset for non-submitters
            submitted_ids = set(int(uid) for uid in gallery.keys())
            all_ids = set(int(uid) for uid in state.get('user_ids', []))
            for user_id in all_ids:
                if user_id in submitted_ids:
                    new_streak = Storage.get_user_streak(user_id) + 1
                    Storage.set_user_streak(user_id, new_streak)
                    user_streaks[user_id] = new_streak
                else:
                    Storage.set_user_streak(user_id, 0)
                    user_streaks[user_id] = 0
            # Compose streak summary
            streak_lines = [f"<@{uid}>: {user_streaks[uid]}🔥" if user_streaks[uid] > 0 else f"<@{uid}>: 0" for uid in user_streaks]
            await channel.send(f"Gallery for '**{theme}**' - {date}! Current group streak: {streak + 1} 🔥\nUser streaks:\n" + "\n".join(streak_lines))
            for user_id, img_path in gallery.items():
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    # Use local image path for gallery
                    with open(img_path, 'rb') as f:
                        img_bytes = f.read()
                    file = discord.File(io.BytesIO(img_bytes), filename=f"gallery_{user_id}.png")
                    await channel.send(file=file)
                except Exception as e:
                    await channel.send(f"Failed to generate gallery image for <@{user_id}>: {e}")
            # Clean up local images
            clear_submission_images(gallery.keys())
        Storage.set_game_state({})

    @app_commands.command(name="end_manual_game", description="End the current manual game and post the gallery.")
    async def end_manual_game(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        state = Storage.get_game_state() or {}
        starter_id = state.get('manual_game_starter_id')
        if not (state.get('theme') and starter_id):
            Storage.set_game_state({})
            await interaction.followup.send("No manual game is currently running.", ephemeral=True)
            return
        if interaction.user.id != starter_id and not is_admin(interaction):
            await interaction.followup.send("Only the game starter or an admin can end the game.", ephemeral=True)
            return
        channel = self.bot.get_channel(GAME_CHANNEL_ID)
        await self.end_game_phase(channel, state)
        Storage.set_game_state({})
        await interaction.followup.send("Manual game ended and gallery posted.", ephemeral=True)

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
        gallery = state.get('gallery', {})
        # Calculate time left if scheduled game
        now = datetime.datetime.now(EST)
        next_end = now.replace(hour=17, minute=0, second=0, microsecond=0)
        if now >= next_end:
            next_end += datetime.timedelta(days=1)
        time_left = next_end - now
        hours, remainder = divmod(time_left.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_left_str = f"{hours}h {minutes}m {seconds}s"
        # Compose status message
        msg = (
            f"**CircleSketch Game Status**\n"
            f"Theme: **{theme}**\n"
            f"Started: {date}\n"
            f"Players in circle: {len(user_ids)}\n"
            f"Submissions so far: {len(gallery)}\n"
            f"Time left: {time_left_str} until next scheduled end\n"
        )
        await interaction.followup.send(msg, ephemeral=True)

    @app_commands.command(name="show_streaks", description="Show the current group and per-user streaks.")
    async def show_streaks(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        group_streak = Storage.get_group_streak()
        state = Storage.get_game_state() or {}
        user_ids = state.get('user_ids', [])
        # If no game running, show all streaks in DB
        if not user_ids:
            # Try to get all user streaks from DB
            try:
                conn = Storage._get_conn()
                c = conn.cursor()
                c.execute('SELECT user_id, streak FROM user_streaks')
                rows = c.fetchall()
                conn.close()
                if not rows:
                    await interaction.followup.send(f"Current group streak: {group_streak}\nNo user streaks found.", ephemeral=True)
                    return
                streak_lines = [f"<@{row['user_id']}>: {row['streak']}🔥" if row['streak'] > 0 else f"<@{row['user_id']}>: 0" for row in rows]
            except Exception:
                streak_lines = []
        else:
            streak_lines = [f"<@{uid}>: {Storage.get_user_streak(uid)}🔥" if Storage.get_user_streak(uid) > 0 else f"<@{uid}>: 0" for uid in user_ids]
        await interaction.followup.send(f"Current group streak: {group_streak} 🔥\n\nUser streaks:\n" + "\n".join(streak_lines), ephemeral=True)

    async def scheduled_start_game(self):
        circle = Storage.get_player_circle()
        if len(circle) < 1:
            return
        prompt = random.choice(PROMPT_LIST)
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        Storage.set_game_state({'theme': prompt, 'date': today, 'user_ids': circle, 'submissions': {}, 'gallery': {}})
        channel = self.bot.get_channel(GAME_CHANNEL_ID)
        img_bytes = make_theme_announcement_image(prompt)
        file = discord.File(img_bytes, filename="theme.png")
        await channel.send(content="@everyone Today's game is starting!", file=file)
        for user_id in circle:
            try:
                user = await self.bot.fetch_user(user_id)
                await user.send(f"Today's drawing theme: **{prompt}**. Please reply with your drawing as an image attachment.")
            except Exception:
                pass

    # Utility for scheduled/timer-based end
    async def scheduled_end_game(self):
        state = Storage.get_game_state()
        if not state or 'theme' not in state:
            return
        channel = self.bot.get_channel(GAME_CHANNEL_ID)
        await self.end_game_phase(channel, state)
        self.manual_game_starter_id = None

async def setup(bot):
    await bot.add_cog(GameManagement(bot))
