from discord.ext import commands
from discord.ext.commands.bot import _mention_pattern, _mentions_transforms
import logging
from . import colors, embeds
from .messages import Messages
from .bot_utils import config
import sys, os
import discord

async def _default_help_command(ctx, *commands : str):
    """Shows this message."""
    bot = ctx.bot
    destination = ctx.message.author if bot.pm_help else ctx.message.channel

    def repl(obj):
        return _mentions_transforms.get(obj.group(0), '')

    # help by itself just lists our own commands.
    if len(commands) == 0:
        pages = bot.formatter.format_help_for(ctx, bot)
    elif len(commands) == 1:
        # try to see if it is a cog name
        name = _mention_pattern.sub(repl, commands[0])
        command = None
        if name in [x.lower() for x in bot.cogs]:
            command = bot.cogs[[x for x in bot.cogs if x.lower() == name][0]]
        else:
            command = bot.commands.get(name)
            if command is None:
                await bot.responses.failure(destination=destination, message=bot.command_not_found.format(name))
                return

        pages = bot.formatter.format_help_for(ctx, command)
    else:
        name = _mention_pattern.sub(repl, commands[0])
        command = bot.commands.get(name)
        if command is None:
            await bot.responses.failure(destination=destination, message=bot.command_not_found.format(name))
            return

        for key in commands[1:]:
            try:
                key = _mention_pattern.sub(repl, key)
                command = command.commands.get(key)
                if command is None:
                    await bot.responses.failure(destination=destination, message=bot.command_not_found.format(name))
                    return
            except AttributeError:
                await bot.responses.failure(destination=destination, message=bot.command_has_no_subcommands.format(command, key))
                return

        pages = bot.formatter.format_help_for(ctx, command)

    if bot.pm_help is None:
        characters = sum(map(lambda l: len(l), pages.values()))
        if characters > 1000:
            destination = ctx.message.author

    await bot.responses.full(destination=destination, **pages)

class DiscordBot(commands.Bot):

    def __init__(self, command_prefix, formatter=None, description=None, pm_help=False, **options):
        super().__init__(command_prefix, formatter=embeds.EmbedHelpFormatter(self),
                         description=description, pm_help=pm_help, command_not_found='No command called "{}" found.',
                         command_has_no_subcommands='Command "{0.name}" has no subcommands.', **options)
        os.makedirs("logs", exist_ok=True)
        discord_logger = logging.getLogger('discord')
        discord_logger.setLevel(logging.CRITICAL)
        discord_logger.addHandler(logging.FileHandler(filename='logs/errors.log', encoding='utf-8'))

        stats_log = logging.getLogger('stats')
        stats_log.setLevel(logging.INFO)
        stats_log.addHandler(logging.FileHandler(filename='logs/stats.log', encoding='utf-8'))

        info_log = logging.getLogger('info')
        info_log.setLevel(logging.INFO)
        info_log.addHandler(logging.FileHandler(filename='logs/info.log', encoding='utf-8'))

        self.logs = {'discord': discord_logger, 'stats': stats_log, 'info': info_log}
        self.config = config.Config('settings.json', directory="")
        credentials = self.config.get('credentials', {})

        client_id = credentials.get('client_id', "")
        token = credentials.get('token', "")

        if not client_id or not token:
            print("Could not find both client_id and token in settings.json")
            sys.exit(1)

        self.client_id = client_id
        self.token = token
        self.colors = colors.Color
        self.responses = Messages(self)

        self.remove_command("help")
        self.command(**self.help_attrs)(_default_help_command)

    async def set_prefix(self, prefix):
        self.command_prefix = prefix
        await self.change_presence(game=discord.Game(name='{}help for help'.format(prefix)))

    def load_cogs(self, cogs):
        for extension in cogs:
            try:
                self.load_extension(extension)
            except Exception as e:
                print('Failed to load extension {}\n{}: {}'.format(extension, type(e).__name__, e))

    def run(self):
        super().run(self.token)