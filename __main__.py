from tonpay.Telegram.core import main
from tonpay.database.Engine import build_DB
from tonpay.database.Models import User, Wallet, TON_Wallet, Internal_Wallet
from dotenv import load_dotenv


if __name__ == "__main__":
    load_dotenv()
    build_DB(overwrite_db=True)
    main()
          