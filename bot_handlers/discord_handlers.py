from discord.ext import commands
from arizona_api_client import arizona_api

class DiscordBotHandlers:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        @self.bot.command(name="servers")
        async def servers(ctx):
            msg = await ctx.send("⏳ Получаю данные о серверах...")
            servers_text = await arizona_api.get_servers_info()
            await msg.edit(content=servers_text)

        @self.bot.command(name="stats")
        async def player(ctx, nickname: str = None, server_id: int = None):
            if not nickname or server_id is None:
                await ctx.send("⚠️ Использование: !player <ник> <ID сервера>")
                return

            valid_nick, error = arizona_api.validate_nickname(nickname)
            if not valid_nick:
                await ctx.send(f"❌ {error}")
                return

            valid_srv, error = arizona_api.validate_server_id(server_id)
            if not valid_srv:
                await ctx.send(f"❌ {error}")
                return

            msg = await ctx.send(f"🔍 Получаю данные игрока **{nickname}** с сервера {arizona_api.get_server_name(server_id)}...")
            data, err = await arizona_api.fetch_player_stats(nickname, server_id)
            if err:
                await msg.edit(content=err)
                return
            if not data:
                await msg.edit(content="⚠️ Данные не найдены.")
                return

            stats = data.get("statistics", {})
            text = f"""
👤 **Информация о {nickname} на сервере {arizona_api.get_server_name(server_id)} [{server_id}]**

📌 **Основное:**
— ⚙️ ID аккаунта: {data.get('account_id', 'Неизвестно')}
— 🎓 Уровень: {data.get('level', '❔')}
— 🎮 Отыграно часов: {stats.get('played_hours', '❔')}
— 💰 Баланс: {stats.get('money', '❔')}$

🏢 **Работа и фракция:**
— 🪪 Работа: {stats.get('job', '❌')}
— 💼 Организация: {stats.get('organization', '❌')}
— 👔 Должность: {stats.get('rank', '❌')}

🔄 Информация обновлена только что
"""
            await msg.edit(content=text)
