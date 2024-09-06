from telegram import InlineKeyboardMarkup, Update, InlineKeyboardButton as IKB
from ton.account import Account
from ...styles.Utils import back_home_keyboard as bhk
from typing import Annotated
from tonpay.Defaults import _blockchains 

_keyboard = [[IKB(bc.upper(), callback_data=bc.upper()) for bc in _blockchains]]

class Eng:
    header = "enter wallet type. available blockchains:"
    keyboard = _keyboard
    
class Fa:
    header = "نوع کیف پول خود را انتخاب کنید. بلاکچین های فعال:"
    keyboard = _keyboard
    