import json
from tonpay import config
import os
from dataclasses import dataclass
from typing import Literal, Any
from enum import Enum

_max_user_demo_wallets = config["user"].get("max_wallets", 5)
_datetime_fmt = config["general"].get("datetime_format", "%Y-%m-%y_%H:%M:%S")
_datetime_fmt_encryption = config["wallet_encryption"].get("datetime_format", _datetime_fmt)
_salt = config["wallet_encryption"]["salt"]
_key_fmt = config["wallet_encryption"]["SYMMETRIC_KEY"]
_platform_name = config["general"]["name"]
_lang = config["general"].get("language", "eng")
_telegram_lang = config["telegram"].get("language", _lang)
_database: dict[str, Any] = config["general"]["database"] 
class Blockchain_enum(str, Enum):
        TON = "TON"
        ETH = "ETH"
        BNB = "BNB"

_blockchains = config["general"].get("blockchains", ["ETH", "BNB", "TON"])
@dataclass
class formats:
    datetime:str = _datetime_fmt
    wallet_name: str = "{name}_Wallet_{datetime}_{ID}"
    class Symm_KEY:
        key_fmt: str = _key_fmt
        salt: str = _salt
    class explorer_url:
        TON = "https://tonviewer.com/{addr}"
    class transfer_url: 
        TON = "ton://transfer/{addr}"
@dataclass        
class users:
    class wallets:
        class count:
            demo: int = 5
            pro: int = 10 
@dataclass
class options:
    lang = _lang
    class telegram:
        lang = _telegram_lang
        token = config["telegram"].get("token", os.getenv("TELEGRAM_TOKEN"))
    class database: 
        as_aync: bool = _database.get("as_aync", True)
        db_uri: str = _database.get("uri", os.getenv("DATABASE_URI"))
        
@dataclass
class types:
    BLOCKCHAIN = Blockchain_enum
         
    