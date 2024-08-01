import json

with open("tonpay/config.json", 'r') as file:
    config = json.loads(file.read() )

max_user_demo_wallets = config["user"].get("max_wallets", 5)
datetime_fmt = config["wallet_encryption"].get("datetime_format", "%Y-%m-%y_%H:%M:%S")
salt = config["wallet_encryption"]["salt"]
key_fmt = config["wallet_encryption"]["SYMMETRIC_KEY"]
platform_name = config["general"]["name"]

class formats:
    datetime:str = datetime_fmt
    class wallet_name:
        internal: str = "{name}_Wallet_{datetime}_{ID}"
        external: str = "TON_Wallet_{datetime}_{ID}"
    class Symm_KEY:
        key_fmt: str = key_fmt
        salt: str = salt
        
class users:
    class wallets:
        class count:
            demo: int = 5
            pro: int = 10 
    