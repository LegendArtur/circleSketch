import discord
from discord.ext import commands
from discord import Message
from ..storage.storage_sqlite import Storage
from ..gallery.gallery import make_gallery_image
from ..config import GAME_CHANNEL_ID
from ..main import log_info, log_warn, log_error, log_success
import logging
import datetime
import os
from colorama import Fore, Style, init as colorama_init

colorama_init(autoreset=True)

# --- Logging Helpers ---
def log_info(msg):
    print(Fore.CYAN + Style.BRIGHT + f"[INFO] {msg}" + Style.RESET_ALL)

def log_success(msg):
    print(Fore.GREEN + Style.BRIGHT + f"[SUCCESS] {msg}" + Style.RESET_ALL)

def log_warn(msg):
    print(Fore.YELLOW + Style.BRIGHT + f"[WARN] {msg}" + Style.RESET_ALL)

def log_error(msg):
    print(Fore.RED + Style.BRIGHT + f"[ERROR] {msg}" + Style.RESET_ALL)

class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_connect(self):
        log_info("Bot connected to Discord gateway.")

    @commands.Cog.listener()
    async def on_disconnect(self):
        log_warn("Bot disconnected from Discord gateway.")

    @commands.Cog.listener()
    async def on_ready(self):
        log_info(f"Logged in as {self.bot.user}")
        try:
            synced = await self.bot.tree.sync()
            log_info(f"Synced {len(synced)} commands.")
        except Exception as e:
            log_error(f"Failed to sync commands: {e}")

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot:
            return
        state = Storage.get_game_state()
        if not state or 'theme' not in state:
            return
        user_id = message.author.id
        # Only process DMs for submissions
        if isinstance(message.channel, discord.DMChannel):
            log_info(f"DM from {message.author} (ID: {user_id}): {message.type}")
            if user_id not in state.get('user_ids', []):
                return
            if user_id in state.get('submissions', {}):
                await message.channel.send("You have already submitted for today's game!")
                log_info(f"User {user_id} tried to submit again.")
                return
            if not message.attachments:
                await message.channel.send("Please submit an image attachment.")
                log_info(f"User {user_id} submitted without an image.")
                return
            img_url = message.attachments[0].url
            # Save submission
            if 'submissions' not in state:
                state['submissions'] = {}
            if 'gallery' not in state:
                state['gallery'] = {}
            state['submissions'][user_id] = img_url
            state['gallery'][user_id] = img_url
            Storage.set_game_state(state)
            await message.channel.send("Submission received! Thank you.")
            log_info(f"User {user_id} submitted their drawing.")
            channel = self.bot.get_channel(GAME_CHANNEL_ID)
            await channel.send(f"<@{user_id}> has submitted their image for today! You can still join the current game by typing `/join_circle`.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        log_info(f"Member joined: {member} (ID: {member.id})")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        log_warn(f"Member left: {member} (ID: {member.id})")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        log_success(f"Bot joined new guild: {guild.name} (ID: {guild.id})")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        log_warn(f"Bot removed from guild: {guild.name} (ID: {guild.id})")

    @commands.Cog.listener()
    async def on_error(self, event_method, *args, **kwargs):
        log_error(f"Error in event: {event_method}")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            log_warn(f"Unknown command used: {ctx.message.content}")
        elif isinstance(error, commands.MissingRequiredArgument):
            log_warn(f"Missing argument for command: {ctx.command}")
        elif isinstance(error, commands.CheckFailure):
            log_warn(f"Check failed for command: {ctx.command}")
        else:
            log_error(f"Unhandled command error: {error}")

async def setup(bot):
    await bot.add_cog(EventsCog(bot))
