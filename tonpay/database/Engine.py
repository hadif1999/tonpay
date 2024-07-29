from sqlmodel import SQLModel, create_engine
import os

ENGINE = create_engine(os.getenv("DB_URI", 
                                 "postgresql+psycopg2://127.0.0.1:5432/tonpay"))


def build_DB():
    SQLModel.metadata.create_all(ENGINE)
    