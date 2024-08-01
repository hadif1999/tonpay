from sqlmodel import SQLModel, create_engine
from sqlalchemy.ext.asyncio import create_async_engine
import os
from . import Models
# from tonpay.database.Models import User, External_Wallet, Internal_Wallet
from loguru import logger
from sqlalchemy_utils import database_exists, create_database

ENGINE = create_engine(os.getenv("DB_URI", 
                                 "postgresql+psycopg2://postgres:secret@172.17.0.2:5432/tonpay.db"))

ASYNC_ENGINE = create_async_engine(os.getenv("DB_URI", 
                                  "postgresql+asyncpg://postgres:secret@172.17.0.2:5432/tonpay.db"))

def build_DB():
    if not database_exists(ENGINE.url):
        create_database(ENGINE.url)
    
    try: SQLModel.metadata.create_all(ASYNC_ENGINE)
    except: SQLModel.metadata.create_all(ENGINE)
    logger.info("initiated Database and tables")
    


    