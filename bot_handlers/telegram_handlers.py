from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from arizona_api_client import arizona_api

class TelegramBotHandlers:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.dp = Dispatcher()

        # Регистрируем команды
        self.dp.message.register(self.servers_command, Command("servers"))
        self.dp.message.register(self.stats_command, Command("stats"))

    async def start_polling(self):
        await self.dp.start_polling(self.bot, skip_updates=True)

    async def servers_command(self, message: types.Message):
        msg = await message.answer("⏳ Получаю данные о серверах...")
        servers_text = await arizona_api.get_servers_info()
        await msg.edit_text(servers_text)

    async def stats_command(self, message: types.Message):
        args = message.text.split()
        if len(args) < 3:
            await message.answer("⚠️ Использование: /stats <ник> <ID сервера>\nПример: /stats Vlad_Mensem 18")
            return

        nickname = args[1]
        try:
            server_id = int(args[2])
        except ValueError:
            await message.answer("❌ ID сервера должен быть числом.")
            return

        valid_nick, error = arizona_api.validate_nickname(nickname)
        if not valid_nick:
            await message.answer(f"❌ {error}")
            return

        valid_srv, error = arizona_api.validate_server_id(server_id)
        if not valid_srv:
            await message.answer(f"❌ {error}")
            return

        msg = await message.answer(f"🔍 Получаю данные игрока <b>{nickname}</b> с сервера {arizona_api.get_server_name(server_id)}...")
        data, err = await arizona_api.fetch_player_stats(nickname, server_id)

        if err:
            await msg.edit_text(err)
            return
        if not data:
            await msg.edit_text("⚠️ Данные не найдены.")
            return

        stats = data.get("statistics", {})
        text = f"""
👤 <b>Информация о {nickname} на сервере {arizona_api.get_server_name(server_id)} [{server_id}]</b>:

📌 <b>Основное:</b>
— ⚙️ ID аккаунта: {data.get('account_id', 'Неизвестно')}
— 🎓 Уровень: {data.get('level', '❔')}
— 🎮 Отыграно часов: {stats.get('played_hours', '❔')}
— 💰 Баланс: {stats.get('money', '❔')}$

🏢 <b>Работа и фракция:</b>
— 🪪 Работа: {stats.get('job', '❌')}
— 💼 Организация: {stats.get('organization', '❌')}
— 👔 Должность: {stats.get('rank', '❌')}

🔄 Информация обновлена только что
"""
        await msg.edit_text(text)
