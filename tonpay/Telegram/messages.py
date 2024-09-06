
from telegram import InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from .styles import MainMenu, FinanceMenu, WalletsMenu, WalletMenu
from .styles.new_wallet import Type
from ton.account import Account
from typing import Annotated
from telegram.constants import ParseMode


async def MainMenu_msg(update: Update, lang:str = "eng", edit_current: bool = False):
    lang = lang.title()
    try: 
        lang_cls = getattr(MainMenu, lang)
        keyboard = lang_cls.keyboard
        header = lang_cls.header
    except AttributeError:
        raise AttributeError(f"{lang} lang not found for main menu")
    keyboard_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    if edit_current:
            await query.answer()
            return await query.edit_message_text(header, reply_markup=keyboard_markup,
                                                parse_mode=ParseMode.HTML)
    else: 
        return await update.message.reply_text(header, reply_markup=keyboard_markup,
                                            parse_mode=ParseMode.HTML)



async def FinanceMenu_msg(update: Update, lang:str = "eng", balance:str|float = 0,
                    balance_dollar:str|float = 0, edit_current: bool = True):
    lang = lang.title()
    try:
        lang_cls = getattr(FinanceMenu, lang)
        keyboard = lang_cls.keyboard
        header:str = lang_cls.header
        header = header.format(balance=balance, balance_dollar=balance_dollar)
    except AttributeError:
        raise AttributeError(f"{lang} lang not found for finance menu")
    keyboard_markup = InlineKeyboardMarkup(keyboard)
    # return update.message.reply_text(header.format(balance=balance, balance_dollar=balance_dollar),
    #                                  reply_markup=keyboard_markup)
    query = update.callback_query 
    if edit_current:
        await query.answer()
        return await query.edit_message_text(header, reply_markup=keyboard_markup,
                                            parse_mode=ParseMode.HTML)
    else: 
        return await update.message.reply_text(header, reply_markup=keyboard_markup,
                                            parse_mode=ParseMode.HTML)
    

ADDRESS = Annotated[str, "wallet address"]
NAME = Annotated[str, "wallet name"]
async def wallets_msg(update: Update, wallets: dict[NAME, ADDRESS], lang:str = "eng", 
                      edit_current: bool = True):
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
    if edit_current:
            await query.answer()
            return await query.edit_message_text(header, reply_markup=keyboard_markup,
                                                parse_mode=ParseMode.HTML)
    else: 
        return await update.message.reply_text(header, reply_markup=keyboard_markup,
                                            parse_mode=ParseMode.HTML)



async def wallet_msg(update: Update, wallet_name: str, 
                     wallet_balance:float, addr:str, lang:str = "eng",
                     edit_current: bool = True):
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
    if edit_current:
            await query.answer()
            return await query.edit_message_text(header, reply_markup=keyboard_markup,
                                                 parse_mode=ParseMode.HTML)
    else: 
        return await update.message.reply_text(header, reply_markup=keyboard_markup,
                                               parse_mode=ParseMode.HTML)
    
    
    
async def NewWalletType_msg(update: Update, lang:str = "eng", edit_current: bool = True):
    lang = lang.title()
    query = update.callback_query
    try: 
        lang_cls = getattr(Type, lang)
        keyboard = lang_cls.keyboard
        header = lang_cls.header
    except AttributeError:
        raise AttributeError(f"{lang} lang not found for wallet menu")
    keyboard_markup = InlineKeyboardMarkup(keyboard)
    if edit_current:
        await query.answer()
        return await query.edit_message_text(header, reply_markup=keyboard_markup,
                                             parse_mode=ParseMode.HTML)
    else: 
        return await update.message.reply_text(header, reply_markup=keyboard_markup,
                                               parse_mode=ParseMode.HTML)
        

async def NewWalletName_msg(update: Update, lang:str = "eng", edit_current: bool = True):
    lang = lang.title()
    query = update.callback_query
    header_eng = """choose a name for your new wallet: 
(/skip to choose a default name, /cancel to cancel making new wallet)"""
    header_fa = """یک اسم برای کیف پول خود انتخاب کن
    (/skip برای نادیده گرفتن /cancel برای لغو)"""
    header = header_eng if lang.lower() == "eng" else header_fa
    if edit_current:
        await query.answer()
        return await query.edit_message_text(header,
                                             parse_mode=ParseMode.HTML)
    else: 
        return await update.message.reply_text(header,
                                               parse_mode=ParseMode.HTML)
        
    
    
    
    
        
    