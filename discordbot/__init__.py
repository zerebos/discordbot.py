# -*- coding: utf-8 -*-

"""
Discord API Wrapper
~~~~~~~~~~~~~~~~~~~
A basic wrapper for the Discord.py library.
:copyright: (c) 2015-2016 Zack Rauen
:license: MIT, see LICENSE for more details.
"""

__title__ = 'discordbot'
__author__ = 'Zack Rauen'
__license__ = 'MIT'
__copyright__ = 'Copyright 2017 Zack Rauen'
__version__ = '0.1.7'


from .discordbot import DiscordBot
from .utilities import *
from .bot_utils import checks, config, paginator, formats
from discord.ext import commands
import discord


from collections import namedtuple
VersionInfo = namedtuple('VersionInfo', 'major minor micro releaselevel serial')

version_info = VersionInfo(major=0, minor=1, micro=7, releaselevel='alpha', serial=0)