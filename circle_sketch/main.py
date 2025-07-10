import discord
from discord import app_commands, Interaction
from discord.ext import commands
from .config import DISCORD_TOKEN, GAME_CHANNEL_ID
from .storage.storage_sqlite import Storage
from .prompts import PROMPT_LIST
from .gallery.gallery import make_gallery_image, make_theme_announcement_image
import asyncio
import logging
import random
import datetime
import os
import io
from colorama import Fore, Style, init as colorama_init
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import threading

colorama_init(autoreset=True)

DEV_MODE = os.getenv('DEV_MODE', 'False').lower() == 'true'
DEV_USER_ID = int(os.getenv('DEV_USER_ID', '269634149726289930'))

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# --- Bot Setup ---
def create_bot():
    intents = discord.Intents.default()
    intents.members = True
    intents.messages = True
    bot = commands.Bot(command_prefix="/", intents=intents)
    return bot

bot = create_bot()
tree = bot.tree

CIRCLE_LIMIT = 10
EST = pytz.timezone('America/New_York')

# --- Logging Helpers ---
def log_info(msg):
    print(Fore.CYAN + Style.BRIGHT + f"[INFO] {msg}" + Style.RESET_ALL)

def log_success(msg):
    print(Fore.GREEN + Style.BRIGHT + f"[SUCCESS] {msg}" + Style.RESET_ALL)

def log_warn(msg):
    print(Fore.YELLOW + Style.BRIGHT + f"[WARN] {msg}" + Style.RESET_ALL)

def log_error(msg):
    print(Fore.RED + Style.BRIGHT + f"[ERROR] {msg}" + Style.RESET_ALL)

# --- Admin Check ---
def is_admin(interaction: Interaction):
    return interaction.user.guild_permissions.administrator

# --- Command Definitions ---
@tree.command(name="join_circle", description="Join the persistent player circle.")
async def join_circle(interaction: Interaction):
    await interaction.response.defer(ephemeral=True)
    user_id = interaction.user.id
    username = interaction.user.display_name
    circle = Storage.get_player_circle()
    if user_id in circle:
        log_info(f"User {username} ({user_id}) tried to join but is already in the circle.")
        await interaction.followup.send("You are already in the circle.", ephemeral=True)
        return
    if len(circle) >= CIRCLE_LIMIT:
        log_info(f"User {username} ({user_id}) tried to join but the circle is full.")
        await interaction.followup.send(f"Sorry, the circle is full ({CIRCLE_LIMIT}/10). A spot will open when someone leaves.", ephemeral=True)
        return
    circle.append(user_id)
    Storage.set_player_circle(circle)
    channel = bot.get_channel(GAME_CHANNEL_ID)
    await channel.send(f"<@{user_id}> joined the Circle!")
    await interaction.followup.send(f"Welcome! The circle now has {len(circle)}/{CIRCLE_LIMIT} players.", ephemeral=True)
    log_success(f"User {username} ({user_id}) joined the circle. Now {len(circle)}/{CIRCLE_LIMIT}.")
    state = Storage.get_game_state()
    if state and 'theme' in state:
        if user_id not in state.get('user_ids', []):
            state['user_ids'].append(user_id)
            Storage.set_game_state(state)
            log_info(f"Added user {username} ({user_id}) to current game's user_ids.")
        try:
            user = await bot.fetch_user(user_id)
            await user.send(f"A game is currently running! Today's drawing theme: **{state['theme']}**. Please reply with your drawing as an image attachment.")
            log_info(f"Sent DM to new joiner {username} ({user_id}) during active game.")
        except Exception as e:
            log_error(f"Failed to DM new joiner {username} ({user_id}): {e}")

@tree.command(name="leave_circle", description="Leave the persistent player circle.")
async def leave_circle(interaction: Interaction):
    await interaction.response.defer(ephemeral=True)
    user_id = interaction.user.id
    username = interaction.user.display_name
    circle = Storage.get_player_circle()
    if user_id not in circle:
        log_info(f"User {username} ({user_id}) tried to leave but was not in the circle.")
        await interaction.followup.send("You are not in the circle.", ephemeral=True)
        return
    circle.remove(user_id)
    Storage.set_player_circle(circle)
    await interaction.followup.send("You have left the circle.", ephemeral=True)
    log_success(f"User {username} ({user_id}) left the circle.")

