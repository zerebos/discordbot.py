import discordbot
from . import embeds
from .colors import Colors


class Messages:

    def __init__(self, bot : discordbot):
        self.bot = bot
        self.default_color = self.bot.config.get("meta", {}).get("default_color", "#738bd7").replace("#", "")
        self.default_color = int(self.default_color, base=16)

    async def say(self, **params):
        embed = params.get("embed", None)
        destination = params.get("destination", None)
        if not embed:
            return

        if destination:
            return await self.bot.send_message(destination, embed=embed)
        else:
            return await self.bot.say(embed=embed)

    async def direct_message(self, **params):
        member = params.get("member", "")
        if not member:
            return
        e = embeds.build_embed(description=params.pop("message", ""), author=member.display_name, author_img=member.avatar_url,
                               color=params.pop("color", self.default_color), **params)
        return await self.say(**params, embed=e)

    async def full(self, **params):
        params["color"] = params.get("color", self.default_color)
        e = embeds.build_embed(**params)
        return await self.say(**params, embed=e)

    async def basic(self, **params):
        color = params.pop("color", self.default_color)
        if isinstance(color, Colors): color = color.value
        e = embeds.build_embed(title=params.pop("title", ""), description=params.pop("message", params.pop("description", "")),
                               color=params.pop("color", self.default_color), **params)
        return await self.say(**params, embed=e)

    async def success(self, **params):
        title = params.pop("title", "")
        message = params.pop("message", "Success")
        return await self.basic(title=title, message=message, color=Colors.success, **params)

    async def failure(self, **params):
        title = params.pop("title", "")
        message = params.pop("message", "Success")
        return await self.basic(title=title, message=message, color=Colors.failure, **params)

    async def toggle(self, **params):
        title = params.pop("title", "")
        success = params.pop("success", True)
        if success:
            fmt = "enabled"
        else:
            fmt = "disabled"
        message = params.pop("message", "{status}").format(status=fmt)

        if success:
            return await self.success(title=title, message=message, **params)
        else:
            return await self.failure(title=title, message=message, **params)