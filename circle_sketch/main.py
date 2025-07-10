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
        cmd = input()
        if cmd.strip().lower() == "stop":
            print("Shutting down bot...")
            shutdown_event.set()
            break
        elif cmd.strip().lower() == "status":
            print("Bot is running.")
        elif cmd.strip().lower() == "help":
            print("Available commands: stop, status, help")

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
