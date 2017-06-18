import argparse
import asyncio
from collections import Counter, defaultdict

import copy
import discord
from discord.ext import commands

import discordbot.embeds
from ..bot_utils import checks
from ..bot_utils import config


class Arguments(argparse.ArgumentParser):
    def error(self, message):
        raise RuntimeError(message)


class BotAdmin:
    """Bot administration commands."""

    def __init__(self, bot):
        self.bot = bot
        self.config = config.Config('botadmin.json', loop=bot.loop, directory="data")

        # guild_id: set(user_id)
        self._recently_kicked = defaultdict(set)

    def bot_user(self, message):
        return message.server.me if message.channel.is_private else self.bot.user

    def is_plonked(self, server, member):
        db = self.config.get('plonks', {}).get(server.id, [])
        bypass_ignore = member.server_permissions.manage_server
        if not bypass_ignore and member.id in db:
            return True
        return False

    def __check(self, ctx):
        msg = ctx.message

        if checks.is_owner_check(msg):
            return True

        # user is bot banned
        if msg.server:
            if self.is_plonked(msg.server, msg.author):
                return False

        # check if the channel is ignored
        # but first, resolve their permissions

        perms = msg.channel.permissions_for(msg.author)
        bypass_ignore = perms.administrator

        # now we can finally realise if we can actually bypass the ignore.

        if not bypass_ignore and msg.channel.id in self.config.get('ignored', []):
            return False

        if checks.is_owner_check(msg):
            return True

        try:
            entry = self.config.get('commands', {}).get(msg.server.id, [])
        except (KeyError, AttributeError):
            return True
        else:
            name = ctx.command.qualified_name.split(' ')[0]
            return name not in entry

    async def on_message(self, message):
        if message.author.bot:
            return

        if message.channel.is_private and not message.content.startswith(self.bot.command_prefix):
            owner_id = self.bot.config.get("meta", {}).get("owner", "249746236008169473")
            to_send = self.bot.config.get("meta", {}).get("send_dms", True)
            image = ""
            embed = {}
            if message.embeds:
                embed = message.embeds[0]
            if message.attachments:
                image = message.attachments[0]['url']
            if message.author.id != owner_id and to_send:
                owner = await self.bot.get_user_info(owner_id)
                if message.content:
                    await self.bot.responses.basic(destination=owner, message=message.content, author=str(message.author), author_img=message.author.avatar_url, color=0x71cd40, image=image)
                if embed:
                    embed.pop("author", "")
                    url = embed.pop("thumbnail", {}).get("url", "")
                    e = discord.Embed.from_data(embed)
                    e.set_image(url=url)
                    e.set_author(name="Embed from " + str(message.author), icon_url=message.author.avatar_url)
                    await self.bot.send_message(destination=owner, embed=e)

    @commands.command(name='dms', hidden=True)
    @checks.is_owner()
    async def _senddms(self):
        """Toggles sending DMs to owner."""
        data = self.bot.config.get("meta", {})
        tosend = data.get('send_dms', True)
        data['send_dms'] = not tosend
        await self.bot.config.put('meta', data)
        await self.bot.responses.toggle(message="Forwarding of DMs to owner has been {status}.", success=data['send_dms'])

    @commands.command(name='quit', hidden=True)
    @checks.is_owner()
    async def _quit(self):
        """Quits the bot."""
        await self.bot.responses.failure(message="Bot shutting down")
        await self.bot.logout()

    @commands.command(name='setname', hidden=True)
    @checks.is_owner()
    async def _setname(self, *, username: str):
        """Changes the bots username."""
        await self.bot.edit_profile(username=username)

    @commands.command(name='setcolor', hidden=True)
    @checks.is_owner()
    async def _setcolor(self, *, color : discord.Colour):
        """Sets the default color of embeds."""
        data = self.bot.config.get("meta", {})
        data['default_color'] = str(color)
        await self.bot.config.put('meta', data)
        await self.bot.responses.basic(message="The default color has been updated.")

    @commands.command(name='runtest', hidden=True)
    @checks.is_owner()
    async def _runtest(self):
        """Sets the default color of embeds."""
        sections = [{"name": "Section 1", "value": "Value 1"}, {"name": "Section 2"}, {"name": "Section 2.5", "value": "Value 2.5"},
                    {"name": "Section 3", "value": "Value 3", "inline": False}]
        e = discordbot.embeds.build_embed(title="IDK", description="foo bar", sections=sections)
        await self.bot.say(embed=e)

    @discordbot.command(name="do", pass_context=True, hidden=True)
    @discordbot.checks.is_owner()
    async def _do(self, ctx, times: int, *, command):
        """Repeats a command a specified number of times."""
        msg = copy.copy(ctx.message)
        msg.content = command
        for i in range(times):
            await self.bot.process_commands(msg)

    @commands.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(manage_server=True)
    async def disable(self, ctx, *, command: str):
        """Disables a command for this server.

        You must have Manage Server permissions or the
        Bot Admin role to use this command.
        """
        command = command.lower()

        if command in ('enable', 'disable'):
            return await self.bot.responses.failure(message='Cannot disable that command.')

        if command not in self.bot.commands:
            return await self.bot.responses.failure(message='Command "{}" was not found.'.format(command))

        guild_id = ctx.message.server.id
        cmds = self.config.get('commands', {})
        entries = cmds.get(guild_id, [])
        entries.append(command)
        cmds[guild_id] = entries
        await self.config.put('commands', cmds)
        await self.bot.responses.success(message='"%s" command disabled in this server.' % command)

    @commands.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(manage_server=True)
    async def enable(self, ctx, *, command: str):
        """Enables a command for this server.

        You must have Manage Server permissions or the
        Bot Admin role to use this command.
        """
        command = command.lower()
        guild_id = ctx.message.server.id
        cmds = self.config.get('commands', {})
        entries = cmds.get(guild_id, [])

        try:
            entries.remove(command)
        except KeyError:
            await self.bot.responses.failure(message='The command does not exist or is not disabled.')
        else:
            cmds[guild_id] = entries
            await self.config.put('commands', cmds)
            await self.bot.responses.success(message='"%s" command enabled in this server.' % command)

    @commands.group(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(manage_channels=True)
    async def ignore(self, ctx):
        """Handles the bot's ignore lists.

        To use these commands, you must have the Bot Admin role or have
        Manage Channels permissions. These commands are not allowed to be used
        in a private message context.

        Users with Manage Roles or Bot Admin role can still invoke the bot
        in ignored channels.
        """
        if ctx.invoked_subcommand is None:
            await self.bot.say('Invalid subcommand passed: {0.subcommand_passed}'.format(ctx))

    @ignore.command(name='list', pass_context=True)
    async def ignore_list(self, ctx):
        """Tells you what channels are currently ignored in this server."""

        ignored = self.config.get('ignored', [])
        channel_ids = set(c.id for c in ctx.message.server.channels)
        result = []
        for channel in ignored:
            if channel in channel_ids:
                result.append('<#{}>'.format(channel))

        if result:
            await self.bot.responses.basic(title="Ignored Channels:", message='\n\n{}'.format(', '.join(result)))
        else:
            await self.bot.responses.failure(message='I am not ignoring any channels here.')

    @ignore.command(name='channel', pass_context=True)
    async def channel_cmd(self, ctx, *, channel : discord.Channel = None):
        """Ignores a specific channel from being processed.

        If no channel is specified, the current channel is ignored.
        If a channel is ignored then the bot does not process commands in that
        channel until it is unignored.
        """

        if channel is None:
            channel = ctx.message.channel

        ignored = self.config.get('ignored', [])
        if channel.id in ignored:
            await self.bot.responses.failure(message='That channel is already ignored.')
            return

        ignored.append(channel.id)
        await self.config.put('ignored', ignored)
        await self.bot.responses.success(message='Channel <#{}> will be ignored.'.format(channel.id))

    @ignore.command(name='all', pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def _all(self, ctx):
        """Ignores every channel in the server from being processed.

        This works by adding every channel that the server currently has into
        the ignore list. If more channels are added then they will have to be
        ignored by using the ignore command.

        To use this command you must have Manage Server permissions along with
        Manage Channels permissions. You could also have the Bot Admin role.
        """

        ignored = self.config.get('ignored', [])
        channels = ctx.message.server.channels
        ignored.extend(c.id for c in channels if c.type == discord.ChannelType.text)
        await self.config.put('ignored', list(set(ignored))) # make unique
        await self.bot.responses.success(message='All channels ignored.')

    @commands.group(pass_context=True, no_pm=True, invoke_without_command=True)
    @checks.admin_or_permissions(manage_channels=True)
    async def unignore(self, ctx, *channels: discord.Channel):
        """Unignores channels from being processed.

        If no channels are specified, it unignores the current channel.

        To use this command you must have the Manage Channels permission or have the
        Bot Admin role.
        """

        if len(channels) == 0:
            channels = (ctx.message.channel,)

        # a set is the proper data type for the ignore list
        # however, JSON only supports arrays and objects not sets.
        ignored = self.config.get('ignored', [])
        result = []
        for channel in channels:
            try:
                ignored.remove(channel.id)
            except ValueError:
                pass
            else:
                result.append('<#{}>'.format(channel.id))

        await self.config.put('ignored', ignored)
        await self.bot.responses.success(message='Channel(s) {} will no longer be ignored.'.format(', '.join(result)))

    @unignore.command(name='all', pass_context=True, no_pm=True)
    @checks.admin_or_permissions(manage_channels=True)
    async def unignore_all(self, ctx):
        """Unignores all channels in this server from being processed.

        To use this command you must have the Manage Channels permission or have the
        Bot Admin role.
        """
        channels = [c for c in ctx.message.server.channels if c.type is discord.ChannelType.text]
        await ctx.invoke(self.unignore, *channels)

    @commands.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def cleanup(self, ctx, search : int = 100):
        """Cleans up the bot's messages from the channel.

        If a search number is specified, it searches that many messages to delete.
        If the bot has Manage Messages permissions, then it will try to delete
        messages that look like they invoked the bot as well.

        After the cleanup is completed, the bot will send you a message with
        which people got their messages deleted and their count. This is useful
        to see which users are spammers.

        To use this command you must have Manage Messages permission or have the
        Bot Mod role.
        """

        spammers = Counter()
        channel = ctx.message.channel
        prefixes = self.bot.command_prefix
        if callable(prefixes):
            prefixes = prefixes(self.bot, ctx.message)

        def is_possible_command_invoke(entry):
            valid_call = any(entry.content.startswith(prefix) for prefix in prefixes)
            return valid_call and not entry.content[1:2].isspace()

        can_delete = channel.permissions_for(channel.server.me).manage_messages

        if not can_delete:
            api_calls = 0
            async for entry in self.bot.logs_from(channel, limit=search, before=ctx.message):
                if api_calls and api_calls % 5 == 0:
                    await asyncio.sleep(1.1)

                if entry.author == self.bot.user:
                    await self.bot.delete_message(entry)
                    spammers['Bot'] += 1
                    api_calls += 1

                if is_possible_command_invoke(entry):
                    try:
                        await self.bot.delete_message(entry)
                    except discord.Forbidden:
                        continue
                    else:
                        spammers[entry.author.display_name] += 1
                        api_calls += 1
        else:
            predicate = lambda m: m.author == self.bot.user or is_possible_command_invoke(m)
            deleted = await self.bot.purge_from(channel, limit=search, before=ctx.message, check=predicate)
            spammers = Counter(m.author.display_name for m in deleted)

        deleted = sum(spammers.values())
        messages = ['%s %s removed.' % (deleted, 'message was' if deleted == 1 else 'messages were')]
        if deleted:
            messages.append('')
            spammers = sorted(spammers.items(), key=lambda t: t[1], reverse=True)
            messages.extend(map(lambda t: '**{0[0]}**: {0[1]}'.format(t), spammers))

        msg = await self.bot.responses.basic(title="Removed Messages:", message='\n'.join(messages))
        await asyncio.sleep(10)
        await self.bot.delete_message(msg)

    @commands.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def plonk(self, ctx, *, member: discord.Member):
        """Bans a user from using the bot.

        This bans a person from using the bot in the current server.
        There is no concept of a global ban. This ban can be bypassed
        by having the Manage Server permission.

        To use this command you must have the Manage Server permission
        or have a Bot Admin role.
        """

        plonks = self.config.get('plonks', {})
        guild_id = ctx.message.server.id
        db = plonks.get(guild_id, [])

        if member.id in db:
            await self.bot.responses.failure(message='That user is already bot banned in this server.')
            return

        db.append(member.id)
        plonks[guild_id] = db
        await self.config.put('plonks', plonks)
        await self.bot.responses.success(message='%s has been banned from using the bot in this server.' % member)

    @commands.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def plonks(self, ctx):
        """Shows members banned from the bot."""
        plonks = self.config.get('plonks', {})
        guild = ctx.message.server
        db = plonks.get(guild.id, [])
        members = '\n'.join(map(str, filter(None, map(guild.get_member, db))))
        if members:
            await self.bot.responses.basic(title="Plonked Users:", message=members)
        else:
            await self.bot.responses.failure(message='No members are banned in this server.')

    @commands.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def unplonk(self, ctx, *, member: discord.Member):
        """Unbans a user from using the bot.

        To use this command you must have the Manage Server permission
        or have a Bot Admin role.
        """

        plonks = self.config.get('plonks', {})
        guild_id = ctx.message.server.id
        db = plonks.get(guild_id, [])

        try:
            db.remove(member.id)
        except ValueError:
            await self.bot.responses.failure(message='%s is not banned from using the bot in this server.' % member)
        else:
            plonks[guild_id] = db
            await self.config.put('plonks', plonks)
            await self.bot.responses.success(message='%s has been unbanned from using the bot in this server.' % member)

def setup(bot):
    bot.add_cog(BotAdmin(bot))
