import discord
from discord.ext import commands
import threading
import asyncio
import os
import signal
from .config import DISCORD_TOKEN
from colorama import Fore, Style, init as colorama_init

colorama_init(autoreset=True)

def log_info(msg):
    print(Fore.CYAN + Style.BRIGHT + f"[INFO] {msg}" + Style.RESET_ALL)

def log_success(msg):
    print(Fore.GREEN + Style.BRIGHT + f"[SUCCESS] {msg}" + Style.RESET_ALL)

def log_warn(msg):
    print(Fore.YELLOW + Style.BRIGHT + f"[WARN] {msg}" + Style.RESET_ALL)

def log_error(msg):
    print(Fore.RED + Style.BRIGHT + f"[ERROR] {msg}" + Style.RESET_ALL)

def create_bot():
    intents = discord.Intents.default()
    intents.members = True
    intents.messages = True
    return commands.Bot(command_prefix="/", intents=intents)

bot = create_bot()

shutdown_event = threading.Event()

def console_control():
    while True:
        try:
            cmd = input()
        except (EOFError, KeyboardInterrupt):
            print("Console input closed. Exiting console control thread.")
            break
        if cmd.strip().lower() == "stop":
            print("Shutting down bot...")
            os._exit(0)
        elif cmd.strip().lower() == "status":
            # Print detailed game status
            from .storage.storage_sqlite import Storage
            import datetime
            from .config import GAME_CHANNEL_ID
            from pytz import timezone
            EST = timezone('America/New_York')
            state = Storage.get_game_state()
            if not state or 'theme' not in state:
                print("No game is currently running.")
            else:
                theme = state['theme']
                date = state.get('date', 'unknown')
                user_ids = state.get('user_ids', [])
                gallery = state.get('gallery', {})
                now = datetime.datetime.now(EST)
                next_end = now.replace(hour=17, minute=0, second=0, microsecond=0)
                if now >= next_end:
                    next_end += datetime.timedelta(days=1)
                time_left = next_end - now
                hours, remainder = divmod(time_left.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                time_left_str = f"{hours}h {minutes}m {seconds}s"
                print(f"\n=== CircleSketch Game Status ===\n"
                      f"Theme: {theme}\n"
                      f"Started: {date}\n"
                      f"Players in circle: {len(user_ids)}\n"
                      f"Submissions so far: {len(gallery)}\n"
                      f"Time left: {time_left_str} until next scheduled end\n")
        elif cmd.strip().lower() == "reset_streaks":
            from .storage.storage_sqlite import Storage
            Storage.reset_all_streaks()
            print("All streaks have been reset.")
        elif cmd.strip().lower() == "help":
            print("Available commands: stop, status, reset_streaks, help")

def handle_sigint(sig, frame):
    print("\nReceived Ctrl+C, shutting down bot gracefully...")
    shutdown_event.set()

async def load_cogs(bot):
    await bot.load_extension("circle_sketch.cogs.circle_management")
    await bot.load_extension("circle_sketch.cogs.game_management")
    await bot.load_extension("circle_sketch.cogs.events_cog")

def main():
    signal.signal(signal.SIGINT, handle_sigint)
    threading.Thread(target=console_control, daemon=True).start()
    asyncio.run(run_bot())

def run_bot():
    async def runner():
        await load_cogs(bot)
        bot_task = asyncio.create_task(bot.start(DISCORD_TOKEN))
        while not shutdown_event.is_set():
            await asyncio.sleep(0.2)
        await bot.close()
        log_success("Bot shutdown complete.")
    return runner()

main()
