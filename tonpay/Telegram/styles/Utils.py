from telegram import InlineKeyboardButton as IKB


def back_home_keyboard(back_txt: str, home_txt:str):
    return [IKB("↩️ " + back_txt, callback_data="back"), 
            IKB("🏠 " + home_txt, callback_data="home")]
    
    
class BackHomeKeyboard:
    Eng = back_home_keyboard("Back", "Home")
    Fa = back_home_keyboard("قبل", "خانه")
    