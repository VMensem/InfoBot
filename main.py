#!/usr/bin/env python3
from flask import Flask
import threading
import os
import asyncio
import logging
import sys

from config import config
from bot_handlers.telegram_handlers import TelegramBotHandlers
from bot_handlers.discord_handlers import DiscordBotHandlers
from arizona_api_client import arizona_api

import discord
from discord.ext import commands
from aiogram import Bot

# ---------------- Flask для Render ----------------
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot is running 🚀"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

# ---------------- Основной класс бота ----------------
class DualPlatformBot:
    def __init__(self):
        self.discord_bot = None
        self.telegram_bot = None
        self.telegram_handlers = None
        self.discord_handlers = None
        self.running = False

    # ---------------- Discord ----------------
    def setup_discord_bot(self):
        intents = discord.Intents.default()
        intents.message_content = True
        self.discord_bot = commands.Bot(
            command_prefix=config.DISCORD_COMMAND_PREFIX,
            intents=intents,
            help_command=None
        )
        self.discord_handlers = DiscordBotHandlers(self.discord_bot)
        print("✅ Discord bot configured")

    async def start_discord_bot(self):
        if self.discord_bot:
            await self.discord_bot.start(config.DISCORD_TOKEN)

    # ---------------- Telegram ----------------
    def setup_telegram_bot(self):
        self.telegram_bot = Bot(token=config.TELEGRAM_TOKEN)
        self.telegram_handlers = TelegramBotHandlers(self.telegram_bot)
        print("✅ Telegram bot configured")

    async def start_telegram_bot(self):
        if self.telegram_handlers:
            await self.telegram_handlers.start_polling()

    # ---------------- Запуск ----------------
    async def run(self):
        if not config.validate():
            print("❌ Конфигурация не валидна")
            return False
        self.setup_discord_bot()
        self.setup_telegram_bot()
        self.running = True

        discord_task = asyncio.create_task(self.start_discord_bot())
        telegram_task = asyncio.create_task(self.start_telegram_bot())

        await asyncio.gather(discord_task, telegram_task, return_exceptions=True)


# ---------------- Запуск ----------------
async def main():
    bot = DualPlatformBot()
    try:
        await bot.run()
    except KeyboardInterrupt:
        print("🛑 Боты остановлены пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
