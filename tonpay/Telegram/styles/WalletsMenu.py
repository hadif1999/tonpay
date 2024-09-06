from telegram import InlineKeyboardMarkup, Update, InlineKeyboardButton as IKB
from ton.account import Account
from ..styles.Utils import back_home_keyboard as bhk
from typing import Annotated
from tonpay.Defaults import _platform_name 

ADDRESS = Annotated[str, "wallet address"]
NAME = Annotated[str, "wallet name"]

def render_keyboard(wallets: dict[NAME, ADDRESS], name_txt:str = "Name",
                    address_txt:str = "Address", refresh_txt:str = "Refresh",
                    type_txt: str = "Type", import_txt:str = "Import",
                    new_txt:str = "New", *other_keyboards):
    _refresh = IKB("🔄 " + refresh_txt, callback_data="refresh")
    _import = IKB("⬇️ " + import_txt, callback_data="import")
    _new = IKB("➕ " + new_txt, callback_data="new_wallet")
    wallets_stack = []
    for name, data in wallets.items():
        addr = data["address"]
        type = data["type"] or _platform_name
        callback_data = "wallet_" + name
        wallet_desc = f"{name_txt}: {name}, {type_txt}: {type}"
        wallets_stack.append([IKB(wallet_desc, callback_data=callback_data)])
        
    walletManage_buttonsRow = [_refresh, _import, _new]
    wallets_stack.append(walletManage_buttonsRow)
    for buttons in other_keyboards:
        if isinstance(buttons, list):
            wallets_stack.append(buttons)
    return wallets_stack
    

class Eng:
    header = "Active wallets:"
    def __init__(self, wallets: dict[str, Account]) -> None:
        self.keyboard = render_keyboard(wallets,"Name", "Address",
                                        "Refresh", "Type", "Import", "New",
                                        bhk("Back", "Home"))
    
    
class Fa:
    header = ":کیف پول های فعال"
    def __init__(self, wallets: dict[str, Account]) -> None:
        self.keyboard = render_keyboard(wallets, "نام", "آدرس",
                                        "به روزرسانی", "نوع", "وارد کردن", "جدید",
                                        bhk("قبلی", "خانه"))

