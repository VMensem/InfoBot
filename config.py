import os

class Config:
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    DISCORD_COMMAND_PREFIX = "!"

    def validate(self):
        ok = True
        if not self.DISCORD_TOKEN:
            print("❌ Отсутствует DISCORD_TOKEN")
            ok = False
        if not self.TELEGRAM_TOKEN:
            print("❌ Отсутствует TELEGRAM_TOKEN")
            ok = False
        return ok

config = Config()
API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")
REQUEST_TIMEOUT = 10
