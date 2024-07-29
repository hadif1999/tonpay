import datetime as dt
from typing import Any, Literal
from sqlmodel import Field, SQLModel, Relationship, Session, select
from pydantic import EmailStr, PositiveFloat, validate_call
from sqlalchemy import JSON
from .Engine import ENGINE


# note: use __tablename__: str = name_in_database to change table name
class User(SQLModel, table=True):
    id: int|None = Field(primary_key=True,
                         min_length=5, max_length=100,
                         unique=True, default=None)
    chat_id: str = Field(index=True, unique=True, 
                         min_length=5, max_length=100)
    email: EmailStr|None = Field(min_length=5, max_length=200,
                                 unique=True, default=None)
    wallets: list["Wallet"] = Relationship(back_populates="user")
    
    
    def get(chat_id: str|int):
        with Session(ENGINE) as session:
            res = session.exec( select(__class__).where(__class__.chat_id == chat_id) )
            user = res.one()
            return user
        
        
    def get_wallet(self, address:str):
        wallets = self.wallets
            # fetching encrypted wallet
        wallets_enc = [_wallet for _wallet in wallets if _wallet.address == address]
        if wallets_enc == []: return None
        else: wallet_enc = wallets_enc[0] 
            # remaking wallet object
        if wallet_enc.is_external:
            KEY = fetch_key()
            org_seeds = decrypt( wallet_enc.seeds, KEY)
            wallet = wallet_from_seeds(org_seeds)
            wallet.is_external = True
            return wallet
        else:
            return wallet_enc
        
            

class Wallet(SQLModel):
    id: int|None = Field(primary_key=True,
                         min_length=5, max_length=100,
                         unique=True, default=None)
    date_created: dt.datetime = Field(default=dt.datetime.now(dt.UTC))
    chat_id: str = Field(index=True, unique=True, 
                         min_length=5, max_length=100)
    user: User = Relationship(back_populates="wallets")


# wallet on blockchain
class External_Wallet(Wallet, table=True):
    address: str = Field(unique=True,
                         min_length=10, max_length=200)
    seeds: str = Field(unique=True, # SHA256(chat_id:date_created("Y-M-D_H:MM:S"):salt)
                       min_length=10, max_length=1000) 
    is_external: bool = True


# wallet inside the platform
class Internal_Wallet(Wallet, table=True):
    balance: PositiveFloat = Field(min_value=0, default=0)
    address: str = Field(unique=True,  # SHA256(chat_id:date_created("Y-M-D_H:MM:S"))
                         min_length=10, max_length=1000)
    unit: Literal["TON", "mTON", "nTON"] = Field(default="nTON") # balance unit in mili-TON, nano-TON or TON
    is_external: bool = False
    

class Transaction_Side(SQLModel):
    address: str = Field(min_length=10, max_length=1000)
    chat_id: str = Field(min_length=10, max_length=100)


Transaction_QueryType = Literal["chat_id", "address"]
class Transaction(SQLModel, table=True):
    id: int|None = Field(primary_key=True,
                         min_length=5, max_length=100,
                         unique=True, default=None)
    src: Transaction_Side = Field(sa_column=Field(JSON)) # "src":{"address": --- , "chat_id": --- }
    dest: Transaction_Side = Field(sa_column=Field(JSON))  # "dest":{"address":---, "chat_id": --- }
    amount: PositiveFloat = Field(gt=0)
    datetime: dt.datetime = Field(default=dt.datetime.now(dt.UTC))
    transaction_id: str = Field(unique=True, # SHA256(src.address:dest.address:datetime("Y-M-D_H:MM:S"))
                                min_length=10, max_length=1000) 
    


    
    
    
    