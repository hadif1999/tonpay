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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await MainMenu_msg(update, LANG)
    chat_id = str(update.effective_user.id)
    user: User = await User.get(chat_id)
    if not user: 
        new_user = User(chat_id = chat_id)
        await insert_row(new_user, True)
        new_user._logger.debug("user added")
    else: 
        user._logger.debug("user already exists")
    return MAIN_ROUTE


async def finance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_user.id)
    query = update.callback_query # getting input query
    user: User = await User.get(chat_id)          
    balance_ton = 0
    balance_USDT = 0
    for wallet in user.wallets:
        if wallet.unit == "TON": 
            balance_ton += wallet.balance # just ton balance
        balance_USDT += wallet.balance_USDT # balance for all wallets 
    user._logger.debug(f"balance calculated: {balance_ton}")
    await query.answer()
    await FinanceMenu_msg(update, LANG, balance_ton, balance_USDT)
    return MAIN_ROUTE
    
    
async def wallets(update: Update, context):
    chat_id = str(update.effective_user.id)
    user: User = await User.get(chat_id)
    _wallets = await user.dump_wallets(asjson=True, include_fields=["address"])
    user._logger.debug("fetched user wallets: {wallets}", wallets=list(_wallets.keys()) )
    await wallets_msg(update, _wallets, LANG)
    return MAIN_ROUTE

    
async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    wallet_name = query.data
    chat_id = str(update.effective_user.id)
    user: User = await User.get(chat_id)
    _logger = user._logger
    _wallet: Wallet = (await user.dump_wallets())[wallet_name]
    _logger.debug("fetched user wallet: {wallet}", wallet=_wallet.name )
    await wallet_msg(update, wallet_name, _wallet.balance, _wallet.address, LANG)
    return MAIN_ROUTE


async def home(update: Update, context):
    await MainMenu_msg(update, LANG)
    return MAIN_ROUTE


async def back(update: Update, context):
    pass
    return MAIN_ROUTE



def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).concurrent_updates(True).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_ROUTE: [
                CallbackQueryHandler(home, pattern=f"^{HOME}$"),
                CallbackQueryHandler(finance, pattern=f"^{FINANCE}$"),
                CallbackQueryHandler(wallets, pattern=f"^{WALLETS}$"),
                CallbackQueryHandler(wallet, pattern=f"^{WALLET}$"),
                CallbackQueryHandler(back, pattern=f"^{BACK}$")
            ]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    # Add ConversationHandler to application that will be used for handling updates
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()