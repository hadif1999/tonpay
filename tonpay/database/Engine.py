from sqlmodel import SQLModel, create_engine
from sqlalchemy.ext.asyncio import create_async_engine
import os
from . import Models
# from tonpay.database.Models import User, External_Wallet, Internal_Wallet
from loguru import logger
from sqlalchemy_utils import database_exists, create_database, drop_database
from tonpay.Defaults import options

URI_RAW = options.database.db_uri
isAsync = options.database.as_aync

if URI_RAW.startswith("postgresql://"):
    URI_async = URI_RAW.replace("postgresql://", "postgresql+asyncpg://")
    URI_sync = URI_RAW.replace("postgresql://", "postgresql+psycopg2://")    
else: raise ValueError("Database URI must start with 'postgresql://'")

ENGINE = create_engine(URI_sync)
ASYNC_ENGINE = create_async_engine(URI_async)


def build_DB(overwrite_db: bool = False):
    if not database_exists(ENGINE.url):
        create_database(ENGINE.url)
    else: 
        if overwrite_db: 
            drop_database(ENGINE.url)
            create_database(ENGINE.url) 
    
    try: SQLModel.metadata.create_all(ASYNC_ENGINE)
    except: SQLModel.metadata.create_all(ENGINE)
    logger.success("initiated Database and tables")
    


    