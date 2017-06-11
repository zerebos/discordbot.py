from collections import OrderedDict

import discord
from ..bot_utils import config, checks
from ..bot_utils.paginator import Pages
from discord.ext import commands


class Reactions:
    """React to different phrases with a response and emoji reactions."""

    def __init__(self, bot):
        self.bot = bot
        self.config = config.Config('reactions.json', loop=bot.loop, directory="data")

    async def on_message(self, message):
        if message.author.bot:
            return

        if message.channel.is_private:
            return

        if message.channel.id in self.bot.get_cog("BotAdmin").config.get('ignored', []):
            return

        if not message.content.startswith(self.bot.command_prefix):
            await self._check_for_reactions(message)

    async def _check_for_reactions(self, message):
        reactions = self.config.get(message.server.id, {})
        activated = [s for s in message.content.lower().split() if s in reactions.keys()]
        activated = []
        msg = message.content.lower()
        for r in reactions.keys():
            location = msg.find(r.lower())
            if location >= 0:
                if location + len(r) >= len(msg):
                    activated.append(r)
                elif msg[location + len(r)] in [' ', '.', '!', '?', ',', "'"]:
                    activated.append(r)
        if activated:
            for reaction in activated:
                response = reactions.get(reaction, {}).get("response", "")
                reacts = reactions.get(reaction, {}).get("reaction", [])
                if response:
                    await self.bot.send_message(message.channel, response)

                if reacts:
                    for r in reacts:
                        await self.bot.add_reaction(message, r)

    @commands.command(pass_context=True, no_pm=True, aliases=["acr"])
    @checks.mod_or_permissions(manage_messages=True)
    async def addreaction(self, ctx, *, reactor : str):
        """Interactively adds a custom reaction"""

        data = self.config.get(ctx.message.server.id, {})
        keyword = data.get(reactor, {})

        if keyword:
            await self.bot.responses.failure(message="Reaction '{}' already exists.".format(reactor))
            return

        await self.bot.say("Okay, I'll react to '{}'. What do you want me to say? (Type $none for no response)".format(reactor))
        response = await self.bot.wait_for_message(author=ctx.message.author)

        reactions = []
        def check(reaction, user):
            if str(reaction.emoji) != "\U000023f9":
                reactions.append(reaction.emoji)
                return False
            else:
                return user == ctx.message.author

        msg = await self.bot.say("Awesome! Now react to this message any reactions I should have to '{}'. (React \U000023f9 to stop)".format(reactor))
        await self.bot.wait_for_reaction(message=msg, check=check)

        for i, reaction in enumerate(reactions):
            reaction = reaction if isinstance(reaction, str) else reaction.name + ":" + str(reaction.id)
            await self.bot.add_reaction(ctx.message, reaction)
            reactions[i] = reaction

        if response:
            keyword["response"] = response.content if response.content.lower() != "$none" else ""
        keyword["reaction"] = reactions
        data[reactor] = keyword
        await self.config.put(ctx.message.server.id, data)

        await self.bot.responses.success(message="Reaction '{}' has been added.".format(reactor))

    @commands.command(pass_context=True, no_pm=True, aliases=["lcr"])
    @checks.mod_or_permissions(manage_messages=True)
    async def listreactions(self, ctx):
        """Lists all the reactions for the server"""
        data = self.config.get(ctx.message.server.id, {})
        if not data:
            await self.bot.responses.failure(message="There are no reactions on this server.")
            return
        try:
            pager = Pages(self.bot, message=ctx.message, entries=list(data.keys()))
            pager.embed.colour = 0x738bd7  # blurple
            pager.embed.set_author(name=ctx.message.server.name + " Reactions", icon_url=ctx.message.server.icon_url)
            await pager.paginate()

        except Exception as e:
            await self.bot.say(e)

    @commands.command(pass_context=True, no_pm=True, aliases=["vcr"])
    @checks.mod_or_permissions(manage_messages=True)
    async def viewreaction(self, ctx, *, reactor : str):
        """Views a specific reaction"""
        data = self.config.get(ctx.message.server.id, {})
        keyword = data.get(reactor, {})

        if not keyword:
            await self.bot.responses.failure(message="Reaction '{}' was not found.".format(reactor))
            return

        response = data.get(reactor, {}).get("response", "")
        reacts = data.get(reactor, {}).get("reaction", [])

        for i, r in enumerate(reacts):
            if ":" in r:
                reacts[i] = "<:" + r + ">"

        reacts = " ".join(reacts) if reacts else "-"
        response = response if response else "-"

        string = "Here's what I say to '{reactor}': {response}\n"\
                 "I'll react to this message how I react to '{reactor}'.".format(reactor=reactor,response=response)

        await self.bot.responses.full(sections=[{"name": "Response", "value": response},
                                                {"name": "Reactions", "value": reacts, "inline": False}])



    @commands.command(pass_context=True, no_pm=True, aliases=["dcr"])
    @checks.mod_or_permissions(manage_messages=True)
    async def deletereaction(self, ctx, *, reactor : str):
        """Removes a reaction"""
        data = self.config.get(ctx.message.server.id, {})
        keyword = data.get(reactor, {})
        if keyword:
            data.pop(reactor)
            await self.config.put(ctx.message.server.id, data)
            await self.bot.responses.success(message="Reaction '{}' has been deleted.".format(reactor))
        else:
            await self.bot.responses.failure(message="Reaction '{}' was not found.".format(reactor))

    @commands.command(pass_context=True, no_pm=True, aliases=["dcrall"])
    @checks.mod_or_permissions(manage_messages=True)
    async def deleteallreactions(self, ctx):
        """Removes a reaction"""
        data = self.config.get(ctx.message.server.id, {})
        if data:
            await self.config.put(ctx.message.server.id, {})
            await self.bot.responses.success(message="All reactions have been deleted.")
        else:
            await self.bot.responses.failure(message="This server has no reactions.")

def setup(bot):
    bot.add_cog(Reactions(bot))
