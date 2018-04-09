# -*- coding: utf-8 -*-

import aiohttp
import mimetypes
from difflib import SequenceMatcher
import re


def wordcount(string: str):
	return len(string.split())


def escape_markdown(string: str):
	return re.sub("([*~_`])", r"\\\1", string)


def similar(a, b):
	return SequenceMatcher(None, a, b).ratio()


async def fetchURL(url, loop):
	async with aiohttp.ClientSession(loop=loop) as session:
		with aiohttp.Timeout(10, loop=session.loop):
			async with session.get(url) as response:
				return await response.text()


async def downloadImage(url, folder, name, loop, chunkSize=20):
	result = {'canAccessURL': False, 'isImage': False, 'fileSaved': False}
	headers = {
		'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
		'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
		'Accept-Encoding': 'none',
		'Accept-Language': 'en-US,en;q=0.8',
		'Connection': 'keep-alive'}
	async with aiohttp.ClientSession(loop=loop) as session:
		with aiohttp.Timeout(10, loop=session.loop):
			async with session.get(url, headers=headers) as response:
				content_type = response.headers['content-type']
				if response.status == 200:
					result['canAccessURL'] = True
				if "image" in content_type:
					result['isImage'] = True
				if not result['canAccessURL'] or not result['isImage']:
					return result
				extension = mimetypes.guess_extension(content_type)
				if extension == '.jpe':
					extension = '.jpg'

				with open(folder + "/" + name + extension, 'wb') as fd:
					while True:
						chunk = await response.content.read(chunkSize)
						if not chunk:
							break
						fd.write(chunk)
				result['fileSaved'] = True
				return result