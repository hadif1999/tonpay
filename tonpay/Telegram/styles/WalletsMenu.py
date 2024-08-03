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
    _new = IKB("➕ " + new_txt, callback_data="new")
    wallets_stack = []
    for name, addr in wallets.items():
        wallet_desc = f""" <b>{name_txt}:</b> {name}
<b>{address_txt}:</b> {addr}
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



def wallets_msg(update: Update, wallets: dict[str, Account]):
    wallets_stack = []
    for name, wallet in wallets.items():
        wallet_desc = f""" name: {name}
Address: {wallet.address}
        """
        wallets_stack.append([IKB(wallet_desc)])
        
    buttons1 = [IKB("🔄 Refresh", callback_data="refresh"), 
                IKB("⬇️ Import", callback_data="import"),
                IKB("➕ New", callback_data="new")]
    buttons2 = [IKB("↩️ Back", callback_data="back"), IKB("🏠 Home", callback_data="home") ]
    wallets_stack.append(buttons1); wallets_stack.append(buttons2)
    keyboard_markup = InlineKeyboardMarkup(wallets_stack)
    return update.message.reply_text("Active wallets:", reply_markup=keyboard_markup)

