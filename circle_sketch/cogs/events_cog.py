import discord
from discord.ext import commands
from discord import Message
from ..storage.storage import Storage
from ..gallery.gallery import make_gallery_image
from ..config import GAME_CHANNEL_ID
import logging

logger = logging.getLogger('circle_sketch')

class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_connect(self):
        logger.info(f'Bot connected to Discord gateway. User: {self.bot.user}, Latency: {getattr(self.bot, "latency", "N/A")}, Guilds: {len(getattr(self.bot, "guilds", []))}')

    @commands.Cog.listener()
    async def on_disconnect(self):
        try:
            reconnecting = getattr(self.bot, 'is_closed', lambda: None)()
            shard_count = getattr(self.bot, 'shard_count', None)
            logger.warning(f'Bot disconnected from Discord gateway. Reconnecting: {reconnecting}, Shard count: {shard_count}')
        except Exception as e:
            logger.error(f'Error during disconnect logging: {e}')

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f'Logged in as {self.bot.user} (ID: {getattr(self.bot.user, "id", "N/A")}), Guilds: {len(getattr(self.bot, "guilds", []))}, Latency: {getattr(self.bot, "latency", "N/A")}')
        try:
            synced = await self.bot.tree.sync()
            logger.info(f'Synced {len(synced)} commands.')
        except Exception as e:
            logger.error(f'Failed to sync commands: {e}')

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
            logger.info(f'DM from {message.author} (ID: {user_id}): {message.type}')
            if user_id not in state.get('user_ids', []):
                return
            if user_id in state.get('submissions', {}):
                await message.channel.send("You have already submitted for today's game!")
                logger.info(f'User {user_id} tried to submit again.')
                return
            if not message.attachments:
                await message.channel.send('Please submit an image attachment.')
                logger.info(f'User {user_id} submitted without an image.')
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
            await message.channel.send('Submission received! Thank you.')
            logger.info(f'User {user_id} submitted their drawing.')
            channel = self.bot.get_channel(GAME_CHANNEL_ID)
            await channel.send(f'<@{user_id}> has submitted their image for today! You can still join the current game by typing `/join_circle`.')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        logger.info(f'Member joined: {member} (ID: {member.id})')

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        logger.warning(f'Member left: {member} (ID: {member.id})')

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        logger.info(f'Bot joined new guild: {guild.name} (ID: {guild.id})')

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        logger.warning(f'Bot removed from guild: {guild.name} (ID: {guild.id})')

    @commands.Cog.listener()
    async def on_error(self, event_method, *args, **kwargs):
        logger.error(f'Error in event: {event_method}')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            logger.warning(f'Unknown command used: {ctx.message.content}')
        elif isinstance(error, commands.MissingRequiredArgument):
            logger.warning(f'Missing argument for command: {ctx.command}')
        elif isinstance(error, commands.CheckFailure):
            logger.warning(f'Check failed for command: {ctx.command}')
        else:
            logger.error(f'Unhandled command error: {error}')

async def setup(bot):
    await bot.add_cog(EventsCog(bot))
print("Bot starting... (events_cog loaded)")
logger.info("Logger imported in events_cog")
