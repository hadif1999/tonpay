import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)

from messages import MainMenu_msg, wallets_msg, FinanceMenu_msg, wallet_msg
import os


# state and page names
HOME, WALLETS, WALLET, FINANCE, BACK = "home", "wallets", "wallet", "finance", "back"
MAIN_ROUTE, END_ROUTE = 0, 1
TOKEN = os.getenv("TOKEN", "7405744199:AAG1Th55Tt6jIa6FRG70_49AzLmwd4eGLtg")


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await MainMenu_msg(update, "eng")
    return MAIN_ROUTE


async def finance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account = fetch_account(chat_id)
    await FinanceMenu_msg(update, "eng", account.balance, account.balance_dollar )
    return MAIN_ROUTE
    
    
async def wallets(update: Update, context):
    account = await fetch_account(chat_id)
    _wallets = account.get_wallets(asdict = True) 
    # await update.callback_query.answer()
    await wallets_msg(update, _wallets, "eng")
    return MAIN_ROUTE

    
async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    wallet_name = query.data
    account = await fetch_account(chat_id) 
    _wallet = account.get_wallet(wallet_name)
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