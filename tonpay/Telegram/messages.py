from telegram import (InlineKeyboardMarkup, Update,
                      ReplyKeyboardRemove, InlineKeyboardButton)
from .styles import MainMenu, FinanceMenu, WalletsMenu, WalletMenu
from .styles.new_wallet import Type
from ton.account import Account
from typing import Annotated
from telegram.constants import ParseMode
from tonpay.Telegram.styles.Utils import back_home_keyboard as bhk, BackHomeKeyboard
from tonpay import Defaults
from loguru import logger

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



async def wallet_msg(update: Update, wallet_name: str, Type: str|None,
                     wallet_balance:float, addr:str, lang:str = "eng",
                     edit_current: bool = True):
    lang = lang.title()
    _Type = Type.upper() if Type else "Internal" 
    from tonpay.Defaults import formats
    explorer_url = getattr(formats.explorer_url, _Type, "")
    query = update.callback_query
    try: 
        lang_cls = getattr(WalletMenu, lang)
        keyboard = lang_cls.keyboard
    except AttributeError:
        raise AttributeError(f"{lang} lang not found for wallet menu")
    lang_obj = lang_cls(wallet_name = wallet_name, 
                        balance = wallet_balance, addr = addr, 
                        explorer_url = explorer_url, Type = Type or Defaults.Blockchain_enum.TON.value)
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
    

class NewWalletMsg:
    
    @staticmethod
    async def type(update: Update, lang:str = "eng", edit_current: bool = True):
        lang = lang.title()
        query = update.callback_query
        try: 
            lang_cls = getattr(Type, lang)
            keyboard:list = lang_cls.keyboard
            header = lang_cls.header
        except AttributeError:
            raise AttributeError(f"{lang} lang not found for wallet menu")
        bhk = getattr(BackHomeKeyboard, lang) # adding back-home kb        
        keyboard_markup = InlineKeyboardMarkup(keyboard)
        if edit_current:
            await query.answer()
            return await query.edit_message_text(header, reply_markup=keyboard_markup,
                                                parse_mode=ParseMode.HTML)
        else: 
            return await update.message.reply_text(header, reply_markup=keyboard_markup,
                                                parse_mode=ParseMode.HTML)
            
    
    @staticmethod
    async def name(update: Update, lang: str = "eng", edit_current: bool = True):
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
        
        
async def seeds_msg(update: Update, seeds: str, edit_current: bool = True, 
                    keyboard: list[list[InlineKeyboardButton]] = [BackHomeKeyboard.Eng]):
    _keyboard = InlineKeyboardMarkup(keyboard)
    title = "keep below seeds somewhere safe, unless you may lose access to your wallet: \n\n"
    _seeds = "    ".join([f"{i+1}.{seed}" for i, seed in enumerate(seeds.split())])
    if edit_current:
        query = update.callback_query
        await query.answer()
        return await query.edit_message_text(title + _seeds, reply_markup=_keyboard)
    else:
        return await update.message.reply_text(title + _seeds, reply_markup=_keyboard)
    
    
async def wait_msg(update: Update, edit_current: bool = True):
    header = "please wait..."
    if edit_current:
        query = update.callback_query
        await query.answer()
        return await query.edit_message_text(header)
    else: 
        return await update.message.reply_text(header)
        

class ImportWalletMsg:
    @staticmethod
    async def type(update: Update):
        from tonpay.Telegram.styles.new_wallet.Type import _keyboard
        keyboard = InlineKeyboardMarkup([_keyboard.copy(), BackHomeKeyboard.Eng])
        header = "choose wallet type to import: \n"
        # editing current msg
        query = update.callback_query
        await query.answer()
        return await query.edit_message_text(header, reply_markup=keyboard)
        
        
    @staticmethod
    async def seeds(update: Update, edit_current: bool = True):
        header = "enter seeds to import wallet (separated by space) \n\n"
        keyboard = InlineKeyboardMarkup([BackHomeKeyboard.Eng])
        if edit_current:
            # editing current msg
            query = update.callback_query
            await query.answer()
            return await query.edit_message_text(header, reply_markup=keyboard)
        else: 
            return await update.message.reply_text(header, reply_markup=keyboard)
        
    
    
    
        
    