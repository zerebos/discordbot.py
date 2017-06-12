from difflib import SequenceMatcher
import aiohttp

def wordcount(string : str):
    return len(string.split())

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


async def fetch(url, loop):
    async with aiohttp.ClientSession(loop=loop) as session:
        with aiohttp.Timeout(10, loop=session.loop):
            async with session.get(url) as response:
                return await response.text()