from telegram import Update, Message
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
                       wallet_msg, NewWalletMsg, ImportWalletMsg,
                       wait_msg, seeds_msg, send_image, del_current_query_msg,
                       TransferMsg)
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
NEW_WALLET, SEEDS, TRANSFER, QRCODE, DELETE, REFRESH, IMPORT = "new_wallet", "seeds", "transfer", "qr_code", "delete", "refresh", "import"
CONFIRM, CANCEL = "confirm", "cancel" # for transaction
### defining routes 
MAIN_ROUTE, END_ROUTE, NEW_WALLET_ROUTE, WALLET_DETAIL_ROUTE, IMPORT_WALLET_ROUTE = 0, 1, 2, 3, 4
IMPORT_WALLET_NAME_ROUTE, QRCODE_ROUTE, TRANSFER_ROUTE, TRANSACTIONS_ROUTE = 5, 6, 7, 8
TRANSFER_AMOUNT_ROUTE = 9
##### params
TOKEN = Defaults.options.telegram.token
LANG = Defaults.options.telegram.lang
blockchains = ["TON", "BNB", "ETH"]
#######

logger.info("starting TONPAY telegram bot")
class MainHandler:
    # below var stores user last route in conversation
    _prev_user_callback_temp = {} # self.prev_user_callback[user_id] = last_callback 
    __users_temp = {} # self.users["user_id"] = user        
        
    @logger.catch
    async def finance(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                      edit_current: bool = True):
        # query = update.callback_query # getting input query
        user_id = str(update.effective_user.id)
        user: User|None = await User.get(user_id)
        self.users[user_id] = user
        await wait_msg(update, context)
        balance_ton = 0
        balance_USDT = 0
        for wallet in user.wallets:
            balance_USDT += (await wallet.balance_USDT) # balance for all wallets 
        user._logger.debug(f"balance calculated: {balance_USDT}")
        if balance_USDT > 0: 
            from tonpay.utils.ccxt import convert_ticker
            balance_ton = balance_USDT/(await convert_ticker(1, "TON", "USDT"))
        else: balance_ton = balance_USDT = 0 
        await FinanceMenu_msg(update, LANG, round(balance_ton, 2), round(balance_USDT, 2),
                              edit_current)
        self._prev_user_callback_temp[user_id] = self.home
        return MAIN_ROUTE
    
    
    @logger.catch
    async def wallets(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                      edit_current: bool = True):
        user_id = str(update.effective_user.id)
        user: User|None = await User.get(user_id)
        _wallets = await user.dump_wallets(asjson=True, include_fields=["address", "type", "id"])
        user._logger.debug("fetched user wallets: {wallets}", wallets=list(_wallets.keys()) )
        await wallets_msg(update, context, _wallets, LANG, edit_current=edit_current)
        self._prev_user_callback_temp[user_id] = self.finance
        return MAIN_ROUTE
    
    
    @logger.catch
    async def wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                     edit_current: bool = True, as_new_msg: bool = False,
                     wallet: str|Wallet|None = None):
        query = update.callback_query
        if isinstance(wallet, str):
            wallet_name = wallet
        elif not wallet: 
            wallet_name = '_'.join(query.data.split('_')[1:])
        user_id = str(update.effective_user.id)
        _wait_msg = await wait_msg(update, context, as_new_msg=True)
        if isinstance(wallet, Wallet):
            _wallet = wallet
            wallet_name = _wallet.name
        else:
            user: User|None = await User.get(user_id)
            _wallet: Wallet = (await user.dump_wallets())[wallet_name]
        balance = await _wallet.balance
        addr = await _wallet.address
        logger.debug("fetched user wallet: {wallet}", wallet=wallet_name )
        await wallet_msg(update, context, wallet_name, getattr(_wallet.type, "value", None),
                         balance, addr, LANG, edit_current, as_new_msg)
        await _wait_msg.delete()
        self._prev_user_callback_temp[user_id] = self.wallets
        WalletDetailHandler._selected_wallet_temp[user_id] = _wallet
        return WALLET_DETAIL_ROUTE
    
    
    @logger.catch
    async def back(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                   edit_current: bool = True):
        user_id = str(update.effective_user.id)
        prev_user_callback = self._prev_user_callback_temp[user_id]
        if not prev_user_callback: self.home(update, context)
        await prev_user_callback(update, context, edit_current)
        return MAIN_ROUTE
    
    
    @logger.catch
    async def home(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                   edit_current: bool = True, as_new_msg: bool = False):
        user_id = str(update.effective_user.id)
        await MainMenu_msg(update, context, LANG, edit_current, as_new_msg)
        self._init_vars()
        if user_id in self.users: del self.users[user_id]
        self._prev_user_callback_temp[user_id] = None
        return MAIN_ROUTE        
    
    
    async def refresh_wallets(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.wallets(update, context)
    
    
    async def refresh_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.wallet(update, context)
    
    
    async def refresh_finance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.finance(update, context)
    
    
    async def new_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                         edit_current: bool = True):
        user_id = str(update.effective_user.id)
        user = await self._get_db_user(user_id, update, context)
        if not user: return MAIN_ROUTE
        await NewWalletMsg.type(update, LANG, edit_current)
        self._prev_user_callback_temp[user_id] = self.wallets
        return NEW_WALLET_ROUTE
    
    
    async def import_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        await ImportWalletMsg.type(update)
        self._prev_user_callback_temp[user_id] = self.wallets
        return IMPORT_WALLET_ROUTE
    
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await MainMenu_msg(update, LANG)
        user_id = str(update.effective_user.id)
        user: User|None = await User.get(user_id)
        self._init_vars()
        if not user: 
            new_user = User(user_id = user_id)
            await insert_row(new_user, True)
            new_user._logger.debug("user added")
            new_user = await User.get(user_id)
            await new_user.add_wallet(name=None, Type=None,
                                      unit=None, throw_exp=True)
            self.users[user_id] = new_user
            self._prev_user_callback_temp[user_id] = None
        else: 
            user._logger.debug("user already exists")
            user._logger.debug(f"user wallets: {user.wallets}")
            self.users[user_id] = user
            self._prev_user_callback_temp[user_id] = None
        return MAIN_ROUTE
    
    
    def _init_vars(self, max_size: int = 5000):
        import sys 
        if sys.getsizeof(self.users) >= max_size:
            self.users = {} 
        if sys.getsizeof(self._prev_user_callback_temp) >= max_size: 
            self._prev_user_callback_temp = {}
            
            
    async def _get_db_user(self, user_id: str, update: Update, 
                 context: ContextTypes.DEFAULT_TYPE) -> User:
        user = self.users.get(str(user_id), None)
        if not user: 
            await self.start(update, context)
            return None
        return user
            
        
    @property
    def users(self):
        return self.__users_temp


