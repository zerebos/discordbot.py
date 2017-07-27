import copy, os
import datetime
import traceback
from collections import Counter
from collections import OrderedDict

import discord
import psutil
from discord.ext import commands

from ..bot_utils import config, checks
from ..bot_utils.paginator import Pages
from ..colors import Colors


class Meta:
    """Commands for utilities related to Discord or the Bot itself."""

    def __init__(self, bot):
        self.bot = bot
        self.process = psutil.Process()
        self.config = config.Config('stats.json', loop=bot.loop, directory="data")

    @commands.command(pass_context=True, aliases=['invite'])
    async def join(self, ctx):
        """Sends you the bot invite link."""
        perms = discord.Permissions.none()
        perms.read_messages = True
        perms.send_messages = True
        perms.manage_messages = True
        perms.embed_links = True
        perms.read_message_history = True
        perms.attach_files = True
        perms.add_reactions = True
        await self.bot.send_message(ctx.message.author, discord.utils.oauth_url(self.bot.client_id, perms))

    @commands.group(pass_context=True, no_pm=True, invoke_without_command=True)
    async def info(self, ctx, *, member : discord.Member = None):
        """Shows info about a member.

        This cannot be used in private messages. If you don't specify
        a member then the info returned will be yours.
        """
        channel = ctx.message.channel
        if member is None:
            member = ctx.message.author

        e = discord.Embed()
        roles = [role.name.replace('@', '@\u200b') for role in member.roles]
        shared = sum(1 for m in self.bot.get_all_members() if m.id == member.id)
        voice = member.voice_channel
        if voice is not None:
            other_people = len(voice.voice_members) - 1
            voice_fmt = '{} with {} others' if other_people else '{} by themselves'
            voice = voice_fmt.format(voice.name, other_people)
        else:
            voice = 'Not connected.'

        e.set_author(name=str(member), icon_url=member.avatar_url or member.default_avatar_url)
        e.set_footer(text='Member since').timestamp = member.joined_at
        e.add_field(name='ID', value=member.id)
        e.add_field(name='Servers', value='%s shared' % shared)
        e.add_field(name='Voice', value=voice)
        e.add_field(name='Created', value=member.created_at)
        e.add_field(name='Roles', value=', '.join(roles))
        e.colour = member.colour

        if member.avatar:
            e.set_image(url=member.avatar_url)

        await self.bot.say(embed=e)

    @info.command(name='server', pass_context=True, no_pm=True)
    async def server_info(self, ctx):
        server = ctx.message.server
        roles = [role.name.replace('@', '@\u200b') for role in server.roles]

        secret_member = copy.copy(server.me)
        secret_member.id = '0'
        secret_member.roles = [server.default_role]

        # figure out what channels are 'secret'
        secret_channels = 0
        secret_voice = 0
        text_channels = 0
        for channel in server.channels:
            perms = channel.permissions_for(secret_member)
            is_text = channel.type == discord.ChannelType.text
            text_channels += is_text
            if is_text and not perms.read_messages:
                secret_channels += 1
            elif not is_text and (not perms.connect or not perms.speak):
                secret_voice += 1

        voice_channels = len(server.channels) - text_channels
        member_by_status = Counter(str(m.status) for m in server.members)

        e = discord.Embed()
        e.title = 'Info for ' + server.name
        e.add_field(name='ID', value=server.id)
        e.add_field(name='Owner', value=server.owner)
        if server.icon:
            e.set_thumbnail(url=server.icon_url)

        if server.splash:
            e.set_image(url=server.splash_url)

        e.add_field(name='Partnered?', value='Yes' if len(server.features) >= 3 else 'No')

        fmt = 'Text %s (%s secret)\nVoice %s (%s locked)'
        e.add_field(name='Channels', value=fmt % (text_channels, secret_channels, voice_channels, secret_voice))

        fmt = 'Total: {0}\nOnline: {1[online]}' \
              ', Offline: {1[offline]}' \
              '\nDnD: {1[dnd]}' \
              ', Idle: {1[idle]}'

        e.add_field(name='Members', value=fmt.format(server.member_count, member_by_status))
        e.add_field(name='Roles', value=', '.join(roles) if len(roles) < 10 else '%s roles' % len(roles))
        e.set_footer(text='Created').timestamp = server.created_at
        await self.bot.say(embed=e)

    async def on_command(self, command, ctx):
        message = ctx.message
        if message.channel.is_private:
            id = ctx.message.author.id
            destination = 'Private Message'
        else:
            id = ctx.message.server.id
            destination = '#{0.channel.name} ({0.server.name})'.format(message)

        self.bot.logs['stats'].info('{0.timestamp}: {0.author.name} in {1}: {0.content}'.format(message, destination))

        data = self.config.get('data', {})
        server_data = data.get(id, {})
        server_data[ctx.command.qualified_name] = server_data.get(ctx.command.qualified_name, 0) + 1
        data[id] = server_data
        await self.config.put('data', data)

    @commands.command(pass_context=True, hidden=True)
    @checks.is_owner()
    async def commandstats(self, ctx, all_stats : bool=False):
        data = self.config.get('data', {})
        if all_stats:
            title = "Bot"
            commands = {}
            for d in data:
                server_cmds = data.get(d, {})
                for c in server_cmds.keys():
                    current = commands.get(c, 0)
                    commands[c] = current + server_cmds[c]
        else:
            title = "This Server"
            commands = data.get(ctx.message.server.id, {})
        commands = OrderedDict(sorted(commands.items(), key=lambda x: x[1], reverse=True))

        stats = []
        for c in commands.keys():
            stats.append(c + ": " + str(commands[c]))
        try:
            pager = Pages(self.bot, message=ctx.message, entries=stats)
            pager.embed.colour = Colors.get_default(self.bot)
            pager.embed.set_author(name="Command stats for " + title,
                                   icon_url=ctx.message.server.icon_url)
            await pager.paginate()

        except Exception as e:
            await self.bot.say(e)

    def get_bot_uptime(self, *, brief=False):
        now = datetime.datetime.utcnow()
        delta = now - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        if not brief:
            if days:
                fmt = '{d} days, {h} hours, {m} minutes, and {s} seconds'
            else:
                fmt = '{h} hours, {m} minutes, and {s} seconds'
        else:
            fmt = '{h}h {m}m {s}s'
            if days:
                fmt = '{d}d ' + fmt

        return fmt.format(d=days, h=hours, m=minutes, s=seconds)

    @commands.command(aliases=['botstats'])
    async def about(self):
        """Tells you information about the bot itself.

        This is more information about the bot, not really
        sure when this comes into play tbh, thats what I am
        testing right now.
        """

        cmd = r'git show -s -3 --format="%s (%cr)"'
        if os.name == 'posix':
            cmd = cmd.format(r'\`%h\`')
        else:
            cmd = cmd.format(r'`%h`')

        embed = discord.Embed()
        embed.colour = Colors.get_default(self.bot)

        embed.add_field(name="About "+self.bot.user.name+":", value=self.bot.description, inline=False)
        
        if os.popen('git rev-list --all --count').close() is None and os.popen('git rev-parse').close() is None:
            revision = os.popen(cmd).read().strip()
            embed.add_field(name="Latest Changes:", value=revision, inline=False)

        try:
            owner = self._owner
        except AttributeError:
            owner = self._owner = await self.bot.get_user_info(self.bot.config.get('meta', {}).get('owner', "249746236008169473"))

        if self.bot.ownerInviteLink:
            embed.title = owner.name+'\'s Server Invite'
            embed.url = self.bot.ownerInviteLink

        embed.set_author(name="Created by "+str(owner), icon_url=owner.avatar_url)

        # statistics
        total_members = sum(len(s.members) for s in self.bot.servers)
        total_online  = sum(1 for m in self.bot.get_all_members() if m.status != discord.Status.offline)
        unique_members = set(self.bot.get_all_members())
        unique_online = sum(1 for m in unique_members if m.status != discord.Status.offline)
        channel_types = Counter(c.type for c in self.bot.get_all_channels())
        voice = channel_types[discord.ChannelType.voice]
        text = channel_types[discord.ChannelType.text]

        members = '%s total\n%s online\n%s unique\n%s unique online' % (total_members, total_online, len(unique_members), unique_online)
        embed.add_field(name='Members', value=members)
        embed.add_field(name='Channels', value='{} total\n{} text\n{} voice'.format(text + voice, text, voice))
        memory_usage = self.process.memory_full_info().uss / 1024**2
        cpu_usage = self.process.cpu_percent() / psutil.cpu_count()
        embed.add_field(name='Process', value='{:.2f} MiB\n{:.2f}% CPU'.format(memory_usage, cpu_usage))
        embed.set_footer(text='Made with discord.py & discordbot.py', icon_url='http://i.imgur.com/5BFecvA.png')
        embed.timestamp = self.bot.uptime

        data = self.config.get('data', {})
        summation = 0
        for server in data:
            summation += sum(data[server].values())

        embed.add_field(name='Servers', value=str(len(self.bot.servers)))
        embed.add_field(name='Commands Run', value=summation)
        embed.add_field(name='Uptime', value=self.get_bot_uptime(brief=True))

        await self.bot.say(embed=embed)

    async def send_server_stat(self, server_event, server):

        bots = sum(m.bot for m in server.members)
        total = server.member_count
        online = sum(m.status is discord.Status.online for m in server.members)

        if server.me:
            time = server.me.joined_at
        else:
            time = datetime.datetime.now()

        message = '{0} at {1}: {2.name} (ID: {2.id}), Owner: {2.owner} (ID: {2.owner.id}), Members: {3}, '\
                  'Bots: {4} ({5:.2%}), Online: {6} ({7:.2%})'
        message = message.format(server_event, time, server, total, bots, bots / total, online, online / total)
        self.bot.logs['info'].info(message)

    async def on_server_join(self, server):
        await self.send_server_stat("Joined Server", server)

    async def on_server_remove(self, server):
        await self.send_server_stat("Left Server", server)

    async def on_command_error(self, error, ctx):
        ignored = (commands.NoPrivateMessage, commands.DisabledCommand, commands.CheckFailure,
                   commands.CommandNotFound, commands.UserInputError, discord.HTTPException)
        error = getattr(error, 'original', error)

        if isinstance(error, ignored):
            return

        if ctx.message.server:
            fmt = 'Channel: {0} (ID: {0.id})\nGuild: {1} (ID: {1.id})'
        else:
            fmt = 'Channel: {0} (ID: {0.id})'

        exc = traceback.format_exception(type(error), error, error.__traceback__, chain=False)
        description = '```py\n%s\n```' % ''.join(exc)
        time = datetime.datetime.utcnow()

        name = ctx.command.qualified_name
        author = '{0} (ID: {0.id})'.format(ctx.message.author)
        location = fmt.format(ctx.message.channel, ctx.message.server)

        message = '{0} at {1}: Called by: {2} in {3}. More info: {4}'.format(name, time, author, location, description)

        self.bot.logs['discord'].critical(message)


def setup(bot):
    bot.add_cog(Meta(bot))
