
from telegram import InlineKeyboardMarkup, Update
from .styles import MainMenu, FinanceMenu, WalletsMenu, WalletMenu
from ton.account import Account
from typing import Annotated
from telegram.constants import ParseMode


def MainMenu_msg(update: Update, lang:str = "eng", edit_current: bool = False):
    lang = lang.title()
    try: 
        lang_cls = getattr(MainMenu, lang)
        keyboard = lang_cls.keyboard
        header = lang_cls.header
    except AttributeError:
        raise AttributeError(f"{lang} lang not found for main menu")
    keyboard_markup = InlineKeyboardMarkup(keyboard)
    def edit_query(update: Update): 
        query = update.callback_query
        return query.edit_message_text(header, reply_markup=keyboard_markup)
    def new_msg(update: Update):
        return update.message.reply_text(header, reply_markup=keyboard_markup)
    return edit_query(update) if edit_current else new_msg(update)


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
    # return update.message.reply_text(header.format(balance=balance, balance_dollar=balance_dollar),
    #                                  reply_markup=keyboard_markup)
    query = update.callback_query 
    return query.edit_message_text(header.format(balance=balance,
                                                 balance_dollar=balance_dollar),
                                                 reply_markup=keyboard_markup,
                                                 parse_mode=ParseMode.HTML)
    

ADDRESS = Annotated[str, "wallet address"]
NAME = Annotated[str, "wallet name"]
async def wallets_msg(update: Update, wallets: dict[NAME, ADDRESS], lang:str = "eng"):
    lang = lang.title()
    query = update.callback_query
    try: 
        lang_cls = getattr(WalletsMenu, lang)
        header = lang_cls.header
    except AttributeError:
        raise AttributeError(f"{lang} lang not found for wallets menu")
    lang_obj = lang_cls(wallets)
    keyboard = lang_obj.keyboard
    keyboard_markup = InlineKeyboardMarkup(keyboard)
    await query.answer()
    return await query.edit_message_text(header, reply_markup=keyboard_markup, 
                                        parse_mode=ParseMode.HTML)



async def wallet_msg(update: Update, wallet_name: str, 
                     wallet_balance:float, addr:str, lang:str = "eng"):
    lang = lang.title()
    query = update.callback_query
    try: 
        lang_cls = getattr(WalletMenu, lang)
        keyboard = lang_cls.keyboard
    except AttributeError:
        raise AttributeError(f"{lang} lang not found for wallet menu")
    lang_obj = await lang_cls(wallet_name = wallet_name, 
                              wallet_balance = wallet_balance, addr = addr)
    header = lang_obj.header
    keyboard_markup = InlineKeyboardMarkup(keyboard)
    # parsmode MarkdownV2 or HTML
    query.answer()
    return await query.edit_message_text(header, reply_markup=keyboard_markup,
                                         parse_mode=ParseMode.HTML)
    
    
        
    