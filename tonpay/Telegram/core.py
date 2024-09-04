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
from tonpay.database.Models import (User, Wallet, insert_row, TON_Wallet)
from tonpay.wallets.blockchain.TON import Wallet as TON_Wallet
from tonpay.Encryption import fromBASE64
from sqlmodel import select
from loguru import logger
from ton.account import Account
from tonpay import Defaults



# state and page names
HOME, WALLETS, WALLET, FINANCE, BACK = "home", "wallets", "wallet", "finance", "back"
NEW_WALLET = "new_wallet"
MAIN_ROUTE, END_ROUTE = 0, 1
TOKEN = Defaults.options.telegram.token
LANG = Defaults.options.telegram.lang


class ButtonsHandler:
    # below var stores user last route in conversation
    prev_user_callback = {} # self.prev_user_callback[user_id] = last_callback 
    __users = {} # self.users["user_id"] = user
    
    def __init__(self) -> None:
        logger.info("starting TONPAY telegram bot")
        
        
    @logger.catch
    async def finance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query # getting input query
        user_id = str(update.effective_user.id)
        user: User|None = await User.get(user_id)
        balance_ton = 0
        balance_USDT = 0
        for wallet in user.wallets:
            if (await wallet.unit) == "TON": 
                balance_ton += (await wallet.balance) # just ton balance
            balance_USDT += (await wallet.balance_USDT) # balance for all wallets 
        user._logger.debug(f"balance calculated: {balance_ton}")
        await query.answer()
        await FinanceMenu_msg(update, LANG, balance_ton, balance_USDT)
        self.prev_user_callback[user_id] = self.home
        return MAIN_ROUTE
    
    
    @logger.catch
    async def wallets(self, update: Update, context):
        user_id = str(update.effective_user.id)
        user: User|None = await User.get(user_id)
        _wallets = await user.dump_wallets(asjson=True, include_fields=["address"])
        user._logger.debug("fetched user wallets: {wallets}", wallets=list(_wallets.keys()) )
        await wallets_msg(update, _wallets, LANG)
        self.prev_user_callback[user_id] = self.finance
        return MAIN_ROUTE
    
    
    @logger.catch
    async def wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        wallet_name = query.data
        user_id = str(update.effective_user.id)
        user = await self.get_user_db(user_id, update, context)
        if not user: return 
        _logger = user._logger
        _wallet: Wallet = (await user.dump_wallets())[wallet_name]
        _logger.debug("fetched user wallet: {wallet}", wallet=_wallet.name )
        await wallet_msg(update, wallet_name, _wallet.balance, _wallet.address, LANG)
        self.prev_user_callback[user_id] = self.wallets
        return MAIN_ROUTE
    
    
    @logger.catch
    async def back(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        prev_user_callback = self.prev_user_callback[user_id]
        if not prev_user_callback: self.home(update, context)
        await prev_user_callback(update, context)
        return MAIN_ROUTE
    
    
    @logger.catch
    async def home(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        await MainMenu_msg(update, LANG, True)
        self.prev_user_callback[user_id] = None
        return MAIN_ROUTE        
    
    
    async def refresh_wallets(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass
    
    
    async def refresh_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass
    
    
    async def refresh_finance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass
    
    
    async def new_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        user = await self.get_user_db(user_id, update, context)
        if not user: return
        path = "".join(['b' for i in range(16)])
        await user.add_wallet(name = "test", path=path,
                              Type="TON", unit = "TON")
        # await self.wallets(update, context)
        return MAIN_ROUTE
    
    
    async def seeds(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass
    
    
    async def import_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass
    
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await MainMenu_msg(update, LANG)
        user_id = str(update.effective_user.id)
        user: User|None = await User.get(user_id)
        self.init_users_db()
        if not user: 
            new_user = User(user_id = user_id)
            await insert_row(new_user, True)
            new_user._logger.debug("user added")
            new_user = await User.get(user_id)
            await new_user.add_wallet(name=None, Type=None,
                                      unit=None, throw_exp=True)
            self.users[user_id] = new_user
            self.prev_user_callback[user_id] = None
        else: 
            user._logger.debug("user already exists")
            user._logger.debug(f"user wallets: {user.wallets}")
            self.users[user_id] = user
            self.prev_user_callback[user_id] = None
        return MAIN_ROUTE
    
    
    def init_users_db(self, max_size: int = 5000):
        import sys 
        if sys.getsizeof(self.users) >= max_size:
            self.users = {} 
        if sys.getsizeof(self.prev_user_callback) >= max_size: 
            self.prev_user_callback = {}
            
            
    async def get_user_db(self, user_id: str, update: Update, 
                 context: ContextTypes.DEFAULT_TYPE) -> User:
        user = self.users.get(str(user_id), None)
        if not user: 
            await self.start(update, context)
            return None
        return user
            
        
    @property
    def users(self):
        return self.__users


def main() -> None:
    button_handler = ButtonsHandler()
    
    application = Application.builder().token(TOKEN) \
                  .concurrent_updates(True).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", button_handler.start)],
        states={
            MAIN_ROUTE: [
                CallbackQueryHandler(button_handler.finance, pattern=f"^{FINANCE}$"),
                CallbackQueryHandler(button_handler.wallets, pattern=f"^{WALLETS}$"),
                CallbackQueryHandler(button_handler.wallet, pattern=f"^{WALLET}$"),
                CallbackQueryHandler(button_handler.home, pattern=f"^{HOME}$"),
                CallbackQueryHandler(button_handler.back, pattern=f"^{BACK}$"),
                CallbackQueryHandler(button_handler.new_wallet, pattern=f"^{NEW_WALLET}$")
            ]
        },
        fallbacks=[CommandHandler("start", button_handler.start)],
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