# arizona/arizona_api_client.py
"""
API client for fetching player statistics from Arizona RP servers via Deps API
"""

import asyncio
import aiohttp
from typing import Dict, Any, Tuple, Optional
import logging
import re
import time
from datetime import datetime, timedelta

from config.config import API_URL, API_KEY, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

class ArizonaRPAPIClient:
    """Client for fetching Arizona RP player information from Deps API"""
    
    def __init__(self):
        self.api_url = API_URL
        self.api_key = API_KEY
        self.timeout = REQUEST_TIMEOUT
        
        # Кэш для статуса серверов
        self._servers_cache: Dict[int, Dict[str, Any]] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_duration = 300  # 5 минут
        
        # Rate limiting
        self._last_request_time = 0.0
        self._request_delay = 0.5  # 500ms между запросами

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
        valid_servers = {}
        for i in range(1, 32):
            valid_servers[i] = f"ПК-{i}"
        for i in range(101, 104):
            valid_servers[i] = f"Мобайл-{i}"
        if server_id not in valid_servers:
            return False, f"Неверный ID сервера. Доступные серверы Arizona RP: ПК 1-31, Мобайл 101-103"
        return True, None

    async def fetch_player_stats(self, nickname: str, server_id: int) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        if not self.api_key:
            return None, "❌ API ключ не настроен. Обратитесь к администратору."
        
        headers = {
            "X-API-Key": self.api_key,
            "User-Agent": "MensemBot/1.0"
        }
        
        params = {
            "nickname": nickname,
            "serverId": server_id
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.api_url, headers=headers, params=params) as response:
                    logger.info(f"API request for {nickname} on server {server_id}: {response.status}")
                    
                    if response.status == 401:
                        return None, "❌ Ошибка авторизации API. Проверьте API ключ."
                    
                    if response.status == 429:
                        return None, "⏳ Слишком много запросов. Попробуйте позже."
                    
                    if response.status != 200:
                        return None, f"❌ Ошибка сервера API: {response.status}"
                    
                    try:
                        data = await response.json()
                    except Exception as e:
                        logger.error(f"Failed to parse JSON response: {e}")
                        return None, "❌ Ошибка обработки ответа от API."
                    
                    if "error_code" in data:
                        error_code = data.get("error_code", "")
                        error_msg = data.get("error_message", "Неизвестная ошибка")
                        if error_code == "FORBIDDEN":
                            return None, f"🔒 Требуется подтверждение IP адреса: {error_msg}"
                        return None, f"❌ Ошибка API ({error_code}): {error_msg}"
                    
                    if "error" in data:
                        error_msg = data.get("error", {}).get("message", "Неизвестная ошибка")
                        return None, f"❌ Ошибка API: {error_msg}"
                    
                    if "status" in data and data["status"] == "error":
                        error_msg = data.get("error", {}).get("message", "Неизвестная ошибка")
                        return None, f"❌ Ошибка API: {error_msg}"
                    
                    if not self._validate_response(data):
                        return None, "❌ Некорректный формат ответа от API."
                    
                    return data, None
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching stats for {nickname}")
            return None, "⏰ Превышено время ожидания ответа от API."
        
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error: {e}")
            return None, "🌐 Ошибка сетевого соединения."
        
        except Exception as e:
            logger.error(f"Unexpected error fetching stats: {e}")
            return None, "❌ Произошла неожиданная ошибка при получении статистики."
    
    def _validate_response(self, data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict):
            return False
        if "id" in data and "level" in data:
            return True
        if any(key in data for key in ["statistics", "account_id", "nickname"]):
            return True
        return False
    
    def create_progress_bar(self, value, max_value: int = 100, length: int = 10) -> str:
        if value is None:
            value = 0
        try:
            value = int(value)
            filled = int((value / max_value) * length)
            if filled < 0:
                filled = 0
            if filled > length:
                filled = length
            bar = "█" * filled + "░" * (length - filled)
            return f"[{bar}] {value}%"
        except (ValueError, TypeError, ZeroDivisionError):
            return f"[{'░' * length}] 0%"

    def format_money(self, amount) -> str:
        if amount is None:
            return "$0"
        try:
            return f"${int(amount):,}"
        except (ValueError, TypeError):
            return f"${amount}"

    def format_stats(self, data: Dict[str, Any], nickname: str, server_id: int) -> str:
        try:
            player_data = data
            if not player_data or "error" in data or "id" not in player_data:
                return f"❌ Игрок '{nickname}' не найден на сервере {server_id}."
            
            server_info = player_data.get("server", {})
            server_name = server_info.get("name", f"Сервер {server_id}")
            
            msg = f"👤 Информация об игроке {nickname}\n\n"
            msg += f"🌐 Сервер: {server_name} (ID: {server_info.get('id', server_id)})\n\n"
            msg += f"🆔 ID игрока: {player_data['id']}\n"
            msg += f"📱 Телефон: {player_data.get('phone_number', 'Неизвестно')}\n"
            msg += f"⏱ Отыграно часов: {player_data.get('hours_played', 0)}\n\n"
            
            level_info = player_data.get("level", {})
            if isinstance(level_info, dict):
                current_level = level_info.get("level", 0)
                current_exp = level_info.get("current_exp", 0)
                next_exp = level_info.get("next_exp", 100)
                msg += f"🌟 Уровень: {current_level}\n"
                msg += f"📊 Опыт: {current_exp}/{next_exp}\n\n"
            elif isinstance(level_info, (int, str)):
                msg += f"🌟 Уровень: {level_info}\n\n"
            
            health = player_data.get("health", 0)
            hunger = player_data.get("hunger", 0)
            drug_addiction = player_data.get("drug_addiction", 0)
            
            health_bar = self.create_progress_bar(health)
            hunger_bar = self.create_progress_bar(hunger)
            msg += f"❤️ Здоровье: {health_bar}\n"
            msg += f"🍗 Голод: {hunger_bar}\n"
            msg += f"💉 Наркозависимость: {drug_addiction}%\n\n"
            
            vip_info = player_data.get("vip_info", {})
            if vip_info:
                vip_level = vip_info.get("level", "None")
                add_vip = vip_info.get("add_vip", "Нет")
                msg += f"👑 VIP: {vip_level}\n"
                if add_vip != "Нет":
                    msg += f"➕ Доп. VIP: {add_vip}\n"
                msg += "\n"
            
            money_info = player_data.get("money", {})
            if money_info:
                msg += f"💰 Финансы:\n"
                total = money_info.get("total", 0)
                hand = money_info.get("hand", 0)
                bank = money_info.get("bank", 0)
                deposit = money_info.get("deposit", 0)
                donate_currency = money_info.get("donate_currency", 0)
                phone_balance = money_info.get("phone_balance", 0)
                charity = money_info.get("charity", 0)
                
                msg += f"  💵 Всего: {self.format_money(total)}\n"
                msg += f"  💴 Наличные: {self.format_money(hand)}\n"
                msg += f"  🏦 Банк: {self.format_money(bank)}\n"
                msg += f"  💼 Депозит: {self.format_money(deposit)}\n"
                msg += f"  💎 Донат валюта: {donate_currency}\n"
                msg += f"  📱 Баланс телефона: {self.format_money(phone_balance)}\n"
                msg += f"  ❤️ Благотворительность: {self.format_money(charity)}\n\n"
            
            job = player_data.get("job", "Безработный")
            msg += f"💼 Работа: {job}\n"
            
            org_info = player_data.get("organization", {})
            if org_info:
                org_name = org_info.get("name", "Нет")
                org_rank = org_info.get("rank", "Нет")
                uniform = org_info.get("uniform", False)
                
                msg += f"🏢 Организация: {org_name}\n"
                msg += f"  🏅 Должность: {org_rank}\n"
                uniform_status = "👔 В форме" if uniform else "👕 Не в форме"
                msg += f"  {uniform_status}\n\n"
            else:
                msg += f"🏢 Организация: Нет\n\n"
            
            law_abiding = player_data.get("law_abiding", 0)
            wanted_level = player_data.get("wanted_level", 0)
            warnings = player_data.get("warnings", 0)
            
            law_bar = self.create_progress_bar(law_abiding)
            msg += f"⚖️ Законопослушность: {law_bar}\n"
            msg += f"🚨 Уровень розыска: {wanted_level}\n"
            msg += f"⚠️ Предупреждения: {warnings}\n\n"
            
            family_info = player_data.get("family", {})
            if family_info:
                family_name = family_info.get("name", "Неизвестно")
                family_leader = family_info.get("leader", "Неизвестно")
                member_info = family_info.get("member_info", {})
                member_rank = member_info.get("rank", 0)
                is_leader = member_info.get("is_leader", False)
                
                msg += f"👥 Семья: {family_name}\n"
                msg += f"  👑 Лидер: {family_leader}\n"
                leader_status = "Да" if is_leader else "Нет"
                msg += f"  🏆 Я лидер: {leader_status}\n"
                msg += f"  🎖️ Ранг в семье: {member_rank}\n\n"
            
            status_info = player_data.get("status", {})
            if status_info:
                online = status_info.get("online", False)
                player_id = status_info.get("player_id", "Неизвестно")
                online_status = "🟢 В сети" if online else "🔴 Не в сети"
                msg += f"Статус: {online_status}\n"
                if online:
                    msg += f"🎮 ID в игре: {player_id}\n"
            
            return msg
            
        except Exception as e:
            logger.error(f"Error formatting Arizona RP stats: {e}")
            return f"❌ Ошибка при форматировании информации для игрока {nickname}."

    def get_server_name(self, server_id: int) -> str:
        server_names = {
            1: "Phoenix", 2: "Tucson", 3: "Scottdale", 4: "Chandler", 5: "Brainburg",
            6: "Saint Rose", 7: "Mesa", 8: "Red Rock", 9: "Yuma", 10: "Surprise",
            11: "Prescott", 12: "Glendale", 13: "Kingman", 14: "Winslow", 15: "Payson",
            16: "Gilbert", 17: "Show Low", 18: "Casa Grande", 19: "Page", 20: "Sun City",
            21: "Queen Creek", 22: "Sedona", 23: "Holiday", 24: "Wednesday", 25: "Yava",
            26: "Faraway", 27: "Bumble Bee", 28: "Christmas", 29: "Mirage", 30: "Love", 31: "Drake",
            101: "Mobile I", 102: "Mobile II", 103: "Mobile III"
        }
        return server_names.get(server_id, f"Server {server_id}")

    async def fetch_server_status(self, server_id: int) -> Dict[str, Any]:
        try:
            is_valid, error = self.validate_server_id(server_id)
            if not is_valid:
                return {
                    "status": "error",
                    "error": error,
                    "online": 0,
                    "is_online": False
                }
                
            if not self.api_key:
                return {
                    "status": "no_api_key",
                    "error": "API ключ не настроен",
                    "online": 0,
                    "is_online": False
                }
            
            await self._rate_limit()
            
            url = f"{self.api_url}/server/info"
            params = {
                "key": self.api_key,
                "server": server_id
            }
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 429:
                        logger.warning(f"Rate limit exceeded for server {server_id}")
                        return {"status":"rate_limit","error":"Превышен лимит","online":0,"is_online":False}
                    elif response.status == 401:
                        return {"status":"unauthorized","error":"Неверный API ключ","online":0,"is_online":False}
                    elif response.status != 200:
                        return {"status":"api_error","error":f"HTTP {response.status}","online":0,"is_online":False}
                    
                    data = await response.json()
                    if data.get("status") != "ok":
                        error_msg = data.get("error", "Неизвестная ошибка API")
                        return {"status":"api_error","error":error_msg,"online":0,"is_online":False}
                    
                    server_info = data.get("server", {})
                    online_count = server_info.get("online", 0)
                    server_status = server_info.get("status", "offline")
                    
                    return {
                        "status": "success",
                        "online": int(online_count),
                        "is_online": server_status == "online",
                        "server_name": self.get_server_name(server_id),
                        "server_id": server_id
                    }
                    
        except asyncio.TimeoutError:
            return {"status":"timeout","error":"Превышено время ожидания","online":0,"is_online":False}
        except Exception as e:
            logger.error(f"Error fetching server {server_id} status: {e}")
            return {"status":"error","error":str(e),"online":0,"is_online":False}

    def _is_cache_valid(self) -> bool:
        if not self._cache_timestamp:
            return False
        return (datetime.now() - self._cache_timestamp).total_seconds() < self._cache_duration

    async def _rate_limit(self):
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        if elapsed < self._request_delay:
            await asyncio.sleep(self._request_delay - elapsed)
        self._last_request_time = time.time()

    async def fetch_all_servers_status(self) -> Dict[int, Dict[str, Any]]:
        if self._is_cache_valid() and self._servers_cache:
            logger.info("Используем кэшированные данные серверов")
            return self._servers_cache.copy()
        
        servers_info: Dict[int, Dict[str, Any]] = {}
        server_ids = list(range(1, 32)) + list(range(101, 104))
        
        try:
            batch_size = 5
            for i in range(0, len(server_ids), batch_size):
                batch = server_ids[i:i + batch_size]
                batch_tasks = [self.fetch_server_status(sid) for sid in batch]
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for sid, result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        servers_info[sid] = {"status":"error","error":str(result),"online":0,"is_online":False}
                    else:
                        servers_info[sid] = result
                
                if i + batch_size < len(server_ids):
                    await asyncio.sleep(1)
            
            self._servers_cache = servers_info.copy()
            self._cache_timestamp = datetime.now()
            logger.info(f"Обновлен кэш статуса серверов ({len(servers_info)} серверов)")
                    
        except Exception as e:
            logger.error(f"Error fetching all servers status: {e}")
            
        return servers_info

    def get_servers_info(self) -> str:
        msg = "🌐 Серверы Arizona RP:\n\n💻 ПК серверы (1-31):\n"
        msg += " 1: Phoenix\n 2: Tucson\n 3: Scottdale\n 4: Chandler\n 5: Brainburg\n 6: Saint Rose\n 7: Mesa\n 8: Red Rock\n 9: Yuma\n10: Surprise\n11: Prescott\n12: Glendale\n13: Kingman\n14: Winslow\n15: Payson\n16: Gilbert\n17: Show Low\n18: Casa Grande\n19: Page\n20: Sun City\n21: Queen Creek\n22: Sedona\n23: Holiday\n24: Wednesday\n25: Yava\n26: Faraway\n27: Bumble Bee\n28: Christmas\n29: Mirage\n30: Love\n31: Drake\n\n"
        
        msg += "📱 Мобайл серверы:\n"
        msg += "101: Mobile 1\n102: Mobile 2\n103: Mobile 3\n\n"
        
        msg += "Использование: /stats <ник> <ID сервера>\n"
        msg += "Пример: /stats PlayerName 1"
        
        return msg
    
    async def get_servers_status_from_api(self) -> str:
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            # Тестовый публичный endpoint (как в старом коде)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get("https://api.depscian.tech/v2/status", 
                                     headers={"X-API-Key": "eybfxnIFZJ5ZciisrE14hiOW5dVMjGLb"}) as response:
                    
                    if response.status != 200:
                        logger.error(f"API status request failed: {response.status}")
                        return self.get_servers_info()  # Fallback to static list
                    
                    data = await response.json()
                    arizona_servers = data.get("arizona", [])
                    
                    if not arizona_servers:
                        return self.get_servers_info()
                    
                    arizona_servers.sort(key=lambda x: x.get("number", 0))
                    
                    msg = "🌐 **Серверы Arizona RP** (Онлайн)\n\n"
                    msg += "📊 **Актуальный статус серверов:**\n\n"
                    
                    total_online = 0
                    online_servers = 0
                    
                    pc_servers = [s for s in arizona_servers if 1 <= s.get("number", 0) <= 31]
                    for server in pc_servers:
                        server_id = server.get("number", 0)
                        server_name = server.get("name", f"Server {server_id}")
                        online_count = server.get("online", 0)
                        max_players = server.get("maxplayers", 1000)
                        status = server.get("status", "offline")
                        
                        if status == "online":
                            msg += f"✅ {server_id}. {server_name} | Онлайн: {online_count:,} / {max_players:,}\n"
                            total_online += online_count
                            online_servers += 1
                        else:
                            msg += f"❌ {server_id}. {server_name} | Сервер офлайн\n"
                    
                    msg += f"\n📱 **Мобайл серверы:**\n"
                    mobile_servers = [s for s in arizona_servers if 101 <= s.get("number", 0) <= 103]
                    for server in mobile_servers:
                        server_id = server.get("number", 0)
                        server_name = server.get("name", f"Mobile {server_id}")
                        online_count = server.get("online", 0)
                        max_players = server.get("maxplayers", 1000)
                        status = server.get("status", "offline")
                        
                        if status == "online":
                            msg += f"✅ {server_id}. {server_name} | Онлайн: {online_count:,} / {max_players:,}\n"
                            total_online += online_count
                            online_servers += 1
                        else:
                            msg += f"❌ {server_id}. {server_name} | Сервер офлайн\n"
                    
                    msg += f"\n📊 **Общая статистика:**\n"
                    msg += f"🎮 Всего игроков онлайн: **{total_online:,}**\n"
                    msg += f"⚡ Серверов онлайн: **{online_servers}/{len(arizona_servers)}**\n"
                    msg += f"\n📝 Статистика игрока: /stats <ник> <ID сервера>\n"
                    msg += f"💡 Пример: /stats PlayerName 1"
                    
                    return msg
                    
        except Exception as e:
            logger.error(f"Error getting servers status from API: {e}")
            return self.get_servers_info()

# Global API client instance
arizona_api = ArizonaRPAPIClient()
