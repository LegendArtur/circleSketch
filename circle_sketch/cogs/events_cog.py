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
    async def on_message(self, message: Message):
        if message.author.bot:
            return
        log_info(f"Message from {message.author} in #{message.channel}: {message.content}")
        # ...existing on_message logic...
        pass

    @commands.Cog.listener()
    async def on_ready(self):
        log_success("Bot is ready and connected to Discord!")

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

async def setup(bot):
    await bot.add_cog(EventsCog(bot))
