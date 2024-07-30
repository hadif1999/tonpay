from sqlmodel import SQLModel, create_engine
from sqlalchemy.ext.asyncio import create_async_engine
import os


ENGINE = create_engine(os.getenv("DB_URI", 
                                 "postgresql+psycopg2://127.0.0.1:5432/tonpay"))

ASYNC_ENGINE = create_async_engine(os.getenv("DB_URI", 
                                             "postgresql+asyncpg://127.0.0.1:5432/tonpay"))

def build_DB():
    try: SQLModel.metadata.create_all(ASYNC_ENGINE)
    except: 
         SQLModel.metadata.create_all(ENGINE)
        
    