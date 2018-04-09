# -*- coding: utf-8 -*-

import discord
from discord.embeds import EmptyEmbed
import itertools
import inspect

from discord.ext.commands.core import GroupMixin, Command
from discord.ext.commands import CommandError
from discord.ext.commands.formatter import HelpFormatter, Paginator

def build_embed(**params):
    title = params.get("title", EmptyEmbed)
    description = params.get("description", EmptyEmbed)
    color = params.get("color", EmptyEmbed)
    url = params.get("url", EmptyEmbed)
    author = params.get("author", "")
    author_url = params.get("author_url", EmptyEmbed)
    author_img = params.get("author_img", EmptyEmbed)
    footer = params.get("footer", "")
    footer_img = params.get("footer_img", EmptyEmbed)
    timestamp = params.get("timestamp", EmptyEmbed)
    image = params.get("image", "")
    thumbnail = params.get("thumbnail", "")
    sections = params.get("sections", params.get("fields", []))
    e = discord.Embed()
    e.title = title
    e.description = description
    e.colour = color
    e.url = url
    if author:
        e.set_author(name=author, url=author_url, icon_url=author_img)
    if footer:
        e.set_footer(text=footer, icon_url=footer_img)
    e.timestamp = timestamp
    e.set_image(url=image)
    e.set_thumbnail(url=thumbnail)
    if sections:
        populate(e, sections)
    return e


def populate(embed : discord.Embed, sections : list):
    for section in sections:
        name = section.get("name", "")
        value = section.get("value", "")
        inline = section.get("inline", True)
        if not name or not value:
            continue
        embed.add_field(name=name, value=value, inline=inline)


class EmbedHelpFormatter(HelpFormatter):
    """The default base implementation that handles formatting of the help
    command.
    To override the behaviour of the formatter, :meth:`format`
    should be overridden. A number of utility functions are provided for use
    inside that method.
    Parameters
    -----------
    bot : DiscordBot
        Bot which will be using this formatter.
    show_hidden : bool
        Dictates if hidden commands should be shown in the output.
        Defaults to ``False``.
    show_check_failure : bool
        Dictates if commands that have their :attr:`Command.checks` failed
        shown. Defaults to ``False``.
    width : int
        The maximum number of characters that fit in a line.
        Defaults to 80.
    """
    def __init__(self, bot, show_hidden=False, show_check_failure=False, width=80):
        super().__init__(show_hidden=show_hidden, show_check_failure=show_check_failure, width=width)
        self.bot = bot

    def get_ending_note(self):
        command_name = self.context.invoked_with
        return "Type {0}{1} command for more info on a command.\n" \
               "You can also type {0}{1} category for more info on a category.".format(self.clean_prefix, command_name)

    def format(self):
        """Handles the actual behaviour involved with formatting.
        To change the behaviour, this method should be overridden.
        Returns
        --------
        list
            A paginated output of the help command.
        """

        values = {}
        title = "Description"
        description = self.command.description + "\n\n" + self.get_ending_note() if not self.is_cog() else inspect.getdoc(self.command)
        sections = []

        if isinstance(self.command, Command):
                description = self.command.short_doc
                sections = [{"name": "Usage", "value": self.get_command_signature()},
                            {"name": "More Info", "value": self.command.help.replace(self.command.short_doc, "").format(prefix=self.clean_prefix),
                             "inline": False}]

        def category(tup):
            cog = tup[1].cog_name
            return cog + ':' if cog is not None else '\u200bNo Category:'

        if self.is_bot():
            title = self.bot.user.display_name + " Help"
            data = sorted(self.filter_command_list(), key=category)
            for category, commands in itertools.groupby(data, key=category):
                section = {}
                commands = list(commands)
                if len(commands) > 0:
                    section['name'] = category
                section['value'] = self.add_commands(commands)
                section['inline'] = False
                sections.append(section)
        elif not sections or self.has_subcommands():
            section = {"name": "Commands:", "inline": False, "value": self.add_commands(self.filter_command_list())}
            sections.append(section)

        values['title'] = title
        values['description'] = description
        values['sections'] = sections
        return values

    def add_commands(self, commands):
        value = ""
        for name, command in commands:
            if name in command.aliases:
                # skip aliases
                continue

            value += name + " - " + command.short_doc + "\n"
        return value
