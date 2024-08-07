import json
from tonpay import config
import os
from dataclasses import dataclass
from typing import Literal

_max_user_demo_wallets = config["user"].get("max_wallets", 5)
_datetime_fmt = config["general"].get("datetime_format", "%Y-%m-%y_%H:%M:%S")
_datetime_fmt_encryption = config["wallet_encryption"].get("datetime_format", _datetime_fmt)
_salt = config["wallet_encryption"]["salt"]
_key_fmt = config["wallet_encryption"]["SYMMETRIC_KEY"]
_platform_name = config["general"]["name"]
_lang = config["general"].get("language", "eng")
_telegram_lang = config["telegram"].get("language", _lang)

@dataclass
class formats:
    datetime:str = _datetime_fmt
    wallet_name: str = "{name}_Wallet_{datetime}_{ID}"
    class Symm_KEY:
        key_fmt: str = _key_fmt
        salt: str = _salt
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
        
@dataclass
class types:
    BLOCKCHAIN = Literal["TON", "ETH", "BNB"]
         
    