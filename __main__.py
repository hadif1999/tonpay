from tonpay.Telegram.core import main, User
from tonpay.database.Engine import build_DB


if __name__ == "__main__":
    build_DB(overwrite_db=True)
    main()
    