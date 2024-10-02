from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)

from .messages import (MainMenu_msg, wallets_msg, FinanceMenu_msg,
                       wallet_msg, NewWalletType_msg, NewWalletName_msg )
import os
from tonpay.database.Models import (User, Wallet, insert_row, TON_Wallet)
from tonpay.wallets.blockchain.TON import Wallet as TON_Wallet
from tonpay.Encryption import fromBASE64
from sqlmodel import select
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession
from tonpay.database.Engine import ASYNC_ENGINE, ENGINE
from loguru import logger
from ton.account import Account
from tonpay import Defaults
from tonpay.utils import Utils
from tonpay.wallets.blockchain.Base import Wallet as BaseWallet



# button names
HOME, WALLETS, WALLET_NAME, FINANCE, BACK = "home", "wallets", "walletname", "finance", "back"
NEW_WALLET, SEEDS, TRANSFER, QRCODE, DELETE, REFRESH = "new_wallet", "seeds", "transfer", "qr_code", "delete", "refresh"
### defining routes 
MAIN_ROUTE, END_ROUTE, NEW_WALLET_ROUTE, WALLET_DETAIL_ROUTE = 0, 1, 2, 3
##### params
TOKEN = Defaults.options.telegram.token
LANG = Defaults.options.telegram.lang
blockchains = ["TON", "BNB", "ETH"]
#######

