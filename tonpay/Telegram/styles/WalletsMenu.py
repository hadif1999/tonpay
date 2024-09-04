from telegram import InlineKeyboardMarkup, Update, InlineKeyboardButton as IKB
from ton.account import Account
from ..styles.Utils import back_home_keyboard as bhk
from typing import Annotated

ADDRESS = Annotated[str, "wallet address"]
NAME = Annotated[str, "wallet name"]

def render_keyboard(wallets: dict[NAME, ADDRESS], name_txt:str = "Name",
                    address_txt:str = "Address", refresh_txt:str = "Refresh",
                    import_txt:str = "Import", new_txt:str = "New", *other_keyboards):
    _refresh = IKB("🔄 " + refresh_txt, callback_data="refresh")
    _import = IKB("⬇️ " + import_txt, callback_data="import")
    _new = IKB("➕ " + new_txt, callback_data="new_wallet")
    wallets_stack = []
    for name, addr in wallets.items():
        wallet_desc = f""" {name_txt}: {name}
        {address_txt}: {addr}
        """
        wallets_stack.append([IKB(wallet_desc, callback_data=name)])
        
    walletManage_buttonsRow = [_refresh, _import, _new]
    wallets_stack.append(walletManage_buttonsRow)
    for buttons in other_keyboards:
        if isinstance(buttons, list):
            wallets_stack.append(buttons)
    return wallets_stack
    

class Eng:
    header = "Active wallets:"
    def __init__(self, wallets: dict[str, Account]) -> None:
        self.keyboard = render_keyboard(wallets, "Name", "Address",
                                        "Refresh", "Import", "New",
                                        bhk("Back", "Home"))
    
    
class Fa:
    header = ":کیف پول های فعال"
    def __init__(self, wallets: dict[str, Account]) -> None:
        self.keyboard = render_keyboard(wallets, "نام", "آدرس",
                                        "به روزرسانی", "وارد کردن", "جدید",
                                        bhk("قبلی", "خانه"))