class ImportWalletHandler(MainHandler):
    _user_input_temp = {} # _user_input_temp[user_id] = {"name": None, "type": None, "seeds": None}
    _user_lastcallback_temp = {}
    
    async def Type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        query = update.callback_query
        self._user_input_temp[user_id] = {"name": None, "type": None, "seeds": None}
        _type = query.data.upper()
        assert _type in blockchains, f"input blockchain {_type} not found"
        self._user_input_temp[user_id]['type'] = _type
        await NewWalletMsg.name(update, lang=LANG)
        self._user_lastcallback_temp[user_id] = "Type"
        return IMPORT_WALLET_NAME_ROUTE
    
    
    async def name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        name = update.message.text.strip().lower()        
        user_id = str(update.effective_user.id)
        self._user_input_temp[user_id]["name"] = name 
        await ImportWalletMsg.seeds(update, False)
        return IMPORT_WALLET_ROUTE
    
    
    async def seeds(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        seeds = update.message.text.strip().lower()        
        user_id = str(update.effective_user.id)
        
        assert len(seeds.split()) > 10, "not enough number of seeds"
        self._user_input_temp[user_id]["seeds"] = seeds
        user: User = await User.get(user_id, load_wallets=False)
        inputs = self._user_input_temp[user_id]
        _name, _type, _seeds = inputs["name"], inputs["type"], inputs["seeds"]
        await user.import_wallet(_type, _seeds, _name)
        await self.wallets(update, context, edit_current=False)
        return MAIN_ROUTE
        
             
    async def skip(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        self._user_input_temp[user_id]["name"] = None
        await ImportWalletMsg.seeds(update, False)
        return IMPORT_WALLET_ROUTE
        
        
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.wallets(update, context, False)
        return MAIN_ROUTE
    
    
    async def home(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        await super().home(update, context)
        if user_id in self._user_input_temp: del self._user_input_temp[user_id]
        if user_id in self._user_lastcallback_temp: del self._user_lastcallback_temp[user_id]
        return MAIN_ROUTE
    
    
    def _init_vars(self, max_size: int = 5000):
        import sys
        super()._init_vars(max_size)
        if sys.getsizeof(self._user_input_temp) >= max_size:
            self._user_input_temp = {}
        if sys.getsizeof(self._user_lastcallback_temp) >= max_size:
            self._user_lastcallback_temp = {}
            
            
    
class WalletDetailHandler(MainHandler):
    _selected_wallet_temp:dict[str, Wallet] = {}
    
    async def qrcode(self, update:Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        wallet: Wallet = self._selected_wallet_temp[user_id]
        wallet_type: str = wallet.type.value.upper()
        from tonpay.Defaults import formats
        # generating url
        url_fmt: str = getattr(formats.transfer_url, wallet_type)
        addr = await wallet.address
        url = url_fmt.format(addr = addr)
        # generating qr-code
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(url)
        qr.make(True)
        img = qr.make_image(fill_color="black", back_color="white")
        # sending to user
        from io import BytesIO
        bio = BytesIO()
        bio.name = "qr_code.jpeg"
        img.save(bio, "JPEG")
        bio.seek(0) 
        await send_image(update, context, bio)
        self._prev_user_callback_temp[user_id] = self.wallet
        return QRCODE_ROUTE  
    
    
    async def qrcode_back(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        wallet: Wallet = self._selected_wallet_temp[user_id]
        ##### delete qr-code
        await del_current_query_msg(update, context)
        ######
        await self.wallet(update, context, as_new_msg=True, wallet=wallet)
        self._prev_user_callback_temp[user_id] = self.wallets
        return WALLET_DETAIL_ROUTE
    
    
    async def qrcode_home(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        ##### delete qr-code
        await del_current_query_msg(update, context)
        ######
        return await super().home(update, context, as_new_msg=True)
        
    
    async def transfer(self, update:Update, context: ContextTypes.DEFAULT_TYPE):
        await TransferMsg.dest(update, context)
        return TRANSFER_ROUTE
    
    
    async def transactions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass
    
    
    @logger.catch
    async def seeds(self, update:Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        wallet: Wallet = self._selected_wallet_temp[user_id]
        detail = await wallet.wallet_detail
        seeds = await detail.seeds  
        from tonpay.Telegram.styles.Utils import back_home_keyboard as bhk
        await seeds_msg(update, seeds, True, [bhk("Back", "Home")])
        self._prev_user_callback_temp[user_id] = self.wallets
        return WALLET_DETAIL_ROUTE  
    
    
    async def delete(self, update:Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        wallet: Wallet = self._selected_wallet_temp[user_id]
        await wallet.delete
        await self.wallets(update, context)
        return MAIN_ROUTE
    
    
    async def home(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        await super().home(update, context)
        if user_id in self._selected_wallet_temp:
            del self._selected_wallet_temp[user_id]
        return MAIN_ROUTE
            
            
    def _init_vars(self, max_size: int = 5000):
        import sys
        super()._init_vars(max_size)
        if sys.getsizeof(self._selected_wallet_temp) >= max_size:
            self._selected_wallet_temp = {}

    
    
class NewWalletHandler(MainHandler):
    _user_input_temp = {} # user_input[user_id] == {"name": ...., "type":....}
    _user_lastcallback_temp = {} # user_lastcallback[user_id] == self.name

    async def Type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        query = update.callback_query
        self._user_input_temp[user_id] = {"name": None, "type": None}
        _type = query.data.upper()
        assert _type in blockchains, f"input blockchain {_type} not found"
        self._user_input_temp[user_id]['type'] = _type
        await NewWalletMsg.name(update)
        self._user_lastcallback_temp[user_id] = "type"
        return NEW_WALLET_ROUTE
    
    
    @logger.catch
    async def name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        name = update.message.text
        self._user_input_temp[user_id]["name"] = name
        _type = self._user_input_temp[user_id]["type"]
        _wait_msg = await wait_msg(update, context, as_new_msg=True)
        user: User|None = await User.get(user_id, load_wallets=False)
        # assert name not in (await user.dump_wallets()).keys(), f"wallet {name=} is used before"
        wallet = await self._create_wallet(_type)
        path = await wallet.get_path()
        addr = await wallet.get_address()
        await user.add_wallet(name=name, address=addr, path=path, 
                              Type=_type, unit=_type)
        await self.wallets(update, context, edit_current=False) # back to wallets menu
        await _wait_msg.delete()
        self._user_lastcallback_temp[user_id] = "name"
        return MAIN_ROUTE
    
    
    async def _create_wallet(self, Type: str = "TON") -> BaseWallet:
        from importlib import import_module
        Type = Type.upper()
        assert Type in blockchains, f"input {Type} blockchain is not acceptable"
        Wallet: BaseWallet = import_module(f"tonpay.wallets.blockchain.{Type}").Wallet
        wallet = await Wallet.new_wallet()
        return wallet    
    
    
    @logger.catch
    async def skip(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        name = None # default wallet name
        _type = self._user_input_temp[user_id]["type"]
        await wait_msg(update, context)
        user: User|None = await User.get(user_id)
        wallet = await self._create_wallet(_type)
        path = await wallet.get_path()
        addr = await wallet.get_address()
        await user.add_wallet(name=name, address=addr, path=path,
                              Type=_type, unit=_type)
        await self.wallets(update, context) # back to wallets menu
        return MAIN_ROUTE
    
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.wallets(update, context, False)
        return MAIN_ROUTE
    
    
    async def home(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        await super().home(update, context)
        if user_id in self._user_input_temp:
            del self._user_input_temp[user_id]
        if user_id in self._user_lastcallback_temp:
            del self._user_lastcallback_temp[user_id]
        return MAIN_ROUTE
            
            
    def _init_vars(self, max_size: int = 5000):
        import sys
        super()._init_vars(max_size)
        if sys.getsizeof(self._user_input_temp) >= max_size:
            self._user_input_temp = {}
        if sys.getsizeof(self._user_lastcallback_temp) >= max_size:
            self._user_lastcallback_temp = {}
            
            
class TransferHandler(WalletDetailHandler):
    _user_input_temp = {}
    
    async def dest(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        dest = update.message.text
        self._user_input_temp[user_id] = {"dest": dest, "amt": None}
        await TransferMsg.amount(update, context, as_new_msg = True)
        return TRANSFER_AMOUNT_ROUTE
    
    
    async def amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        amt = float(update.message.text)
        self._user_input_temp[user_id]["amt"] = amt
        dest = self._user_input_temp[user_id]["dest"]
        wallet_db: Wallet = self._selected_wallet_temp[user_id]
        src = await wallet_db.address
        Type = wallet_db.type.value
        await TransferMsg.confirm(update, context, src, 
                                  dest, amt, Type, as_new_msg = True)
        return TRANSFER_AMOUNT_ROUTE
    
    
    async def confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        inputs = self._user_input_temp[user_id]
        dest, amt = inputs["dest"], inputs["amt"]
        wallet_db: Wallet = self._selected_wallet_temp[user_id]
        Type = wallet_db.type.value
        path = await (await wallet_db.wallet_detail).decrypt_path
        from importlib import import_module
        wallet_cls = import_module(f"tonpay.wallets.blockchain.{Type}").Wallet
        wallet: BaseWallet = await wallet_cls.find_wallet(path)
        await del_current_query_msg(update, context)
        await wallet.transfer(dest, amt, "any comment", "TON")
        await TransferMsg.success(update, context)
        await self.wallet(update, context, wallet=wallet_db, as_new_msg=True)
        return WALLET_DETAIL_ROUTE    
    
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        wallet_db: Wallet = self._selected_wallet_temp[user_id]
        await self.wallet(update, context, wallet=wallet_db)
        return WALLET_DETAIL_ROUTE
        


def main() -> None:
    main_handler = MainHandler()
    wallet = NewWalletHandler()
    wallet_detail = WalletDetailHandler()
    import_wallet = ImportWalletHandler()
    transfer = TransferHandler()
    # transaction = TransactionsHandler()
    
    application = Application.builder().token(TOKEN) \
                  .concurrent_updates(True).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", main_handler.start)],
        states={
            MAIN_ROUTE: [
                CallbackQueryHandler(main_handler.finance, pattern=f"^{FINANCE}$"),
                CallbackQueryHandler(main_handler.wallets, pattern=f"^{WALLETS}$"),
                CallbackQueryHandler(main_handler.wallet, pattern=f"^{WALLET_NAME}"),
                CallbackQueryHandler(main_handler.home, pattern=f"^{HOME}$"),
                CallbackQueryHandler(main_handler.back, pattern=f"^{BACK}$"),
                CallbackQueryHandler(main_handler.new_wallet, pattern=f"^{NEW_WALLET}$"),
                CallbackQueryHandler(main_handler.import_wallet, pattern=f"^{IMPORT}$")
            ],
            NEW_WALLET_ROUTE: [
                CallbackQueryHandler(wallet.Type, pattern=Utils.selectables2regex(blockchains)),
                CommandHandler("skip", wallet.skip),
                CommandHandler("cancel", wallet.cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, wallet.name),
                CallbackQueryHandler(wallet.back, pattern=f"^{BACK}$"),
                CallbackQueryHandler(wallet.home, pattern=f"^{HOME}$"),
            ],
            WALLET_DETAIL_ROUTE:[
                CallbackQueryHandler(wallet_detail.refresh_wallet, pattern=f"^{REFRESH}$"),
                CallbackQueryHandler(wallet_detail.qrcode, pattern=f"^{QRCODE}$"),
                CallbackQueryHandler(wallet_detail.transfer, pattern=f"^{TRANSFER}$"),
                CallbackQueryHandler(wallet_detail.seeds, pattern=f"^{SEEDS}$"),
                CallbackQueryHandler(wallet_detail.delete, pattern=f"^{DELETE}$"),
                CallbackQueryHandler(wallet_detail.back, pattern=f"^{BACK}$"),
                CallbackQueryHandler(wallet_detail.home, pattern=f"^{HOME}$"),
            ],
            IMPORT_WALLET_ROUTE: [
                CallbackQueryHandler(import_wallet.Type, 
                                     pattern=Utils.selectables2regex(blockchains)),
                MessageHandler(filters.TEXT & ~filters.COMMAND, import_wallet.seeds),
                CallbackQueryHandler(import_wallet.back, pattern=f"^{BACK}$"),
                CallbackQueryHandler(import_wallet.home, pattern=f"^{HOME}$"),
            ],
            IMPORT_WALLET_NAME_ROUTE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, import_wallet.name),
                CommandHandler("skip", import_wallet.skip),
                CommandHandler("cancel", import_wallet.cancel)
            ],
            QRCODE_ROUTE: [
                CallbackQueryHandler(wallet_detail.qrcode_back, pattern=f"^{BACK}$"),
                CallbackQueryHandler(wallet_detail.qrcode_home, pattern=f"^{HOME}$"),
            ],
            TRANSFER_ROUTE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, transfer.dest),
                CallbackQueryHandler(transfer.back, pattern=f"^{BACK}$"),
                CallbackQueryHandler(transfer.home, pattern=f"^{HOME}$"),
            ],
            TRANSFER_AMOUNT_ROUTE: [
                MessageHandler(filters.Regex(Utils.isFloat_regex) & ~filters.COMMAND,
                transfer.amount),
                CallbackQueryHandler(transfer.confirm, pattern=f"^{CONFIRM}$"),
                CallbackQueryHandler(transfer.cancel, pattern=f"^{CANCEL}$")
            ],
            TRANSACTIONS_ROUTE: [
            ]
        },
        fallbacks=[CommandHandler("start", main_handler.start)],
        conversation_timeout=60*4,
        per_chat=False
    )

    # Add ConversationHandler to application that will be used for handling updates
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES, timeout=30, 
                            drop_pending_updates=True)


if __name__ == "__main__":
    main()