logger.info("starting TONPAY telegram bot")
class ButtonsHandler:
    # below var stores user last route in conversation
    _prev_user_callback = {} # self.prev_user_callback[user_id] = last_callback 
    __users = {} # self.users["user_id"] = user        
        
    @logger.catch
    async def finance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query # getting input query
        user_id = str(update.effective_user.id)
        user: User|None = await User.get(user_id)
        balance_ton = 0
        balance_USDT = 0
        for wallet in user.wallets:
            balance_USDT += (await wallet.balance_USDT) # balance for all wallets 
        user._logger.debug(f"balance calculated: {balance_ton}")
        await query.answer()
        if balance_USDT > 0: 
            from tonpay.utils.ccxt import convert_ticker
            balance_ton = balance_USDT/(await convert_ticker(1, "TON", "USDT"))
            balance_ton = balance_USDT
        else: balance_ton = balance_USDT = 0 
        await FinanceMenu_msg(update, LANG, balance_ton, balance_USDT)
        self._prev_user_callback[user_id] = self.home
        return MAIN_ROUTE
    
    
    @logger.catch
    async def wallets(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                      edit_current: bool = True):
        user_id = str(update.effective_user.id)
        user: User|None = await User.get(user_id)
        _wallets = await user.dump_wallets(asjson=True, include_fields=["address", "type"])
        user._logger.debug("fetched user wallets: {wallets}", wallets=list(_wallets.keys()) )
        await wallets_msg(update, _wallets, LANG, edit_current=edit_current)
        self._prev_user_callback[user_id] = self.finance
        return MAIN_ROUTE
    
    
    @logger.catch
    async def wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        wallet_name: str = '_'.join(query.data.split('_')[1:])
        user_id = str(update.effective_user.id)
        logger.debug(f"{wallet_name = }")
        query = select(Wallet).options(selectinload(Wallet.user)) \
                .where(Wallet.user.user_id == user_id, 
                       Wallet.name == wallet_name)
        async with AsyncSession(ASYNC_ENGINE) as session:
            _wallet: Wallet = (await session.exec(query)).one()
        logger.debug("fetched user wallet: {wallet}", wallet=_wallet.name )
        balance = await _wallet.balance
        addr = await _wallet.address
        await wallet_msg(update, wallet_name, _wallet.type,
                         balance, addr, LANG)
        self._prev_user_callback[user_id] = self.wallets
        WalletDetail._selected_wallet[user_id] = _wallet
        return WALLET_DETAIL_ROUTE
    
    
    @logger.catch
    async def back(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        prev_user_callback = self._prev_user_callback[user_id]
        if not prev_user_callback: self.home(update, context)
        await prev_user_callback(update, context)
        return MAIN_ROUTE
    
    
    @logger.catch
    async def home(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        await MainMenu_msg(update, LANG, True)
        self._prev_user_callback[user_id] = None
        return MAIN_ROUTE        
    
    
    async def refresh_wallets(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.wallets(update, context)
    
    
    async def refresh_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.wallet(update, context)
    
    
    async def refresh_finance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.finance(update, context)
    
    
    async def new_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        user = await self._get_db_user(user_id, update, context)
        if not user: return MAIN_ROUTE
        await NewWalletType_msg(update)
        return NEW_WALLET_ROUTE
    
    
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
            self._prev_user_callback[user_id] = None
        else: 
            user._logger.debug("user already exists")
            user._logger.debug(f"user wallets: {user.wallets}")
            self.users[user_id] = user
            self._prev_user_callback[user_id] = None
        return MAIN_ROUTE
    
    
    def init_users_db(self, max_size: int = 5000):
        import sys 
        if sys.getsizeof(self.users) >= max_size:
            self.users = {} 
        if sys.getsizeof(self._prev_user_callback) >= max_size: 
            self._prev_user_callback = {}
            
            
    async def _get_db_user(self, user_id: str, update: Update, 
                 context: ContextTypes.DEFAULT_TYPE) -> User:
        user = self.users.get(str(user_id), None)
        if not user: 
            await self.start(update, context)
            return None
        return user
            
        
    @property
    def users(self):
        return self.__users
    
    
class WalletDetail:
    _selected_wallet:dict[str, str] = {}
    
    async def qrcode(self, update:Update, context: ContextTypes.DEFAULT_TYPE):
        pass
    
    
    async def transfer(self, update:Update, context: ContextTypes.DEFAULT_TYPE):
        pass
    
    
    async def seeds(self, update:Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        wallet: Wallet = self._selected_wallet[user_id]
        detail = await wallet.wallet_detail
        seeds = detail.seeds  
        from tonpay.Telegram.styles.Utils import back_home_keyboard as bhk
        await update.message.reply_text(seeds, reply_markup=[bhk("Back", "Home")])
        return WALLET_DETAIL_ROUTE  
    
    
    async def delete(self, update:Update, context: ContextTypes.DEFAULT_TYPE):
        pass
    
    
class NewWalletHandler(ButtonsHandler):
    _user_input = {} # user_input[user_id] == {"name": ...., "type":....}
    user_lastcallback = {} # user_lastcallback[user_id] == self.name

    async def Type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        query = update.callback_query
        self._user_input[user_id] = {"name": None, "type": None}
        
        _type = query.data.upper()
        assert _type in blockchains, f"input blockchain {_type} not found"
        self._user_input[user_id]['type'] = _type
        await NewWalletName_msg(update)
        self.user_lastcallback[user_id] = "type"
        return NEW_WALLET_ROUTE
    
    
    async def name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        name = update.message.text
        self._user_input[user_id]["name"] = name
        _type = self._user_input[user_id]["type"]
        user: User|None = await User.get(user_id)
        assert name not in (await user.dump_wallets()).keys(), f"wallet {name=} is used before"
        wallet = await self._create_wallet(_type)
        path = await wallet.get_path()
        addr = await wallet.get_address()
        await user.add_wallet(name=name, address=addr, path=path, 
                              Type=_type, unit=_type)
        await self.wallets(update, context, edit_current=False) # back to wallets menu
        self.user_lastcallback[user_id] = "name"
        return MAIN_ROUTE
    
    
    async def _create_wallet(self, Type: str = "TON") -> BaseWallet:
        from importlib import import_module
        Type = Type.upper()
        assert Type in blockchains, f"input {Type} blockchain is not acceptable"
        Wallet: BaseWallet = import_module(f"tonpay.wallets.blockchain.{Type}").Wallet
        wallet = await Wallet.new_wallet()
        return wallet    
    
    
    async def skip(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        name = None # default wallet name
        _type = self._user_input[user_id]["type"]
        user: User|None = await User.get(user_id)
        wallet = await self._create_wallet(_type)
        path = await wallet.get_path()
        addr = await wallet.get_address()
        await user.add_wallet(name=name, address=addr, path=path,
                              Type=_type, unit=_type)
        await self.wallets(update, context, edit_current=False) # back to wallets menu
        return MAIN_ROUTE
    
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.wallets(update, context, False)
        return MAIN_ROUTE
    



def main() -> None:
    button_handler = ButtonsHandler()
    wallet = NewWalletHandler()
    wallet_detail = WalletDetail()
    
    application = Application.builder().token(TOKEN) \
                  .concurrent_updates(True).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", button_handler.start)],
        states={
            MAIN_ROUTE: [
                CallbackQueryHandler(button_handler.finance, pattern=f"^{FINANCE}$"),
                CallbackQueryHandler(button_handler.wallets, pattern=f"^{WALLETS}$"),
                CallbackQueryHandler(button_handler.wallet, pattern=f"^{WALLET_NAME}"),
                CallbackQueryHandler(button_handler.home, pattern=f"^{HOME}$"),
                CallbackQueryHandler(button_handler.back, pattern=f"^{BACK}$"),
                CallbackQueryHandler(button_handler.new_wallet, pattern=f"^{NEW_WALLET}$")
            ],
            NEW_WALLET_ROUTE: [
                CommandHandler("skip", wallet.skip),
                CommandHandler("cancel", wallet.cancel),
                CallbackQueryHandler( wallet.Type,
                    pattern=Utils.selectables2regex(blockchains)),
                MessageHandler(filters.TEXT & ~filters.COMMAND, wallet.name),
            ],
            WALLET_DETAIL_ROUTE:[
                CallbackQueryHandler(wallet.refresh_wallet, pattern=f"^{REFRESH}$"),
                CallbackQueryHandler(wallet_detail.qrcode, pattern=f"^{QRCODE}$"),
                CallbackQueryHandler(wallet_detail.transfer, pattern=f"^{TRANSFER}$"),
                CallbackQueryHandler(wallet_detail.seeds, pattern=f"^{SEEDS}$"),
                CallbackQueryHandler(wallet_detail.delete, pattern=f"^{DELETE}$"),
                CallbackQueryHandler(wallet.back, pattern=f"^{BACK}$"),
                CallbackQueryHandler(wallet.home, pattern=f"^{HOME}$"),
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