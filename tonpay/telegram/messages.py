
from telegram import InlineKeyboardMarkup, Update
from styles import MainMenu, FinanceMenu, WalletsMenu, WalletMenu
from ton.account import Account


def MainMenu_msg(update: Update, lang:str = "eng"):
    lang = lang.title()
    try: 
        lang_cls = getattr(MainMenu, lang)
        keyboard = lang_cls.keyboard
        header = lang_cls.header
    except AttributeError:
        raise AttributeError(f"{lang} lang not found for main menu")
    keyboard_markup = InlineKeyboardMarkup(keyboard)
    return update.message.reply_text(header, reply_markup=keyboard_markup)


def FinanceMenu_msg(update: Update, lang:str = "eng", balance:str|float = 0,
                    balance_dollar:str|float = 0):
    lang = lang.title()
    try:
        lang_cls = getattr(FinanceMenu, lang)
        keyboard = lang_cls.keyboard
        header = lang_cls.header
    except AttributeError:
        raise AttributeError(f"{lang} lang not found for finance menu")
    keyboard_markup = InlineKeyboardMarkup(keyboard)
    return update.message.reply_text(header.format(balance=balance, balance_dollar=balance_dollar),
                                     reply_markup=keyboard_markup)
    
    
def wallets_msg(update: Update, wallets: dict[str, Account], lang:str = "eng"):
    lang = lang.title()
    try: 
        lang_cls = getattr(WalletsMenu, lang)
        header = lang_cls.header
    except AttributeError:
        raise AttributeError(f"{lang} lang not found for wallets menu")
    lang_obj = lang_cls(wallets)
    keyboard = lang_obj.keyboard
    keyboard_markup = InlineKeyboardMarkup(keyboard)
    return update.message.reply_text(header, reply_markup=keyboard_markup, 
                                     parse_mode="HTML")


async def wallet_msg(update: Update, wallet_name: str, 
                     wallet: Account, lang:str = "eng"):
    lang = lang.title()
    try: 
        lang_cls = getattr(WalletsMenu, lang)
        keyboard = lang_cls.keyboard
    except AttributeError:
        raise AttributeError(f"{lang} lang not found for wallet menu")
    lang_obj = await lang_cls(wallet_name, wallet)
    header = lang_obj.header
    keyboard_markup = InlineKeyboardMarkup(keyboard)
    # parsmode MarkdownV2 or HTML
    return update.message.reply_text(header, reply_markup=keyboard_markup,
                                     parse_mode="HTML")
    
    
        
    