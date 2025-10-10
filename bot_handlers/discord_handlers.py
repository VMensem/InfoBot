# bot_handlers/discord_handlers.py
from discord.ext import commands
from arizona.arizona_api_client import arizona_api

class DiscordBotHandlers:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        @bot.command(name="servers")
        async def servers(ctx):
            msg = await ctx.send("⏳ Получаю статус серверов...")
            text = await arizona_api.get_servers_status_from_api()
            # Discord supports markdown/asterisks
            await msg.edit(content=text)

        @bot.command(name="stats")
        async def stats(ctx, nickname: str = None, server_id: int = None):
            if not nickname or server_id is None:
                await ctx.send("⚠️ Использование: !stats <ник> <ID сервера>\nПример: !stats Vlad_Mensem 18")
                return

            valid_nick, err = arizona_api.validate_nickname(nickname)
            if not valid_nick:
                await ctx.send(f"❌ {err}")
                return

            valid_srv, err = arizona_api.validate_server_id(server_id)
            if not valid_srv:
                await ctx.send(f"❌ {err}")
                return

            msg = await ctx.send(f"⏳ Получаю данные игрока {nickname}...")
            data, error = await arizona_api.fetch_player_stats(nickname, server_id)
            if error:
                return await msg.edit(content=error)

            result = arizona_api.format_stats(data, nickname, server_id)
            # Discord messages have 2000 char limit — if long, split
            if len(result) <= 1900:
                await msg.edit(content=result)
            else:
                # split into chunks
                chunks = [result[i:i+1900] for i in range(0, len(result), 1900)]
                await msg.edit(content=chunks[0])
                for c in chunks[1:]:
                    await ctx.send(c)
