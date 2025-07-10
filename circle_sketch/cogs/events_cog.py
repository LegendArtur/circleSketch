import discord
from discord.ext import commands
from discord import Message
from ..storage.storage_sqlite import Storage
from ..gallery.gallery import make_gallery_image
from ..config import GAME_CHANNEL_ID
from ..main import log_info, log_warn, log_error, log_success

class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_connect(self):
        log_info("Bot connected to Discord gateway.")

    @commands.Cog.listener()
    async def on_disconnect(self):
        log_warn("Bot disconnected from Discord gateway.")
        log_success("Bot shutdown complete.")

    @commands.Cog.listener()
    async def on_ready(self):
        log_success("Bot is ready and connected to Discord!")

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot:
            return
        log_info(f"Message from {message.author} in #{message.channel}: {message.content}")
        # ...existing on_message logic...
        pass

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
