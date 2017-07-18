from difflib import SequenceMatcher
import aiohttp
import re

def wordcount(string : str):
    return len(string.split())

def escape_markdown(string : str):
    return re.sub("([*~_`])", r"\\\1", string)

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def constant(f):
    def fset(self, value):
        raise TypeError
    def fget(self):
        return f()
    return property(fget, fset)

async def fetch(url, loop):
    async with aiohttp.ClientSession(loop=loop) as session:
        with aiohttp.Timeout(10, loop=session.loop):
            async with session.get(url) as response:
                return await response.text()