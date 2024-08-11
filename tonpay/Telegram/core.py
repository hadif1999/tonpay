from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)

from .messages import MainMenu_msg, wallets_msg, FinanceMenu_msg, wallet_msg
import os
from tonpay.database.Models import (User, Wallet, insert_row)
from sqlmodel import select
from loguru import logger
from ton.account import Account
from tonpay import Defaults



# state and page names
HOME, WALLETS, WALLET, FINANCE, BACK = "home", "wallets", "wallet", "finance", "back"
MAIN_ROUTE, END_ROUTE = 0, 1
TOKEN = Defaults.options.telegram.token
LANG = Defaults.options.telegram.lang


class ButtonsHandler:
    # below var stores user last route in conversation
    prev_callback = {} # self.prev_callback[user_id] = last_callback 
    
    def __init__(self) -> None:
        logger.info("starting TONPAY telegram bot")
        
        
    @logger.catch
    async def finance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query # getting input query
        user_id = str(update.effective_user.id)
        user: User = await User.get(user_id)      
        balance_ton = 0
        balance_USDT = 0
        for wallet in user.wallets:
            if wallet.unit == "TON": 
                balance_ton += (await wallet.balance) # just ton balance
            balance_USDT += (await wallet.balance_USDT) # balance for all wallets 
        user._logger.debug(f"balance calculated: {balance_ton}")
        await query.answer()
        await FinanceMenu_msg(update, LANG, balance_ton, balance_USDT)
        self.prev_callback[user_id] = self.home
        return MAIN_ROUTE
    
    
    @logger.catch
    async def wallets(self, update: Update, context):
        user_id = str(update.effective_user.id)
        user: User = await User.get(user_id)
        _wallets = await user.dump_wallets(asjson=True, include_fields=["address"])
        user._logger.debug("fetched user wallets: {wallets}", wallets=list(_wallets.keys()) )
        await wallets_msg(update, _wallets, LANG)
        self.prev_callback[user_id] = self.finance
        return MAIN_ROUTE
    
    
    @logger.catch
    async def wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        wallet_name = query.data
        user_id = str(update.effective_user.id)
        user: User = await User.get(user_id)
        _logger = user._logger
        _wallet: Wallet = (await user.dump_wallets())[wallet_name]
        _logger.debug("fetched user wallet: {wallet}", wallet=_wallet.name )
        await wallet_msg(update, wallet_name, _wallet.balance, _wallet.address, LANG)
        self.prev_callback[user_id] = self.wallets
        return MAIN_ROUTE
    
    
    @logger.catch
    async def back(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        prev_callback = self.prev_callback[user_id]
        if not prev_callback: self.home(update, context)
        await prev_callback(update, context)
        return MAIN_ROUTE
    
    
    @logger.catch
    async def home(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        await MainMenu_msg(update, LANG, True)
        self.prev_callback[user_id] = None
        return MAIN_ROUTE
    
            
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await MainMenu_msg(update, LANG)
    user_id = str(update.effective_user.id)
    user: User = await User.get(user_id)
    if not user: 
        new_user = User(user_id = user_id)
        await insert_row(new_user, True)
        new_user._logger.debug("user added")
    else: 
        user._logger.debug("user already exists")
    return MAIN_ROUTE


def main() -> None:
    button_handler = ButtonsHandler()
    
    application = Application.builder().token(TOKEN) \
                  .concurrent_updates(True).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_ROUTE: [
                CallbackQueryHandler(button_handler.finance, pattern=f"^{FINANCE}$"),
                CallbackQueryHandler(button_handler.wallets, pattern=f"^{WALLETS}$"),
                CallbackQueryHandler(button_handler.wallet, pattern=f"^{WALLET}$"),
                CallbackQueryHandler(button_handler.home, pattern=f"^{HOME}$"),
                CallbackQueryHandler(button_handler.back, pattern=f"^{BACK}$")
            ]
        },
        fallbacks=[CommandHandler("start", start)],
        conversation_timeout=60*4,
        per_chat=False
    )

    # Add ConversationHandler to application that will be used for handling updates
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES, timeout=20, 
                            drop_pending_updates=True)


if __name__ == "__main__":
    main()