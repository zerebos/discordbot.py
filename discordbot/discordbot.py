# -*- coding: utf-8 -*-

import logging
import os
import sys

import discord
from discord.ext import commands
from discord.ext.commands.bot import _mention_pattern, _mentions_transforms

import colors, embeds
from bot_utils import config
from messages import Messages
import traceback, datetime


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

	def __init__(self, command_prefix=None, formatter=None, description=None, pm_help=None, **options):
		self.config = config.Config('settings.json', directory="")

		if command_prefix is None:
			command_prefix = self.config.get("meta", {}).get("prefix", "")
		if not command_prefix:
			print("Prefix was not supplied")
			sys.exit(1)

		if description is None:
			description = self.config.get("meta", {}).get("description", "")

		if pm_help is None:
			pm_help = self.config.get("meta", {}).get("pm_help", None)

		help_attrs = options.pop("help_attrs", {})
		help_attrs['hidden'] = True

		super().__init__(command_prefix, formatter=formatter if formatter else embeds.EmbedHelpFormatter(self),
						 description=description, pm_help=pm_help, command_not_found='No command called "{}" found.',
						 command_has_no_subcommands='Command "{0.name}" has no subcommands.', help_attrs=help_attrs, **options)
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

		credentials = self.config.get('credentials', {})

		client_id = credentials.get('client_id', "")
		token = credentials.get('token', "")

		if not client_id or not token:
			print("Could not find both client_id and token in settings.json")
			sys.exit(1)

		self.ownerInviteLink = self.config.get("meta", {}).get("invite_link", "")
		self.client_id = client_id
		self.token = token
		self.colors = colors.Colors
		self.responses = Messages(self)

		self.remove_command("help")
		self.command(**self.help_attrs)(_default_help_command)

	async def set_prefix(self, prefix):
		self.command_prefix = prefix
		await self.change_presence(game=discord.Game(name='{}help for help'.format(prefix)))

	def load_cogs(self, cogs = None):
		if cogs is None:
			cogs = self.config.get("cogs", [])
		for extension in cogs:
			print("Loading: " + extension)
			try:
				self.load_extension(extension)
			except Exception as e:
				print('Failed to load extension {}\n{}: {}'.format(extension, type(e).__name__, e))

	def run(self):
		super().run(self.token)

	async def on_command_error(self, error, ctx):
		if isinstance(error, commands.NoPrivateMessage):
			await self.send_message(ctx.message.author, 'This command cannot be used in private messages.')
		elif isinstance(error, commands.DisabledCommand):
			await self.send_message(ctx.message.author, 'Sorry. This command is disabled and cannot be used.')
		elif isinstance(error, commands.CommandInvokeError):
			print('In {0.command.qualified_name}:'.format(ctx), file=sys.stderr)
			traceback.print_tb(error.original.__traceback__)
			print('{0.__class__.__name__}: {0}'.format(error.original), file=sys.stderr)

	async def on_ready(self):
		print('Logged in as:')
		print('Username: ' + self.user.name)
		print('ID: ' + self.user.id)
		print('------')
		await self.change_presence(game=discord.Game(name='{}help for help'.format(self.command_prefix)))
		if not hasattr(self, 'uptime'):
			self.uptime = datetime.datetime.utcnow()

	async def on_message(self, message):
		if message.author.bot:
			return

		await self.process_commands(message)

	async def on_resumed(self):
		print('resumed...')

	async def logout(self):
		await super(DiscordBot, self).logout()
		for log in self.logs.values():
			for h in log.handlers:
				h.close()
				log.removeHandler(h)