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
    

def get_balance_str(title:str = "total balance"):
    _balance_str_base = f"<b>{title}</b>:" + "\n{balance} <b>TON</b> ~ {balance_dollar} <b>USDT</b>"
    return _balance_str_base


class Eng:
    _show_balance = True
    _balance_str = get_balance_str("total balance") if _show_balance else ""
    header = f"""📈 Finance Dashboard
    {_balance_str}"""
    keyboard = render_keyboard("Refresh", "Wallets", "Transactions", 
                               "Equity chart", "Payment Gateway", bhk("Back", "Home"))
    
    
class Fa:
    _show_balance = True
    _balance_str = get_balance_str("دارایی کل") if _show_balance else ""
    header = f"""📈 پنل مالی
    {_balance_str}"""
    keyboard = render_keyboard("به روزرسانی", "کیف پول ها", "مبادلات", "نمودار دارایی ها",
                               "درگاه پرداخت", "قبل", "خانه", bhk("قبل", "خانه"))
