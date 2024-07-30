import datetime as dt
from typing import Any, Literal
from sqlmodel import Field, SQLModel, Relationship, Session, select
from sqlmodel.ext.asyncio.session import AsyncSession

from pydantic import EmailStr, PositiveFloat, validate_call, PositiveInt
from sqlalchemy import JSON

from pytonlib.ton.client import TonlibClient
from .Engine import ASYNC_ENGINE
from random import randint, seed
import datetime as dt



# note: use __tablename__: str = name_in_database to change table name
class User(SQLModel, table=True):
    id: int|None = Field(primary_key=True,
                         min_length=5, max_length=100,
                         unique=True, default=None)
    chat_id: str = Field(index=True, unique=True, 
                         min_length=5, max_length=100)
    email: EmailStr|None = Field(min_length=5, max_length=200,
                                 unique=True, default=None)
    max_allowed_wallets: PositiveInt = Field(default=5, le=10, gt=0)
    payment_gateway_active: bool = False
    wallets: list["Wallet"] = Relationship(back_populates="user")
    
    
    async def get(chat_id: str|int):
        async with AsyncSession(ASYNC_ENGINE) as session:
            res = await session.exec( select(__class__).where(__class__.chat_id == chat_id) )
            user = res.one()
            return user
        
        
    async def get_wallet(self, address:str):
        from ton.sync import TonlibClient
            # fetching encrypted wallet
        async with AsyncSession(ASYNC_ENGINE) as session:
            res = await session.exec( select(Wallet).where(Wallet.address == address))
            wallet_enc = res.one()
            # remaking wallet object
        if wallet_enc.is_external:
            from ..Encryption import Symmetric
            from .. import config
            
            KEY_raw:str = config["wallet_encryption"]["SYMMETRIC_KEY"]
            salt:str = config["wallet_encryption"]["salt"]
            dt_fmt = config["wallet_encryption"].get("datetime_format", "%Y-%m-%y_%H:%M:%S") # toDo: dt format
            KEY = KEY_raw.format(chat_id=wallet_enc.chat_id,
                                 datetime=wallet_enc.date_created.strftime(dt_fmt),
                                 salt=salt, address=wallet_enc.address)
            org_seeds = Symmetric(KEY).decrypt(wallet_enc.seeds)
            # getting a tonlib client
            # toDo add tonlib CLient to a moudule as get_client()
            client = TonlibClient()
            TonlibClient.enable_unaudited_binaries()
            await client.init_tonlib()
            wallet = await client.find_account(org_seeds) # fetching wallet
            wallet.is_external = True
            return wallet
        else:
            return wallet_enc
        
    
    async def add_wallet(self, *, name:str|None = None,
                         is_external:bool = True, throw_exp: bool = False):
        allowed = len(self.wallets) <= self.max_allowed_wallets
        if throw_exp: assert allowed, "max wallets reached"
        if is_external:
            # getting a tonlib client
            client = TonlibClient()
            TonlibClient.enable_unaudited_binaries()
            await client.init_tonlib()
            wallet  = await client.create_wallet()
            seeds = await wallet.export()
            addr = wallet.address
            from .. import config
            # toDo: add external wallet name as constants.default.wallet.name
            _dt = dt.datetime.now(dt.UTC).strftime("%Y-%m-%y_%H:%M:%S")
            KEY_raw:str = config["wallet_encryption"]["SYMMETRIC_KEY"]
            salt:str = config["wallet_encryption"]["salt"]
            dt_fmt = config["wallet_encryption"].get("datetime_format", "%Y-%m-%y_%H:%M:%S")
            KEY = KEY_raw.format(chat_id=self.chat_id,
                        datetime=_dt.strftime(dt_fmt),
                        salt=salt, address=addr)
            from ..Encryption import Symmetric
            KEY_enc = Symmetric(KEY).encrypt(seeds)
            name = name if name else f"Ton_Wallet_{_dt}_{self.chat_id[:4]}"
            wallet_db = External_Wallet(chat_id=self.chat_id, name=name, 
                                        address=addr, seeds=KEY_enc)
            async with AsyncSession(ASYNC_ENGINE) as session:
                session.add(wallet_db)
                await session.commit()
                await session.refresh()
        else: 
            name = name if name else f"Ton_Wallet_{_dt}_{self.chat_id[:4]}"
            # addr = SHA256(chat_id:date_created("Y-M-D_H:MM:S"):salt)
            Internal_Wallet(chat_id=self.chat_id, name=name, address="addr")
            
            
             
            

class Wallet(SQLModel):
    id: int|None = Field(primary_key=True,
                         min_length=5, max_length=100,
                         unique=True, default=None)
    date_created: dt.datetime = Field(default=dt.datetime.now(dt.UTC))
    chat_id: str = Field(index=True, unique=True, 
                         min_length=5, max_length=100)
    ######### toDo: add wallet name to each wallet class
    ######## toDo: add strftime format to constants.formats module
    name:str = Field(default="Wallet_"+str(date_created.strftime("%Y-%m-%y_%H:%M:%S_"))+str(chat_id)[:4],
                     index=True)
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
    


    
    
    
    