@tree.command(name="list_circle", description="List current members of the player circle.")
async def list_circle(interaction: Interaction):
    await interaction.response.defer(ephemeral=True)
    circle = Storage.get_player_circle()
    if not circle:
        log_info(f"User {interaction.user.display_name} ({interaction.user.id}) listed the circle (empty).")
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
    log_info(f"User {interaction.user.display_name} ({interaction.user.id}) listed the circle: {members}")

@tree.command(name="reset_circle", description="[Admin] Reset the player circle.")
@app_commands.check(is_admin)
async def reset_circle(interaction: Interaction):
    await interaction.response.defer(ephemeral=True)
    username = interaction.user.display_name
    user_id = interaction.user.id
    class Confirm(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=30)
            self.value = None
        @discord.ui.button(label="Yes. I am sure.", style=discord.ButtonStyle.danger)
        async def confirm(self, interaction2: Interaction, button: discord.ui.Button):
            Storage.reset()
            await interaction2.response.edit_message(content="Player circle has been reset.", view=None)
            self.value = True
            self.stop()
            log_success(f"Admin {username} ({user_id}) reset the circle.")
        async def on_timeout(self):
            # When the view times out, edit the message to indicate cancellation
            for item in self.children:
                item.disabled = True
            try:
                await self.message.edit(content="Reset cancelled (no confirmation received).", view=None)
            except Exception as e:
                log_warn(f"Failed to edit message on reset timeout: {e}")
    view = Confirm()
    msg = await interaction.followup.send("Are you sure you want to reset the player circle?", ephemeral=True, view=view)
    view.message = msg

@reset_circle.error
async def reset_circle_error(interaction: Interaction, error):
    if isinstance(error, app_commands.errors.CheckFailure):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        logging.warning(f"User {interaction.user.id} tried to reset the circle without permission.")

