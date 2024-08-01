from telegram import InlineKeyboardButton as IKB


def render_keyboard(finance_txt:str, exchange_txt:str, webapp_txt:str,
                    setting_txt:str, referral_txt:str, help_txt:str, 
                    webapp_url:str|None = None):
    finance = IKB("💵 " + finance_txt, callback_data="finance")
    exchange = IKB("🤑 " + exchange_txt, callback_data="exchange")
    webapp = IKB("🌐 " + webapp_txt, callback_data="webapp", url=webapp_url)
    setting = IKB("⚙️ " + setting_txt, callback_data="setting")
    refferal = IKB("⛓️ " + referral_txt, callback_data="referral")
    _help = IKB("❔ " + help_txt, callback_data="help")
    keyboard = [[finance, exchange], [webapp], [setting, refferal, _help]]
    return keyboard


class Eng:
    header = """welcome to TonPay! 👋 
use the below buttons to navigate throw the bot."""
    keyboard = render_keyboard("Finance", "Exchange", "Webapp",
                               "Setting", "Referral", "Help")


class Fa:
    header = """به تون پی خوش آمدی!👋
میتوانی از دکمه های زیر برای استفاده از امکانات مختلف ربات استفاده کنی."""
    keyboard = render_keyboard("مالی", "تبادل", "وب اپلیکیشن", 
                               "تنظیمات", "معرفی", "راهنما")