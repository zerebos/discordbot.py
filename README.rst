Discordbot.py
=============
|PyPI| |Python|

.. |PyPI| image:: https://img.shields.io/pypi/v/discordbot.py.svg
   :target: https://pypi.python.org/pypi/discordbot.py/
.. |Python| image:: https://img.shields.io/pypi/pyversions/discordbot.py.svg
   :target: https://pypi.python.org/pypi/discordbot.py/
This is an extention of `Rapptz'
discord.py <https://github.com/Rapptz/discord.py>`__ to help make it
even easier to make new bots, and simpler to make complex ones.

Current version of the code should be stable, but use at your own risk.

The documentation will be built up over time hopefully.

Installation
------------

This is a part of the official PyPI package directory and can be installed with pip.

.. code:: bash

   pip install discordbot.py


Examples
--------

Simple Example
~~~~~~~~~~~~~~

To create a bot that will greet new members when they join and greet
anyone that types ``!greet`` you can do the following:

.. code:: py

    import discordbot
    import asyncio

    bot = discordbot.DiscordBot()

    @bot.event
    async def on_member_join(member):
        await bot.send_message(member.server, "Welcome {0.mention}, would you like to introduce yourself?".format(member))
        
    @bot.command(pass_context=True)
    async def greet(ctx):
        """Greets the user.

        This is additional help text that will only show up if 
        help is called on the command itself as opposed to the 
        normal short help which shows up in the main help.
        """
        await bot.responses.say("Hi there, {0.mention}, how are you?".format(ctx.message.author))

    bot.run()

This should be accompanied by a ``settings.json`` file like this:

.. code:: json

    {
      "meta": {
        "owner": "YOUR_ID",
        "prefix": "!",
        "description": "Optional description of the bot."
      },
      "credentials": {
        "token": "YOUR_TOKEN_HERE",
        "client_id": "YOUR_CLIENT_ID"
      }
    }

Features
--------

Built-in Cogs
~~~~~~~~~~~~~

Administrative and Meta cogs are built-in.

Commands Extension
~~~~~~~~~~~~~~~~~~

This bakes the commands extension directly in by default.

Flexible Settings
~~~~~~~~~~~~~~~~~

The bot can be fully set up through python with no JSON or vice versa.

Through JSON
^^^^^^^^^^^^

Your ``bot.py`` could be as minimal as this:

.. code:: py

    import asyncio
    import discordbot

    bot = discordbot.DiscordBot()

    if __name__ == '__main__':
        bot.load_cogs()
        bot.run()

As long as you have a JSON file like this:

.. code:: json

    {
      "meta": {
        "owner": "YOUR_ID",
        "prefix": "ANY_PREFIX",
        "description": "Optional description of the bot."
      },
      "credentials": {
        "token": "YOUR_TOKEN_HERE",
        "client_id": "YOUR_CLIENT_ID"
      },
      "cogs": ["cog_folder.cog_name", "cog_folder.another_cog"]
    }

Through Python
^^^^^^^^^^^^^^

This is very similar to how it is done for discord.py

New Help
~~~~~~~~

Embed Formatter
^^^^^^^^^^^^^^^

The new help formatter is prettier and done using embeds.

Smarter Searching
^^^^^^^^^^^^^^^^^

The searching and matching has been adjusted to better match what the
user is looking for including being case insensitive.

Helper Classes
~~~~~~~~~~~~~~

Embeds
^^^^^^

This includes a simpler and easy to follow embed builder.

Colors
^^^^^^

This allows a preset of colors for things like success, failure, or the
Discord blurple. Also has utility functions for generating ``Color``
objects from RGB values.

Messages
^^^^^^^^

This allows responses and other messages to be sent using automatically
built embeds to make the messages look nicer. This also some utility
functions like a toggle which uses the success and failure colors.

Utilities
^^^^^^^^^

The utilities include setting constants, asynchronous web requests,
string similarity ratios, word counts, and markdown escaping—this is
especially useful for those funky usernames.

Logs
~~~~

In a separate folder the bot will generate 3 logs, one for errors
(hopefully empty), one for stats which gives more specifics and can help
track down pesky bugs and the last one which rounds out additional info
like where your bot is being added and kicked from. This can be
overridden of course.