# --- Game Logic Functions ---
async def post_prompt_and_collect(channel, theme, date_str, user_ids):
    # --- Streak and user stats announcement ---
    streak = Storage.get_group_streak()
    user_stats = Storage.get_user_stats()
    if streak > 0:
        streak_msg = f"**Your group is on a {streak} day streak!** 🔥 Here are yesterday's results:\n"
        lines = []
        for user_id in user_ids:
            count = user_stats.get(user_id, 0)
            lines.append(f"<@{user_id}>: {count}/{streak} drawings!")
        streak_msg += "\n".join(lines)
        await channel.send(streak_msg)
    # --- End streak announcement ---
    img_bytes = make_theme_announcement_image(theme)
    file = discord.File(img_bytes, filename="theme.png")
    await channel.send(content="@everyone Today's game is starting!", file=file)
    Storage.set_game_state({
        'theme': theme,
        'date': date_str,
        'submissions': {},
        'gallery': {},
        'start_time': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'user_ids': user_ids
    })
    for user_id in user_ids:
        try:
            user = await bot.fetch_user(user_id)
            await user.send(f"Today's drawing theme: **{theme}**. Please reply with your drawing as an image attachment.")
            log_info(f"DM sent to user {user_id} for daily prompt.")
        except Exception as e:
            log_error(f"Failed to DM user {user_id}: {e}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    state = Storage.get_game_state()
    if not state or 'theme' not in state:
        return
    user_id = message.author.id
    if DEV_MODE and user_id == DEV_USER_ID and isinstance(message.channel, discord.DMChannel):
        if not message.attachments:
            await message.channel.send("Please submit an image attachment.")
            logging.info(f"[DEV] User {user_id} submitted without an image.")
            return
        img_url = message.attachments[0].url
        theme = state['theme']
        date_str = state['date']
        user = await bot.fetch_user(user_id)
        img_bytes = make_gallery_image(theme, date_str, user, img_url)
        channel = bot.get_channel(GAME_CHANNEL_ID)
        file = discord.File(img_bytes, filename=f"gallery_{user_id}.png")
        await channel.send(file=file)
        await message.channel.send("Submission received and posted!")
        logging.info(f"[DEV] User {user_id} submitted and image posted.")
        Storage.set_game_state(None)
        return
    if not DEV_MODE and isinstance(message.channel, discord.DMChannel):
        if user_id not in state.get('user_ids', []):
            return
        if user_id in state['submissions']:
            await message.channel.send("You have already submitted for today's game!")
            log_info(f"User {user_id} tried to submit again.")
            return
        if not message.attachments:
            await message.channel.send("Please submit an image attachment.")
            log_info(f"User {user_id} submitted without an image.")
            return
        img_url = message.attachments[0].url
        state['submissions'][user_id] = img_url
        state['gallery'][user_id] = img_url
        Storage.set_game_state(state)
        await message.channel.send("Submission received! Thank you.")
        log_info(f"User {user_id} submitted their drawing.")
        channel = bot.get_channel(GAME_CHANNEL_ID)
        await channel.send(f"<@{user_id}> has submitted their image for today! You can still join the current game by typing `/join_circle`.")

async def end_daily_game(channel):
    state = Storage.get_game_state()
    if not state or 'theme' not in state:
        return
    theme = state['theme']
    date_str = state['date']
    gallery = state.get('gallery', {})
    # --- Streak and user stats logic ---
    if gallery:
        # Increment streak
        streak = Storage.get_group_streak() + 1
        Storage.set_group_streak(streak)
        # Increment user stats
        for user_id in gallery:
            Storage.increment_user_submission(int(user_id))
    else:
        # Reset streak if no submissions
        Storage.set_group_streak(0)
        streak = 0
    # --- End streak logic ---
    if not gallery:
        await channel.send(f"No submissions for today's theme: **{theme}**.")
        log_info("No submissions to reveal.")
    else:
        await channel.send(f"Gallery for '**{theme}**' - {date_str}!")
        for user_id, img_url in gallery.items():
            user = await bot.fetch_user(int(user_id))
            img_bytes = make_gallery_image(theme, date_str, user, img_url)
            file = discord.File(img_bytes, filename=f"gallery_{user_id}.png")
            await channel.send(file=file)
            log_info(f"Posted gallery image for user {user_id}.")
    Storage.set_game_state(None)
    log_info("Game state reset for next round.")

@bot.event
async def on_ready():
    log_info(f"Logged in as {bot.user}")
    try:
        synced = await tree.sync()
        log_info(f"Synced {len(synced)} commands.")
    except Exception as e:
        log_error(f"Failed to sync commands: {e}")
    if scheduled_mode_enabled and not scheduler.running:
        scheduler.start()

if DEV_MODE:
    logging.info("DEV_MODE is enabled. Registering /dev_start_game command.")
    @tree.command(name="dev_start_game", description="[DEV] Start a dev mode game with one user.")
    async def dev_start_game(interaction: Interaction):
        logging.info("/dev_start_game command invoked.")
        if interaction.user.id != DEV_USER_ID:
            await interaction.response.send_message("Only the dev user can use this.", ephemeral=True)
            logging.info(f"User {interaction.user.id} tried to use /dev_start_game but is not DEV_USER_ID.")
            return
        channel = bot.get_channel(GAME_CHANNEL_ID)
        theme = random.choice(PROMPT_LIST)
        date_str = datetime.datetime.now(datetime.timezone.utc).strftime('%B %d, %Y')
        await post_prompt_and_collect(channel, theme, date_str, [DEV_USER_ID])
        await interaction.response.send_message(f"Dev game started for <@{DEV_USER_ID}>. Post your image in the channel.", ephemeral=True)
        logging.info(f"Dev game started for user {DEV_USER_ID}.")
else:
    scheduled_mode_enabled = False
    manual_game_starter_id = None
    scheduler = AsyncIOScheduler(timezone=EST)
    async def start_daily_game():
        # If first game not started, start immediately and set flag
        if not Storage.get_first_game_started():
            circle = Storage.get_player_circle()
            if len(circle) < 1:
                logging.info("Not enough players to start the game.")
                return
            theme = random.choice(PROMPT_LIST)
            date_str = datetime.datetime.now(datetime.timezone.utc).strftime('%B %d, %Y')
            channel = bot.get_channel(GAME_CHANNEL_ID)
            await post_prompt_and_collect(channel, theme, date_str, circle)
            Storage.set_first_game_started(True)
            logging.info("First game started immediately after bot launch.")
            return
        # Otherwise, only start at 5pm as scheduled
        now = datetime.datetime.now(EST)
        if now.hour == 17 and now.minute == 0:
            circle = Storage.get_player_circle()
            if len(circle) < 1:
                logging.info("Not enough players to start the game.")
                return
            theme = random.choice(PROMPT_LIST)
            date_str = datetime.datetime.now(datetime.timezone.utc).strftime('%B %d, %Y')
            channel = bot.get_channel(GAME_CHANNEL_ID)
            await post_prompt_and_collect(channel, theme, date_str, circle)
            logging.info("Scheduled 5pm game started.")
    async def end_game_job():
        channel = bot.get_channel(GAME_CHANNEL_ID)
        await end_daily_game(channel)
    # Schedule jobs for 5 PM EST
    scheduler.add_job(lambda: asyncio.create_task(start_daily_game()), CronTrigger(hour=17, minute=0, timezone=EST))
    scheduler.add_job(lambda: asyncio.create_task(end_game_job()), CronTrigger(hour=17, minute=0, second=10, timezone=EST))
    @tree.command(name="start_scheduled_game", description="Start daily scheduled game mode (5pm UTC)")
    async def start_scheduled_game(interaction: Interaction):
        global scheduled_mode_enabled
        if scheduled_mode_enabled:
            await interaction.response.send_message("Scheduled game mode is already running.", ephemeral=True)
            return
        scheduled_mode_enabled = True
        async def scheduled_start():
            channel = bot.get_channel(GAME_CHANNEL_ID)
            circle = Storage.get_player_circle()
            if len(circle) < 1:
                log_info("Not enough players to start the game.")
                return
            theme = random.choice(PROMPT_LIST)
            date_str = datetime.datetime.now(datetime.timezone.utc).strftime('%B %d, %Y')
            await post_prompt_and_collect(channel, theme, date_str, circle)
        async def scheduled_end():
            channel = bot.get_channel(GAME_CHANNEL_ID)
            await end_daily_game(channel)
        scheduler.add_job(lambda: asyncio.create_task(scheduled_start()), CronTrigger(hour=17, minute=0, timezone=EST))
        scheduler.add_job(lambda: asyncio.create_task(scheduled_end()), CronTrigger(hour=17, minute=0, second=10, timezone=EST))
        await interaction.response.send_message("Scheduled game mode enabled. Daily games will start at 5pm UTC.", ephemeral=True)
        log_info(f"Scheduled game mode enabled by {interaction.user.id}")
    @tree.command(name="start_manual_game", description="Start a manual game (ends only when ended by the starter)")
    async def start_manual_game(interaction: Interaction):
        global manual_game_starter_id
        await interaction.response.defer(ephemeral=True)
        if manual_game_starter_id is not None:
            await interaction.followup.send("A manual game is already running.", ephemeral=True)
            return
        manual_game_starter_id = interaction.user.id
        channel = bot.get_channel(GAME_CHANNEL_ID)
        circle = Storage.get_player_circle()
        if len(circle) < 1:
            await interaction.followup.send("Not enough players to start the game.", ephemeral=True)
            return
        theme = random.choice(PROMPT_LIST)
        date_str = datetime.datetime.now(datetime.timezone.utc).strftime('%B %d, %Y')
        await post_prompt_and_collect(channel, theme, date_str, circle)
        await interaction.followup.send("Manual game started. Use /end_manual_game to end.", ephemeral=True)
        log_info(f"Manual game started by {interaction.user.id}")

    @tree.command(name="end_manual_game", description="End the current manual game and post the gallery.")
    async def end_manual_game(interaction: Interaction):
        global manual_game_starter_id
        if manual_game_starter_id is None:
            await interaction.response.send_message("No manual game is running.", ephemeral=True)
            return
        if interaction.user.id != manual_game_starter_id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Only the game starter or an admin can end the game.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        channel = bot.get_channel(GAME_CHANNEL_ID)
        await end_daily_game(channel)
        manual_game_starter_id = None
        await interaction.followup.send("Manual game ended and gallery posted.", ephemeral=True)
        log_info(f"Manual game ended by {interaction.user.id}")

# --- Scheduler Setup ---
def setup_scheduler():
    scheduler = AsyncIOScheduler(timezone=EST)
    # Schedule jobs for 5 PM EST
    scheduler.add_job(lambda: asyncio.create_task(start_daily_game()), CronTrigger(hour=17, minute=0, timezone=EST))
    scheduler.add_job(lambda: asyncio.create_task(end_game_job()), CronTrigger(hour=17, minute=0, second=10, timezone=EST))
    return scheduler

# --- Console Control Thread ---
def console_control():
    while True:
        cmd = input()
        if cmd.strip().lower() == "stop":
            print("Shutting down bot...")
            os._exit(0)
        elif cmd.strip().lower() == "status":
            print("Bot is running.")
        elif cmd.strip().lower() == "help":
            print("Available commands: stop, status, help")

# --- Main Entrypoint ---
def main():
    threading.Thread(target=console_control, daemon=True).start()
    bot.run(DISCORD_TOKEN)

main()
