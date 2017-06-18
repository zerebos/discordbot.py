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
__version__ = '0.1.9'


from .discordbot import DiscordBot
from .colors import Colors
from .utilities import *
from .bot_utils.config import Config
from .bot_utils.paginator import Pages
from .bot_utils.formats import human_timedelta
from .bot_utils import checks, config, paginator, formats
from discord.ext import commands
from discord.ext.commands import *
from discord import *


from collections import namedtuple
VersionInfo = namedtuple('VersionInfo', 'major minor micro releaselevel serial')

version_info = VersionInfo(major=0, minor=1, micro=9, releaselevel='alpha', serial=0)