from typing import Iterable
from telegram import InlineKeyboardButton as IKB
from ..styles.Utils import back_home_keyboard as bhk


def render_keyboard(refresh_txt:str, wallets_txt:str, transactions_txt:str,
                equity_txt:str, payment_txt:str, *other_buttons):
    refresh = IKB("🔄 "+ refresh_txt, callback_data="refresh")
    wallets = IKB("💰 " + wallets_txt, callback_data="wallets")
    transactions = IKB("📒 " + transactions_txt, callback_data="transactions")
    equity = IKB("📈 " + equity_txt, callback_data="equity")
    payment = IKB("💳 " + payment_txt, callback_data="payment")
    keyboard = [[refresh, wallets], [transactions, equity], [payment]]
    for buttons in other_buttons:
        if isinstance(buttons, list):
            keyboard.append(buttons)
    return keyboard
    

class Eng:
    header = """📈 Finance Dashboard
    total balance: 
{balance} TON ~ {balance_dollar} USDT"""
    keyboard = render_keyboard("Refresh", "Wallets", "Transactions", 
                               "Equity chart", "Payment Gateway", bhk("Back", "Home"))
    
    
class Fa:
    header = """📈 پنل مالی
    دارایی کل: 
{balance} TON ~ {balance_dollar} USDT"""
    keyboard = render_keyboard("به روزرسانی", "کیف پول ها", "مبادلات", "نمودار دارایی ها",
                               "درگاه پرداخت", "قبل", "خانه", bhk("قبل", "خانه"))
