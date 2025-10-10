# bot_handlers/telegram_handlers.py
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from arizona.arizona_api_client import arizona_api

class TelegramBotHandlers:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.dp = Dispatcher()

        # Register handlers
        self.dp.message.register(self.cmd_start, Command("start"))
        self.dp.message.register(self.cmd_servers, Command("servers"))
        self.dp.message.register(self.cmd_stats, Command("stats"))

    async def start_polling(self):
        await self.dp.start_polling(self.bot, skip_updates=True)

    async def cmd_start(self, message: types.Message):
        await message.answer(
            "👋 Привет! Я InfoBot.\n\n"
            "Команды:\n"
            "/servers — список серверов и их статус\n"
            "/stats <ник> <ID сервера> — статистика игрока\n\n"
            "Пример: /stats Vlad_Mensem 18"
        )

    async def cmd_servers(self, message: types.Message):
        # Try to fetch API status, fallback to static list inside client
        text = await arizona_api.get_servers_status_from_api()
        # send as plain text (API returns some markdown/asterisks — Telegram will show them as is)
        await message.answer(text)

    async def cmd_stats(self, message: types.Message):
        args = message.text.strip().split()
        if len(args) != 3:
            return await message.answer("⚠️ Использование: /stats <ник> <ID сервера>\nПример: /stats Vlad_Mensem 18")

        nickname = args[1]
        try:
            server_id = int(args[2])
        except ValueError:
            return await message.answer("❌ ID сервера должен быть числом.")

        valid_nick, err = arizona_api.validate_nickname(nickname)
        if not valid_nick:
            return await message.answer(f"❌ {err}")

        valid_srv, err = arizona_api.validate_server_id(server_id)
        if not valid_srv:
            return await message.answer(f"❌ {err}")

        await message.answer("⏳ Получаю данные игрока...")
        data, error = await arizona_api.fetch_player_stats(nickname, server_id)
        if error:
            return await message.answer(error)

        result = arizona_api.format_stats(data, nickname, server_id)
        await message.answer(result)
