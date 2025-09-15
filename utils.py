import re
from typing import Tuple, Optional, Dict

def validate_nickname(nickname: str) -> Tuple[bool, Optional[str]]:
    """
    Validate player nickname format
    
    Args:
        nickname: Player nickname to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not nickname:
        return False, "Ник игрока не может быть пустым."
    
    if len(nickname) < 3:
        return False, "Ник игрока должен содержать минимум 3 символа."
    
    if len(nickname) > 24:
        return False, "Ник игрока не может содержать более 24 символов."
    
    # Check for valid characters (letters, numbers, underscore)
    if not re.match(r'^[a-zA-Z0-9_]+$', nickname):
        return False, "Ник может содержать только буквы, цифры и подчёркивания."
    
    return True, None


# Полный список серверов Arizona RP
ARIZONA_SERVERS: Dict[int, str] = {
    1: "Phoenix",
    2: "Tucson",
    3: "Scottdale",
    4: "Chandler",
    5: "Brainburg",
    6: "Saint-Rose",
    7: "Mesa",
    8: "Red-Rock",
    9: "Yuma",
    10: "Surprise",
    11: "Prescott",
    12: "Glendale",
    13: "Kingman",
    14: "Winslow",
    15: "Payson",
    16: "Gilbert",
    17: "Show Low",
    18: "Casa-Grande",
    19: "Page",
    20: "Sun-City",
    21: "Queen-Creek",
    22: "Sedona",
    23: "Holiday",
    24: "Wednesday",
    25: "Yava",
    26: "Faraway",
    27: "Bumble Bee",
    28: "Christmas",
    29: "Mirage",
    30: "Love",
    31: "Drake",
    32: "Space",
    101: "Mobile I",
    102: "Mobile II",
    103: "Mobile III",
    1000: "Vice City"
}

def validate_server_id(server_id: int) -> Tuple[bool, Optional[str]]:
    """
    Validate server ID for Arizona RP
    
    Args:
        server_id: Server ID to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if server_id not in ARIZONA_SERVERS:
        server_list = "\n".join([f"{id}: {name}" for id, name in ARIZONA_SERVERS.items()])
        return False, f"Неверный ID сервера. Доступные серверы Arizona RP:\n{server_list}"
    
    return True, None


def truncate_message(message: str, max_length: int = 2000) -> str:
    """
    Truncate message to fit platform limits
    
    Args:
        message: Message to truncate
        max_length: Maximum allowed length
        
    Returns:
        Truncated message if needed
    """
    if len(message) <= max_length:
        return message
    
    return message[:max_length - 3] + "..."


def escape_markdown(text: str) -> str:
    """
    Escape markdown characters in text
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text
    """
    # Characters that need escaping in Discord markdown
    escape_chars = ['*', '_', '`', '~', '\\', '|']
    
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text
