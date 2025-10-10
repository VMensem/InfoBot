# main.py
#!/usr/bin/env python3
import os
import sys
import threading
import asyncio
import logging

# Flask keepalive so Render won't sleep (параллельно)
from flask import Flask
app = Flask(__name__)

@app.route("/")
def index():
    return "InfoBot is running 🚀"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# start flask thread
flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

# logging
from config.config import DISCORD_TOKEN, TELEGRAM_TOKEN, DISCORD_COMMAND_PREFIX, LOG_LEVEL
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("InfoBot")

# import bots
from aiogram import Bot as AiogramBot
from bot_handlers.telegram_handlers import TelegramBotHandlers
from bot_handlers.discord_handlers import DiscordBotHandlers

import discord
from discord.ext import commands

async def start_bots():
    # Telegram setup
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN is not set in environment")
        sys.exit(1)
    tg_bot = AiogramBot(token=TELEGRAM_TOKEN)
    tg_handlers = TelegramBotHandlers(tg_bot)

    # Discord setup
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN is not set in environment")
        sys.exit(1)
    intents = discord.Intents.default()
    intents.message_content = True
    discord_bot = commands.Bot(command_prefix=DISCORD_COMMAND_PREFIX, intents=intents, help_command=None)
    DiscordBotHandlers(discord_bot)

    # Run both
    loop = asyncio.get_running_loop()

    # Telegram polling in background task
    tg_task = loop.create_task(tg_handlers.start_polling(), name="telegram_polling")

    # Discord start (blocking) -> run in task
    discord_task = loop.create_task(discord_bot.start(DISCORD_TOKEN), name="discord_start")

    # Wait for tasks to finish (they shouldn't on normal run)
    gathered = await asyncio.gather(tg_task, discord_task, return_exceptions=True)
    logger.info("Bots finished: %s", gathered)

if __name__ == "__main__":
    try:
        asyncio.run(start_bots())
    except KeyboardInterrupt:
        logger.info("Shutdown by user")
    except Exception as e:
        logger.exception("Fatal error in main: %s", e)
        sys.exit(1)
