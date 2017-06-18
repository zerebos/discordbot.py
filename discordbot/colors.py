from enum import Enum

class Colors(Enum):
    success = 0x71cd40
    failure = 0xe74a3c
    blurple = 0x738bd7

    @staticmethod
    def generate_color(red, green, blue):
        return int("0x{:02X}{:02X}{:02X}".format(red, green, blue), base=16)

    @staticmethod
    def get_default(bot):
        color = bot.config.get("meta", {}).get("default_color", "#738bd7").replace("#", "")
        return int(color, base=16)