"""
API client for fetching player statistics and server status from Arizona RP
"""

import asyncio
import aiohttp
from typing import Dict, Any, Tuple, Optional
import re
from datetime import datetime
import os
# Настройки (можно вынести в config)
API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")
REQUEST_TIMEOUT = 10


class ArizonaRPAPIClient:
    """Client for fetching Arizona RP player information and server status"""

    def __init__(self):
        self.api_url = API_URL
        self.api_key = API_KEY
        self.timeout = REQUEST_TIMEOUT

        # Кэш для серверов
        self._servers_cache: Dict[int, Dict[str, Any]] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_duration = 300  # 5 минут

    # =============== Проверки =================
    def validate_nickname(self, nickname: str) -> Tuple[bool, Optional[str]]:
        if not nickname:
            return False, "Ник игрока не может быть пустым."
        if len(nickname) < 3:
            return False, "Ник игрока должен содержать минимум 3 символа."
        if len(nickname) > 24:
            return False, "Ник игрока не может содержать более 24 символов."
        if not re.match(r'^[a-zA-Z0-9_]+$', nickname):
            return False, "Ник может содержать только буквы, цифры и подчёркивания."
        return True, None

    def validate_server_id(self, server_id: int) -> Tuple[bool, Optional[str]]:
        valid_servers = list(range(1, 33)) + [200] + list(range(101, 104))
        if server_id not in valid_servers:
            return False, "Неверный ID сервера. Доступные: ПК 1–32, ViceCity (200), Мобайл 101–103"
        return True, None

    # =============== API игрока =================
    async def fetch_player_stats(
        self, nickname: str, server_id: int
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:

        if not self.api_key:
            return None, "❌ API ключ не настроен."

        headers = {"X-API-Key": self.api_key, "User-Agent": "InfoBot/1.0"}
        params = {"nickname": nickname, "serverId": server_id}

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.api_url, headers=headers, params=params) as response:

                    if response.status != 200:
                        return None, f"❌ Ошибка API: {response.status}"

                    data = await response.json()
                    if not isinstance(data, dict):
                        return None, "❌ Некорректный формат ответа API."

                    return data, None

        except asyncio.TimeoutError:
            return None, "⏰ Превышено время ожидания API."
        except aiohttp.ClientError:
            return None, "🌐 Ошибка сетевого соединения."
        except Exception as e:
            return None, f"❌ Непредвиденная ошибка: {e}"

    # =============== Серверы =================
    def get_server_name(self, server_id: int) -> str:
        names = {
            1: "Phoenix", 2: "Tucson", 3: "Scottdale", 4: "Chandler", 5: "Brainburg",
            6: "Saint Rose", 7: "Mesa", 8: "Red-Rock", 9: "Yuma", 10: "Surprise",
            11: "Prescott", 12: "Glendale", 13: "Kingman", 14: "Winslow", 15: "Payson",
            16: "Gilbert", 17: "Show Low", 18: "Casa-Grande", 19: "Page", 20: "Sun-City",
            21: "Queen-Creek", 22: "Sedona", 23: "Holiday", 24: "Wednesday", 25: "Yava",
            26: "Faraway", 27: "Bumble Bee", 28: "Christmas", 29: "Mirage", 30: "Love",
            31: "Drake", 32: "Space", 200: "ViceCity",
            101: "Mobile I", 102: "Mobile II", 103: "Mobile III"
        }
        return names.get(server_id, f"Server {server_id}")

    async def fetch_server_status(self, server_id: int) -> Dict[str, Any]:
        """Фейковый пример, можно заменить на реальный API онлайн"""
        return {"server_id": server_id, "online": 500, "max_online": 1000, "is_online": True}

    async def fetch_all_servers_status(self) -> Dict[int, Dict[str, Any]]:
        if self._cache_timestamp and (datetime.now() - self._cache_timestamp).total_seconds() < self._cache_duration:
            return self._servers_cache.copy()

        servers_info = {}
        server_ids = list(range(1, 33)) + [200] + list(range(101, 104))

        for sid in server_ids:
            servers_info[sid] = await self.fetch_server_status(sid)

        self._servers_cache = servers_info.copy()
        self._cache_timestamp = datetime.now()
        return servers_info

    async def get_servers_info(self) -> str:
        servers = await self.fetch_all_servers_status()
        msg = "📊 Онлайн серверов Arizona RP\n\n"

        for sid, info in servers.items():
            name = self.get_server_name(sid)
            if not info.get("is_online", False):
                msg += f"🔴 [{sid}] {name} — Offline\n"
            else:
                msg += f"🟢 [{sid}] {name} — {info['online']} / {info['max_online']}\n"
        return msg


# Глобальный клиент
arizona_api = ArizonaRPAPIClient()
