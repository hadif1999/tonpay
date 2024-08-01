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
from database.Models import (User,
                            #  External_Wallet, Internal_Wallet,
                               AsyncSession, ASYNC_ENGINE, add_row)
from sqlmodel import select
from loguru import logger


# state and page names
HOME, WALLETS, WALLET, FINANCE, BACK = "home", "wallets", "wallet", "finance", "back"
MAIN_ROUTE, END_ROUTE = 0, 1
TOKEN = os.getenv("TOKEN", "7405744199:AAG1Th55Tt6jIa6FRG70_49AzLmwd4eGLtg")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await MainMenu_msg(update, "eng")
    chat_id = update.effective_user.id
    user = await User.get(chat_id)
    if not user: 
        user.logger.debug("user instance made")
        user = User(chat_id = chat_id)
        add_row(user)
    return MAIN_ROUTE


async def finance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_user.id
    user: User = await User.get(chat_id)
    # toDo: get balance by single unit e.g = "nTON"             
    balance_ton = sum([(await wallet.get_balance()) if wallet.is_external else wallet.balance
                        for wallet in user.wallets])
    user.logger.debug(f"balance calculated: {balance_ton}")
    # toDo: get_online price by ccxt and update Ton price in dollar
    balance_dollar = balance_ton
    await FinanceMenu_msg(update, "eng", balance_ton, balance_dollar )
    return MAIN_ROUTE
    
    
async def wallets(update: Update, context):
    chat_id = update.effective_user.id
    user: User = await User.get(chat_id)
    _wallets = {wal.name:wal for wal in user.wallets} 
    user.logger.debug("fetched user wallets: {wallets}", wallets=list(_wallets.keys()) )
    # await update.callback_query.answer()
    await wallets_msg(update, _wallets, "eng")
    return MAIN_ROUTE

    
async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    wallet_name = query.data
    chat_id = update.effective_user.id
    user: User = await User.get(chat_id)
    _wallets = {wal.name:wal for wal in user.wallets}
    _wallet = _wallets[wallet_name]
    user.logger.debug("fetched user wallet: {wallet}", wallet=_wallet.name )
    await query.answer()
    await wallet_msg(update, wallet_name, _wallet, "eng")
    return MAIN_ROUTE


async def home(update: Update, context):
    await MainMenu_msg(update, "eng")
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