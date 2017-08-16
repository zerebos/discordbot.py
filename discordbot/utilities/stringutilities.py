from difflib import SequenceMatcher
import re

class StringUtilities:
    @staticmethod
    def wordcount(string: str):
        return len(string.split())

    @staticmethod
    def escape_markdown(string: str):
        return re.sub("([*~_`])", r"\\\1", string)

    @staticmethod
    def similar(a, b):
        return SequenceMatcher(None, a, b).ratio()