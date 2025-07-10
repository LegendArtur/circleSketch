import discord
from discord.ext import commands
import threading
import asyncio
import os
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

async def load_cogs(bot):
    await bot.load_extension("circle_sketch.cogs.circle_management")
    await bot.load_extension("circle_sketch.cogs.game_management")
    await bot.load_extension("circle_sketch.cogs.events_cog")

def main():
    threading.Thread(target=console_control, daemon=True).start()
    asyncio.run(load_cogs(bot))
    bot.run(DISCORD_TOKEN)

main()
