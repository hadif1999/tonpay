from telegram import InlineKeyboardMarkup, Update, InlineKeyboardButton as IKB
from ton.account import Account
from styles.Utils import back_home_keyboard as bhk


def render_keyboard(refresh_txt:str, QrCode_txt:str, transfer_txt:str,
                    seeds_txt:str, delete_txt:str, *other_keyboards):
    refresh = IKB("🔄 " + refresh_txt, callback_data="refresh")
    qrcode = IKB("🔲 " + QrCode_txt, callback_data="qrcode")
    transfer = IKB("💸 " + transfer_txt, callback_data="transfer")
    seeds = IKB("🔑 " + seeds_txt, callback_data="seeds")
    delete = IKB("❌ " + delete_txt, callback_data="delete")
    keyboard = [[refresh, qrcode], [transfer, seeds, delete]]
    for kbs in other_keyboards:
        if isinstance(kbs, list):
            keyboard.append(kbs)
    return keyboard
    

class Eng:
    keyboard = render_keyboard("Refresh", "QR Code", "Transfer", 
                               "Seeds", "Delete", bhk("Back", "Home"))
    async def __init__(self, wallet_name:str, wallet:Account) -> None:
        addr = wallet.address
        balance = await wallet.get_balance()
        self.header = f"""TonPay Wallet
        <b>name:</b> {wallet_name}
        
        <b>balance:</b> {balance}
        
        <b>address:</b> 
        {addr}
        <a href="https://tonviewer.com/{addr}">(open in explorer)</a>
        
        
        You can use the address printed above to send TON to your TONPAY account 
        from any TON-compatible wallets or services, including the exchanges.
        also you can use the 'seeds' button below to export your wallet to any
        TON-compatible wallet including another TONPAY wallet.
        """
        
        
class Fa:
    keyboard = render_keyboard("به روزرسانی", "QR کد", "انتقال", 
                               "کلمات عبور", "حذف", bhk("قبلی", "خانه"))
    async def __init__(self, wallet_name:str, wallet:Account) -> None:
        addr = wallet.address
        balance = await wallet.get_balance()
        self.header = f"""TonPay کیف پول
        <b>نام:</b> {wallet_name}
        
        <b>دارایی:</b> {balance}
        
        <b>آدرس:</b> 
        {addr}
        <a href="https://tonviewer.com/{addr}">(open in explorer)</a>
        
        شما میتوانید از آدرس چاپ شده در بالا برای انتقال ارز TON از هر صرافی یا کیف پولی 
        که این ارز را پشتیبانی میکند استفاده کنید. همچنین میتوانید از دکمه کلمات عبور استفاده 
        کنید و این کیف پول را در یک اکانت TONPAY یا هر کیف پولی که از TON پشتیبانی میکند وارد کنید.
        """
        
        
            